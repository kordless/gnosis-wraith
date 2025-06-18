import os
import re
import base64
import logging
import asyncio
from typing import List, Dict, Any, Optional, Union

from core.browser import BrowserControl
# from ai.processing import process_with_llm  # Moved to provider-specific modules
from core.markdown_generation import DefaultMarkdownGenerator, PruningContentFilter

# Get logger
logger = logging.getLogger("gnosis_wraith")


# URL extraction function
def extract_urls(content: str) -> List[str]:
    """Extract URLs from the given content."""
    url_pattern = re.compile(r'https?://\S+')
    return url_pattern.findall(content)

async def crawl_url(
    url: str,
    javascript_enabled: bool = True,
    javascript_payload: Optional[str] = None,
    screenshot_mode: Optional[str] = None,  # 'top', 'full', or None/off
    wait_time: int = 3000,
    timeout: int = 30000,
    user_email: Optional[str] = None,
    wait_before_js: int = 2000,
    wait_after_js: int = 1000,
    js_timeout: int = 30000
) -> Dict[str, Any]:

    """
    Opens one URL in the browser and returns the results asked for.
    
    Args:
        url: The URL to crawl
        javascript_enabled: Whether to enable JavaScript in the browser
        javascript_payload: Optional JavaScript code to inject after page load
        screenshot_mode: Screenshot capture mode - 'top' (viewport), 'full' (entire page), or None (no screenshot)
        wait_time: Time to wait for page to load (milliseconds)
        timeout: Maximum time for page load (milliseconds)
        user_email: Optional user email for tracking
        wait_before_js: Time to wait before JS execution (milliseconds)
        wait_after_js: Time to wait after JS execution (milliseconds)
        js_timeout: Maximum execution time for JavaScript (milliseconds)
    
    Returns:
        A dictionary containing:
            - success: bool
            - url: str
            - title: str
            - html_content: str
            - javascript_enabled: bool
            - javascript_result: Any (result of JS execution if provided)
            - screenshot_data: str (base64 encoded PNG data) or None
            - screenshot_format: str ("base64") or None
            - user_email: str or None
            - content_length: int
            - execution_time: int (if JS was executed)
    """


    browser = None
    try:
        # Initialize browser
        browser = BrowserControl()
        await browser.start_browser(javascript_enabled=javascript_enabled)
        
        # Navigate to URL with timeout
        logger.info(f"Crawling URL: {url}")
        await browser.navigate(url, javascript_enabled=javascript_enabled, timeout=timeout)


        
        # Wait for page to stabilize
        if wait_time > 0:
            await asyncio.sleep(wait_time / 1000)
        
        # Execute custom JavaScript if provided
        js_result = None
        execution_time = None
        if javascript_payload and javascript_enabled:
            try:
                # Wait before execution if specified
                if wait_before_js > 0:
                    await asyncio.sleep(wait_before_js / 1000)
                
                # Wrap the code for execution with timeout and error handling
                wrapped_code = _wrap_code_for_execution(javascript_payload, js_timeout)
                
                logger.info("Executing custom JavaScript with enhanced wrapper")
                result = await browser.page.evaluate(wrapped_code)
                
                # Wait after execution if specified
                if wait_after_js > 0:
                    await asyncio.sleep(wait_after_js / 1000)
                
                # Process the result
                if isinstance(result, dict):
                    if 'error' in result:
                        js_result = {"error": result['error'], "success": False}
                        execution_time = result.get('executionTime', 0)
                    else:
                        js_result = result.get('result')
                        execution_time = result.get('executionTime', 0)
                else:
                    js_result = result
                    
            except Exception as e:
                logger.error(f"JavaScript execution error: {str(e)}")
                js_result = {"error": str(e), "success": False}

        
        # Get HTML content (after JS execution if any)
        html_content = await browser.page.content()
        
        # Get page title
        title = await browser.page.title()
        
        # Take screenshot if requested
        screenshot_data = None
        screenshot_error = None
        if screenshot_mode in ['top', 'full']:
            try:
                logger.info(f"Taking {screenshot_mode} screenshot")
                
                # Take screenshot as bytes
                screenshot_bytes = await browser.page.screenshot(
                    full_page=(screenshot_mode == 'full')
                )
                
                # Encode to base64
                screenshot_data = base64.b64encode(screenshot_bytes).decode('utf-8')
                logger.info(f"Screenshot captured: {len(screenshot_bytes)} bytes")
                
            except Exception as e:
                logger.error(f"Screenshot error: {str(e)}")
                screenshot_error = str(e)


        # Prepare result
        result = {
            "success": True,
            "url": url,
            "title": title,
            "html_content": html_content,
            "javascript_enabled": javascript_enabled,
            "javascript_result": js_result,
            "screenshot_data": screenshot_data,
            "screenshot_format": "base64" if screenshot_data else None,
            "user_email": user_email,
            "content_length": len(html_content)
        }
        
        # Add optional fields if they exist
        if execution_time is not None:
            result["execution_time"] = execution_time
        if screenshot_error:
            result["screenshot_error"] = screenshot_error

        return result


        
    except Exception as e:
        logger.error(f"Crawl error for {url}: {str(e)}")
        return {
            "success": False,
            "url": url,
            "error": str(e),
            "javascript_enabled": javascript_enabled,
            "user_email": user_email
        }
    finally:
        if browser:
            await browser.close()

def _wrap_code_for_execution(code: str, timeout: int) -> str:
    """
    Wrap user code with timeout and error handling.
    """
    return f"""
(async function() {{
    const startTime = Date.now();
    const timeout = {timeout};
    
    // Create a promise that rejects after timeout
    const timeoutPromise = new Promise((_, reject) => {{
        setTimeout(() => reject(new Error('Execution timeout')), timeout);
    }});
    
    // Create a promise that executes the user code
    const codePromise = new Promise((resolve, reject) => {{
        try {{
            // User code execution
            const result = (function() {{
                {code}
            }})();
            
            // Handle async results
            Promise.resolve(result).then(resolve).catch(reject);
        }} catch (error) {{
            reject(error);
        }}
    }});
    
    try {{
        // Race between code execution and timeout
        const result = await Promise.race([codePromise, timeoutPromise]);
        const executionTime = Date.now() - startTime;
        
        return {{
            success: true,
            result: result,
            executionTime: executionTime
        }};
    }} catch (error) {{
        return {{
            success: false,
            error: error.message || 'Unknown error',
            executionTime: Date.now() - startTime
        }};
    }}
}})();
"""


# screenshot
async def capture_screenshot(

    url: str,
    screenshot_mode: str = 'full',  # 'top' or 'full'
    wait_time: int = 3000,
    timeout: int = 30000,
    user_email: Optional[str] = None
) -> Dict[str, Any]:
    """
    Capture a screenshot of a webpage.
    
    Args:
        url: The URL to capture
        screenshot_mode: Screenshot capture mode - 'top' (viewport) or 'full' (entire page)
        wait_time: Time to wait for page to load (milliseconds)
        timeout: Maximum time for page load (milliseconds)
        user_email: Optional user email for tracking
    
    Returns:
        A dictionary containing:
            - success: bool
            - url: str
            - title: str
            - screenshot_data: str (base64 encoded PNG data) or None
            - screenshot_format: str ("base64") or None
            - user_email: str or None
    """
    browser = None
    try:
        # Initialize browser
        browser = BrowserControl()
        await browser.start_browser(javascript_enabled=True)
        
        # Navigate to URL with timeout
        logger.info(f"Capturing screenshot for URL: {url}")
        await browser.navigate(url, javascript_enabled=True, timeout=timeout)


        
        # Wait for page to stabilize
        if wait_time > 0:
            await asyncio.sleep(wait_time / 1000)
        
        # Get page title
        title = await browser.page.title()
        
        # Take screenshot
        screenshot_data = None
        try:
            logger.info(f"Taking {screenshot_mode} screenshot")
            
            # Take screenshot as bytes
            screenshot_bytes = await browser.page.screenshot(
                full_page=(screenshot_mode == 'full')
            )
            
            # Encode to base64
            screenshot_data = base64.b64encode(screenshot_bytes).decode('utf-8')
            logger.info(f"Screenshot captured: {len(screenshot_bytes)} bytes")
            
        except Exception as e:
            logger.error(f"Screenshot error: {str(e)}")
            screenshot_data = None
        
        # Prepare result
        result = {
            "success": True,
            "url": url,
            "title": title,
            "screenshot_data": screenshot_data,
            "screenshot_format": "base64" if screenshot_data else None,
            "user_email": user_email
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Screenshot capture error for {url}: {str(e)}")
        return {
            "success": False,
            "url": url,
            "error": str(e),
            "screenshot_data": None,
            "screenshot_format": None,
            "user_email": user_email
        }
    finally:
        if browser:
            await browser.close()

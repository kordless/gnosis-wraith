"""JavaScript execution handler for browser automation"""
import json
import asyncio
import logging
from typing import Dict, Any, Optional
from core.browser import BrowserControl
from ai.validators.javascript_validator import JavaScriptValidator

logger = logging.getLogger("gnosis_wraith")

class JavaScriptExecutor:
    """Handles JavaScript execution in browser context"""
    
    def __init__(self):
        self.validator = JavaScriptValidator()
    
    async def execute_javascript(
        self,
        url: str,
        javascript_code: str,
        wait_before: int = 2000,
        wait_after: int = 1000,
        timeout: int = 30000,
        take_screenshot: bool = False,
        screenshot_options: Optional[Dict[str, Any]] = None,
        extract_markdown: bool = False,
        markdown_options: Optional[Dict[str, Any]] = None,
        user_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute JavaScript code on a webpage.
        
        Args:
            url: Target URL
            javascript_code: JavaScript code to execute
            wait_before: Time to wait before execution (ms)
            wait_after: Time to wait after execution (ms)
            timeout: Maximum execution time (ms)
            take_screenshot: Whether to capture screenshot after execution
            screenshot_options: Options for screenshot (full_page, format, etc.)
            extract_markdown: Whether to extract markdown from the DOM after execution
            markdown_options: Options for markdown extraction
            user_email: User email for tracking
            
        Returns:
            Execution results with optional screenshot and markdown
        """
        browser = None
        try:
            # Validate the JavaScript code first
            is_safe, violations = self.validator.validate(javascript_code)
            if not is_safe:
                return {
                    'success': False,
                    'error': 'JavaScript code failed safety validation',
                    'violations': violations
                }
            
            # Initialize browser
            browser = BrowserControl()
            await browser.start_browser(javascript_enabled=True)
            
            # Navigate to the URL
            await browser.navigate(url, javascript_enabled=True)
            
            # Wait before execution if specified
            if wait_before > 0:
                await asyncio.sleep(wait_before / 1000)
            
            # Wrap the code for execution with timeout and error handling
            wrapped_code = self._wrap_code_for_execution(javascript_code, timeout)
            
            # Execute the JavaScript
            logger.info(f"Executing JavaScript on {url}")
            result = await browser.page.evaluate(wrapped_code)
            
            # Wait after execution if specified
            if wait_after > 0:
                await asyncio.sleep(wait_after / 1000)
            
            # Process the result
            if isinstance(result, dict) and 'error' in result:
                return {
                    'success': False,
                    'error': result['error'],
                    'url': url
                }
            
            response = {
                'success': True,
                'result': result,
                'url': url,
                'execution_time': result.get('executionTime', 0) if isinstance(result, dict) else 0
            }
            
            # Take screenshot if requested
            if take_screenshot:
                try:
                    logger.info("Taking screenshot after JavaScript execution")
                    screenshot_opts = screenshot_options or {}
                    
                    # Default screenshot options
                    full_page = screenshot_opts.get('full_page', True)
                    screenshot_bytes = await browser.page.screenshot(full_page=full_page)
                    
                    # Convert to base64
                    import base64
                    screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                    
                    # Add screenshot to response
                    response['screenshot'] = {
                        'data': screenshot_base64,
                        'format': 'png',
                        'full_page': full_page,
                        'size': len(screenshot_bytes)
                    }
                    
                    logger.info(f"Screenshot captured: {len(screenshot_bytes)} bytes")
                except Exception as e:
                    logger.error(f"Screenshot capture error: {str(e)}")
                    response['screenshot_error'] = str(e)
            
            # Extract markdown if requested
            if extract_markdown:
                try:
                    logger.info("Extracting markdown from DOM after JavaScript execution")
                    
                    # Get the HTML content from the page
                    html_content = await browser.page.content()
                    
                    # Convert HTML to markdown using the available tools
                    from core.markdown_generation import DefaultMarkdownGenerator
                    
                    markdown_opts = markdown_options or {}
                    
                    # Create markdown generator
                    generator = DefaultMarkdownGenerator()
                    
                    # Generate markdown from the current page HTML
                    markdown_result = generator.generate_markdown(
                        html_content,
                        base_url=url,
                        ignore_links=not markdown_opts.get('include_links', True),
                        ignore_images=not markdown_opts.get('include_images', True)
                    )
                    
                    # Get the appropriate markdown content
                    if markdown_opts.get('extract_main_content', True) and markdown_result.fit_markdown:
                        markdown_content = markdown_result.fit_markdown
                    else:
                        markdown_content = markdown_result.raw_markdown
                    
                    # Add markdown to response
                    response['markdown'] = {
                        'content': markdown_content,
                        'length': len(markdown_content),
                        'options': markdown_opts
                    }
                    
                    logger.info(f"Markdown extracted: {len(markdown_content)} characters")
                except Exception as e:
                    logger.error(f"Markdown extraction error: {str(e)}")
                    response['markdown_error'] = str(e)
            
            return response
            
        except Exception as e:
            logger.error(f"JavaScript execution error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'url': url
            }
        finally:
            if browser:
                await browser.close()
    
    async def execute_javascript_batch(
        self,
        urls: list,
        javascript_code: str,
        concurrent: int = 3,
        **execution_options
    ) -> Dict[str, Any]:
        """
        Execute JavaScript on multiple URLs.
        
        Args:
            urls: List of target URLs
            javascript_code: JavaScript code to execute
            concurrent: Number of concurrent executions
            **execution_options: Additional options passed to execute_javascript
            
        Returns:
            Batch execution results
        """
        # Validate the JavaScript code first
        is_safe, violations = self.validator.validate(javascript_code)
        if not is_safe:
            return {
                'success': False,
                'error': 'JavaScript code failed safety validation',
                'violations': violations
            }
        
        results = []
        errors = []
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(concurrent)
        
        async def execute_on_url(url):
            async with semaphore:
                try:
                    result = await self.execute_javascript(
                        url=url,
                        javascript_code=javascript_code,
                        **execution_options
                    )
                    results.append(result)
                    if not result['success']:
                        errors.append(result)
                except Exception as e:
                    error_result = {
                        'success': False,
                        'url': url,
                        'error': str(e)
                    }
                    results.append(error_result)
                    errors.append(error_result)
        
        # Execute on all URLs
        await asyncio.gather(*[execute_on_url(url) for url in urls])
        
        return {
            'success': len(errors) == 0,
            'total': len(urls),
            'successful': len(urls) - len(errors),
            'failed': len(errors),
            'results': results
        }
    
    def _wrap_code_for_execution(self, code: str, timeout: int) -> str:
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
    
    def validate_code(self, code: str) -> Dict[str, Any]:
        """
        Validate JavaScript code without executing it.
        """
        is_safe, violations = self.validator.validate(code)
        
        return {
            'is_safe': is_safe,
            'violations': violations,
            'safe_code': self.validator.sanitize_for_execution(code) if is_safe else None
        }
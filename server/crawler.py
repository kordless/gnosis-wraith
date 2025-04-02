import os
import re
import uuid
import logging
import asyncio
from typing import List, Dict, Any, Optional

from server.browser import BrowserControl
from ai.processing import process_with_llm

# Get logger and config path
logger = logging.getLogger("webwraith")
SCREENSHOTS_DIR = os.environ.get('WEBWRAITH_SCREENSHOTS_DIR', os.path.join(os.path.expanduser("~"), ".webwraith/screenshots"))

# URL extraction function
def extract_urls(content: str) -> List[str]:
    """Extract URLs from the given content."""
    url_pattern = re.compile(r'https?://\S+')
    return url_pattern.findall(content)

async def crawl_url(url: str, browser_control: BrowserControl, javascript_enabled: bool = False) -> Dict[str, Any]:
    """Crawl a single URL and return the results with better error handling."""
    # Create a safe filename from the URL
    filename = url.replace('https://', '').replace('http://', '').replace('/', '_').replace('.', '_')
    filename = re.sub(r'[^\w\-_.]', '_', filename)
    screenshot_path = os.path.join(SCREENSHOTS_DIR, f"{filename}_{uuid.uuid4().hex[:8]}.png")
    
    try:
        logger.info(f"Attempting to navigate to {url}")
        try:
            await browser_control.navigate(url)
            logger.info(f"Successfully navigated to {url}")
        except Exception as nav_error:
            logger.error(f"Navigation failed for {url}: {str(nav_error)}")
            # Continue with a blank page instead of failing
            await browser_control.page.set_content(f"<html><body><h1>Failed to load {url}</h1><p>Error: {str(nav_error)}</p></body></html>")
            
        # Take screenshot even if navigation failed
        try:
            await browser_control.screenshot(screenshot_path)
            logger.info(f"Screenshot saved at {screenshot_path}")
        except Exception as ss_error:
            logger.error(f"Screenshot failed for {url}: {str(ss_error)}")
            # Create a simple error image
            with open(screenshot_path, 'w') as f:
                f.write("Error capturing screenshot")
        
        # Extract text from the screenshot if it exists
        extracted_text = ""
        if os.path.exists(screenshot_path):
            try:
                extracted_text = await browser_control.extract_text_from_screenshot(screenshot_path)
                logger.info(f"Text extraction complete for {url}")
            except Exception as ocr_error:
                logger.error(f"OCR failed for {url}: {str(ocr_error)}")
                extracted_text = f"Text extraction failed: {str(ocr_error)}"
        
        # Get page title safely
        title = "Untitled Page"
        try:
            title = await browser_control.page.title()
            logger.info(f"Retrieved page title: '{title}' for {url}")
        except Exception as title_error:
            logger.error(f"Failed to get title for {url}: {str(title_error)}")
        
        return {
            'url': url,
            'title': title,
            'screenshot': screenshot_path,
            'extracted_text': extracted_text,
            'javascript_enabled': javascript_enabled  # Include JavaScript setting in result
        }
        
    except Exception as e:
        logger.error(f"Unhandled error processing {url}: {str(e)}", exc_info=True)
        # Return a basic error result
        return {
            'url': url,
            'error': f"Processing failed: {str(e)}",
            'screenshot': None,
            'extracted_text': '',
            'javascript_enabled': javascript_enabled  # Include JavaScript setting in result
        }

async def crawl_urls(urls: List[str], javascript_enabled: bool = False, 
                    llm_provider: Optional[str] = None, llm_token: Optional[str] = None) -> List[Dict[str, Any]]:
    """Crawl each URL and take screenshots, returning results."""
    browser_control = BrowserControl()
    try:
        logger.info(f"Starting browser for crawling URLs with JavaScript {'enabled' if javascript_enabled else 'disabled'}")
        await browser_control.start_browser(javascript_enabled=javascript_enabled)
        
        results = []
        for url in urls:
            try:
                logger.info(f"Processing URL: {url}")
                result = await crawl_url(url, browser_control, javascript_enabled=javascript_enabled)
                
                # Process extracted text with LLM if provider is specified
                if llm_provider and 'extracted_text' in result and result['extracted_text']:
                    try:
                        llm_summary = await process_with_llm(result['extracted_text'], llm_provider, llm_token)
                        result['llm_summary'] = llm_summary
                        result['llm_provider'] = llm_provider
                    except Exception as llm_error:
                        logger.error(f"LLM processing error: {str(llm_error)}")
                        result['llm_error'] = str(llm_error)
                
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing URL {url}: {str(e)}", exc_info=True)
                results.append({
                    'url': url,
                    'error': f"Processing error: {str(e)}",
                    'javascript_enabled': javascript_enabled  # Include JavaScript setting in result
                })
    finally:
        # Ensure browser is always closed
        try:
            logger.info("Closing browser after URL processing")
            await browser_control.close()
        except Exception as e:
            logger.error(f"Error closing browser: {str(e)}")
    
    return results
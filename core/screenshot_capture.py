"""Screenshot capture functionality"""
import base64
import logging
from typing import Dict, Any, Optional
from core.browser import BrowserControl

logger = logging.getLogger("gnosis_wraith")

async def capture_screenshot(
    url: str,
    full_page: bool = True,
    wait_for: int = 2000,
    quality: int = 90,
    clip: Optional[Dict[str, int]] = None,
    user_email: Optional[str] = None
) -> Dict[str, Any]:
    """
    Capture a screenshot of a webpage.
    
    Args:
        url: Target URL
        full_page: Whether to capture full page or viewport only
        wait_for: Time to wait before capture (ms)
        quality: Image quality (1-100)
        clip: Optional clipping rectangle
        user_email: User email for tracking
        
    Returns:
        Screenshot data including base64, bytes, dimensions, etc.
    """
    browser = None
    try:
        # Initialize browser
        browser = BrowserControl()
        await browser.start_browser(javascript_enabled=True)
        
        # Navigate to URL
        await browser.navigate(url, javascript_enabled=True)
        
        # Wait if specified
        if wait_for > 0:
            import asyncio
            await asyncio.sleep(wait_for / 1000)
        
        # Take screenshot
        screenshot_options = {
            'full_page': full_page,
            'quality': quality
        }
        
        if clip:
            screenshot_options['clip'] = clip
        
        # Capture to bytes
        screenshot_bytes = await browser.page.screenshot(**screenshot_options)
        
        # Get page dimensions
        dimensions = await browser.page.evaluate("""() => ({
            width: document.documentElement.scrollWidth,
            height: document.documentElement.scrollHeight,
            viewportWidth: window.innerWidth,
            viewportHeight: window.innerHeight
        })""")
        
        # Convert to base64
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        
        # Generate filename
        from urllib.parse import urlparse
        import datetime
        domain = urlparse(url).netloc.replace('www.', '').replace('.', '_')
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{domain}_{timestamp}.png"
        
        return {
            'base64': screenshot_base64,
            'bytes': screenshot_bytes,
            'filename': filename,
            'width': dimensions['viewportWidth'] if not full_page else dimensions['width'],
            'height': dimensions['viewportHeight'] if not full_page else dimensions['height'],
            'capture_time': datetime.datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Screenshot capture error: {str(e)}")
        raise
    finally:
        if browser:
            await browser.close()
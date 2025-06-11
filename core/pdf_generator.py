"""PDF generation functionality"""
import logging
from typing import Optional, Dict, Any
from core.browser import BrowserControl

logger = logging.getLogger("gnosis_wraith")

async def generate_pdf(
    url: str,
    format: str = 'A4',
    landscape: bool = False,
    print_background: bool = True,
    margin: Optional[Dict[str, str]] = None,
    wait_for: int = 2000,
    user_email: Optional[str] = None
) -> bytes:
    """
    Generate a PDF from a webpage.
    
    Args:
        url: Target URL
        format: Paper format (A4, Letter, etc.)
        landscape: Whether to use landscape orientation
        print_background: Whether to print background graphics
        margin: Page margins
        wait_for: Time to wait before generation (ms)
        user_email: User email for tracking
        
    Returns:
        PDF bytes
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
        
        # Prepare PDF options
        pdf_options = {
            'format': format,
            'landscape': landscape,
            'print_background': print_background
        }
        
        if margin:
            pdf_options['margin'] = margin
        
        # Generate PDF
        pdf_bytes = await browser.page.pdf(**pdf_options)
        
        logger.info(f"Generated PDF for {url}, size: {len(pdf_bytes)} bytes")
        
        return pdf_bytes
        
    except Exception as e:
        logger.error(f"PDF generation error: {str(e)}")
        raise
    finally:
        if browser:
            await browser.close()
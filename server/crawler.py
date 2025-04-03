import os
import re
import uuid
import logging
import asyncio
from typing import List, Dict, Any, Optional

from server.browser import BrowserControl
from ai.processing import process_with_llm

# Get logger and config path
logger = logging.getLogger("gnosis_wraith")
SCREENSHOTS_DIR = os.environ.get('GNOSIS_WRAITH_SCREENSHOTS_DIR', os.path.join(os.path.expanduser("~"), ".gnosis-wraith/screenshots"))

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
        
        # Get page content and extract HTML
        html_content = ""
        try:
            html_content = await browser_control.page.content()
            logger.info(f"Retrieved HTML content for {url}")
        except Exception as html_error:
            logger.error(f"Failed to get HTML content for {url}: {str(html_error)}")
        
        # Get page title safely
        title = "Untitled Page"
        try:
            title = await browser_control.page.title()
            logger.info(f"Retrieved page title: '{title}' for {url}")
        except Exception as title_error:
            logger.error(f"Failed to get title for {url}: {str(title_error)}")
        
        # Perform content filtering for more relevant text
        filtered_content = extracted_text
        if html_content:
            try:
                # Basic content filtering - could be expanded with more sophisticated approaches
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Remove script, style elements
                for s in soup(['script', 'style', 'noscript', 'iframe', 'header', 'footer', 'nav']):
                    s.decompose()
                
                # Prioritize certain elements
                important_content = []
                
                # Add title with higher importance
                if title and title != "Untitled Page":
                    important_content.append(f"# {title}")
                
                # Extract headings
                for idx, h in enumerate(soup.find_all(['h1', 'h2', 'h3', 'h4'])):
                    if h.text.strip():
                        if h.name == 'h1':
                            prefix = '# '
                        elif h.name == 'h2':
                            prefix = '## '
                        elif h.name == 'h3':
                            prefix = '### '
                        else:
                            prefix = '#### '
                        important_content.append(f"{prefix}{h.text.strip()}")
                
                # Extract paragraph content
                for p in soup.find_all(['p', 'div', 'article', 'section']):
                    text = p.get_text().strip()
                    if len(text) > 50:  # Only include substantial paragraphs
                        important_content.append(text)
                
                # If important content was found, use it instead of raw extracted text
                if important_content:
                    filtered_content = "\n\n".join(important_content)
            except Exception as filter_error:
                logger.error(f"Content filtering failed for {url}: {str(filter_error)}")
        
        return {
            'url': url,
            'title': title,
            'screenshot': screenshot_path,
            'extracted_text': extracted_text,
            'filtered_content': filtered_content,
            'html_content': html_content,
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
            'filtered_content': '',
            'html_content': '',
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
                
                # Process content with LLM if provider is specified
                if llm_provider and llm_token:
                    # Determine what content to send to the LLM - prefer filtered content if available
                    content_for_llm = result.get('filtered_content') or result.get('extracted_text') or ""
                    
                    if content_for_llm:
                        try:
                            # Process with LLM
                            llm_summary = await process_with_llm(content_for_llm, llm_provider, llm_token)
                            result['llm_summary'] = llm_summary
                            result['llm_provider'] = llm_provider
                            
                            # Process with a different prompt that focuses on key information
                            try:
                                extraction_prompt = f"""Extract the key information from this content as a structured summary. 
                                Focus on main topics, key facts, and important details.
                                
                                Content:
                                {content_for_llm[:4000]}  # Limiting to first 4000 chars to avoid token limits
                                
                                Format the response as bullet points.
                                """
                                llm_key_points = await process_with_llm(extraction_prompt, llm_provider, llm_token)
                                result['llm_key_points'] = llm_key_points
                            except Exception as extract_error:
                                logger.error(f"Key points extraction error: {str(extract_error)}")
                                
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
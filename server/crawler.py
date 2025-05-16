import os
import re
import uuid
import logging
import asyncio
from typing import List, Dict, Any, Optional, Union

from server.browser import BrowserControl
from ai.processing import process_with_llm
from server.markdown_generation import DefaultMarkdownGenerator, PruningContentFilter

# Get logger and config path
logger = logging.getLogger("gnosis_wraith")
SCREENSHOTS_DIR = os.environ.get('GNOSIS_WRAITH_SCREENSHOTS_DIR', os.path.join(os.path.expanduser("~"), ".gnosis-wraith/screenshots"))

# URL extraction function
def extract_urls(content: str) -> List[str]:
    """Extract URLs from the given content."""
    url_pattern = re.compile(r'https?://\S+')
    return url_pattern.findall(content)

async def crawl_url(url: Union[str, List[str]], 
                   javascript_enabled: bool = False, 
                   take_screenshot: bool = True, 
                   ocr_extraction: bool = True, 
                   markdown_extraction: str = "enhanced",
                   llm_provider: Optional[str] = None,
                   llm_token: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Crawl one or more URLs and return the results with better error handling.
    
    Args:
        url: A single URL string or a list of URL strings to crawl
        javascript_enabled: Whether to enable JavaScript for the crawl
        take_screenshot: Whether to take screenshots of pages
        ocr_extraction: Whether to extract text from screenshots using OCR
        markdown_extraction: Type of markdown to generate ("enhanced", "basic", or "none")
        llm_provider: Optional LLM provider for content summarization
        llm_token: Optional API token for the LLM provider
        
    Returns:
        A single result dictionary or a list of result dictionaries
    """
    # Convert single URL to list for consistent handling
    # Make sure url is a string or list, not another type
    if not isinstance(url, (str, list)):
        logger.error(f"Invalid URL type: {type(url)}. Expected string or list.")
        return {
            "url": str(url),
            "title": "Error: Invalid URL",
            "error": f"Invalid URL type: {type(url)}. Expected string or list."
        }
    
    # Explicit type conversion but preserve False values
    if isinstance(take_screenshot, str):
        take_screenshot = take_screenshot.lower() == 'true'
    # Only apply bool() if not already False - prevents false->True conversion
    if take_screenshot is not False:
        take_screenshot = bool(take_screenshot)
    
    urls = [url] if isinstance(url, str) else url
    
    # Log the crawl parameters
    logger.info(f"crawl_url called with {len(urls)} URLs")
    logger.info(f"Parameters: javascript_enabled={javascript_enabled}, take_screenshot={take_screenshot}, "
               f"ocr_extraction={ocr_extraction}, markdown_extraction={markdown_extraction}")
    
    # Ensure OCR is not used if no screenshot is taken
    if not take_screenshot:
        ocr_extraction = False
        logger.info("OCR extraction disabled because screenshots are disabled")
    
    # Start browser
    browser_control = BrowserControl()
    results = []
    
    try:
        logger.info(f"Starting browser with JavaScript {'enabled' if javascript_enabled else 'disabled'}")
        await browser_control.start_browser(javascript_enabled=javascript_enabled)
        
        # Process each URL
        for url in urls:
            try:
                # Create a safe filename from the URL
                filename = url.replace('https://', '').replace('http://', '').replace('/', '_').replace('.', '_')
                filename = re.sub(r'[^\w\-_.]', '_', filename)
                
                try:
                    # Navigate to the URL
                    logger.info(f"Navigating to {url}")
                    await browser_control.navigate(url, javascript_enabled=javascript_enabled)
                except Exception as nav_error:
                    logger.error(f"Navigation failed for {url}: {str(nav_error)}")
                    # Continue with a blank page instead of failing
                    await browser_control.page.set_content(f"<html><body><h1>Failed to load {url}</h1><p>Error: {str(nav_error)}</p></body></html>")
                
                # Get HTML content
                html_content = ""
                try:
                    html_content = await browser_control.page.content()
                    logger.info(f"Retrieved HTML content for {url}")
                except Exception as html_error:
                    logger.error(f"Failed to get HTML content for {url}: {str(html_error)}")
                
                # Get page title
                title = "Untitled Page"
                try:
                    title = await browser_control.page.title()
                except Exception as title_error:
                    logger.error(f"Failed to get title for {url}: {str(title_error)}")
                
                # Take screenshot if requested
                screenshot_path = None
                
                if take_screenshot:
                    logger.info(f"Taking screenshot as requested (take_screenshot=True)")
                    screenshot_path = os.path.join(SCREENSHOTS_DIR, f"{filename}_{uuid.uuid4().hex[:8]}.png")
                    try:
                        await browser_control.screenshot(screenshot_path)
                        logger.info(f"Screenshot successfully saved at {screenshot_path}")
                    except Exception as ss_error:
                        logger.error(f"Screenshot failed for {url}: {str(ss_error)}")
                        screenshot_path = None
                else:
                    logger.info(f"Screenshot explicitly skipped for {url} as requested (take_screenshot=False)")
                
                # Extract text from screenshot if available and requested
                extracted_text = ""
                if screenshot_path and ocr_extraction:
                    try:
                        logger.info(f"Extracting text from screenshot at {screenshot_path}")
                        extracted_text = await browser_control.extract_text_from_screenshot(screenshot_path)
                        logger.info(f"OCR text extraction complete for {url}")
                    except Exception as ocr_error:
                        logger.error(f"OCR failed for {url}: {str(ocr_error)}")
                        extracted_text = f"Text extraction failed: {str(ocr_error)}"
                elif not take_screenshot:
                    logger.info(f"OCR skipped for {url} because screenshot was not taken")
                elif not ocr_extraction:
                    logger.info(f"OCR skipped for {url} as requested")
                
                # Generate markdown from HTML if requested
                markdown_content = ""
                fit_markdown_content = ""
                
                if markdown_extraction != "none" and html_content:
                    try:
                        # Configure content filter for enhanced mode
                        content_filter = None
                        if markdown_extraction == "enhanced":
                            content_filter = PruningContentFilter(threshold=0.48)
                            logger.info(f"Using enhanced markdown with content filtering for {url}")
                        else:
                            logger.info(f"Using basic markdown without filtering for {url}")
                        
                        # Create markdown generator
                        markdown_generator = DefaultMarkdownGenerator(content_filter=content_filter)
                        
                        # Generate markdown with citations
                        markdown_result = markdown_generator.generate_markdown(
                            html_content, 
                            base_url=url,
                            citations=True
                        )
                        
                        # Extract different markdown formats
                        markdown_content = markdown_result.raw_markdown
                        markdown_with_citations = markdown_result.markdown_with_citations
                        references = markdown_result.references_markdown
                        
                        # Only include fit_markdown_content for enhanced mode
                        if markdown_extraction == "enhanced":
                            fit_markdown_content = markdown_result.fit_markdown
                        
                        logger.info(f"Successfully generated markdown from HTML for {url}")
                        
                        # Determine which content to use as filtered content
                        if markdown_extraction == "enhanced" and fit_markdown_content:
                            filtered_content = fit_markdown_content
                            logger.info(f"Using enhanced markdown as filtered content for {url}")
                        else:
                            filtered_content = markdown_content
                            logger.info(f"Using basic markdown as filtered content for {url}")
                        
                    except Exception as md_error:
                        logger.error(f"Markdown generation failed for {url}: {str(md_error)}")
                        filtered_content = extracted_text if extracted_text else "No content could be extracted"
                else:
                    # Fall back to OCR or basic HTML content
                    if extracted_text:
                        filtered_content = extracted_text
                    elif html_content:
                        try:
                            from bs4 import BeautifulSoup
                            soup = BeautifulSoup(html_content, 'html.parser')
                            
                            # Remove script and style elements
                            for s in soup(['script', 'style', 'noscript', 'iframe', 'header', 'footer', 'nav']):
                                s.decompose()
                            
                            # Get text content
                            filtered_content = soup.get_text(separator='\n\n')
                            logger.info(f"Extracted basic text content from HTML for {url}")
                        except Exception as filter_error:
                            logger.error(f"HTML content filtering failed for {url}: {str(filter_error)}")
                            filtered_content = "Error extracting content from HTML"
                    else:
                        filtered_content = "No content could be extracted"
                
                # Process content with LLM if provider is specified
                if llm_provider and llm_token:
                    content_for_llm = filtered_content
                    
                    if content_for_llm:
                        try:
                            llm_summary = await process_with_llm(content_for_llm, llm_provider, llm_token)
                        except Exception as llm_error:
                            logger.error(f"LLM processing error for {url}: {str(llm_error)}")
                            llm_summary = None
                    else:
                        logger.warning(f"No content available for LLM processing for {url}")
                        llm_summary = None
                else:
                    llm_summary = None
                
                # Prepare the result
                result = {
                    'url': url,
                    'title': title,
                    'javascript_enabled': javascript_enabled,
                    'filtered_content': filtered_content,
                    'html_content': html_content,
                }
                
                # Only include optional fields if they were generated
                if screenshot_path:
                    result['screenshot'] = screenshot_path
                
                if extracted_text:
                    result['extracted_text'] = extracted_text
                
                if markdown_content:
                    result['markdown_content'] = markdown_content
                
                if fit_markdown_content:
                    result['fit_markdown_content'] = fit_markdown_content
                
                if llm_summary:
                    result['llm_summary'] = llm_summary
                    result['llm_provider'] = llm_provider
                
                results.append(result)
                logger.info(f"Successfully processed {url}")
                
            except Exception as e:
                logger.error(f"Error processing URL {url}: {str(e)}", exc_info=True)
                results.append({
                    'url': url,
                    'error': f"Processing failed: {str(e)}",
                    'javascript_enabled': javascript_enabled
                })
    
    finally:
        # Ensure browser is always closed
        try:
            logger.info("Closing browser after URL processing")
            await browser_control.close()
        except Exception as e:
            logger.error(f"Error closing browser: {str(e)}")
    
    # Add detailed logging before returning
    if isinstance(url, str) and len(results) == 1:
        # Log the first result
        result_item = results[0]
        logger.info(f"Returning single result for URL: {url}")
        logger.info(f"Result type: {type(result_item)}")
        
        # Log keys if it's a dictionary
        if isinstance(result_item, dict):
            logger.info(f"Result keys: {list(result_item.keys())}")
        else:
            logger.error(f"CRITICAL: Result is not a dictionary but {type(result_item)}")
            logger.error(f"Result content: {str(result_item)[:200]}...")
            # Convert non-dictionary to dictionary as a failsafe
            result_item = {
                "url": str(url),
                "title": "Error: Invalid Result Type",
                "error": f"Expected dictionary but got {type(result_item)}"
            }
            results[0] = result_item
            
        # Return the first result for single URL
        return results[0]
    else:
        # Log for multiple results
        logger.info(f"Returning list of {len(results)} results")
                
        # Convert any non-dictionary results to dictionaries as a failsafe
        for i, r in enumerate(results):
            if not isinstance(r, dict):
                logger.error(f"Converting non-dictionary result at index {i} to dictionary")
                results[i] = {
                    "url": f"Item {i}" if not isinstance(url, list) else str(url[i]) if i < len(url) else str(i),
                    "title": "Error: Invalid Result Type",
                    "error": f"Expected dictionary but got {type(r)}"
                }
                
        # DEBUG LOG: Log what's being returned from multiple results
        screenshot_counts = sum(1 for r in results if 'screenshot' in r)
        
        # Return the list for multiple URLs
        return results
# End of crawl_url function
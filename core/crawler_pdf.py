"""
PDF Generation for Web Crawling

This module provides PDF generation functionality for crawled web pages,
with integrated storage service support for saving PDFs.
"""
import os
import logging
import datetime
import hashlib
from typing import Optional, Dict, Any, Tuple
from core.browser import BrowserControl
from core.storage_service import get_storage_service

logger = logging.getLogger("gnosis_wraith")

async def generate_pdf(
    url: str,
    format: str = 'A4',
    landscape: bool = False,
    print_background: bool = True,
    margin: Optional[Dict[str, str]] = None,
    wait_for: int = 2000,
    user_email: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a PDF from a webpage and save to storage.
    
    Args:
        url: Target URL
        format: Paper format (A4, Letter, etc.)
        landscape: Whether to use landscape orientation
        print_background: Whether to print background graphics
        margin: Page margins (top, right, bottom, left)
        wait_for: Time to wait before generation (ms)
        user_email: User email for tracking and storage partitioning
        
    Returns:
        Dictionary containing:
            - success: bool
            - pdf_url: Storage URL for the saved PDF
            - filename: Generated filename
            - size: File size in bytes
            - storage_path: Path in storage
            - metadata: Additional metadata
    """

    browser = None
    try:
        # Initialize browser
        browser = BrowserControl()
        await browser.start_browser(javascript_enabled=True)
        
        # Navigate to URL
        logger.info(f"Navigating to {url} for PDF generation")
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
        logger.info("Generating PDF...")
        pdf_bytes = await browser.page.pdf(**pdf_options)
        
        logger.info(f"Generated PDF for {url}, size: {len(pdf_bytes)} bytes")
        
        # Generate filename
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:8]
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"pdf_{url_hash}_{timestamp}.pdf"
        
        # Get storage service for user
        storage = get_storage_service(user_email)
        
        # Save PDF to storage
        file_info = await storage.save_file(
            pdf_bytes, 
            filename=filename
        )
        
        # Get URL for the saved file
        pdf_url = storage.get_file_url(filename)
        
        result = {
            "success": True,
            "pdf_url": pdf_url,
            "filename": filename,
            "size": len(pdf_bytes),
            "storage_path": file_info.get("path"),
            "metadata": {
                "url": url,
                "format": format,
                "landscape": landscape,
                "generated_at": datetime.datetime.now().isoformat()
            }
        }
        
        logger.info(f"PDF saved to storage: {filename}")
        
        return result

        
    except Exception as e:
        logger.error(f"PDF generation error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "url": url
        }
    finally:
        if browser:
            await browser.close()


async def crawl_and_save_pdf(
    url: str,
    pdf_options: Optional[Dict[str, Any]] = None,
    user_email: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to crawl a URL and save it as PDF with default options.
    
    Args:
        url: Target URL
        pdf_options: Optional PDF generation options
        user_email: User email for storage
        
    Returns:
        Dictionary with PDF generation results
    """
    # Default PDF options
    default_options = {
        'format': 'A4',
        'landscape': False,
        'print_background': True,
        'margin': {
            'top': '1cm',
            'right': '1cm',
            'bottom': '1cm',
            'left': '1cm'
        },
        'wait_for': 2000
    }

    
    # Merge with provided options
    if pdf_options:
        default_options.update(pdf_options)
    
    # Generate and save PDF
    return await generate_pdf(
        url=url,
        user_email=user_email,
        **default_options
    )


async def batch_generate_pdfs(
    urls: list,
    pdf_options: Optional[Dict[str, Any]] = None,
    user_email: Optional[str] = None,
    concurrent: int = 3
) -> Dict[str, Any]:
    """
    Generate PDFs for multiple URLs concurrently.
    
    Args:
        urls: List of URLs to convert to PDF
        pdf_options: Optional PDF generation options
        user_email: User email for storage
        concurrent: Number of concurrent PDF generations
        
    Returns:
        Dictionary containing results for all URLs
    """
    import asyncio
    
    results = []
    errors = []
    
    # Create semaphore for concurrency control
    semaphore = asyncio.Semaphore(concurrent)
    
    async def generate_single_pdf(url):
        async with semaphore:
            try:
                result = await crawl_and_save_pdf(url, pdf_options, user_email)
                if result["success"]:
                    results.append(result)
                else:
                    errors.append(result)
                return result
            except Exception as e:
                error_result = {
                    "success": False,
                    "url": url,
                    "error": str(e)
                }
                errors.append(error_result)
                return error_result
    
    # Generate all PDFs
    all_results = await asyncio.gather(*[generate_single_pdf(url) for url in urls])
    
    return {
        "success": len(errors) == 0,
        "total": len(urls),
        "successful": len(results),
        "failed": len(errors),
        "results": all_results,
        "summary": {
            "total_size": sum(r.get("size", 0) for r in results),
            "urls_processed": [r.get("metadata", {}).get("url") for r in results]
        }
    }

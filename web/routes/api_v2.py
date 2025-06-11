"""API v2 routes - Streamlined endpoints following crawl4ai patterns.

This module implements focused, single-purpose endpoints for better performance
and cleaner API design.
"""
import os
import logging
import datetime
from quart import request, jsonify, Response, Blueprint
from core.config import logger
from core.crawler import crawl_url
from core.markdown_extractor import extract_markdown
from core.screenshot_capture import capture_screenshot
from core.pdf_generator import generate_pdf
# Import the enhanced login_required decorator that supports API tokens
from web.routes.auth import login_required, api_token_optional


# Create v2 API blueprint
api_v2 = Blueprint('api_v2', __name__, url_prefix='/api/v2')

@api_v2.route('/md', methods=['POST'])
@login_required
async def markdown_endpoint():
    """Dedicated endpoint for markdown extraction.
    
    Optimized for getting clean markdown without screenshots or other overhead.
    """
    try:
        data = await request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({
                "success": False,
                "error": "URL is required"
            }), 400
        
        # Extract options
        filter_type = data.get('filter')  # null, "pruning", "bm25"
        filter_options = data.get('filter_options', {})
        format_type = data.get('format', 'clean')  # "raw", "clean", "fit"
        
        logger.info(f"Markdown extraction for {url} with filter={filter_type}")
        
        # Perform lightweight crawl - no screenshots, just content
        result = await crawl_url(
            [url],
            javascript_enabled=data.get('javascript', True),
            take_screenshot=False,
            ocr_extraction=False,
            markdown_extraction='enhanced' if filter_type else 'basic',
            email=request.user_email
        )
        
        if not result or isinstance(result, list) and len(result) == 0:
            return jsonify({
                "success": False,
                "error": "Failed to extract content"
            }), 500
        
        # Get the first result
        crawl_data = result[0] if isinstance(result, list) else result
        
        # Extract markdown content
        markdown_content = (
            crawl_data.get('markdown_content') or
            crawl_data.get('filtered_content') or
            crawl_data.get('fit_markdown_content') or
            crawl_data.get('extracted_text') or
            ""
        )
        
        # Apply additional filtering if requested
        if filter_type == 'bm25' and filter_options.get('query'):
            from core.content_filter import apply_bm25_filter
            markdown_content = apply_bm25_filter(
                markdown_content, 
                filter_options['query']
            )
        
        # Return clean response
        return jsonify({
            "success": True,
            "url": url,
            "markdown": markdown_content,
            "stats": {
                "word_count": len(markdown_content.split()),
                "char_count": len(markdown_content),
                "extraction_time": crawl_data.get('extraction_time', 0)
            }
        })
        
    except Exception as e:
        logger.error(f"Markdown extraction error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_v2.route('/screenshot', methods=['POST'])
@login_required
async def screenshot_endpoint():
    """Dedicated endpoint for screenshot capture."""
    try:
        data = await request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({
                "success": False,
                "error": "URL is required"
            }), 400
        
        # Extract options
        mode = data.get('mode', 'viewport')  # "viewport" or "full"
        format_type = data.get('format', 'base64')  # "base64", "url", "file"
        wait_for = data.get('wait_for', 2000)
        options = data.get('options', {})
        
        logger.info(f"Screenshot capture for {url} mode={mode}")
        
        # Capture screenshot
        screenshot_data = await capture_screenshot(
            url=url,
            full_page=(mode == 'full'),
            wait_for=wait_for,
            quality=options.get('quality', 90),
            clip=options.get('clip'),
            user_email=request.user_email
        )
        
        if format_type == 'file':
            # Return as downloadable file
            return Response(
                screenshot_data['bytes'],
                mimetype='image/png',
                headers={
                    'Content-Disposition': f'attachment; filename="{screenshot_data["filename"]}"'
                }
            )
        elif format_type == 'url':
            # Return URL to saved file
            return jsonify({
                "success": True,
                "url": url,
                "screenshot_url": f"/screenshots/{screenshot_data['filename']}",
                "width": screenshot_data['width'],
                "height": screenshot_data['height']
            })
        else:
            # Return base64 encoded (default)
            return jsonify({
                "success": True,
                "url": url,
                "screenshot": {
                    "data": screenshot_data['base64'],
                    "format": "png",
                    "width": screenshot_data['width'],
                    "height": screenshot_data['height'],
                    "file_size": len(screenshot_data['bytes'])
                },
                "capture_time": screenshot_data['capture_time']
            })
        
    except Exception as e:
        logger.error(f"Screenshot capture error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_v2.route('/pdf', methods=['POST'])
@login_required
async def pdf_endpoint():
    """Generate PDF from URL."""
    try:
        data = await request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({
                "success": False,
                "error": "URL is required"
            }), 400
        
        options = data.get('options', {})
        
        logger.info(f"PDF generation for {url}")
        
        # Generate PDF
        pdf_data = await generate_pdf(
            url=url,
            format=options.get('format', 'A4'),
            landscape=options.get('landscape', False),
            print_background=options.get('print_background', True),
            margin=options.get('margin'),
            wait_for=options.get('wait_for', 2000),
            user_email=request.user_email
        )
        
        # Generate filename
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.replace('www.', '').replace('.', '_')
        timestamp = datetime.datetime.now().strftime('%Y_%m_%d_%H%M%S')
        filename = f"{domain}_{timestamp}.pdf"
        
        # Return PDF file
        return Response(
            pdf_data,
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Length': str(len(pdf_data))
            }
        )
        
    except Exception as e:
        logger.error(f"PDF generation error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_v2.route('/html', methods=['POST'])
@login_required
async def html_endpoint():
    """Extract cleaned HTML from URL."""
    try:
        data = await request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({
                "success": False,
                "error": "URL is required"
            }), 400
        
        clean = data.get('clean', True)
        javascript = data.get('javascript', True)
        wait_for = data.get('wait_for')
        
        logger.info(f"HTML extraction for {url}")
        
        # Crawl with HTML focus
        result = await crawl_url(
            [url],
            javascript_enabled=javascript,
            take_screenshot=False,
            ocr_extraction=False,
            markdown_extraction='none',  # Skip markdown conversion
            wait_for=wait_for,
            email=request.user_email
        )
        
        if not result:
            return jsonify({
                "success": False,
                "error": "Failed to extract HTML"
            }), 500
        
        crawl_data = result[0] if isinstance(result, list) else result
        
        # Get HTML content
        html_content = crawl_data.get('html_content', '')
        
        if clean and html_content:
            # Apply cleaning if requested
            from core.html_cleaner import clean_html
            html_content = clean_html(html_content)
        
        return jsonify({
            "success": True,
            "url": url,
            "html": html_content,
            "title": crawl_data.get('title', ''),
            "metadata": {
                "extracted_at": datetime.datetime.now().isoformat(),
                "javascript_used": javascript
            }
        })
        
    except Exception as e:
        logger.error(f"HTML extraction error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_v2.route('/batch', methods=['POST'])
@login_required
async def batch_endpoint():
    """Process multiple URLs in batch."""
    try:
        data = await request.get_json()
        urls = data.get('urls', [])
        
        if not urls:
            return jsonify({
                "success": False,
                "error": "URLs array is required"
            }), 400
        
        options = data.get('options', {})
        batch_config = data.get('batch', {})
        
        # Extract batch settings
        concurrent = min(batch_config.get('concurrent', 3), 10)  # Max 10
        delay = batch_config.get('delay', 1000)
        continue_on_error = batch_config.get('continue_on_error', True)
        
        logger.info(f"Batch processing {len(urls)} URLs")
        
        results = []
        errors = []
        
        # Process URLs with concurrency control
        from asyncio import Semaphore, sleep
        semaphore = Semaphore(concurrent)
        
        async def process_url(url):
            async with semaphore:
                try:
                    # Add delay between requests
                    if delay > 0:
                        await sleep(delay / 1000)
                    
                    # Process single URL
                    result = await crawl_url(
                        [url],
                        **options,
                        email=request.user_email
                    )
                    
                    if result:
                        crawl_data = result[0] if isinstance(result, list) else result
                        results.append({
                            "url": url,
                            "success": True,
                            "data": crawl_data
                        })
                    else:
                        raise Exception("No result returned")
                        
                except Exception as e:
                    error_data = {
                        "url": url,
                        "success": False,
                        "error": str(e)
                    }
                    errors.append(error_data)
                    
                    if continue_on_error:
                        results.append(error_data)
                    else:
                        raise
        
        # Process all URLs
        import asyncio
        await asyncio.gather(*[process_url(url) for url in urls])
        
        return jsonify({
            "success": len(errors) == 0,
            "total": len(urls),
            "processed": len(results),
            "errors": len(errors),
            "results": results
        })
        
    except Exception as e:
        logger.error(f"Batch processing error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Health check for v2 API
@api_v2.route('/health', methods=['GET'])
async def health_check():
    """Health check for v2 API."""
    return jsonify({
        "status": "healthy",
        "version": "2.0",
        "endpoints": [
            "/api/v2/md",
            "/api/v2/screenshot",
            "/api/v2/pdf",
            "/api/v2/html",
            "/api/v2/batch"
        ]
    })

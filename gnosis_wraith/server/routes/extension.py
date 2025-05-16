"""
Extension DOM Capture API for Gnosis Wraith

This module provides an API endpoint that receives DOM content captured by the browser extension.
"""
import os
import re
import uuid
import base64
import logging
import datetime
from io import BytesIO
from typing import Dict, Any, Optional, List, Union

from quart import Blueprint, request, jsonify
from PIL import Image

from server.config import SCREENSHOTS_DIR, REPORTS_DIR, logger
from server.markdown_generation import DefaultMarkdownGenerator, PruningContentFilter
from server.reports import save_markdown_report, convert_markdown_to_html

# Create a blueprint for extension-specific endpoints
extension_bp = Blueprint('extension', __name__, url_prefix='/api')

@extension_bp.route('/extension-capture', methods=['POST'])
async def extension_capture():
    """
    API endpoint to receive DOM content captured by the browser extension.
    
    Expects a JSON payload with the following structure:
    {
        "html": "...",  // Full HTML content of the page
        "metadata": {
            "title": "Page Title",
            "url": "https://example.com",
            "baseUrl": "https://example.com",
            "timestamp": "2025-05-14T23:45:22Z",
            "mainContentSelector": "#main-content",
            "pageStats": { ... }
        },
        "screenshot": "data:image/png;base64,...",  // Optional base64 encoded screenshot
        "processingOptions": {
            "processingMode": "enhanced",  // 'enhanced', 'basic', or 'none'
            "includeScreenshot": true
        }
    }
    """
    logger.info("Extension capture endpoint called")
    
    try:
        # Get JSON data from request
        data = await request.get_json()
        logger.info(f"Extension capture received for URL: {data.get('metadata', {}).get('url', 'Unknown URL')}")
        
        # Extract required fields
        html_content = data.get('html')
        metadata = data.get('metadata', {})
        url = metadata.get('url')
        title = metadata.get('title', 'Untitled Page')
        screenshot_data = data.get('screenshot')
        processing_options = data.get('processingOptions', {})
        
        # Validate required fields
        if not html_content or not url:
            logger.error(f"Missing required fields: html={bool(html_content)}, url={bool(url)}")
            return jsonify({
                "success": False,
                "error": "Missing required data: html content and URL are required"
            }), 400
        
        # Process the HTML content based on options
        processing_mode = processing_options.get('processingMode', 'enhanced')
        logger.info(f"Using processing mode: {processing_mode}")
        
        # Initialize the result
        result = {
            'url': url,
            'title': title,
            'html_content': html_content,
            'source': 'extension',
            'javascript_enabled': True,  # Content from extension always has JavaScript enabled
            'metadata': metadata
        }
        
        # Save screenshot if provided
        screenshot_path = None
        if screenshot_data and processing_options.get('includeScreenshot', True):
            try:
                # Extract base64 image data, handling data URL prefix if present
                image_data = screenshot_data.split(',')[1] if ',' in screenshot_data else screenshot_data
                
                # Decode base64 to image and save
                image = Image.open(BytesIO(base64.b64decode(image_data)))
                
                # Generate a filename based on URL and timestamp
                safe_url = re.sub(r'[^\w\-_]', '_', url.replace('https://', '').replace('http://', ''))
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{safe_url}_{timestamp}.png"
                
                # Save to screenshots directory
                screenshot_path = os.path.join(SCREENSHOTS_DIR, filename)
                image.save(screenshot_path)
                logger.info(f"Screenshot saved to {screenshot_path}")
                
                # Add to result
                result['screenshot'] = screenshot_path
                
            except Exception as screenshot_error:
                logger.error(f"Error saving screenshot: {str(screenshot_error)}")
                result['screenshot_error'] = str(screenshot_error)
        
        # Generate markdown based on the processing mode
        if processing_mode != 'none':
            try:
                # Configure content filter based on mode
                content_filter = None
                if processing_mode == 'enhanced':
                    content_filter = PruningContentFilter(threshold=0.48)
                    logger.info("Using enhanced markdown with content filtering")
                
                # Create markdown generator with appropriate filter
                markdown_generator = DefaultMarkdownGenerator(content_filter=content_filter)
                
                # Generate markdown with citations
                markdown_result = markdown_generator.generate_markdown(
                    html_content, 
                    base_url=url,
                    citations=True
                )
                
                # Extract different markdown formats
                result['markdown_content'] = markdown_result.raw_markdown
                
                # Include fit_markdown_content for enhanced mode
                if processing_mode == 'enhanced':
                    result['fit_markdown_content'] = markdown_result.fit_markdown
                
                logger.info(f"Successfully generated markdown from extension HTML")
                
            except Exception as markdown_error:
                logger.error(f"Markdown generation failed: {str(markdown_error)}")
                result['markdown_error'] = str(markdown_error)
        
        # Generate a report
        report_path = None
        try:
            # Define report title
            report_title = f"{title} - Extension Capture ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
            
            # Generate report
            report_path = await save_markdown_report(report_title, [result])
            logger.info(f"Report saved to {report_path}")
            
            # Generate HTML version
            html_report_path = await convert_markdown_to_html(report_path)
            logger.info(f"HTML report saved to {html_report_path}")
            
        except Exception as report_error:
            logger.error(f"Error generating report: {str(report_error)}")
            return jsonify({
                "success": False,
                "error": f"Report generation failed: {str(report_error)}"
            }), 500
        
        # Build the response
        response = {
            "success": True,
            "url_processed": url,
            "title": title,
            "processing_mode": processing_mode,
            "report_path": os.path.basename(report_path) if report_path else None,
            "html_report_path": os.path.basename(html_report_path) if 'html_report_path' in locals() else None,
            "screenshot_path": os.path.basename(screenshot_path) if screenshot_path else None
        }
        
        logger.info(f"Extension capture processed successfully for {url}")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Extension capture endpoint error: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Server processing error: {str(e)}"
        }), 500

# Register the extension blueprint with the app
def register_extension_blueprint(app):
    app.register_blueprint(extension_bp)
    logger.info("Extension API blueprint registered")

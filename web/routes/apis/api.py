"""
Gnosis Wraith API - Core Endpoints

This module contains the core API endpoints including health checks,
error handlers, and validation exception handlers.
"""

import os
import sys
import datetime
import json
import asyncio
from typing import Dict, Any, List, Optional
from quart import Blueprint, jsonify, request
from pydantic import ValidationError

from core.config import logger
from core.storage_service import get_storage_service
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import login_required, api_token_optional

# Create API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')


# ============================================================================
# Error Handlers
# ============================================================================

@api_bp.errorhandler(404)
async def not_found(error):
    """Handle 404 errors for API endpoints"""
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "message": "The requested API endpoint does not exist. Check the API documentation.",
        "status": 404
    }), 404


@api_bp.errorhandler(ValidationError)
async def handle_validation_error(error):
    """Handle Pydantic validation errors"""
    return jsonify({
        "success": False,
        "error": "Validation error",
        "details": error.errors(),
        "status": 422
    }), 422


@api_bp.errorhandler(Exception)
async def handle_general_error(error):
    """Handle general errors in API"""
    logger.error(f"API Error: {str(error)}")
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "message": str(error),
        "status": 500
    }), 500


# ============================================================================
# Health Check Endpoint
# ============================================================================

@api_bp.route('/health', methods=['GET', 'HEAD'])
@api_bp.route('/v2/health', methods=['GET', 'HEAD'])
async def health_check():
    """Health check endpoint for monitoring and load balancer checks.

    
    Returns basic health status and optional system information.
    """
    try:
        # Basic health response
        health_status = {
            "status": "healthy",
            "timestamp": datetime.datetime.now().isoformat(),
            "service": "gnosis-wraith",
            "version": "3.2.7"
        }
        
        # Optional: Add more detailed health checks
        storage_service = get_storage_service()
        health_status["checks"] = {
            "storage": True,  # Storage service is available
            "storage_config": storage_service is not None
        }
        
        # Return 200 OK with health status
        return jsonify(health_status), 200
        
    except Exception as e:
        # If there's any error, return unhealthy status
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.datetime.now().isoformat(),
            "error": str(e)
        }), 503


# ============================================================================
# Protected Endpoint Example
# ============================================================================

@api_bp.route('/protected', methods=['GET'])
@login_required
async def protected_endpoint():
    """Example of a protected endpoint that requires authentication.
    
    Can be accessed with:
    - Session authentication (logged in via web)
    - Bearer token: Authorization: Bearer YOUR_API_TOKEN
    - X-API-Token header: X-API-Token: YOUR_API_TOKEN
    - JSON body (POST only): {"api_token": "YOUR_API_TOKEN"}
    """
    # Access user info from request
    user_email = getattr(request, 'user_email', None)
    auth_method = getattr(request, 'auth_method', 'unknown')
    
    return jsonify({
        "success": True,
        "message": "Successfully accessed protected endpoint",
        "user": user_email,
        "auth_method": auth_method,
        "timestamp": datetime.datetime.now().isoformat()
    })


# ============================================================================
# Markdown Extraction Endpoint
# ============================================================================

async def _handle_batch_markdown(data: Dict[str, Any], urls: List[str]):
    """Handle batch markdown extraction with parallel processing."""
    import asyncio
    from core.batch_processor import BatchProcessor
    from core.url_predictor import URLPredictor
    
    user_email = getattr(request, 'user_email', None)
    
    # Validate batch size
    if len(urls) > 50:
        return jsonify({
            "success": False,
            "error": "Maximum 50 URLs allowed per batch"
        }), 400
    
    # Extract options
    async_mode = data.get('async', True)
    collate = data.get('collate', False)
    callback_url = data.get('callback_url')
    callback_headers = data.get('callback_headers', {})
    
    # Generate job ID
    job_id = f"batch_{int(datetime.datetime.now().timestamp() * 1000)}"
    
    # Get storage service and create predictor
    storage = get_storage_service(user_email)
    predictor = URLPredictor(storage._user_hash)
    
    # Predict URLs for immediate response
    predicted_results = predictor.predict_batch_urls(urls, job_id)
    
    # Prepare response
    response = {
        "success": True,
        "mode": "batch_async" if async_mode else "batch_sync",
        "job_id": job_id,
        "status_url": f"/api/jobs/{job_id}",
        "results": predicted_results
    }
    
    if collate:
        response["collated_url"] = predictor.predict_collated_url(job_id)
    
    if async_mode:
        # Start background processing
        asyncio.create_task(_process_batch_background(
            urls=urls,
            options=data,
            job_id=job_id,
            user_email=user_email,
            callback_url=callback_url,
            callback_headers=callback_headers,
            collate=collate
        ))
        
        # Return immediately with 202 Accepted
        return jsonify(response), 202
    else:
        # Process synchronously
        processor = BatchProcessor(user_email)
        batch_results = await processor.process_batch(urls, data)
        
        # Update response with actual results
        response["results"] = batch_results["results"]
        
        # Collate if requested
        if collate and batch_results["completed"] > 0:
            collation_result = await processor.collate_results(
                batch_results["results"],
                job_id,
                data.get('collate_options', {})
            )
            response["collated_url"] = collation_result["url"]
        
        return jsonify(response), 200


async def _process_batch_background(urls: List[str], 
                                   options: Dict[str, Any],
                                   job_id: str,
                                   user_email: str,
                                   callback_url: Optional[str],
                                   callback_headers: Dict[str, str],
                                   collate: bool):
    """Process batch URLs in the background."""
    try:
        from core.batch_processor import BatchProcessor
        import aiohttp
        
        processor = BatchProcessor(user_email)
        
        # TODO: Update job status as processing
        # This would integrate with your existing job system
        
        # Process the batch
        batch_results = await processor.process_batch(urls, options)
        
        # Collate if requested
        collated_url = None
        if collate and batch_results["completed"] > 0:
            collation_result = await processor.collate_results(
                batch_results["results"],
                job_id,
                options.get('collate_options', {})
            )
            collated_url = collation_result["url"]
        
        # Trigger webhook if provided
        if callback_url:
            await _trigger_webhook(
                callback_url=callback_url,
                headers=callback_headers,
                payload={
                    "job_id": job_id,
                    "status": "completed",
                    "stats": batch_results["stats"],
                    "results": batch_results["results"],
                    "collated_url": collated_url
                }
            )
        
        # TODO: Update job status as completed
        
    except Exception as e:
        logger.error(f"Batch processing error for job {job_id}: {str(e)}")
        # TODO: Update job status as failed
        
        # Still try to send webhook on failure
        if callback_url:
            await _trigger_webhook(
                callback_url=callback_url,
                headers=callback_headers,
                payload={
                    "job_id": job_id,
                    "status": "failed",
                    "error": str(e)
                }
            )


async def _trigger_webhook(callback_url: str, headers: Dict[str, str], payload: Dict[str, Any]):
    """Send webhook notification."""
    try:
        import aiohttp
        import json
        
        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-Type": "application/json",
                **headers
            }
            
            async with session.post(
                callback_url,
                data=json.dumps(payload),
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status >= 400:
                    logger.warning(f"Webhook returned status {response.status}")
                else:
                    logger.info(f"Webhook sent successfully to {callback_url}")
                    
    except Exception as e:
        logger.error(f"Failed to send webhook: {str(e)}")


@api_bp.route('/markdown', methods=['POST'])
@login_required
async def markdown_extraction():
    """Extract clean markdown content from URL(s) and save to user storage.
    
    Supports both single URL (backward compatible) and batch URL processing.
    Always saves both markdown and JSON to the user's storage directory.
    Optionally captures and saves screenshots.

    
    Request body:
    {
        "url": "https://example.com",        // Single URL (backward compatible)
        "urls": ["url1", "url2", ...],       // Multiple URLs (new batch mode)
        "javascript_enabled": true,           // Optional: enable JS rendering (default: true)
        "javascript_payload": "...",          // Optional: JS code to inject
        "screenshot_mode": "full",            // Optional: "top", "full", or null (default: null)
        "async": true,                        // Optional: async batch processing (default: true for batch)
        "collate": false,                     // Optional: merge results into single file
        "callback_url": "https://...",        // Optional: webhook for completion notification
        "callback_headers": {...}             // Optional: headers for webhook
    }


    """
    try:
        data = await request.get_json()
        
        # Debug logging
        logger.info(f"Markdown endpoint received data: {json.dumps(data)[:200]}")
        
        # Check if this is a batch request
        urls = data.get('urls', [])
        single_url = data.get('url')
        
        logger.info(f"URLs: {urls}, Single URL: {single_url}")
        
        # If both urls and url are provided, urls takes precedence
        if urls and isinstance(urls, list) and len(urls) > 0:
            # Batch mode
            return await _handle_batch_markdown(data, urls)
        elif single_url:
            # Single URL mode (backward compatible)
            url = single_url
        else:
            return jsonify({
                "success": False,
                "error": "Either 'url' or 'urls' is required"
            }), 400

        # Extract options
        filter_type = data.get('filter', None)
        filter_options = data.get('filter_options', {})
        javascript_enabled = data.get('javascript_enabled', True)
        javascript_payload = data.get('javascript_payload', None)
        screenshot_mode = data.get('screenshot_mode', None)  # "top", "full", or None
        
        # Import markdown generation components
        from core.markdown_generation import (
            DefaultMarkdownGenerator,
            PruningContentFilter,
            SimpleBM25ContentFilter
        )
        from core.crawler import crawl_url
        
        # Configure content filter based on request
        content_filter = None
        if filter_type == 'pruning':
            threshold = filter_options.get('threshold', 0.48)
            content_filter = PruningContentFilter(
                threshold=threshold,
                min_word_threshold=filter_options.get('min_words', 2)
            )
        elif filter_type == 'bm25':
            query = filter_options.get('query', '')
            threshold = filter_options.get('threshold', 0.5)
            content_filter = SimpleBM25ContentFilter(
                user_query=query,
                threshold=threshold
            )
        
        # Log the request
        logger.info(f"Markdown extraction for {url} with filter: {filter_type}")

        # Crawl the URL to get HTML content
        crawl_result = await crawl_url(
            url=url,
            javascript_enabled=javascript_enabled,
            javascript_payload=javascript_payload,  # Pass the injected JS if provided
            screenshot_mode=screenshot_mode,  # Pass screenshot mode if requested
            user_email=getattr(request, 'user_email', None)
        )

        if not crawl_result.get('success'):
            error_msg = crawl_result.get('error', 'Failed to crawl URL')
            
            # Determine appropriate status code based on error type
            status_code = 500
            if 'Cannot navigate to invalid URL' in error_msg:
                status_code = 400  # Bad Request for invalid URLs
            elif 'net::ERR_NAME_NOT_RESOLVED' in error_msg:
                status_code = 502  # Bad Gateway for DNS failures
            elif 'net::ERR_CONNECTION_REFUSED' in error_msg:
                status_code = 503  # Service Unavailable
            elif 'net::ERR_CONNECTION_TIMED_OUT' in error_msg:
                status_code = 504  # Gateway Timeout
            
            return jsonify({
                "success": False,
                "error": error_msg
            }), status_code

        
        html_content = crawl_result.get('html_content', '')
        
        if not html_content:
            return jsonify({
                "success": False,
                "error": "No content found at URL"
            }), 404
        
        # Generate markdown with the configured filter
        markdown_generator = DefaultMarkdownGenerator(content_filter=content_filter)
        
        start_time = datetime.datetime.utcnow()
        markdown_result = markdown_generator.generate_markdown(
            html_content,
            base_url=url,
            citations=True  # Always use citations for enhanced format
        )
        extraction_time = (datetime.datetime.utcnow() - start_time).total_seconds()
        
        # Always use enhanced markdown format
        markdown_content = markdown_result.markdown_with_citations

        # Calculate statistics
        word_count = len(markdown_content.split())
        char_count = len(markdown_content)
        
        # Get storage service for user
        user_email = getattr(request, 'user_email', None)
        storage = get_storage_service(user_email)
        
        # Handle screenshot saving if captured
        screenshot_url = None
        if screenshot_mode and crawl_result.get('screenshot_data'):
            try:
                # Decode base64 screenshot data
                import base64
                screenshot_bytes = base64.b64decode(crawl_result['screenshot_data'])
                
                # Save screenshot
                screenshot_info = await storage.save_screenshot(screenshot_bytes, url)
                screenshot_url = screenshot_info.get('url')
                logger.info(f"Screenshot saved: {screenshot_info.get('filename')}")
            except Exception as e:
                logger.error(f"Failed to save screenshot: {str(e)}")
        
        # Always save markdown report
        markdown_url = None
        try:
            report_info = await storage.save_report(markdown_content, url, format='md')
            markdown_url = report_info.get('url')
            logger.info(f"Markdown saved: {report_info.get('filename')}")
        except Exception as e:
            logger.error(f"Failed to save markdown: {str(e)}")
        
        # Save crawl data as JSON
        json_url = None
        try:
            # Prepare crawl data
            crawl_data = {
                "url": url,
                "title": crawl_result.get('title'),
                "markdown": markdown_content,
                "extraction_time": extraction_time,
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "filter_used": filter_type,
                "javascript_enabled": javascript_enabled,
                "javascript_result": crawl_result.get('javascript_result') if javascript_payload else None,
                "screenshot_url": screenshot_url,
                "markdown_url": markdown_url
            }
            
            json_info = await storage.save_crawl_data(crawl_data, url)
            json_url = json_info.get('url')
            logger.info(f"JSON saved: {json_info.get('filename')}")
        except Exception as e:
            logger.error(f"Failed to save JSON: {str(e)}")

        
        response = {
            "success": True,
            "url": url,
            "markdown": markdown_content,
            "markdown_url": markdown_url,
            "json_url": json_url,
            "stats": {
                "word_count": word_count,
                "char_count": char_count,
                "extraction_time": round(extraction_time, 2),
                "filter_used": filter_type,
                "javascript_enabled": javascript_enabled,
                "javascript_injected": javascript_payload is not None
            }
        }
        
        # Add screenshot URL if captured
        if screenshot_url:
            response["screenshot_url"] = screenshot_url
        
        # Add JavaScript execution result if any
        if javascript_payload and crawl_result.get('javascript_result'):
            response["javascript_result"] = crawl_result.get('javascript_result')
        
        # Add references if using citations
        if markdown_result.references_markdown:
            response["references"] = markdown_result.references_markdown
        
        return jsonify(response)

    except Exception as e:
        logger.error(f"Markdown extraction error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================================
# Raw HTML Endpoint
# ============================================================================

@api_bp.route('/raw', methods=['POST'])
@login_required
async def raw_html_extraction():
    """Extract raw HTML from a URL without saving or processing.
    
    This endpoint:
    - Returns raw HTML content
    - Can execute JavaScript and return results
    - Does NOT save anything to storage
    - Does NOT take screenshots
    - Does NOT convert to markdown
    
    Request body:
    {
        "url": "https://example.com",
        "javascript_enabled": true,        // Optional: enable JS rendering (default: true)
        "javascript_payload": "..."        // Optional: JS code to execute
    }
    
    Response:
    {
        "success": true,
        "url": "https://example.com",
        "html": "<html>...</html>",
        "title": "Page Title",
        "javascript_result": {...}         // If JS payload was provided
    }
    """
    try:
        data = await request.get_json()
        
        # Validate required fields
        url = data.get('url')
        if not url:
            return jsonify({
                "success": False,
                "error": "URL is required"
            }), 400


        # Extract options
        javascript_enabled = data.get('javascript_enabled', True)
        javascript_payload = data.get('javascript_payload', None)
        
        # Log the request
        logger.info(f"Raw HTML extraction for {url}")
        logger.info(f"  JavaScript enabled: {javascript_enabled}")
        logger.info(f"  JavaScript payload: {'Yes' if javascript_payload else 'No'}")
        
        # Import crawler
        from core.crawler import crawl_url
        
        # Crawl the URL to get HTML content
        # Pass screenshot_mode=None to skip screenshot capture
        crawl_result = await crawl_url(
            url=url,
            javascript_enabled=javascript_enabled,
            javascript_payload=javascript_payload,
            screenshot_mode=None,  # No screenshots for raw endpoint
            user_email=getattr(request, 'user_email', None)
        )
        
        if not crawl_result.get('success'):
            error_msg = crawl_result.get('error', 'Failed to crawl URL')
            
            # Determine appropriate status code based on error type
            status_code = 500
            if 'Cannot navigate to invalid URL' in error_msg:
                status_code = 400  # Bad Request for invalid URLs
            elif 'net::ERR_NAME_NOT_RESOLVED' in error_msg:
                status_code = 502  # Bad Gateway for DNS failures
            elif 'net::ERR_CONNECTION_REFUSED' in error_msg:
                status_code = 503  # Service Unavailable
            elif 'net::ERR_CONNECTION_TIMED_OUT' in error_msg:
                status_code = 504  # Gateway Timeout
            
            return jsonify({
                "success": False,
                "error": error_msg
            }), status_code

        
        # Build response with raw HTML
        response = {
            "success": True,
            "url": url,
            "html": crawl_result.get('html_content', ''),
            "title": crawl_result.get('title', ''),
            "content_length": crawl_result.get('content_length', 0)
        }
        
        # Add JavaScript execution result if any
        if javascript_payload and crawl_result.get('javascript_result'):
            response["javascript_result"] = crawl_result.get('javascript_result')
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Raw HTML extraction error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================================
# Crawl Endpoint
# ============================================================================


@api_bp.route('/crawl', methods=['POST'])
@login_required
async def crawl_endpoint():
    """Crawl a URL and extract content - logs request for debugging.
    
    This endpoint logs all incoming data to help debug what the UI is sending.
    """
    try:
        # Get request data
        data = await request.get_json()
        
        # Log the entire request
        logger.info("="*60)
        logger.info("CRAWL ENDPOINT - REQUEST RECEIVED")
        logger.info("="*60)
        logger.info(f"User: {getattr(request, 'user_email', 'unknown')}")
        logger.info(f"Auth Method: {getattr(request, 'auth_method', 'unknown')}")
        logger.info(f"Request Method: {request.method}")
        logger.info(f"Request Headers: {dict(request.headers)}")
        logger.info(f"Request JSON Data: {json.dumps(data, indent=2)}")
        logger.info("="*60)
        
        # Extract parameters
        url = data.get('url')
        if not url:
            return jsonify({
                "success": False,
                "error": "URL is required"
            }), 400
        
        # Log specific parameters
        javascript_enabled = data.get('javascript_enabled', True)
        javascript_payload = data.get('javascript_payload')
        screenshot_enabled = data.get('screenshot', False)
        ocr_enabled = data.get('ocr', False)
        
        logger.info(f"Parsed parameters:")
        logger.info(f"  - URL: {url}")
        logger.info(f"  - JavaScript Enabled: {javascript_enabled}")
        logger.info(f"  - JavaScript Payload: {javascript_payload[:100] if javascript_payload else 'None'}")
        logger.info(f"  - Screenshot Enabled: {screenshot_enabled}")
        logger.info(f"  - OCR Enabled: {ocr_enabled}")
        
        # For now, return a mock response to see what happens
        return jsonify({
            "success": True,
            "url": url,
            "message": "Crawl endpoint called - check logs for details",
            "debug_info": {
                "javascript_enabled": javascript_enabled,
                "javascript_payload": bool(javascript_payload),
                "screenshot_enabled": screenshot_enabled,
                "ocr_enabled": ocr_enabled
            }
        })
        
    except Exception as e:
        logger.error(f"Crawl endpoint error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================================
# Core API Information
# ============================================================================


@api_bp.route('/', methods=['GET'])
async def api_info():
    """Return basic API information at /api/"""
    return jsonify({
        "service": "Gnosis Wraith API",
        "version": "3.2.7",
        "description": "Web crawling and content extraction service with AI capabilities",
        "endpoints": {
            "core": {
                "info": "/api/",
                "health": "/api/health",
                "markdown": "/api/markdown",
                "raw": "/api/raw",
                "crawl": "/api/crawl"
            },
            "shortcuts": {
                "markdown": "/md -> /api/markdown"
            },
            "v2": {
                "crawl": "/api/crawl",
                "suggest": "/api/suggest",
                "code": "/api/code",
                "health": "/api/health"
            }
        },
        "documentation": "https://github.com/gnosis-wraith/docs",
        "authentication": "Bearer token required for most endpoints"
    })



# ============================================================================
# Catch-all 404 handler for undefined API routes
# ============================================================================

@api_bp.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
async def catch_all(path):
    """Catch all undefined API routes and return a proper 404 response"""
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "message": f"The API endpoint '/api/{path}' does not exist. Check the API documentation.",
        "status": 404,
        "requested_path": f"/api/{path}"
    }), 404



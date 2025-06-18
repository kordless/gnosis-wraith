"""
API Routes - Smart sync/async crawling with enhanced features
"""
import os
import json
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from quart import Blueprint, request, jsonify, Response
from pydantic import BaseModel, HttpUrl, Field, ValidationError

from web.routes.auth import login_required
from core.config import logger
from core.crawl_functions import crawl_url_direct, estimate_crawl_time
from core.integration import WraithIntegration
from core.storage_service import get_storage_service


# Create V2 API blueprints
api_v2 = Blueprint('api_v2', __name__, url_prefix='/api/v2')
v2_api = Blueprint('v2_api', __name__, url_prefix='/v2')



# Error handlers
@v2_api.errorhandler(404)
async def v2_not_found(error):
    """Handle 404 errors for V2 API endpoints"""
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "message": "The requested V2 API endpoint does not exist. Check the API documentation.",
        "status": 404
    }), 404


@v2_api.errorhandler(ValidationError)
async def handle_validation_error(error):
    """Handle Pydantic validation errors"""
    return jsonify({
        "success": False,
        "error": "Validation error",
        "details": error.errors(),
        "status": 422
    }), 422


@v2_api.errorhandler(Exception)
async def handle_general_error(error):
    """Handle general errors in V2 API"""
    logger.error(f"V2 API Error: {str(error)}")
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "message": str(error),
        "status": 500
    }), 500


# Main endpoints
@v2_api.route('/crawl', methods=['POST'])
@login_required
async def crawl_endpoint():
    """
    Smart crawl endpoint with automatic sync/async execution
    """
    try:
        # Get JSON data
        data = await request.get_json()
        
        # Validate with Pydantic
        try:
            crawl_req = CrawlRequest(**data)
        except ValidationError as e:
            return jsonify({
                "success": False,
                "error": "Invalid request data",
                "details": e.errors()
            }), 422
        
        # Convert to options dict
        options = {
            "javascript": crawl_req.javascript,
            "screenshot": crawl_req.screenshot,
            "full_content": crawl_req.full_content,
            "depth": crawl_req.depth,
            "response_format": crawl_req.response_format
        }
        
        # Get user email from request
        user_email = getattr(request, 'user_email', None)
        
        # Execute crawl
        result = await crawl_url_direct(
            str(crawl_req.url),
            options,
            session_id=crawl_req.session_id,
            user_id=user_email
        )
        
        # Return result
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Crawl error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@v2_api.route('/jobs/<job_id>', methods=['GET'])
@login_required
async def job_status_endpoint(job_id: str):
    """
    Check status of async crawl job
    """
    try:
        # Get job from storage or job system
        storage = get_storage_service()
        
        # Check job status (implementation depends on job system)
        job_data = await storage.get_job_status(job_id)
        
        if not job_data:
            return jsonify({
                "success": False,
                "error": "Job not found"
            }), 404
        
        return jsonify({
            "success": True,
            "job_id": job_id,
            "status": job_data.get("status", "unknown"),
            "progress": job_data.get("progress", 0),
            "result": job_data.get("result") if job_data.get("status") == "completed" else None,
            "error": job_data.get("error") if job_data.get("status") == "failed" else None
        })
        
    except Exception as e:
        logger.error(f"Job status error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@v2_api.route('/search', methods=['POST'])
@login_required
async def search_endpoint():
    """
    Search through previous crawls
    """
    try:
        data = await request.get_json()
        
        # Validate
        try:
            search_req = SearchRequest(**data)
        except ValidationError as e:
            return jsonify({
                "success": False,
                "error": "Invalid request data",
                "details": e.errors()
            }), 422
        
        # Get user email
        user_email = getattr(request, 'user_email', None)
        
        # Search in storage
        storage = get_storage_service()
        results = await storage.search_crawls(
            user_email,
            search_req.query,
            limit=search_req.limit,
            offset=search_req.offset
        )
        
        return jsonify({
            "success": True,
            "query": search_req.query,
            "results": results.get("items", []),
            "total": results.get("total", 0),
            "limit": search_req.limit,
            "offset": search_req.offset
        })
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@v2_api.route('/workflows/<workflow_name>', methods=['POST'])
@login_required
async def workflow_endpoint(workflow_name: str):
    """
    Execute a predefined workflow
    """
    try:
        data = await request.get_json()
        
        # Validate
        try:
            workflow_req = WorkflowRequest(**data)
        except ValidationError as e:
            return jsonify({
                "success": False,
                "error": "Invalid request data",
                "details": e.errors()
            }), 422
        
        # Get integration instance
        integration = WraithIntegration()
        
        # Execute workflow
        result = await integration.execute_workflow(
            workflow_name,
            workflow_req.parameters,
            api_key=workflow_req.api_key
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Workflow error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@v2_api.route('/estimate', methods=['POST'])
@login_required
async def estimate_complexity_endpoint():
    """
    Estimate crawl complexity and execution time
    """
    try:
        data = await request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({
                "success": False,
                "error": "URL is required"
            }), 400
        
        options = {
            "javascript": data.get('javascript', False),
            "screenshot": data.get('screenshot', False),
            "full_content": data.get('full_content', False),
            "depth": data.get('depth', 0)
        }
        
        # Estimate time
        estimated_time = estimate_crawl_time(url, options)
        
        return jsonify({
            "success": True,
            "url": url,
            "estimated_time": estimated_time,
            "recommended_mode": "sync" if estimated_time < 3 else "async",
            "complexity": "simple" if estimated_time < 3 else "complex"
        })
        
    except Exception as e:
        logger.error(f"Estimate error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@v2_api.route('/health', methods=['GET'])
async def health_check():
    """Health check endpoint"""
    return jsonify({
        "success": True,
        "status": "healthy",
        "version": "2.0",
        "timestamp": datetime.utcnow().isoformat()
    })


# Documentation endpoint
@v2_api.route('/docs', methods=['GET'])
async def api_docs():
    """Return API documentation"""
    docs = {
        "version": "2.0",
        "endpoints": {
            "/v2/crawl": {
                "method": "POST",
                "description": "Smart crawl with automatic sync/async execution",
                "parameters": {
                    "url": "URL to crawl (required)",
                    "javascript": "Enable JavaScript (default: false)",
                    "screenshot": "Capture screenshot (default: false)",
                    "full_content": "Extract full content (default: false)",
                    "depth": "Crawl depth 0-3 (default: 0)",
                    "session_id": "Browser session ID for persistence",
                    "response_format": "Output format: full|minimal|llm (default: full)"
                }
            },
            "/v2/jobs/{job_id}": {
                "method": "GET",
                "description": "Check status of async crawl job"
            },
            "/v2/search": {
                "method": "POST",
                "description": "Search through previous crawls",
                "parameters": {
                    "query": "Search query (required)",
                    "limit": "Results per page 1-100 (default: 10)",
                    "offset": "Pagination offset (default: 0)"
                }
            },
            "/v2/workflows/{workflow_name}": {
                "method": "POST",
                "description": "Execute predefined workflows",
                "available_workflows": [
                    "analyze_website",
                    "monitor_changes",
                    "extract_data",
                    "research_topic"
                ]
            },
            "/v2/estimate": {
                "method": "POST",
                "description": "Estimate crawl complexity and time"
            }
        }
    }
    
    return jsonify(docs)


# Legacy compatibility - also register on /api/v2
@api_v2.route('/crawl', methods=['POST'])
@login_required
async def crawl_endpoint_legacy():
    """Legacy route for /api/v2/crawl"""
    return await crawl_endpoint()


@api_v2.route('/search', methods=['POST'])
@login_required  
async def search_endpoint_legacy():
    """Legacy route for /api/v2/search"""
    return await search_endpoint()


# ============================================================================
# ENDPOINTS FROM api.py - Migrated to V2
# ============================================================================

@v2_api.route('/suggest-urls', methods=['POST'])
@login_required
async def suggest_urls():
    """API endpoint to suggest URLs based on a topic or domain using Claude AI."""
    try:
        data = await request.get_json()
        
        # Extract parameters
        query = data.get('query', '').strip()
        limit = data.get('limit', 10)
        category = data.get('category', 'general')
        
        if not query:
            return jsonify({
                "success": False,
                "error": "No query provided"
            }), 400
        
        # Import the URL suggestion tool
        from ai.tools.url_suggestion import suggest_urls_based_on_topic
        
        logger.info(f"URL suggestion request for query: {query}, category: {category}")
        
        # Call the tool
        result = await suggest_urls_based_on_topic(
            topic=query,
            num_suggestions=limit,
            category=category
        )
        
        # Return the result
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"URL suggestion error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@v2_api.route('/code', methods=['POST'])
async def api_code():
    """Generate code examples based on user queries."""
    try:
        data = await request.get_json()
        query = data.get('query', '').strip()
        options = data.get('options', {})
        
        if not query:
            return jsonify({
                "success": False,
                "error": "No query provided"
            }), 400
        
        # Import the code generator
        from ai.code_generator import CodeGenerator
        generator = CodeGenerator()
        
        start_time = datetime.utcnow()
        result = await generator.generate_code(query, options)
        
        if not result.get('success'):
            return jsonify(result), 500
        
        # Calculate query time
        query_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Add metadata
        result['metadata']['query_time_ms'] = query_time_ms
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Code generation error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@v2_api.route('/models', methods=['GET'])
@login_required
async def get_claude_models():
    """Get available Claude models."""
    try:
        from ai.tools.claude_models import list_available_claude_models
        result = list_available_claude_models()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error fetching Claude models: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@v2_api.route('/claude-analyze', methods=['POST'])
@login_required
async def claude_analyze():
    """Analyze content with Claude AI."""
    try:
        data = await request.get_json()
        content = data.get('content', '')
        prompt = data.get('prompt', 'Analyze this content')
        model = data.get('model', 'claude-3-haiku-20240307')
        
        if not content:
            return jsonify({
                "success": False,
                "error": "No content provided"
            }), 400
        
        # Import Claude API
        from ai.anthropic import process_with_anthropic
        
        # Process with Claude
        result = await process_with_anthropic(content, {
            'prompt': prompt,
            'model': model
        })
        
        return jsonify({
            "success": True,
            "analysis": result,
            "model": model
        })
        
    except Exception as e:
        logger.error(f"Claude analysis error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================================
# ENDPOINTS FROM api_v2_llm.py - JavaScript Execution & Content Processing
# ============================================================================

@v2_api.route('/execute', methods=['POST'])
@login_required
async def execute_javascript_endpoint():
    """Execute JavaScript code on a webpage."""
    try:
        data = await request.get_json()
        url = data.get('url')
        javascript = data.get('javascript')
        
        if not url:
            return jsonify({
                "success": False,
                "error": "URL is required"
            }), 400
        
        if not javascript:
            return jsonify({
                "success": False,
                "error": "JavaScript code is required"
            }), 400
        
        # Extract execution options
        options = data.get('options', {})
        wait_before = options.get('wait_before', 2000)
        wait_after = options.get('wait_after', 1000)
        timeout = options.get('timeout', 30000)
        
        # Screenshot options
        take_screenshot = data.get('take_screenshot', False)
        screenshot_options = data.get('screenshot_options', {})
        
        # Markdown extraction options
        extract_markdown = data.get('extract_markdown', False)
        markdown_options = data.get('markdown_options', {})
        
        logger.info(f"JavaScript execution requested for {url}")
        
        # For now, execute via crawl with JavaScript
        from core.crawler import crawl_url
        
        # Create a JavaScript injection script
        inject_script = f"""
        (async function() {{
            // Wait before execution
            await new Promise(resolve => setTimeout(resolve, {wait_before}));
            
            // Execute user script
            {javascript}
            
            // Wait after execution
            await new Promise(resolve => setTimeout(resolve, {wait_after}));
        }})();
        """
        
        # Perform crawl with JavaScript injection
        result = await crawl_url(
            [url],
            javascript_enabled=True,
            custom_javascript=inject_script,
            take_screenshot=take_screenshot,
            markdown_extraction='enhanced' if extract_markdown else None,
            email=getattr(request, 'user_email', None)
        )
        
        if result and len(result) > 0:
            crawl_data = result[0]
            response = {
                "success": True,
                "url": url,
                "executed": True,
                "content": crawl_data.get('markdown_content', ''),
                "screenshot": crawl_data.get('screenshot_path', '') if take_screenshot else None,
                "metadata": {
                    'timestamp': datetime.utcnow().isoformat(),
                    'processing_time_ms': crawl_data.get('extraction_time', 0) * 1000
                }
            }
        else:
            response = {
                "success": False,
                "error": "Failed to execute JavaScript"
            }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"JavaScript execution error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@v2_api.route('/inject', methods=['POST'])
@login_required
async def inject_javascript_endpoint():
    """Generate and execute JavaScript based on natural language request."""
    try:
        data = await request.get_json()
        url = data.get('url')
        request_text = data.get('request')
        
        if not url:
            return jsonify({
                "success": False,
                "error": "URL is required"
            }), 400
        
        if not request_text:
            return jsonify({
                "success": False,
                "error": "Request description is required"
            }), 400
        
        # Generate JavaScript code from natural language
        from ai.anthropic import process_with_anthropic
        
        prompt = f"""Generate JavaScript code to: {request_text}
        
        Requirements:
        - The code should be safe and not access sensitive data
        - Use modern JavaScript (ES6+)
        - Include error handling
        - Return meaningful results
        
        Output only the JavaScript code, no explanation."""
        
        generated_code = await process_with_anthropic(prompt, {
            'model': 'claude-3-haiku-20240307',
            'max_tokens': 1000
        })
        
        # Execute the generated code
        data['javascript'] = generated_code
        return await execute_javascript_endpoint()
        
    except Exception as e:
        logger.error(f"JavaScript injection error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@v2_api.route('/validate', methods=['POST'])
@login_required
async def validate_javascript_endpoint():
    """Validate JavaScript code for safety and correctness."""
    try:
        data = await request.get_json()
        javascript = data.get('javascript', '')
        
        if not javascript:
            return jsonify({
                "success": False,
                "error": "JavaScript code is required"
            }), 400
        
        # Basic validation checks
        dangerous_patterns = [
            'eval(',
            'Function(',
            'setTimeout(',
            'setInterval(',
            'document.cookie',
            'localStorage',
            'sessionStorage',
            'XMLHttpRequest',
            'fetch('
        ]
        
        issues = []
        for pattern in dangerous_patterns:
            if pattern in javascript:
                issues.append(f"Potentially dangerous pattern found: {pattern}")
        
        # Check for syntax errors (basic)
        try:
            # This is a basic check - in production you'd use a proper JS parser
            compile(javascript, '<string>', 'exec')
        except SyntaxError as e:
            issues.append(f"Syntax error: {str(e)}")
        
        is_valid = len(issues) == 0
        
        return jsonify({
            "success": True,
            "valid": is_valid,
            "issues": issues,
            "metadata": {
                "code_length": len(javascript),
                "line_count": javascript.count('\n') + 1
            }
        })
        
    except Exception as e:
        logger.error(f"JavaScript validation error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@v2_api.route('/summarize', methods=['POST'])
@login_required
async def summarize_content_endpoint():
    """Generate AI-powered summary of content."""
    try:
        data = await request.get_json()
        content = data.get('content', '')
        options = data.get('options', {})
        
        if not content:
            return jsonify({
                "success": False,
                "error": "Content is required"
            }), 400
        
        # Extract options
        summary_type = options.get('type', 'concise')
        max_length = options.get('max_length', 500)
        format_type = options.get('format', 'paragraph')
        language = options.get('language', 'en')
        
        # Generate summary using AI
        from ai.anthropic import process_with_anthropic
        
        prompt = f"""Summarize the following content in a {summary_type} manner.
        Maximum length: {max_length} characters
        Format: {format_type}
        Language: {language}
        
        Content:
        {content[:5000]}  # Limit content to avoid token limits
        """
        
        summary = await process_with_anthropic(prompt, {
            'model': 'claude-3-haiku-20240307',
            'max_tokens': 1000
        })
        
        return jsonify({
            "success": True,
            "summary": summary,
            "metadata": {
                "original_length": len(content),
                "summary_length": len(summary),
                "compression_ratio": round(len(summary) / len(content), 2) if content else 0,
                "summary_type": summary_type
            }
        })
        
    except Exception as e:
        logger.error(f"Content summarization error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================================
# Additional V2 Utility Endpoints
# ============================================================================

@v2_api.route('/screenshot', methods=['POST'])
@login_required
async def screenshot_endpoint():
    """Capture screenshot of a webpage."""
    try:
        data = await request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({
                "success": False,
                "error": "URL is required"
            }), 400
        
        # Options
        full_page = data.get('full_page', False)
        wait_time = data.get('wait_time', 3000)
        width = data.get('width', 1920)
        height = data.get('height', 1080)
        
        from core.crawler import crawl_url
        
        # Capture screenshot via crawler
        result = await crawl_url(
            [url],
            javascript_enabled=True,
            take_screenshot=True,
            screenshot_options={
                'full_page': full_page,
                'viewport': {'width': width, 'height': height}
            },
            wait_time=wait_time,
            email=getattr(request, 'user_email', None)
        )
        
        if result and len(result) > 0:
            crawl_data = result[0]
            screenshot_path = crawl_data.get('screenshot_path', '')
            
            if screenshot_path and os.path.exists(screenshot_path):
                # Generate URL for screenshot
                filename = os.path.basename(screenshot_path)
                screenshot_url = f"/screenshots/{filename}"
                
                return jsonify({
                    "success": True,
                    "url": url,
                    "screenshot_url": screenshot_url,
                    "screenshot_path": screenshot_path,
                    "metadata": {
                        "full_page": full_page,
                        "viewport": {"width": width, "height": height},
                        "timestamp": datetime.utcnow().isoformat()
                    }
                })
        
        return jsonify({
            "success": False,
            "error": "Failed to capture screenshot"
        }), 500
        
    except Exception as e:
        logger.error(f"Screenshot error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@v2_api.route('/markdown', methods=['POST'])
@login_required
async def markdown_endpoint():
    """Extract clean markdown from a webpage."""
    try:
        data = await request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({
                "success": False,
                "error": "URL is required"
            }), 400
        
        # Options
        include_links = data.get('include_links', True)
        include_images = data.get('include_images', True)
        clean_format = data.get('clean_format', True)
        
        from core.crawler import crawl_url
        
        # Extract markdown via crawler
        result = await crawl_url(
            [url],
            javascript_enabled=data.get('javascript', True),
            markdown_extraction='enhanced',
            markdown_options={
                'include_links': include_links,
                'include_images': include_images,
                'clean_format': clean_format
            },
            email=getattr(request, 'user_email', None)
        )
        
        if result and len(result) > 0:
            crawl_data = result[0]
            markdown_content = crawl_data.get('markdown_content', '')
            
            return jsonify({
                "success": True,
                "url": url,
                "markdown": markdown_content,
                "metadata": {
                    "word_count": len(markdown_content.split()),
                    "char_count": len(markdown_content),
                    "extraction_time": crawl_data.get('extraction_time', 0)
                }
            })
        
        return jsonify({
            "success": False,
            "error": "Failed to extract markdown"
        }), 500
        
    except Exception as e:
        logger.error(f"Markdown extraction error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
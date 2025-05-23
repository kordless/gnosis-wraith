"""API routes for the Gnosis Wraith application.

Version: 2025-05-19 - Added AI endpoints for URL suggestion, code generation, and Claude model listing
"""
import os
import uuid
import logging
import datetime
import re
import json
import time
import random
from quart import request, jsonify, send_from_directory, url_for, session

from gnosis_wraith.server.routes import api_bp
from server.config import SCREENSHOTS_DIR, REPORTS_DIR, logger
from server.crawler import crawl_url
from server.reports import save_markdown_report, convert_markdown_to_html
# from ai.processing import process_with_llm  # This module was moved to individual provider files
from ai.toolbag import toolbag
from lightning.client import make_lightning_payment
from quart import Blueprint

# Create a blueprint for direct routes (missing /api prefix)
direct_bp = Blueprint('direct', __name__)

@api_bp.route('/crawl', methods=['POST'])
async def api_crawl():
    """API endpoint to crawl URLs with LLM processing."""
    logger.info("Blueprint /api/crawl endpoint called")
    data = await request.get_json()
    logger.info(f"API crawl received data: {data}")
    
    urls = data.get('urls', [])
    if 'url' in data and data['url']:
        urls.append(data['url'])
    
    if not urls:
        return jsonify({
            "success": False,
            "error": "No URLs provided"
        }), 400
    
    title = data.get('title', f"Web Crawl Report - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output_format = data.get('output_format', 'markdown')  # Options: 'markdown', 'html', 'json', or 'all'
    
    # Process all settings from request
    # Process JavaScript enabled setting
    javascript_enabled = data.get('javascript_enabled', False)
    if isinstance(javascript_enabled, str):
        javascript_enabled = javascript_enabled.lower() == 'true'
    
    # Process screenshot settings
    take_screenshot = data.get('take_screenshot', True)
    if isinstance(take_screenshot, str):
        take_screenshot = take_screenshot.lower() == 'true'
    
    # Process OCR extraction settings
    ocr_extraction = data.get('ocr_extraction', True)
    if isinstance(ocr_extraction, str):
        ocr_extraction = ocr_extraction.lower() == 'true'
    
    # Process markdown extraction settings
    markdown_extraction = data.get('markdown_extraction', 'enhanced')
    
    logger.info(f"Crawl settings: JS={javascript_enabled}, Screenshot={take_screenshot}, OCR={ocr_extraction}, Markdown={markdown_extraction}")
    
    # Get LLM configuration from request
    llm_provider = data.get('llm_provider', '')
    llm_token = data.get('llm_token', '')
    
    # Check if we should use Lightning Network for payment
    use_lightning = data.get('use_lightning', False)
    lightning_budget = data.get('lightning_budget', 0)
    
    # If Lightning is enabled but no provider specified, use local model as fallback
    if use_lightning and not llm_provider:
        llm_provider = 'local'
    
    logger.info(f"API crawl request: {len(urls)} URLs, JavaScript {'enabled' if javascript_enabled else 'disabled'}, LLM: {llm_provider or 'None'}")
    
    try:
        # Crawl the URLs
        # Pass all the settings to the crawl_url function
        # Make sure the crawl_url function is updated to accept these parameters
        raw_crawl_results = await crawl_url(
            urls, 
            javascript_enabled=javascript_enabled,
            take_screenshot=take_screenshot,
            ocr_extraction=ocr_extraction,
            markdown_extraction=markdown_extraction
        )
        
        # Ensure crawl_results is always a list
        if isinstance(raw_crawl_results, dict):
            logger.info("Single result converted to list for processing")
            crawl_results = [raw_crawl_results]
        else:
            logger.info(f"Results type: {type(raw_crawl_results)}")
            crawl_results = raw_crawl_results if isinstance(raw_crawl_results, list) else []
        
        # Process extracted text with LLM if provider and token are specified
        if llm_provider:
            overall_text = ""
            
            # Process each result with LLM
            for result in crawl_results:
                if 'extracted_text' in result and result['extracted_text']:
                    try:
                        # Check if we need to pay for this processing via Lightning
                        if use_lightning:
                            # Make Lightning Network payment
                            payment_successful = await make_lightning_payment(
                                service_type="text-analysis", 
                                amount=min(100, lightning_budget),  # Use 100 sats or budget, whichever is lower
                                provider=llm_provider
                            )
                            
                            # If payment failed, skip LLM processing
                            if not payment_successful:
                                result['llm_error'] = "Lightning payment failed"
                                continue
                            
                            # Reduce available budget
                            lightning_budget -= 100
                            
                            # If budget exhausted, skip future processing
                            if lightning_budget <= 0:
                                break
                        
                        # Process the extracted text with the specified LLM
                        if llm_provider == 'anthropic':
                            from ai.anthropic import process_with_anthropic
                            llm_summary = await process_with_anthropic(
                                result['extracted_text'], 
                                llm_token
                            )
                        elif llm_provider == 'openai':
                            from ai.openai import process_with_openai
                            llm_summary = await process_with_openai(
                                result['extracted_text'], 
                                llm_token
                            )
                        else:
                            llm_summary = f"Unsupported LLM provider: {llm_provider}"
                        
                        result['llm_summary'] = llm_summary
                        result['llm_provider'] = llm_provider
                        
                        # Collect text for overall summary
                        if len(overall_text) < 10000:  # Keep overall text within reasonable limits
                            overall_text += f"\n\n--- {result.get('title', 'Untitled Page')} ---\n\n"
                            overall_text += result['extracted_text'][:1000]  # Take first 1000 chars from each result
                        
                        logger.info(f"LLM processing completed for {result.get('url', 'unknown URL')}")
                    except Exception as llm_error:
                        logger.error(f"LLM processing error: {str(llm_error)}")
                        result['llm_error'] = str(llm_error)
            
            # Generate an overall summary if we have enough text
            if overall_text and len(crawl_results) > 1:
                try:
                    # Check if we need to pay for this processing via Lightning
                    if use_lightning and lightning_budget >= 200:
                        # Make Lightning Network payment for overall summary
                        payment_successful = await make_lightning_payment(
                            service_type="overall-analysis", 
                            amount=200,  # Higher cost for overall analysis
                            provider=llm_provider
                        )
                        
                        if payment_successful:
                            lightning_budget -= 200
                            
                            # Process for overall summary
                            overall_prompt = f"You've analyzed content from {len(crawl_results)} webpages. Please provide a brief executive summary that synthesizes the key information across all pages:\n\n{overall_text}"
                            if llm_provider == 'anthropic':
                                from ai.anthropic import process_with_anthropic
                                overall_summary = await process_with_anthropic(overall_prompt, llm_token)
                            elif llm_provider == 'openai':
                                from ai.openai import process_with_openai
                                overall_summary = await process_with_openai(overall_prompt, llm_token)
                            else:
                                overall_summary = f"Unsupported LLM provider: {llm_provider}"
                            
                            # Add to first result for inclusion in the report
                            if overall_summary:
                                crawl_results[0]['overall_summary'] = overall_summary
                    elif not use_lightning:
                        # Process for overall summary without Lightning payment
                        overall_prompt = f"You've analyzed content from {len(crawl_results)} webpages. Please provide a brief executive summary that synthesizes the key information across all pages:\n\n{overall_text}"
                        if llm_provider == 'anthropic':
                            from ai.anthropic import process_with_anthropic
                            overall_summary = await process_with_anthropic(overall_prompt, llm_token)
                        elif llm_provider == 'openai':
                            from ai.openai import process_with_openai
                            overall_summary = await process_with_openai(overall_prompt, llm_token)
                        else:
                            overall_summary = f"Unsupported LLM provider: {llm_provider}"
                    
                        # Add to first result for inclusion in the report
                        if overall_summary:
                            crawl_results[0]['overall_summary'] = overall_summary
                except Exception as overall_error:
                    logger.error(f"Overall summary error: {str(overall_error)}")
        
        results = {
            "success": True,
            "urls_processed": urls,
            "results": []
        }
        
        for result in crawl_results:
            # Process URL to handle list/string inconsistencies
            response_url = result.get('url', urls[0] if urls else "Unknown URL")
            if isinstance(response_url, list) and len(response_url) > 0:
                response_url = response_url[0]  # Extract single URL from list
            
            result_item = {
                "url": response_url,  # Use processed URL
                "title": result.get('title', 'Untitled Page'),
                "javascript_enabled": result.get('javascript_enabled', javascript_enabled),
                "take_screenshot": result.get('take_screenshot', take_screenshot),
                "ocr_extraction": result.get('ocr_extraction', ocr_extraction),
                "markdown_extraction": result.get('markdown_extraction', markdown_extraction)
            }
            
            if 'error' in result:
                result_item['error'] = result['error']
            else:
                # Get relative paths for the web app
                if 'screenshot' in result:
                    result_item['screenshot'] = os.path.basename(result['screenshot'])
                
                # Truncate extracted text if too long
                if 'extracted_text' in result:
                    result_item['extracted_text'] = result['extracted_text'][:1000] + '...' if len(result['extracted_text']) > 1000 else result['extracted_text']
                
                # Include LLM summary if available
                if 'llm_summary' in result:
                    result_item['llm_summary'] = result['llm_summary']
                
                # Include overall summary if available
                if 'overall_summary' in result:
                    result_item['overall_summary'] = result['overall_summary']
                
                # Include any LLM errors
                if 'llm_error' in result:
                    result_item['llm_error'] = result['llm_error']
            
            results['results'].append(result_item)
        
        # Process reports based on requested output format
        if output_format in ['markdown', 'all', 'both']:
            markdown_path = await save_markdown_report(title, crawl_results)
            results['report_path'] = os.path.basename(markdown_path)
            
            # Convert to HTML if requested
            if output_format in ['html', 'all', 'both']:
                html_path = await convert_markdown_to_html(markdown_path)
                results['html_path'] = os.path.basename(html_path)
        
        # Generate JSON if requested
        if output_format in ['json', 'all']:
            from server.reports import save_json_report
            json_path = await save_json_report(title, crawl_results)
            results['json_path'] = os.path.basename(json_path)
        
        # Check if 'results' is a dictionary with a 'results' key or a string
        if isinstance(results, dict) and 'results' in results:
            result_count = len(results.get('results', []))
            logger.info(f"API crawl success: returning {result_count} results")
        else:
            logger.info(f"API crawl success: returning direct result")
        return jsonify(results)
    
    except Exception as e:
        logger.error(f"API crawl error: {str(e)}")
        error_response = {
            "success": False,
            "error": str(e)
        }
        logger.error(f"Returning error response: {error_response}")
        return jsonify(error_response), 500

@api_bp.route('/upload', methods=['POST'])
async def api_upload():
    """API endpoint to upload images - defers to the main app implementation."""
    try:
        # This route is handled by the main app.py implementation
        from app import api_upload as main_api_upload
        return await main_api_upload()
    except Exception as e:
        logger.error(f"API upload error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_bp.route('/reports/<path:filename>', methods=['DELETE'])
async def delete_report(filename):
    """Delete a report file."""
    try:
        file_path = os.path.join(REPORTS_DIR, filename)
        
        if not os.path.exists(file_path):
            return jsonify({
                "success": False,
                "error": "File not found"
            }), 404
        
        # Delete the file
        os.remove(file_path)
        
        # If HTML version exists, delete it too
        if filename.endswith('.md'):
            html_path = file_path.replace('.md', '.html')
            if os.path.exists(html_path):
                os.remove(html_path)
        
        return jsonify({
            "success": True,
            "message": f"Report {filename} deleted successfully"
        })
    
    except Exception as e:
        logger.error(f"Error deleting report {filename}: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_bp.route('/settings', methods=['POST'])
async def update_settings():
    """Update application settings."""
    try:
        data = await request.get_json()
        
        # Update environment variables for server-side settings
        if 'server_url' in data:
            os.environ['GNOSIS_WRAITH_SERVER_URL'] = data['server_url']
            
        if 'screenshot_quality' in data:
            os.environ['GNOSIS_WRAITH_SCREENSHOT_QUALITY'] = data['screenshot_quality']
            
        if 'javascript_enabled' in data:
            os.environ['GNOSIS_WRAITH_JAVASCRIPT_ENABLED'] = str(data['javascript_enabled']).lower()
            
        if 'storage_path' in data and data['storage_path']:
            new_path = data['storage_path']
            # Validate the path exists or create it
            try:
                os.makedirs(new_path, exist_ok=True)
                os.environ['GNOSIS_WRAITH_STORAGE_PATH'] = new_path
                
                # Update global variables if storage path changed
                global STORAGE_PATH, SCREENSHOTS_DIR, REPORTS_DIR, DATA_DIR
                from server.config import STORAGE_PATH
                STORAGE_PATH = new_path
                SCREENSHOTS_DIR = os.path.join(STORAGE_PATH, "screenshots")
                REPORTS_DIR = os.path.join(STORAGE_PATH, "reports")
                DATA_DIR = os.path.join(STORAGE_PATH, "data")
                
                # Ensure the new directories exist
                os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
                os.makedirs(REPORTS_DIR, exist_ok=True)
                os.makedirs(DATA_DIR, exist_ok=True)
                
                logger.info(f"Storage path updated to {new_path}")
            except Exception as e:
                logger.error(f"Error setting storage path: {str(e)}")
                return jsonify({
                    "success": False,
                    "error": f"Invalid storage path: {str(e)}"
                }), 400
        
        # Save non-sensitive settings to data directory for persistence
        try:
            # Import DATA_DIR from config
            from server.config import DATA_DIR
            
            # Create settings object with only non-sensitive data
            settings_to_save = {
                "server_url": data.get('server_url', os.environ.get('GNOSIS_WRAITH_SERVER_URL', '')),
                "screenshot_quality": data.get('screenshot_quality', os.environ.get('GNOSIS_WRAITH_SCREENSHOT_QUALITY', 'medium')),
                "javascript_enabled": data.get('javascript_enabled', os.environ.get('GNOSIS_WRAITH_JAVASCRIPT_ENABLED', 'false') == 'true'),
                "storage_path": STORAGE_PATH,
                "saved_timestamp": datetime.datetime.now().isoformat()
            }
            
            # Save settings to JSON file
            settings_file = os.path.join(DATA_DIR, "server_settings.json")
            with open(settings_file, 'w') as f:
                json.dump(settings_to_save, f, indent=2)
                
            logger.info(f"Settings saved to {settings_file}")
        except Exception as save_error:
            logger.error(f"Error saving settings to file: {str(save_error)}")
            # Continue even if saving to file fails - settings are still in environment variables
        
        # Note: We don't store LLM tokens on the server for security reasons
        # The client will send the appropriate token with each API request
        
        logger.info("Settings updated successfully")
        return jsonify({
            "success": True,
            "message": "Settings updated successfully"
        })
        
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_bp.route('/code', methods=['POST'])
async def api_code():
    """API endpoint to generate code examples based on user queries.
    
    This endpoint processes a user's natural language request and returns
    appropriately formatted code examples with proper syntax highlighting.
    
    Request format:
    {
        "query": "string",
        "options": {
            "language_preference": "string", // Optional preferred language
            "max_tokens": int,               // Optional max token limit
            "format": "string"               // Optional format preference (raw/formatted)
        }
    }
    
    Response format:
    {
        "success": true,
        "language": "string",       // The language of the generated code
        "code": "string",           // The generated code
        "metadata": {
            "token_count": int,     // Number of tokens in the generated code
            "model": "string",      // Model used for generation
            "query_time_ms": int,   // Time taken to generate the code
            "language_info": {      // Language-specific metadata
                "name": "string",   // Full language name
                "icon": "string",   // Icon class for the language
                "class": "string"   // CSS class for highlighting
            }
        }
    }
    """
    try:
        data = await request.get_json()
        
        # Extract query and options
        query = data.get('query', '').strip()
        options = data.get('options', {})
        
        if not query:
            return jsonify({
                "success": False,
                "error": "No query provided"
            }), 400
        
        # Extract optional parameters
        language_preference = options.get('language_preference', '')
        max_tokens = options.get('max_tokens', 2000)
        format_type = options.get('format', 'formatted')
        
        logger.info(f"Code generation requested for query: {query}")
        
        # Language detection logic
        # This is a simplified version for the stub - in a real implementation,
        # this would use more sophisticated language detection
        language = detect_language_from_query(query)
        
        # If language_preference is specified and is valid, use it instead
        if language_preference and language_preference in LANGUAGE_MAP:
            language = language_preference
        
        # Get example code - this would be replaced with actual LLM code generation
        code = get_code_example(language)
        
        # Get language information
        language_info = get_language_info(language)
        
        # Simulate processing time
        time.sleep(0.3)  # Simulate a brief delay
        
        return jsonify({
            "success": True,
            "language": language,
            "code": code,
            "metadata": {
                "token_count": len(code),
                "model": "gnosis-wraith-code-v1",
                "query_time_ms": random.randint(300, 800),
                "language_info": language_info
            }
        })
        
    except Exception as e:
        logger.error(f"Code generation API error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/suggest', methods=['POST'])
async def suggest_url():
    """
    Suggest a URL based on a query using the toolbag system.
    """
    try:
        # Parse request data
        data = await request.get_json()
        
        # Extract parameters
        query = data.get('query', '').strip()
        provider = data.get('provider', 'anthropic')
        model = data.get('model', 'claude-3-5-haiku-20241022')
        tools = data.get('tools', ['suggest_url', 'check_for_odd_user'])
        api_key = data.get('api_key', '')
        
        # Validate query
        if not query:
            return jsonify({
                "success": False,
                "error": "No query provided"
            }), 400
        
        # STEP 1: Check if user is acting odd
        logger.info(f"STEP 1: Calling check_for_odd_user with query: '{query}'")
        check_result = await toolbag.execute(
            tools=['check_for_odd_user'],
            query=query,
            provider=provider,
            model=model,
            api_key=api_key
        )
        
        # Extract check_for_odd_user result
        check_for_odd_user_result = None
        if check_result.get('success') and 'conversation' in check_result:
            for message in reversed(check_result['conversation']):
                if message.get('role') == 'user' and isinstance(message.get('content'), list):
                    for content_item in message['content']:
                        if content_item.get('type') == 'tool_result':
                            tool_result_str = content_item.get('content', '{}')
                            try:
                                parsed_result = json.loads(tool_result_str)
                                if 'user_is_acting_odd' in parsed_result:
                                    check_for_odd_user_result = parsed_result
                                    logger.info(f"Found check_for_odd_user result: {check_for_odd_user_result}")
                                    break
                            except json.JSONDecodeError:
                                logger.error(f"Failed to parse check_for_odd_user result: {tool_result_str}")
                if check_for_odd_user_result:
                    break
        
        # STEP 2: Always call suggest_url, but with context if user is acting odd
        is_odd = check_for_odd_user_result and check_for_odd_user_result.get('user_is_acting_odd', False)
        
        # Build the suggest_url query with context
        suggest_query = query
        if is_odd:
            suggest_query += f"\n\nContext: User appears to be chatting rather than requesting URL crawling. Please suggest a relevant URL based on their input and provide a friendly response explaining this is a web crawler."
        
        logger.info(f"STEP 2: Calling suggest_url with query: '{suggest_query}', is_odd: {is_odd}")
        suggest_result = await toolbag.execute(
            tools=['suggest_url'],
            query=suggest_query,
            provider=provider,
            model=model,
            api_key=api_key
        )
        
        # Extract suggest_url result
        tool_result = None
        if suggest_result.get('success') and 'conversation' in suggest_result:
            for message in reversed(suggest_result['conversation']):
                if message.get('role') == 'user' and isinstance(message.get('content'), list):
                    for content_item in message['content']:
                        if content_item.get('type') == 'tool_result':
                            tool_result_str = content_item.get('content', '{}')
                            try:
                                parsed_result = json.loads(tool_result_str)
                                if 'suggested_url' in parsed_result:
                                    tool_result = parsed_result
                                    logger.info(f"Found suggest_url result: {tool_result}")
                                    break
                            except json.JSONDecodeError:
                                logger.error(f"Failed to parse suggest_url result: {tool_result_str}")
                if tool_result:
                    break
        
        # Log combined results
        logger.info(f"Pipeline results:")
        logger.info(f"  - check_for_odd_user_result: {check_for_odd_user_result}")
        logger.info(f"  - suggest_url tool_result: {tool_result}")
        
        # Always ensure we have a URL result - combine the two tool results
        if tool_result and tool_result.get('success'):
            # We have a suggest_url result, enhance it with odd user context if needed
            response = tool_result.copy()
            
            # Add odd user context if user is acting odd
            if check_for_odd_user_result and check_for_odd_user_result.get('user_is_acting_odd', False):
                response['user_acting_odd'] = True
                response['odd_user_guidance'] = check_for_odd_user_result.get('guidance', '')
                response['check_for_odd_user_thinking'] = check_for_odd_user_result.get('thinking_notes', '')
                logger.info(f"Enhanced suggest_url result with odd user context")
            else:
                response['user_acting_odd'] = False
                logger.info(f"Normal suggest_url result (not odd user)")
            suggested_url = response.get('suggested_url', '')
            
            # Import URL validation functions
            from ai.tools.url_suggestion import is_valid_url, create_search_url
            
            # Check if the suggested URL is valid
            if suggested_url and not is_valid_url(suggested_url):
                logger.warning(f"Invalid URL from AI: '{suggested_url}', applying search fallback")
                
                # Create search URL fallback
                search_url = create_search_url(suggested_url, query)
                
                if search_url:
                    logger.info(f"Generated search URL fallback: {search_url}")
                    response.update({
                        "suggested_url": search_url,
                        "original_input": suggested_url,
                        "fallback_used": True,
                        "search_engine": "Search Engine",
                        "javascript_recommended": True,
                        "javascript_settle_time_ms": 3000,
                        "crawling_notes": f"Converted '{suggested_url}' to search URL: {search_url}"
                    })
                    return jsonify(response)
                else:
                    logger.error(f"Search URL fallback failed for: '{suggested_url}'")
                    response.update({
                        "success": False,
                        "error": "Invalid URL format and search fallback failed",
                        "suggested_url": suggested_url
                    })
                    return jsonify(response)
            else:
                # URL is valid, return the enhanced response
                logger.info(f"Valid URL returned: {suggested_url}")
                return jsonify(response)
        
        # If we somehow don't have a suggest_url result, this is a failure case
        logger.error("No suggest_url result found after pipeline execution")
        return jsonify({
            "success": False,
            "error": "Failed to get URL suggestion from pipeline",
            "query": query,
            "check_for_odd_user_result": check_for_odd_user_result
        })
    
    except Exception as e:
        logger.error(f"URL suggestion error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_bp.route('/code_assistant', methods=['POST'])
async def code_assistant():
    return False

# Add a direct route for /suggest that forwards to the API route
@direct_bp.route('/suggest', methods=['POST'])
async def direct_suggest():
    """Direct /suggest endpoint that forwards to /api/suggest.
    
    This endpoint exists to support the minimal interface which calls /suggest 
    directly instead of /api/suggest. It forwards the request to the main API endpoint.
    """
    # Just call the main API endpoint's function
    return await suggest_url()


@api_bp.route('/log', methods=['POST'])
async def api_log():
    """API endpoint to handle client-side logging events.
    
    This endpoint receives log events from the frontend and can store them
    or process them as needed. Currently just acknowledges receipt.
    """
    try:
        data = await request.get_json()
        
        # Extract log information
        event_type = data.get('event', 'unknown')
        timestamp = data.get('timestamp', datetime.datetime.now().isoformat())
        
        # Log the event server-side for debugging/monitoring
        logger.info(f"Client log event: {event_type} at {timestamp}")
        
        # Could store in database, file, or send to monitoring service here
        # For now, just acknowledge receipt
        
        return jsonify({
            "success": True,
            "message": "Log event received",
            "event": event_type,
            "timestamp": timestamp
        })
        
    except Exception as e:
        logger.error(f"Error handling log event: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_bp.route('/models/claude', methods=['GET'])
async def list_claude_models():
    """API endpoint to list available Claude models with their capabilities.
    
    This is an informational endpoint that doesn't require authentication.
    It provides details about Claude models that can be used with the application.
    """
    try:
        # Define Claude model information
        claude_models = [
            {
                "id": "claude-3-haiku-20240307",
                "name": "Claude 3 Haiku",
                "description": "Fast and affordable model for natural chat and quick tasks",
                "capabilities": ["Text Analysis", "Code Generation", "Content Summarization"],
                "context_window": 200000,
                "pricing_tier": "Low",
                "release_date": "March 2024",
                "best_for": ["Quick responses", "Low-complexity tasks", "High volume interactions"]
            },
            {
                "id": "claude-3-sonnet-20240229",
                "name": "Claude 3 Sonnet",
                "description": "Balanced model for complex tasks with excellent reasoning",
                "capabilities": ["Text Analysis", "Code Generation", "Content Summarization", "Complex Reasoning"],
                "context_window": 200000,
                "pricing_tier": "Medium",
                "release_date": "March 2024",
                "best_for": ["Balanced performance", "Medium-complexity tasks", "Technical writing"]
            },
            {
                "id": "claude-3-opus-20240229",
                "name": "Claude 3 Opus",
                "description": "Most powerful model with exceptional reasoning and instruction following",
                "capabilities": ["Text Analysis", "Code Generation", "Content Summarization", "Complex Reasoning", "Advanced Analysis"],
                "context_window": 200000,
                "pricing_tier": "High",
                "release_date": "March 2024",
                "best_for": ["High-complexity tasks", "Advanced reasoning", "Critical applications"]
            }
        ]
        
        # Get application's default model
        default_model = "claude-3-5-haiku-20241022"  # Default to Haiku for faster, more affordable responses
        
        # Check if app has a token
        has_app_token = bool(os.environ.get('ANTHROPIC_API_KEY'))
        
        return jsonify({
            "success": True,
            "models": claude_models,
            "default_model": default_model,
            "app_token_available": has_app_token,
            "app_supported": True
        })
    
    except Exception as e:
        logger.error(f"Error listing Claude models: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

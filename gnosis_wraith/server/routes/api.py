"""API routes for the Gnosis Wraith application."""
import os
import uuid
import logging
import datetime
from quart import request, jsonify, send_from_directory, url_for

from gnosis_wraith.server.routes import api_bp
from server.config import SCREENSHOTS_DIR, REPORTS_DIR, logger
from server.crawler import crawl_urls
from server.reports import save_markdown_report, convert_markdown_to_html
from ai.processing import process_with_llm
from lightning.client import make_lightning_payment

@api_bp.route('/crawl', methods=['POST'])
async def api_crawl():
    """API endpoint to crawl URLs with LLM processing."""
    data = await request.get_json()
    
    urls = data.get('urls', [])
    if 'url' in data and data['url']:
        urls.append(data['url'])
    
    if not urls:
        return jsonify({
            "success": False,
            "error": "No URLs provided"
        }), 400
    
    title = data.get('title', f"Web Crawl Report - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output_format = data.get('output_format', 'markdown')
    
    # Process JavaScript enabled setting from request
    javascript_enabled = data.get('javascript_enabled', False)
    if isinstance(javascript_enabled, str):
        javascript_enabled = javascript_enabled.lower() == 'true'
    
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
        crawl_results = await crawl_urls(urls, javascript_enabled=javascript_enabled)
        
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
                        llm_summary = await process_with_llm(
                            result['extracted_text'], 
                            llm_provider, 
                            llm_token
                        )
                        
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
                            overall_summary = await process_with_llm(overall_prompt, llm_provider, llm_token)
                            
                            # Add to first result for inclusion in the report
                            if overall_summary:
                                crawl_results[0]['overall_summary'] = overall_summary
                    elif not use_lightning:
                        # Process for overall summary without Lightning payment
                        overall_prompt = f"You've analyzed content from {len(crawl_results)} webpages. Please provide a brief executive summary that synthesizes the key information across all pages:\n\n{overall_text}"
                        overall_summary = await process_with_llm(overall_prompt, llm_provider, llm_token)
                        
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
            result_item = {
                "url": result['url'],
                "title": result.get('title', 'Untitled Page'),
                "javascript_enabled": result.get('javascript_enabled', javascript_enabled)
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
        
        if output_format in ['markdown', 'both']:
            markdown_path = await save_markdown_report(title, crawl_results)
            results['report_path'] = os.path.basename(markdown_path)
            
            # Convert to HTML if both formats requested
            if output_format == 'both':
                html_path = await convert_markdown_to_html(markdown_path)
                results['html_path'] = os.path.basename(html_path)
        
        return jsonify(results)
    
    except Exception as e:
        logger.error(f"API crawl error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

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
                global STORAGE_PATH, SCREENSHOTS_DIR, REPORTS_DIR
                from server.config import STORAGE_PATH
                STORAGE_PATH = new_path
                SCREENSHOTS_DIR = os.path.join(STORAGE_PATH, "screenshots")
                REPORTS_DIR = os.path.join(STORAGE_PATH, "reports")
                
                # Ensure the new directories exist
                os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
                os.makedirs(REPORTS_DIR, exist_ok=True)
                
                logger.info(f"Storage path updated to {new_path}")
            except Exception as e:
                logger.error(f"Error setting storage path: {str(e)}")
                return jsonify({
                    "success": False,
                    "error": f"Invalid storage path: {str(e)}"
                }), 400
        
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
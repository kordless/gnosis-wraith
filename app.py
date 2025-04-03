"""
Gnosis Wraith Main Application

This is the main entry point for the Gnosis Wraith application which can 
run as both a web server and a CLI tool.
"""

import os
import re
import sys
import json
import asyncio
import datetime
import uuid
import click
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from quart import Quart, render_template, request, jsonify, send_from_directory, redirect, url_for

# Import config and initialize logging
from server.config import logger, STORAGE_PATH, SCREENSHOTS_DIR, REPORTS_DIR, check_gpu_availability

# Import crawler and reporting modules
from server.crawler import extract_urls, crawl_urls
from server.reports import save_markdown_report, convert_markdown_to_html, generate_markdown_report

# Import AI processing modules
from ai.processing import process_with_llm
from lightning.client import make_lightning_payment

# Create Quart app
app = Quart(__name__, 
           static_folder='gnosis_wraith/server/static', 
           template_folder='gnosis_wraith/server/templates')

# Register blueprints if available (in try block to handle restructuring phase)
try:
    from gnosis_wraith.server.routes import register_blueprints
    register_blueprints(app)
    # Note: When blueprints are registered, they take precedence over routes defined here
    # During refactoring, we'll keep the original routes as fallbacks
    logger.info("Blueprints registered successfully")
except ImportError as e:
    logger.warning(f"Could not register blueprints: {str(e)}")
    logger.warning("Falling back to monolithic route definitions")

# Ensure the downloads directory exists
os.makedirs(os.path.join(os.path.dirname(__file__), 'gnosis_wraith/server/static/downloads'), exist_ok=True)

# Web routes - These will be used if blueprints aren't registered
# They'll be ignored if the route is already defined by a blueprint

@app.route('/')
async def index():
    """Render the index page."""
    return await render_template('index.html')

@app.route('/api/crawl', methods=['POST'])
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
                            # Make Lightning Network payment (this is a placeholder for your actual payment code)
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
                        # Make Lightning Network payment for overall summary (more expensive than individual summaries)
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
        
        # Always generate markdown report
        markdown_path = await save_markdown_report(title, crawl_results)
        results['report_path'] = os.path.basename(markdown_path)
        
        # Always convert to HTML as well
        html_path = await convert_markdown_to_html(markdown_path)
        results['html_path'] = os.path.basename(html_path)
        
        return jsonify(results)
    
    except Exception as e:
        logger.error(f"API crawl error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/upload', methods=['POST'])
async def api_upload():
    """API endpoint to upload images."""
    logger.info("API upload endpoint called")
    files = await request.files
    form = await request.form
    logger.info(f"Files received: {files.keys()}, Form data: {form.keys()}")
    
    if 'image' not in files:
        return jsonify({
            "success": False,
            "error": "No image file provided"
        }), 400
    
    try:
        file = files['image']
        title = form.get('title', 'Image Analysis Report')
        filename = f"{uuid.uuid4().hex}.png"
        file_path = os.path.join(SCREENSHOTS_DIR, filename)
        await file.save(file_path)
        
        # Use ModelManager to extract text from the image
        from ai.models import ModelManager
        model_manager = ModelManager()
        extracted_text = await model_manager.extract_text_from_image(file_path)
        
        # Copy the image to a predictable location relative to REPORTS_DIR
        # This ensures the screenshot can be properly referenced in the Markdown
        report_images_dir = os.path.join(REPORTS_DIR, "images")
        os.makedirs(report_images_dir, exist_ok=True)
        
        # Copy the image to the reports/images directory
        import shutil
        report_image_path = os.path.join(report_images_dir, os.path.basename(file_path))
        shutil.copy2(file_path, report_image_path)
        
        logger.info(f"Image uploaded to {file_path} and copied to {report_image_path} for reports")
        
        # Create a simplified result for report generation
        image_result = {
            'url': f"Uploaded Image: {os.path.basename(file_path)}",  # Descriptive URL
            'title': f"Image Analysis: {os.path.basename(file_path)}",
            'screenshot': report_image_path,  # Use the path in reports/images
            'extracted_text': extracted_text
        }
        
        # Generate a report
        report_title = f"{title} - {datetime.datetime.now().strftime('%Y-%m-%d')}"
        logger.info(f"Generating image upload report with title: {report_title}")
        
        try:
            report_path = await save_markdown_report(report_title, [image_result])
            logger.info(f"Successfully generated markdown report: {report_path}")
            
            # Always convert to HTML as well
            html_path = await convert_markdown_to_html(report_path)
            logger.info(f"Successfully generated HTML report: {html_path}")
        except Exception as report_error:
            logger.error(f"Error generating reports: {str(report_error)}")
            raise
        
        return jsonify({
            "success": True,
            "file_path": os.path.basename(file_path),
            "extracted_text": extracted_text,
            "report_path": os.path.basename(report_path),
            "html_path": os.path.basename(html_path)
        })
    
    except Exception as e:
        logger.error(f"API upload error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/reports')
async def list_reports():
    """List all generated reports."""
    reports = []
    for file in os.listdir(REPORTS_DIR):
        if file.endswith('.md'):
            file_path = os.path.join(REPORTS_DIR, file)
            creation_time = os.path.getctime(file_path)
            reports.append({
                "filename": file,
                "created": datetime.datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S'),
                "size": os.path.getsize(file_path)
            })
    
    # Sort reports by creation time (newest first)
    reports.sort(key=lambda x: x['created'], reverse=True)
    
    return await render_template('reports.html', reports=reports)

@app.route('/reports/<path:filename>')
async def serve_report(filename):
    """Serve a report file."""
    return await send_from_directory(REPORTS_DIR, filename)

@app.route('/screenshots/<path:filename>')
async def serve_screenshot(filename):
    """Serve a screenshot file."""
    return await send_from_directory(SCREENSHOTS_DIR, filename)

@app.route('/extension')
async def serve_extension():
    """Generate and serve the extension zip file."""
    downloads_dir = os.path.join(os.path.dirname(__file__), 'gnosis_wraith/server/static/downloads')
    zip_path = os.path.join(downloads_dir, 'gnosis-wraith-extension.zip')
    
    # Check if extension zip exists, create it if not
    if not os.path.exists(zip_path):
        extension_dir = os.path.join(os.path.dirname(__file__), 'gnosis_wraith/extension')
        if os.path.exists(extension_dir):
            # Create downloads directory if it doesn't exist
            os.makedirs(downloads_dir, exist_ok=True)
            
            # Create zip file
            import zipfile
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(extension_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, os.path.join(extension_dir, '..'))
                        zipf.write(file_path, arcname)
    
    # Redirect to the static file
    return redirect(url_for('static', filename='downloads/gnosis-wraith-extension.zip'))

@app.route('/settings')
async def settings():
    """Render the settings page."""
    # Default settings
    settings_data = {
        'server_url': os.environ.get('GNOSIS_WRAITH_SERVER_URL', 'http://localhost:5678'),
        'llm_api_token': os.environ.get('GNOSIS_WRAITH_LLM_API_TOKEN', ''),
        'screenshot_quality': os.environ.get('GNOSIS_WRAITH_SCREENSHOT_QUALITY', 'medium'),
        'javascript_enabled': os.environ.get('GNOSIS_WRAITH_JAVASCRIPT_ENABLED', 'false') == 'true',
        'storage_path': STORAGE_PATH
    }
    
    return await render_template('settings.html', **settings_data)

@app.route('/api/reports/<path:filename>', methods=['DELETE'])
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

@app.route('/api/settings', methods=['POST'])
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

# CLI part using Click
@click.group()
def cli():
    """Gnosis Wraith CLI - A powerful web crawling tool that outputs markdown and images."""
    pass

@cli.command()
@click.option('-f', '--file', type=click.Path(exists=True), default=None, help="Path to the file containing URLs to crawl.")
@click.option('-u', '--uri', default=None, help="A single URI to crawl.")
@click.option('-o', '--output', default='markdown', type=click.Choice(['markdown', 'image', 'both']), 
              help="Output format: markdown, image, or both.")
@click.option('-t', '--title', default=None, help="Title for the markdown report.")
@click.option('-d', '--dir', default=None, help="Directory to save outputs. Defaults to current directory.")
def crawl(file, uri, output, title, dir):
    """Crawl specified URLs, capture screenshots, and generate output as markdown or images."""
    if bool(file) == bool(uri):
        click.echo("Error: Exactly one of --file or --uri must be provided.")
        return
    
    # Set output directory
    output_dir = dir if dir else REPORTS_DIR
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Set default title if not provided
    if not title:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if file:
            title = f"Web Crawl Report for URLs in {os.path.basename(file)} - {timestamp}"
        else:
            title = f"Web Crawl Report for {uri} - {timestamp}"
    
    # Extract URLs from file or use provided URI
    urls = []
    if file:
        with open(file, 'r') as f:
            content = f.read()
            urls = extract_urls(content)
    elif uri:
        urls = [uri]
    
    # Run the async crawl
    result = asyncio.run(async_crawl_cli(urls, output, title, output_dir))
    click.echo(json.dumps(result, indent=2))

async def async_crawl_cli(urls, output_format, title, output_dir):
    """Async function to crawl URLs and generate output for CLI."""
    try:
        crawl_results = await crawl_urls(urls)
        
        outputs = {}
        
        if output_format in ['markdown', 'both']:
            report_content = generate_markdown_report(title, crawl_results)
            import string
            valid_chars = string.ascii_letters + string.digits + '-_'
            safe_title = ''.join(c if c in valid_chars else '_' for c in title)
            filename = f"{safe_title}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

            markdown_path = os.path.join(output_dir, filename)
            
            import aiofiles
            async with aiofiles.open(markdown_path, 'w') as f:
                await f.write(report_content)
            
            outputs['markdown'] = markdown_path
            click.echo(f"Markdown report saved to {markdown_path}")
            
            # If both formats requested, convert markdown to HTML
            if output_format == 'both':
                html_path = await convert_markdown_to_html(markdown_path)
                outputs['html'] = html_path
                click.echo(f"HTML report saved to {html_path}")
            
        if output_format in ['image', 'both']:
            outputs['images'] = [result['screenshot'] for result in crawl_results if 'screenshot' in result]
            image_paths = ", ".join(outputs['images'])
            click.echo(f"Images saved to: {image_paths if outputs['images'] else 'None'}")
        
        click.echo(f"Crawling completed. {len(urls)} URLs processed.")
        return {
            "success": True,
            "result": {
                "output_format": output_format,
                "title": title,
                "urls_processed": urls,
                "url_count": len(urls),
                "outputs": outputs
            }
        }

    except Exception as e:
        error_message = f"An error occurred while processing: {str(e)}"
        click.echo(error_message)
        return {
            "success": False,
            "error": error_message
        }

# Main entry point
if __name__ == '__main__':
    # Call GPU check during application startup
    gpu_available = check_gpu_availability()

    # Check if running as CLI or as a web service
    if len(sys.argv) > 1:
        cli()
    else:
        print(f"Starting Gnosis Wraith service on port 5678")
        app.run(host='0.0.0.0', port=5678)
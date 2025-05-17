"""
Gnosis Wraith Main Application with Job-Based Processing

This is the main entry point for the Gnosis Wraith application which can 
run as both a web server and a CLI tool.
"""

# VERSION: 2025-05-14-V2 - Simple fix for string indices error

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
from server.browser import BrowserControl

from quart import Quart, render_template, request, jsonify, send_from_directory, redirect, url_for

# Import config and initialize logging
from server.config import logger, STORAGE_PATH, SCREENSHOTS_DIR, REPORTS_DIR, check_gpu_availability

# Import crawler and reporting modules
from server.crawler import extract_urls, crawl_url
from server.reports import save_markdown_report, convert_markdown_to_html, generate_markdown_report

# Import AI processing modules
from ai.processing import process_with_llm
from lightning.client import make_lightning_payment

from server.initializers import init_job_system

# Create Quart app
app = Quart(__name__, 
           static_folder='gnosis_wraith/server/static', 
           template_folder='gnosis_wraith/server/templates')

# Add version log at startup
@app.before_serving
async def log_version():
    version = "2025-05-14-V2"  # Match the version at the top of the file
    logger.info(f"Starting app_with_jobs.py version {version}")

# Initialize job-based processing system
init_job_system(app)

# Add a middleware-like function to log all requests - but only for non-static paths
@app.before_request
async def log_request():
    # Skip logging for static resources to reduce noise
    if not request.path.startswith('/static/'):
        logger.info(f"Request to: {request.path}")
    return None  # Continue with the request

# Register blueprints if available (in try block to handle restructuring phase)
try:
    from gnosis_wraith.server.routes import register_blueprints
    register_blueprints(app)
    # Note: When blueprints are registered, they take precedence over routes defined here
    # During refactoring, we'll keep the original routes as fallbacks
    logger.info("Blueprints registered successfully")
except ImportError as e:
    logger.warning(f"Could not register blueprints: {str(e)}")

# Ensure the downloads directory exists
os.makedirs(os.path.join(os.path.dirname(__file__), 'gnosis_wraith/server/static/downloads'), exist_ok=True)

# Web routes - These will be used if blueprints aren't registered
# They'll be ignored if the route is already defined by a blueprint

# Read version from manifest.json - THE SOURCE OF TRUTH for extension version
manifest_path = os.path.join(os.path.dirname(__file__), 'gnosis_wraith', 'extension', 'manifest.json')

# Always read from manifest.json to get the latest version
try:
    # Read directly from manifest.json - this is the source of truth
    with open(manifest_path, 'r') as f:
        manifest_data = json.load(f)
        EXTENSION_VERSION = manifest_data.get('version')
        if EXTENSION_VERSION:
            logger.info(f"Found extension version {EXTENSION_VERSION} in manifest.json")
        else:
            raise ValueError("No version key found in manifest.json")
except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
    # Fallback only in case of emergency
    EXTENSION_VERSION = '1.1.2'  # Updated fallback version
    logger.error(f"Could not read extension version from manifest.json: {e}")
    logger.warning(f"Using fallback extension version: {EXTENSION_VERSION}")

# Override with environment variable if set
if os.environ.get('EXTENSION_VERSION'):
    EXTENSION_VERSION = os.environ.get('EXTENSION_VERSION')
    logger.info(f"Overriding with extension version {EXTENSION_VERSION} from environment")

# Log the version being used
logger.info(f"Extension version {EXTENSION_VERSION} will be used for all operations")
    
# Then in the index route, pass the version to the template
@app.route('/')
async def index():
    """Render the index page."""
    return await render_template('index.html', extension_version=EXTENSION_VERSION)

@app.route('/api/upload', methods=['POST'])
async def api_upload():
    """API endpoint to upload images."""
    files = await request.files
    form = await request.form
    
    if 'image' not in files:
        return jsonify({
            "success": False,
            "error": "No image file provided"
        }), 400
    
    try:
        file = files['image']
        title = form.get('title', 'Image Analysis Report')
        original_filename = file.filename
        filename = f"{uuid.uuid4().hex}.png"
        file_path = os.path.join(SCREENSHOTS_DIR, filename)
        await file.save(file_path)
        
        # Check if OCR is enabled or disabled
        ocr_enabled = form.get('ocr_extraction', 'false').lower() == 'true'
        
        extracted_text = ""
        if ocr_enabled:
            # Use ModelManager to extract text from the image
            from ai.models import ModelManager
            model_manager = ModelManager()
            extracted_text = await model_manager.extract_text_from_image(file_path)
        else:
            extracted_text = "OCR text extraction was not enabled for this image."
        
        # Copy the image to a predictable location relative to REPORTS_DIR
        # This ensures the screenshot can be properly referenced in the Markdown
        report_images_dir = os.path.join(REPORTS_DIR, "images")
        os.makedirs(report_images_dir, exist_ok=True)
        
        # Copy the image to the reports/images directory
        import shutil
        report_image_path = os.path.join(report_images_dir, os.path.basename(file_path))
        shutil.copy2(file_path, report_image_path)
        
        # Create a simplified result for report generation
        image_result = {
            'url': f"Uploaded Image: {os.path.basename(file_path)}",  # Descriptive URL
            'title': f"Image Analysis: {os.path.basename(file_path)}",
            'original_filename': original_filename,  # Store the original filename
            'screenshot': report_image_path,  # Use the path in reports/images
            'extracted_text': extracted_text,
            'ocr_enabled': ocr_enabled  # Store whether OCR was enabled
        }
        
        # Generate a report
        report_title = f"{title} - {datetime.datetime.now().strftime('%Y-%m-%d')}"
        
        try:
            report_path = await save_markdown_report(report_title, [image_result])
            
            # Always convert to HTML as well
            html_path = await convert_markdown_to_html(report_path)
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
            
            # Get the title from the markdown file (first heading)
            title = file  # Default to filename
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(1000)  # Read just the beginning
                    match = re.search(r'^# (.+)$', content, re.MULTILINE)
                    if match:
                        title = match.group(1)
            except Exception as e:
                logger.error(f"Error reading report title: {str(e)}")
            
            reports.append({
                "filename": file,
                "title": title,
                "created": datetime.datetime.fromtimestamp(creation_time),  # Store as datetime object
                "created_str": datetime.datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S'),
                "size": os.path.getsize(file_path)
            })
    
    # Sort reports by creation time (newest first)
    reports.sort(key=lambda x: x['created'], reverse=True)
    
    return await render_template('reports.html', reports=reports)

@app.route('/reports/<path:filename>')
async def serve_report(filename):
    """Serve a report file."""
    # Check if the file exists
    file_path = os.path.join(REPORTS_DIR, filename)
    if not os.path.exists(file_path):
        # If HTML file doesn't exist, check if we need to convert from markdown
        if filename.endswith('.html'):
            # Try to find the corresponding markdown file
            md_filename = filename.replace('.html', '.md')
            md_file_path = os.path.join(REPORTS_DIR, md_filename)
            
            if os.path.exists(md_file_path):
                # Convert markdown to HTML on-demand
                try:
                    from server.reports import convert_markdown_to_html
                    html_file = await convert_markdown_to_html(md_file_path)
                    logger.info(f"Generated HTML file on-demand: {html_file}")
                    # Now try to serve the newly created file
                    return await send_from_directory(REPORTS_DIR, filename)
                except Exception as e:
                    logger.error(f"Error generating HTML on-demand: {str(e)}")
                    return f"Error generating HTML: {str(e)}", 500
            else:
                logger.error(f"Markdown file not found for HTML conversion: {md_file_path}")
                return f"Report not found: {filename}", 404
        else:
            logger.error(f"Report file not found: {file_path}")
            return f"Report not found: {filename}", 404
    
    return await send_from_directory(REPORTS_DIR, filename)

@app.route('/screenshots/<path:filename>')
async def serve_screenshot(filename):
    """Serve a screenshot file."""
    return await send_from_directory(SCREENSHOTS_DIR, filename)

@app.route('/extension')
async def serve_extension():
    """Generate and serve the extension zip file."""
    # Use absolute paths for better reliability
    app_root = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(app_root, 'gnosis_wraith', 'server', 'static')
    downloads_dir = os.path.join(static_dir, 'downloads')
    
    # Create downloads directory - ensure it exists with all parent directories
    os.makedirs(downloads_dir, exist_ok=True)
    
    # Log the relevant paths
    logger.info(f"App root: {app_root}")
    logger.info(f"Static directory: {static_dir}")
    logger.info(f"Downloads directory: {downloads_dir}")
    
    # Use the global version variable
    extension_version = EXTENSION_VERSION
    logger.info(f"Creating extension bundle version {extension_version}")
    
    # Create versioned filenames to prevent browser caching
    gnosis_zip_filename = f'gnosis-wraith-extension-{extension_version}.zip'
    webwraith_zip_filename = f'webwraith-extension-{extension_version}.zip'
    
    gnosis_zip_path = os.path.join(downloads_dir, gnosis_zip_filename)
    webwraith_zip_path = os.path.join(downloads_dir, webwraith_zip_filename)
    
    # Create extension zips with version in filename
    extension_dir = os.path.join(app_root, 'gnosis_wraith', 'extension')
    
    logger.info(f"Extension directory: {extension_dir}")
    logger.info(f"Extension directory exists: {os.path.exists(extension_dir)}")
    
    if os.path.exists(extension_dir):
        # Remove any old version zip files
        import glob
        old_zips = glob.glob(os.path.join(downloads_dir, 'gnosis-wraith-extension-*.zip'))
        old_zips.extend(glob.glob(os.path.join(downloads_dir, 'webwraith-extension-*.zip')))
        for old_zip in old_zips:
            try:
                os.remove(old_zip)
                logger.info(f"Removed old zip file: {old_zip}")
            except Exception as e:
                logger.error(f"Error removing old zip: {str(e)}")
        
        # Create fresh zip files with version in filename
        import zipfile
        
        try:
            # Create gnosis zip
            with zipfile.ZipFile(gnosis_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                files_added = 0
                for root, dirs, files in os.walk(extension_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, os.path.join(extension_dir, '..'))
                        zipf.write(file_path, arcname)
                        files_added += 1
                        
                logger.info(f"Added {files_added} files to extension zip")
            
            # Create webwraith zip (copy of gnosis zip with different name)
            import shutil
            shutil.copy2(gnosis_zip_path, webwraith_zip_path)
            
            logger.info(f"Extension zip created at: {gnosis_zip_path}")
            logger.info(f"Extension zip file exists: {os.path.exists(gnosis_zip_path)}")
            logger.info(f"Extension zip file size: {os.path.getsize(gnosis_zip_path)} bytes")
        except Exception as zip_error:
            logger.error(f"Error creating extension zip: {str(zip_error)}", exc_info=True)
            return jsonify({
                "success": False,
                "error": f"Failed to create extension zip: {str(zip_error)}"
            }), 500
    else:
        logger.error(f"Extension directory not found: {extension_dir}")
        return jsonify({
            "success": False,
            "error": "Extension directory not found"
        }), 500
    
    # Send file directly instead of redirecting to preserve filename
    from quart import send_file
    
    try:
        # For Quart 0.18.0 and above
        try:
            response = await send_file(
                gnosis_zip_path, 
                mimetype='application/zip',
                as_attachment=True,
                download_name=gnosis_zip_filename
            )
        except TypeError:
            # Fallback for older Quart versions
            response = await send_file(
                gnosis_zip_path, 
                mimetype='application/zip',
                as_attachment=True,
                attachment_filename=gnosis_zip_filename
            )
        
        # Force download headers
        response.headers['Content-Disposition'] = f'attachment; filename="{gnosis_zip_filename}"'
        response.headers['Content-Type'] = 'application/zip'
        
        # Add Cache-Control header to prevent caching
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        logger.info(f"Extension download successful: {gnosis_zip_filename}")
        return response
    
    except Exception as e:
        logger.error(f"Error sending extension file: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Failed to send extension file: {str(e)}"
        }), 500

@app.route('/webwraith-extension')
async def serve_webwraith_extension():
    """Alternate URL for serving the extension zip file."""
    downloads_dir = os.path.join(os.path.dirname(__file__), 'gnosis_wraith/server/static/downloads')
    
    # Use the global version variable
    extension_version = EXTENSION_VERSION
    
    # Create versioned filename
    webwraith_zip_filename = f'webwraith-extension-{extension_version}.zip'
    webwraith_zip_path = os.path.join(downloads_dir, webwraith_zip_filename)
    
    # Ensure the file exists
    if not os.path.exists(webwraith_zip_path):
        # If not, redirect to main extension route which will create it
        return redirect(url_for('serve_extension'))
    
    # Send file directly instead of redirecting to preserve filename
    from quart import send_file
    
    # For Quart 0.18.0 and above
    try:
        response = await send_file(
            webwraith_zip_path, 
            mimetype='application/zip',
            as_attachment=True,
            download_name=webwraith_zip_filename
        )
    except TypeError:
        # Fallback for older Quart versions
        response = await send_file(
            webwraith_zip_path, 
            mimetype='application/zip',
            as_attachment=True,
            attachment_filename=webwraith_zip_filename
        )
    
    # Force download headers
    response.headers['Content-Disposition'] = f'attachment; filename="{webwraith_zip_filename}"'
    response.headers['Content-Type'] = 'application/zip'
    
    # Add Cache-Control header to prevent caching
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

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
            except Exception as e:
                logger.error(f"Error setting storage path: {str(e)}")
                return jsonify({
                    "success": False,
                    "error": f"Invalid storage path: {str(e)}"
                }), 400
        
        # Note: We don't store LLM tokens on the server for security reasons
        # The client will send the appropriate token with each API request
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
@click.option('--enhanced-markdown/--no-enhanced-markdown', default=True, help="Use enhanced markdown generation.")
def crawl(file, uri, output, title, dir, enhanced_markdown):
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
    result = asyncio.run(async_crawl_cli(urls, output, title, output_dir, enhanced_markdown))
    click.echo(json.dumps(result, indent=2))

async def async_crawl_cli(urls, output_format, title, output_dir, enhanced_markdown=True):
    """Async function to crawl URLs and generate output for CLI."""
    try:
        crawl_results = await crawl_url(urls)
        
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
                "enhanced_markdown": enhanced_markdown,
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

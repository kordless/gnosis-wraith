"""Web page routes for the Gnosis Wraith application."""
import os
import datetime
import zipfile
from quart import render_template, send_from_directory, redirect, url_for

from gnosis_wraith.server.routes import pages_bp
from server.config import SCREENSHOTS_DIR, REPORTS_DIR, STORAGE_PATH, logger

@pages_bp.route('/')
async def index():
    """Render the index page."""
    # Get the extension version from the main app
    from app import EXTENSION_VERSION
    return await render_template('index.html', extension_version=EXTENSION_VERSION)

@pages_bp.route('/philosophy')
async def philosophy():
    """Render the philosophy page."""
    return await render_template('philosophy.html')

@pages_bp.route('/reports')
async def list_reports():
    """List all generated reports."""
    reports = []
    for file in os.listdir(REPORTS_DIR):
        if file.endswith('.md'):
            file_path = os.path.join(REPORTS_DIR, file)
            creation_time = os.path.getctime(file_path)
            
            # Format title from filename
            # Extract report name from filename, removing date suffix and underscores
            display_name = file.replace('.md', '')
            # Remove timestamp pattern if present (typically last part after underscore)
            if '_' in display_name:
                parts = display_name.rsplit('_', 1)
                if len(parts[1]) == 15 and parts[1].isdigit():  # Assuming YYYYMMDD_HHMMSS format = 15 chars
                    display_name = parts[0]
            # Replace underscores with spaces and capitalize words
            display_name = display_name.replace('_', ' ').title()
            
            reports.append({
                "filename": file,
                "title": display_name,
                "created": datetime.datetime.fromtimestamp(creation_time),
                "created_str": datetime.datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S'),
                "size": os.path.getsize(file_path)
            })
    
    # Sort reports by creation time (newest first)
    reports.sort(key=lambda x: x['created'], reverse=True)
    
    return await render_template('reports.html', reports=reports)

@pages_bp.route('/reports/<path:filename>')
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
                    return await render_template('error.html', 
                                          error_title="Report Generation Error",
                                          error_message=f"Error generating HTML: {str(e)}",
                                          error_type="error")
            else:
                logger.error(f"Markdown file not found for HTML conversion: {md_file_path}")
                # Return nice error page for report not found
                return await render_template('error.html', 
                                      error_title="Report Not Found",
                                      error_message=f"The report '{filename}' could not be found. It may have been deleted or moved.",
                                      error_type="not-found")
        else:
            logger.error(f"Report file not found: {file_path}")
            # Return nice error page for report not found
            return await render_template('error.html', 
                                  error_title="Report Not Found",
                                  error_message=f"The report '{filename}' could not be found. It may have been deleted or moved.",
                                  error_type="not-found")
    
    return await send_from_directory(REPORTS_DIR, filename)

@pages_bp.route('/screenshots/<path:filename>')
async def serve_screenshot(filename):
    """Serve a screenshot file."""
    return await send_from_directory(SCREENSHOTS_DIR, filename)

@pages_bp.route('/extension')
async def serve_extension():
    """Generate and serve the extension zip file."""
    downloads_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'downloads')
    zip_path = os.path.join(downloads_dir, 'gnosis-wraith-extension.zip')
    
    # Ensure downloads directory exists
    os.makedirs(downloads_dir, exist_ok=True)
    logger.info(f"Downloads directory: {downloads_dir}")
    
    # Check if extension zip exists, create it if not
    if not os.path.exists(zip_path):
        # First try relative path from server directory
        extension_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'extension')
        if not os.path.exists(extension_dir):
            # Try alternate path structure
            extension_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'extension')
        if os.path.exists(extension_dir):
            # Create downloads directory if it doesn't exist
            os.makedirs(downloads_dir, exist_ok=True)
            
            try:
                # Log the paths
                logger.info(f"Creating extension zip from {extension_dir} to {zip_path}")
                
                # Create zip file
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(extension_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, os.path.join(extension_dir, '..'))
                            logger.debug(f"Adding file to zip: {arcname}")
                            zipf.write(file_path, arcname)
                
                logger.info(f"Extension zip file created: {zip_path}")
            except Exception as e:
                logger.error(f"Error creating extension zip: {str(e)}")
                # Return a simple error message instead of failing silently
                return f"Error creating extension zip: {str(e)}", 500
        else:
            logger.error(f"Extension directory not found: {extension_dir}")
            return "Extension directory not found", 404
    else:
        logger.info(f"Using existing extension zip: {zip_path}")
    
    # Redirect to the static file
    static_url = url_for('static', filename='downloads/gnosis-wraith-extension.zip')
    logger.info(f"Redirecting to: {static_url}")
    return redirect(static_url)

@pages_bp.route('/wraith')
async def wraith():
    """Render the simplified wraith page."""
    return await render_template('wraith.html')

@pages_bp.route('/crawl')
async def crawl_redirect():
    """Handle crawl links with query parameters.
    
    This route accepts:
    - q: search query or URL-slugified description
    - w: (wait) if '1', the page will be auto-submitted
    
    The route redirects to the home page with query parameters that
    the JavaScript will use to populate the form.
    """
    from quart import request, redirect
    
    # Get query parameters
    q = request.args.get('q', '')
    w = request.args.get('w', '')
    
    # Redirect to home page with the query as a fragment
    target_url = '/#'
    
    # Add parameters to the fragment
    params = []
    if q:
        # Convert slug to spaces if needed (e.g., tech-news -> tech news)
        q_processed = q.replace('-', ' ')
        params.append(f"q={q_processed}")
        
    if w:
        params.append(f"w={w}")
    
    # Add parameters to the URL if any exist
    if params:
        target_url += '?' + '&'.join(params)
        
    logger.info(f"Redirecting from /crawl to: {target_url}")
    return redirect(target_url)

@pages_bp.route('/settings')
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
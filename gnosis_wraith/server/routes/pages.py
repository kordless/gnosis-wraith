"""Web page routes for the Gnosis Wraith application."""
import os
import json
import datetime
import zipfile
from quart import render_template, send_from_directory, redirect, url_for, request

from gnosis_wraith.server.routes import pages_bp
from server.config import SCREENSHOTS_DIR, REPORTS_DIR, STORAGE_PATH, logger

@pages_bp.route('/')
async def index():
    """Redirect to the crawl page."""
    return redirect('/crawl')

@pages_bp.route('/philosophy')
async def philosophy():
    """Render the philosophy page."""
    return await render_template('philosophy.html')

@pages_bp.route('/reports')
async def list_reports():
    """List all generated reports."""
    reports = []
    
    # Verify storage path is properly set
    from server.config import STORAGE_PATH
    logger.info(f"Storage path is set to: {STORAGE_PATH}")
    
    # Ensure the storage directory and REPORTS_DIR exist - create entire path
    try:
        os.makedirs(STORAGE_PATH, exist_ok=True)
        os.makedirs(REPORTS_DIR, exist_ok=True)
        
        # Create an images subdirectory for screenshots - important for reports
        reports_images_dir = os.path.join(REPORTS_DIR, "images")
        os.makedirs(reports_images_dir, exist_ok=True)
        
        logger.info(f"Ensured reports directory exists: {REPORTS_DIR}")
        logger.info(f"Ensured reports images directory exists: {reports_images_dir}")
    except Exception as dir_error:
        logger.error(f"Error creating reports directory structure: {str(dir_error)}")
        # Try to continue anyway
    
    # Verify directory exists after creation attempt
    if not os.path.exists(REPORTS_DIR):
        logger.error(f"Reports directory doesn't exist even after creation attempt: {REPORTS_DIR}")
        # Include the REPORTS_DIR in the template for better error handling
        if request.args.get('json'):
            from quart import jsonify
            return jsonify({"error": "Reports directory could not be created", "reports": []})
        else:
            return await render_template('reports.html', reports=[], 
                                error_message="Reports directory could not be created", 
                                config={'REPORTS_DIR': REPORTS_DIR},
                                active_page='reports')
    
    # Log the path being used for debugging
    logger.info(f"Listing reports from directory: {REPORTS_DIR}")
    
    try:
        # Create a sample report if directory is empty (debugging only)
        files = os.listdir(REPORTS_DIR)
        if not any(f.endswith('.md') for f in files):
            logger.info("No reports found in directory. This is expected if no reports have been generated yet.")
        
        # Process all report files (markdown and JSON)
        for file in files:
            if file.endswith('.md') or file.endswith('.json'):
                file_path = os.path.join(REPORTS_DIR, file)
                creation_time = os.path.getctime(file_path)
                
                # Format title from filename
                # Extract report name from filename, removing date suffix and underscores
                if file.endswith('.md'):
                    display_name = file.replace('.md', '')
                    format_type = 'markdown'
                else:  # .json
                    display_name = file.replace('.json', '')
                    format_type = 'json'
                
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
                    "size": os.path.getsize(file_path),
                    "format": format_type
                })
        
        # Sort reports by creation time (newest first)
        reports.sort(key=lambda x: x['created'], reverse=True)
        
        logger.info(f"Found {len(reports)} reports")
    except Exception as e:
        logger.error(f"Error listing reports: {str(e)}")
        # Continue with empty reports list
    
    # Add current time for calculating report age
    current_time = datetime.datetime.now()
    
    # Check if JSON format was requested
    if request.args.get('json'):
        from quart import jsonify
        
        # Clean up report objects for JSON (remove datetime objects)
        json_safe_reports = []
        for report in reports:
            report_copy = dict(report)
            # Remove the datetime object as it's not JSON serializable
            if 'created' in report_copy:
                del report_copy['created']
            json_safe_reports.append(report_copy)
        
        return jsonify({"reports": json_safe_reports})
    else:
        return await render_template('reports.html', reports=reports, active_page='reports', now=current_time)

@pages_bp.route('/reports/<path:filename>')
async def serve_report(filename):
    """Serve a report file."""
    # Sanitize filename to prevent directory traversal
    filename = os.path.basename(filename)
    logger.info(f"Requested report file: {filename} from {REPORTS_DIR}")
    
    # Check if the file exists
    file_path = os.path.join(REPORTS_DIR, filename)
    logger.info(f"Checking existence of file: {file_path}")
    
    if not os.path.exists(file_path):
        logger.warning(f"Report file not found: {file_path}")
        
        # If HTML file doesn't exist, check if we need to convert from markdown
        if filename.endswith('.html'):
            # Try to find the corresponding markdown file
            md_filename = filename.replace('.html', '.md')
            md_file_path = os.path.join(REPORTS_DIR, md_filename)
            logger.info(f"Looking for markdown source: {md_file_path}")
            
            if os.path.exists(md_file_path):
                # Convert markdown to HTML on-demand
                try:
                    from server.reports import convert_markdown_to_html
                    logger.info(f"Converting markdown to HTML on-demand: {md_file_path}")
                    html_file = await convert_markdown_to_html(md_file_path)
                    logger.info(f"Generated HTML file on-demand: {html_file}")
                    
                    # Verify the HTML file was created
                    if os.path.exists(os.path.join(REPORTS_DIR, filename)):
                        logger.info(f"HTML file successfully created, serving: {filename}")
                        return await send_from_directory(REPORTS_DIR, filename)
                    else:
                        logger.error(f"Generated HTML file not found: {os.path.join(REPORTS_DIR, filename)}")
                        return await render_template('error.html', 
                                              error_title="Report Generation Error",
                                              error_message=f"HTML file was not generated correctly: {filename}",
                                              error_type="error")
                except Exception as e:
                    logger.error(f"Error generating HTML on-demand: {str(e)}")
                    return await render_template('error.html', 
                                          error_title="Report Generation Error",
                                          error_message=f"Error generating HTML: {str(e)}",
                                          error_type="error",
                                          active_page='reports')
            else:
                logger.error(f"Markdown file not found for HTML conversion: {md_file_path}")
                # Return nice error page for report not found
                return await render_template('error.html', 
                                      error_title="Report Not Found",
                                      error_message=f"The report '{filename}' could not be found. It may have been deleted or moved.",
                                      error_type="not-found",
                                      filename=filename,
                                      active_page='reports')
        # Handle JSON file viewing - convert JSON to HTML for better display
        elif filename.endswith('.json'):
            # Try to serve as a JSON file with Content-Type: application/json
            if os.path.exists(file_path):
                from quart import send_file
                logger.info(f"Serving JSON file: {file_path}")
                return await send_file(file_path, mimetype='application/json')
            else:
                logger.error(f"JSON file not found: {file_path}")
                return await render_template('error.html',
                                      error_title="Report Not Found",
                                      error_message=f"The JSON report '{filename}' could not be found. It may have been deleted or moved.",
                                      error_type="not-found",
                                      filename=filename,
                                      active_page='reports')
        else:
            logger.error(f"Report file not found: {file_path}")
            # Return cryptic glitchy error page for report not found
            return await render_template('error.html', 
                                  error_title="0xF1LE_V01D",
                                  error_message=f"R3P0RT_FRAGMENT '[{filename[:8]}...]' EXISTS_IN_LIMINAL_SPACE... AWAITING RESURRECTION PROTOCOL... AUTHENTICATE TO CONTINUE...",
                                  error_type="void-state",
                                  filename=filename,
                                  active_page='reports')
    
    logger.info(f"Serving report file: {filename}")
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
    """Render the simplified wraith page (legacy route)."""
    return redirect(url_for('pages.crawl'))

@pages_bp.route('/crawl')
async def crawl():
    """Render the crawl page."""
    return await render_template('gnosis.html', active_page='crawl')

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
    
    # Redirect to crawl page with the query as a fragment
    target_url = '/crawl#'
    
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

@pages_bp.route('/code')
async def code():
    """Render the code examples page."""
    return await render_template('code_examples.html', active_page='code')

@pages_bp.route('/terminal')
async def terminal():
    """Render the terminal page."""
    return await render_template('terminal.html', active_page='terminal')

@pages_bp.route('/settings')
async def settings():
    """Render the settings page."""
    # Try to load settings from data directory if available
    saved_settings = {}
    try:
        from server.config import DATA_DIR
        settings_file = os.path.join(DATA_DIR, "server_settings.json")
        
        if os.path.exists(settings_file):
            logger.info(f"Loading settings from {settings_file}")
            try:
                with open(settings_file, 'r') as f:
                    saved_settings = json.load(f)
                logger.info(f"Loaded settings: {saved_settings}")
            except Exception as e:
                logger.error(f"Error loading settings from file: {str(e)}")
                # Continue with defaults if loading fails
    except Exception as e:
        logger.error(f"Error accessing data directory: {str(e)}")
    
    # Default settings (use saved values if available)
    settings_data = {
        'server_url': saved_settings.get('server_url', os.environ.get('GNOSIS_WRAITH_SERVER_URL', 'http://localhost:5678')),
        'llm_api_token': os.environ.get('GNOSIS_WRAITH_LLM_API_TOKEN', ''),  # Don't load from saved settings for security
        'screenshot_quality': saved_settings.get('screenshot_quality', os.environ.get('GNOSIS_WRAITH_SCREENSHOT_QUALITY', 'medium')),
        'javascript_enabled': saved_settings.get('javascript_enabled', os.environ.get('GNOSIS_WRAITH_JAVASCRIPT_ENABLED', 'false') == 'true'),
        'storage_path': saved_settings.get('storage_path', STORAGE_PATH),
        'active_page': 'settings',  # Add active_page parameter for header navigation
        'last_saved': saved_settings.get('saved_timestamp', 'Never')
    }
    
    return await render_template('settings.html', **settings_data)

@pages_bp.route('/min')
async def minimal_interface():
    """Render the minimal Gnosis interface."""
    return await render_template('gnosis.html', active_page='min')

@pages_bp.route('/min/logs')
async def minimal_interface_logs():
    """View logs from the minimal interface.
    
    This route provides a simple interface for viewing the logs
    generated by the minimal interface.
    """
    log_file_path = os.path.join(STORAGE_PATH, "minimal_interface_logs.json")
    logs = []
    
    try:
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r') as f:
                logs = json.load(f)
                
            # Reverse logs to show newest first
            logs.reverse()
    except Exception as e:
        logger.error(f"Error reading logs: {str(e)}")
    
    return await render_template('min_logs.html', 
                          logs=logs, 
                          log_count=len(logs),
                          active_page='min_logs')

@pages_bp.route('/forge')
async def forge():
    """Render the code forge page."""
    return await render_template('forge.html', active_page='forge')

@pages_bp.route('/about')
async def about():
    """Render the about page."""
    return await render_template('about.html', active_page='about')

@pages_bp.route('/vault')
async def vault():
    """Render the vault page - locked and offline system."""
    return await render_template('vault.html', active_page='vault')

@pages_bp.route('/chrome-error')
async def chrome_error():
    """Render a fake Chrome error page."""
    return await render_template('chrome_error.html')

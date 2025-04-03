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
    return await render_template('index.html')

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
    
    # Check if extension zip exists, create it if not
    if not os.path.exists(zip_path):
        extension_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'extension')
        if os.path.exists(extension_dir):
            # Create downloads directory if it doesn't exist
            os.makedirs(downloads_dir, exist_ok=True)
            
            # Create zip file
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(extension_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, os.path.join(extension_dir, '..'))
                        zipf.write(file_path, arcname)
    
    # Redirect to the static file
    return redirect(url_for('static', filename='downloads/gnosis-wraith-extension.zip'))

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
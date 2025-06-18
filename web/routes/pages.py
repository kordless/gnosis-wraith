"""Web page routes for the Gnosis Wraith application."""
import os
import json
import datetime
import zipfile
from quart import render_template, send_from_directory, redirect, url_for, request

from web.routes import pages_bp
from web.routes.auth import login_required
from core.config import SCREENSHOTS_DIR, REPORTS_DIR, STORAGE_PATH, logger

@pages_bp.route('/')
async def home():
    """Render the home/landing page."""
    return await render_template('home.html', active_page='home')

@pages_bp.route('/crawl')
@login_required
async def crawl():
    """Render the crawl page."""
    from quart import session
    user_data = {
        'email': session.get('user_email'),
        'name': session.get('user_name'),
        'uid': session.get('user_uid')
    }
    return await render_template('index.html', active_page='crawl', user_data=user_data)

@pages_bp.route('/forge')
async def forge():
    """Render the code forge page."""
    return await render_template('forge.html', active_page='forge')

@pages_bp.route('/rocket')
async def rocket():
    """Render the rocket explorer page."""
    return await render_template('rocket.html', active_page='rocket')



@pages_bp.route('/reports')
@login_required
async def list_reports():
    """List all generated reports."""
    reports = []
    
    # Get user email from session (simplified for development)
    from quart import session
    user_email = session.get('user_email', None)
    
    # For now, just use email-based storage without NDB
    from core.reports import get_user_reports_dir, get_user_screenshots_dir
    user_reports_dir = get_user_reports_dir(user_email)
    user_screenshots_dir = get_user_screenshots_dir(user_email)
    
    # Store basic user data for template
    user_data = {
        'email': user_email or 'anonymous',
        'crawl_count': 0,  # Would come from NDB in production
        'last_crawl': None,  # Would come from NDB in production
        'storage_used': 0  # Would come from NDB in production
    }
    
    # Verify storage path is properly set
    from core.config import STORAGE_PATH
    logger.info(f"Storage path is set to: {STORAGE_PATH}")
    logger.info(f"User reports directory: {user_reports_dir}")
    
    # Ensure the storage directory and user-specific directories exist
    try:
        os.makedirs(STORAGE_PATH, exist_ok=True)
        os.makedirs(user_reports_dir, exist_ok=True)
        os.makedirs(user_screenshots_dir, exist_ok=True)
        
        # Create an images subdirectory for screenshots - important for reports
        reports_images_dir = os.path.join(user_reports_dir, "images")
        os.makedirs(reports_images_dir, exist_ok=True)
        
        logger.info(f"Ensured user reports directory exists: {user_reports_dir}")
        logger.info(f"Ensured user screenshots directory exists: {user_screenshots_dir}")
        logger.info(f"Ensured reports images directory exists: {reports_images_dir}")
    except Exception as dir_error:
        logger.error(f"Error creating reports directory structure: {str(dir_error)}")
        # Try to continue anyway
    
    # Verify directory exists after creation attempt
    if not os.path.exists(user_reports_dir):
        logger.error(f"User reports directory doesn't exist even after creation attempt: {user_reports_dir}")
        # Include the user_reports_dir in the template for better error handling
        if request.args.get('json'):
            from quart import jsonify
            return jsonify({"error": "User reports directory could not be created", "reports": []})
        else:
            return await render_template('reports.html', reports=[], 
                                error_message="User reports directory could not be created", 
                                config={'REPORTS_DIR': user_reports_dir},
                                active_page='reports')
    
    # Log the path being used for debugging
    logger.info(f"Listing reports from user directory: {user_reports_dir}")
    
    try:
        # Create a sample report if directory is empty (debugging only)
        files = os.listdir(user_reports_dir)
        if not any(f.endswith('.md') for f in files):
            logger.info("No reports found in user directory. This is expected if no reports have been generated yet.")
        
        # Process all report files - group by base name to avoid duplicates
        # We'll prefer markdown files but include format info for both md and json
        report_groups = {}
        
        for file in files:
            if file.endswith('.md') or file.endswith('.json'):
                file_path = os.path.join(user_reports_dir, file)
                creation_time = os.path.getctime(file_path)
                
                # Get base name without extension for grouping
                if file.endswith('.md'):
                    base_name = file.replace('.md', '')
                    format_type = 'markdown'
                else:  # .json
                    base_name = file.replace('.json', '')
                    format_type = 'json'
                
                # Remove timestamp pattern if present (typically last part after underscore)
                display_name = base_name
                if '_' in display_name:
                    parts = display_name.rsplit('_', 1)
                    if len(parts[1]) == 15 and parts[1].isdigit():  # Assuming YYYYMMDD_HHMMSS format = 15 chars
                        display_name = parts[0]
                # Replace underscores with spaces and capitalize words
                display_name = display_name.replace('_', ' ').title()
                
                # Group reports by base name
                if base_name not in report_groups:
                    report_groups[base_name] = {
                        "name": base_name,
                        "path": base_name,  # Use base name as path
                        "title": display_name,
                        "created": datetime.datetime.fromtimestamp(creation_time),
                        "created_str": datetime.datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S'),
                        "size": os.path.getsize(file_path),
                        "formats": {},
                        "screenshot_url": None  # Will be set if screenshot is found
                    }
                
                # Add this format to the group
                report_groups[base_name]["formats"][format_type] = {
                    "filename": file,
                    "size": os.path.getsize(file_path)
                }
                
                # Check for corresponding screenshot file
                if format_type == 'markdown':
                    # Look for screenshot in user-specific screenshots directory
                    
                    # Try different screenshot naming patterns
                    possible_screenshot_names = [
                        f"{base_name}.png",
                        f"{base_name}.jpg", 
                        f"{base_name}.jpeg"
                    ]
                    
                    # Use glob to find matching screenshots
                    import glob
                    screenshot_found = False
                    
                    # First try exact matches
                    for pattern in possible_screenshot_names:
                        screenshot_path = os.path.join(user_screenshots_dir, pattern)
                        if os.path.exists(screenshot_path):
                            # Include user email hash in URL for proper routing
                            if user_email and user_email != 'anonymous':
                                import hashlib
                                user_hash = hashlib.sha256(user_email.encode()).hexdigest()[:12]
                                report_groups[base_name]["screenshot_url"] = f"/screenshots/{user_hash}/{pattern}"
                            else:
                                report_groups[base_name]["screenshot_url"] = f"/screenshots/anonymous/{pattern}"
                            logger.info(f"Found exact screenshot match for report {base_name}: {pattern}")
                            screenshot_found = True
                            break
                    
                    # If no exact match found, try to match by domain pattern
                    if not screenshot_found and '_' in base_name:
                        # Extract domain part from report name (e.g., "news_ycombinator_com" from "news_ycombinator_com_53e9f95b")
                        parts = base_name.split('_')
                        if len(parts) >= 3:  # Should have at least domain_tld_hash format
                            # Find the last part that looks like a hash (8+ hex chars)
                            hash_index = -1
                            for i in range(len(parts)-1, -1, -1):
                                if len(parts[i]) >= 8 and all(c in '0123456789abcdef' for c in parts[i]):
                                    hash_index = i
                                    break
                            
                            if hash_index > 0:
                                # Reconstruct domain without hash
                                domain_parts = parts[:hash_index]
                                domain_pattern = '_'.join(domain_parts)
                                
                                # Look for any screenshot matching this domain
                                pattern = f"{domain_pattern}_*.png"
                                matches = glob.glob(os.path.join(user_screenshots_dir, pattern))
                                
                                if matches:
                                    # If multiple matches, prefer the newest (by modification time)
                                    matches.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                                    screenshot_filename = os.path.basename(matches[0])
                                    
                                    # Include user hash in URL for proper routing
                                    if user_email and user_email != 'anonymous':
                                        import hashlib
                                        user_hash = hashlib.sha256(user_email.encode()).hexdigest()[:12]
                                    else:
                                        user_hash = hashlib.sha256('anonymous@system'.encode()).hexdigest()[:12]
                                    report_groups[base_name]["screenshot_url"] = f"/screenshots/{user_hash}/{screenshot_filename}"
                                    logger.info(f"Found domain match screenshot for report {base_name}: {screenshot_filename} using pattern {pattern}")
                                    screenshot_found = True
        
        # Convert grouped reports to list format
        for base_name, group_data in report_groups.items():
            report_entry = {
                "filename": group_data["name"],  # Use base name as filename
                "name": group_data["name"],
                "path": group_data["path"],
                "title": group_data["title"], 
                "created": group_data["created"],
                "created_str": group_data["created_str"],
                "size": group_data["size"],
                "formats": group_data["formats"]  # Available formats (markdown, json)
            }
            
            # Include screenshot URL if available
            if group_data.get("screenshot_url"):
                report_entry["screenshot_url"] = group_data["screenshot_url"]
                
            reports.append(report_entry)
        
        # Sort reports by creation time (newest first)
        reports.sort(key=lambda x: x['created'], reverse=True)
        
        logger.info(f"Found {len(reports)} reports")
    except Exception as e:
        logger.error(f"Error listing reports: {str(e)}")
        # Continue with empty reports list
    
    # End of NDB context
    
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
        # Pass user data to template if available
        template_data = {
            'reports': reports,
            'active_page': 'reports',
            'now': current_time
        }
        
        # Add user data if we have it
        if 'user_data' in locals():
            template_data['user'] = user_data
        
        return await render_template('reports.html', **template_data)

@pages_bp.route('/reports/<path:filename>')
@login_required
async def serve_report(filename):
    """Serve a report file."""
    # Get user email from session
    from quart import session
    user_email = session.get('user_email', None)
    
    # Get user-specific reports directory
    from core.reports import get_user_reports_dir
    user_reports_dir = get_user_reports_dir(user_email)
    
    # Sanitize filename to prevent directory traversal
    filename = os.path.basename(filename)
    logger.info(f"Requested report file: {filename} from {user_reports_dir}")
    
    # Check if the file exists
    file_path = os.path.join(user_reports_dir, filename)
    logger.info(f"Checking existence of file: {file_path}")
    
    if not os.path.exists(file_path):
        logger.warning(f"Report file not found: {file_path}")
        
        # If HTML file doesn't exist, check if we need to convert from markdown
        if filename.endswith('.html'):
            # Try to find the corresponding markdown file
            md_filename = filename.replace('.html', '.md')
            md_file_path = os.path.join(user_reports_dir, md_filename)
            logger.info(f"Looking for markdown source: {md_file_path}")
            
            if os.path.exists(md_file_path):
                # Convert markdown to HTML on-demand
                try:
                    from core.reports import convert_markdown_to_html
                    logger.info(f"Converting markdown to HTML on-demand: {md_file_path}")
                    html_file = await convert_markdown_to_html(md_file_path)
                    logger.info(f"Generated HTML file on-demand: {html_file}")
                    logger.info(f"User REPORTS DIR: {user_reports_dir}")
                    
                    # Verify the HTML file was created
                    if os.path.exists(os.path.join(user_reports_dir, filename)):
                        logger.info(f"HTML file successfully created, serving: {filename}")
                        return await send_from_directory(user_reports_dir, filename)
                    else:
                        logger.error(f"Generated HTML file not found: {os.path.join(user_reports_dir, filename)}")
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
    return await send_from_directory(user_reports_dir, filename)

@pages_bp.route('/screenshots/<user_hash>/<path:filename>')
@login_required
async def serve_screenshot(user_hash, filename):
    """Serve a screenshot file from user-specific directory."""
    # Get user email from session
    from quart import session, abort
    user_email = session.get('user_email', None)
    
    # Verify user hash matches current user
    if user_email and user_email != 'anonymous':
        import hashlib
        expected_hash = hashlib.sha256(user_email.encode()).hexdigest()[:12]
    else:
        expected_hash = hashlib.sha256('anonymous@system'.encode()).hexdigest()[:12]
    
    if user_hash != expected_hash:
        logger.warning(f"User hash mismatch: expected {expected_hash}, got {user_hash}")
        abort(403)  # Forbidden
    
    # Get user-specific screenshots directory
    from core.reports import get_user_screenshots_dir
    user_screenshots_dir = get_user_screenshots_dir(user_email)
    
    return await send_from_directory(user_screenshots_dir, filename)

@pages_bp.route('/screenshots/<path:filename>')
@login_required  
async def serve_screenshot_legacy(filename):
    """Legacy route for backwards compatibility - serves from current user's directory."""
    # Get user email from session
    from quart import session
    user_email = session.get('user_email', None)
    
    # Get user-specific screenshots directory
    from core.reports import get_user_screenshots_dir
    user_screenshots_dir = get_user_screenshots_dir(user_email)
    
    return await send_from_directory(user_screenshots_dir, filename)

@pages_bp.route('/storage/<user_hash>/<path:filename>')
@login_required
async def serve_storage_file(user_hash, filename):
    """Serve any file from user-specific storage directory."""
    # Get user email from session
    from quart import session, abort
    user_email = session.get('user_email', None)
    
    # Verify user hash matches current user
    if user_email and user_email != 'anonymous':
        import hashlib
        expected_hash = hashlib.sha256(user_email.encode()).hexdigest()[:12]
    else:
        import hashlib
        expected_hash = hashlib.sha256('anonymous@gnosis-wraith.local'.encode()).hexdigest()[:12]
    
    if user_hash != expected_hash:
        logger.warning(f"User hash mismatch: expected {expected_hash}, got {user_hash}")
        abort(403)  # Forbidden
    
    # Construct the user storage path
    user_storage_path = os.path.join(STORAGE_PATH, 'users', user_hash)
    
    # Check if the file exists
    file_path = os.path.join(user_storage_path, filename)
    if not os.path.exists(file_path):
        logger.error(f"Storage file not found: {file_path}")
        abort(404)
    
    # Serve the file
    logger.info(f"Serving storage file: {filename} from {user_storage_path}")
    return await send_from_directory(user_storage_path, filename)


@pages_bp.route('/extension')
async def serve_extension():
    """Serve the extension zip file with version number."""
    from quart import send_file
    
    # Get version from manifest.json
    manifest_path = os.path.join(os.path.dirname(__file__), '..', '..', 'gnosis_wraith', 'extension', 'manifest.json')
    version = "1.4.1"  # Default version
    
    try:
        if os.path.exists(manifest_path):
            with open(manifest_path, 'r') as f:
                manifest_data = json.load(f)
                version = manifest_data.get('version', version)
                logger.info(f"Found extension version: {version}")
    except Exception as e:
        logger.error(f"Error reading manifest.json: {str(e)}")
    
    # Look for pre-built versioned zip
    downloads_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'downloads')
    versioned_zip = os.path.join(downloads_dir, f'gnosis-wraith-extension-{version}.zip')
    legacy_zip = os.path.join(downloads_dir, 'gnosis-wraith-extension.zip')
    
    # Prefer versioned zip if it exists
    if os.path.exists(versioned_zip):
        logger.info(f"Serving versioned extension: {versioned_zip}")
        return await send_file(
            versioned_zip, 
            as_attachment=True,
            download_name=f'gnosis-wraith-extension-{version}.zip'
        )
    elif os.path.exists(legacy_zip):
        logger.info(f"Serving legacy extension with version name: {legacy_zip}")
        return await send_file(
            legacy_zip,
            as_attachment=True,
            download_name=f'gnosis-wraith-extension-{version}.zip'
        )
    else:
        # Build it on the fly if neither exists
        extension_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'gnosis_wraith', 'extension')
        if os.path.exists(extension_dir):
            os.makedirs(downloads_dir, exist_ok=True)
            
            try:
                logger.info(f"Creating extension zip on-demand")
                with zipfile.ZipFile(versioned_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(extension_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, os.path.dirname(extension_dir))
                            zipf.write(file_path, arcname)
                
                logger.info(f"Extension zip created: {versioned_zip}")
                return await send_file(
                    versioned_zip,
                    as_attachment=True,
                    download_name=f'gnosis-wraith-extension-{version}.zip'
                )
            except Exception as e:
                logger.error(f"Error creating extension zip: {str(e)}")
                return f"Error creating extension zip: {str(e)}", 500
        else:
            logger.error(f"Extension directory not found")
            return "Extension directory not found", 404


# Path-based URL route - put this at the end to avoid conflicts
@pages_bp.route('/http/<path:url>')
@pages_bp.route('/https/<path:url>')
async def crawl_with_path(url):
    """Handle path-based URLs like /https://example.com"""
    # Reconstruct the full URL
    protocol = 'https' if request.endpoint == 'pages.crawl_with_path' and 'https' in request.path else 'http'
    full_url = f"{protocol}://{url}"
    
    # Convert special characters back from URL-safe format  
    full_url = full_url.replace('_id_3D', '?id=')  # Convert _id_3D back to ?id=
    full_url = full_url.replace('_', '/')   # Convert _ back to /
    
    # Redirect to crawl page with the URL as a parameter
    return redirect(f'/crawl?q={full_url}')
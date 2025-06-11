"""
Example: Updated report saving functions using StorageService

This shows how to modify the existing save functions in reports.py
to use the enhanced storage service.
"""

import os
import datetime
import logging
from typing import List, Dict, Any

# Import the enhanced storage service
from core.enhanced_storage_service import StorageService

logger = logging.getLogger("gnosis_wraith")


async def save_markdown_report_v2(title: str, crawl_results: List[Dict[str, Any]], 
                                  storage_service: StorageService = None) -> str:
    """
    Save a markdown report using the storage service.
    
    This is the updated version that uses StorageService instead of direct file I/O.
    """
    # Initialize storage service if not provided
    if storage_service is None:
        storage_service = StorageService()
    
    # Generate the report content (reuse existing function)
    from core.reports import generate_markdown_report
    report_content = generate_markdown_report(title, crawl_results)
    
    # Generate filename using existing logic
    from core.filename_utils import generate_report_filename, extract_url_from_crawl_results
    
    # Extract primary URL from crawl results for filename generation
    primary_url = extract_url_from_crawl_results(crawl_results)
    
    if primary_url:
        # Use hash-based naming with optional custom title
        base_filename = generate_report_filename(primary_url, title, "md")
        # Remove the extension as save_report will add it
        base_filename = os.path.splitext(base_filename)[0]
    else:
        # Fallback to timestamp-based naming
        import string
        valid_chars = string.ascii_letters + string.digits + '-_'
        safe_title = ''.join(c if c in valid_chars else '_' for c in title)
        base_filename = f"{safe_title}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Save using storage service
    report_path = await storage_service.save_report(
        content=report_content,
        filename=base_filename,
        format='md'
    )
    
    logger.info(f"Report saved via StorageService: {report_path}")
    return report_path


async def save_json_report_v2(title: str, crawl_results: List[Dict[str, Any]], 
                              storage_service: StorageService = None) -> str:
    """
    Save a JSON report using the storage service.
    
    This is the updated version that uses StorageService instead of direct file I/O.
    """
    # Initialize storage service if not provided
    if storage_service is None:
        storage_service = StorageService()
    
    # Generate the report content (reuse existing function)
    from core.reports import generate_json_report
    import json
    
    json_report = generate_json_report(title, crawl_results)
    report_content = json.dumps(json_report, indent=2)
    
    # Generate filename using existing logic
    from core.filename_utils import generate_report_filename, extract_url_from_crawl_results
    
    # Extract primary URL from crawl results for filename generation
    primary_url = extract_url_from_crawl_results(crawl_results)
    
    if primary_url:
        # Use hash-based naming with optional custom title
        base_filename = generate_report_filename(primary_url, title, "json")
        # Remove the extension as save_report will add it
        base_filename = os.path.splitext(base_filename)[0]
    else:
        # Fallback to timestamp-based naming
        import string
        valid_chars = string.ascii_letters + string.digits + '-_'
        safe_title = ''.join(c if c in valid_chars else '_' for c in title)
        base_filename = f"{safe_title}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Save using storage service
    report_path = await storage_service.save_report(
        content=report_content,
        filename=base_filename,
        format='json'
    )
    
    logger.info(f"JSON report saved via StorageService: {report_path}")
    return report_path


# Example route handler update
"""
# In app.py, update the crawl endpoint:

@app.route('/api/crawl', methods=['POST'])
async def crawl():
    # ... existing crawl logic ...
    
    # Initialize storage service
    storage_service = StorageService()
    
    # Save reports using the new functions
    if output_format in ['md', 'markdown']:
        report_path = await save_markdown_report_v2(
            title=report_title,
            crawl_results=results,
            storage_service=storage_service
        )
    elif output_format == 'json':
        report_path = await save_json_report_v2(
            title=report_title,
            crawl_results=results,
            storage_service=storage_service
        )
    
    # Generate download URL
    if is_running_in_cloud():
        # Get signed URL for cloud storage
        download_url = storage_service.get_report_url(
            os.path.basename(report_path),
            signed=True,
            expiry_hours=24
        )
    else:
        # Local URL
        download_url = f"/download/report/{os.path.basename(report_path)}"
    
    return jsonify({
        'success': True,
        'report_path': report_path,
        'download_url': download_url
    })
"""


# Example: List reports endpoint
async def get_reports_list(storage_service: StorageService = None, 
                           format: str = None) -> List[Dict[str, Any]]:
    """
    Get a list of all available reports.
    
    Args:
        storage_service: The storage service instance
        format: Optional filter by format ('md', 'json', 'html')
    
    Returns:
        List of report metadata
    """
    if storage_service is None:
        storage_service = StorageService()
    
    reports = await storage_service.list_reports(format=format)
    
    # Enhance report metadata with additional info
    for report in reports:
        # Add human-readable size
        size_mb = report['size'] / (1024 * 1024)
        report['size_human'] = f"{size_mb:.2f} MB" if size_mb > 1 else f"{report['size'] / 1024:.2f} KB"
        
        # Add format from filename
        report['format'] = report['filename'].split('.')[-1]
        
        # Parse title from filename if possible
        base_name = os.path.splitext(report['filename'])[0]
        report['title'] = base_name.replace('_', ' ').title()
    
    return reports


# Example: Download report endpoint
async def download_report(filename: str, storage_service: StorageService = None) -> tuple:
    """
    Download a report by filename.
    
    Returns:
        Tuple of (content, mimetype) for Flask response
    """
    if storage_service is None:
        storage_service = StorageService()
    
    try:
        # Get report content
        content = await storage_service.get_report(filename)
        
        # Determine mimetype
        if filename.endswith('.md'):
            mimetype = 'text/markdown'
        elif filename.endswith('.json'):
            mimetype = 'application/json'
        elif filename.endswith('.html'):
            mimetype = 'text/html'
        else:
            mimetype = 'text/plain'
        
        return content, mimetype
        
    except FileNotFoundError:
        raise Exception(f"Report not found: {filename}")


# Example: Environment detection helper
def get_storage_info() -> Dict[str, Any]:
    """Get information about current storage configuration."""
    from core.enhanced_storage_service import is_running_in_cloud
    
    info = {
        'environment': 'cloud' if is_running_in_cloud() else 'local',
        'is_cloud': is_running_in_cloud(),
    }
    
    if is_running_in_cloud():
        info.update({
            'bucket_name': os.environ.get('GCS_BUCKET_NAME', 'Not configured'),
            'project_id': os.environ.get('GOOGLE_CLOUD_PROJECT', 'Not configured'),
        })
    else:
        info.update({
            'reports_dir': os.environ.get('GNOSIS_WRAITH_REPORTS_DIR', 
                                          os.path.join(os.path.expanduser("~"), ".gnosis-wraith/reports")),
            'storage_path': os.environ.get('STORAGE_PATH', './storage'),
        })
    
    return info

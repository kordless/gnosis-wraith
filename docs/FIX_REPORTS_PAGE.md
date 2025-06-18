# Reports Page Fix Plan

## Problem
The `/reports` page is failing because `REPORTS_DIR` is not defined in `core/reports.py`. This variable was likely removed during the storage refactor to use the new `storage_service.py`.

## Root Cause
The reports system was refactored to use user-partitioned storage, but the reports listing page wasn't updated to use the new storage service.

## Files to Fix

### 1. **core/reports.py**
- Remove old `get_user_reports_dir()` function that references `REPORTS_DIR`
- Update to use `StorageService` for listing reports
- Change from file system operations to storage service operations

### 2. **web/routes/pages.py** 
- Update `list_reports()` function to use the new storage service
- Change from directory listing to storage service file listing
- Update the report data structure to match new storage format

## Implementation Steps

### Step 1: Update core/reports.py
```python
# Remove old function:
def get_user_reports_dir(user_email):
    return REPORTS_DIR  # This is broken

# Replace with:
from core.storage_service import get_storage_service

async def get_user_reports(user_email):
    """Get all reports for a user using storage service"""
    storage = get_storage_service(user_email)
    # List all markdown files
    files = await storage.list_files(prefix='report_')
    reports = []
    for file in files:
        if file['filename'].endswith('.md'):
            reports.append({
                'filename': file['filename'],
                'size': file['size'],
                'created': file['created'],
                'modified': file['modified'],
                'url': storage.get_file_url(file['filename'])
            })
    return reports
```

### Step 2: Update web/routes/pages.py
```python
@pages.route('/reports')
@login_required
async def list_reports():
    """List all reports for the current user"""
    user_email = session.get('user_email')
    
    # Use new async function
    reports = await get_user_reports(user_email)
    
    # Sort by modified date (newest first)
    reports.sort(key=lambda x: x['modified'], reverse=True)
    
    return await render_template('reports.html', 
                                reports=reports,
                                user_email=user_email)
```

### Step 3: Update reports.html template
The template likely expects different data structure. Update to use:
- `report.url` instead of file paths
- `report.filename` for display
- `report.created` and `report.modified` for dates

## Quick Fix (Temporary)
If you need a quick fix while implementing the proper solution:

```python
# In core/reports.py, add at the top:
import os
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'storage', 'reports')

# But this won't work well with user-partitioned storage
```

## Benefits of Proper Fix
1. Works with both local and cloud storage
2. Properly partitions reports by user
3. Generates signed URLs for cloud storage
4. Consistent with rest of the application

## Testing
After implementing:
1. Test locally with file storage
2. Test in Cloud Run with GCS
3. Verify reports are listed correctly
4. Check that report URLs work

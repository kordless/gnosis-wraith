# Storage Abstraction Plan for Gnosis Wraith

## Current State Analysis

### Local Storage
- **Reports Directory**: `~/.gnosis-wraith/reports/` (from `GNOSIS_WRAITH_REPORTS_DIR` env var)
- **Screenshots**: `~/.gnosis-wraith/screenshots/`
- **StorageService**: Located in `server/storage_service.py`
  - Already has abstraction between local and GCS (Google Cloud Storage)
  - Uses `RUNNING_IN_CLOUD` env var to detect environment
  - Uses `GCS_BUCKET_NAME` for cloud storage bucket
  - Uses `STORAGE_PATH` for local storage root

### Key Observations
1. The `StorageService` class already provides abstraction between local and cloud storage
2. Reports are saved directly to `REPORTS_DIR` in `reports.py`, bypassing the storage service
3. There's a mismatch: StorageService manages general storage, but reports have their own path logic
4. No user isolation - all reports are stored in a flat structure

## Proposed Solution

### 1. User Hash Bucketing Strategy

To support multi-tenant usage and improve organization, implement user-based bucketing:

#### A. User Hash Generation
```python
import hashlib

def get_user_hash(user_id: str = None, request_headers: dict = None) -> str:
    """
    Generate a consistent hash for user identification.
    Falls back to IP-based hash if no user ID is available.
    """
    if user_id:
        # Authenticated user
        return hashlib.sha256(user_id.encode()).hexdigest()[:12]
    elif request_headers:
        # Anonymous user - use IP + User-Agent for consistency
        ip = request_headers.get('X-Forwarded-For', request_headers.get('Remote-Addr', 'unknown'))
        user_agent = request_headers.get('User-Agent', 'unknown')
        identity = f"{ip}:{user_agent}"
        return hashlib.sha256(identity.encode()).hexdigest()[:12]
    else:
        # Default bucket for system-generated reports
        return 'system'
```

#### B. Storage Path Structure
```
Local Storage:
~/.gnosis-wraith/
├── users/
│   ├── a1b2c3d4e5f6/    # User hash bucket
│   │   ├── reports/
│   │   │   ├── report_20250604_123456.md
│   │   │   └── report_20250604_123456.json
│   │   └── screenshots/
│   │       └── screenshot_abc123.png
│   └── system/          # System/shared reports
│       └── reports/

Cloud Storage (GCS):
gs://gnosis-wraith-storage/
├── users/
│   ├── a1b2c3d4e5f6/
│   │   ├── reports/
│   │   └── screenshots/
│   └── system/
│       └── reports/
```

### 2. Enhanced StorageService with User Bucketing

#### A. Extended StorageService Class
```python
class StorageService:
    def __init__(self, user_hash: str = None):
        """Initialize storage service with optional user context."""
        self._user_hash = user_hash or 'system'
        # ... existing initialization code ...
    
    def set_user_context(self, user_hash: str):
        """Set the user context for storage operations."""
        self._user_hash = user_hash
    
    def _get_user_path(self, folder: str) -> str:
        """Get the user-specific path for a folder."""
        if is_running_in_cloud():
            return f"users/{self._user_hash}/{folder}"
        else:
            return os.path.join(self._storage_path, 'users', self._user_hash, folder)
    
    async def save_report(self, content: str, filename: str, format: str = 'md', 
                          user_hash: str = None) -> str:
        """Save a report with user bucketing."""
        # Use provided user_hash or fall back to instance default
        current_user = user_hash or self._user_hash
        
        if is_running_in_cloud():
            # Save to GCS with user bucket
            user_folder = f"users/{current_user}/reports"
            return await self.save_file(content, user_folder, f'{filename}.{format}')
        else:
            # Save to local user-specific directory
            user_reports_dir = os.path.join(
                self._storage_path, 'users', current_user, 'reports'
            )
            os.makedirs(user_reports_dir, exist_ok=True)
            
            report_path = os.path.join(user_reports_dir, f'{filename}.{format}')
            async with aiofiles.open(report_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            return report_path
    
    async def list_user_reports(self, user_hash: str = None, format: str = None) -> List[Dict[str, Any]]:
        """List reports for a specific user."""
        current_user = user_hash or self._user_hash
        
        if is_running_in_cloud():
            prefix = f"users/{current_user}/reports/"
            # ... GCS listing logic ...
        else:
            user_reports_dir = os.path.join(
                self._storage_path, 'users', current_user, 'reports'
            )
            # ... local listing logic ...
```

#### B. Request Context Middleware
```python
# In app.py or middleware
from functools import wraps

def with_user_storage(f):
    """Decorator to inject user-aware storage service."""
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        # Extract user context from request
        user_id = get_current_user_id()  # From session/JWT/etc
        user_hash = get_user_hash(
            user_id=user_id,
            request_headers=request.headers if not user_id else None
        )
        
        # Create storage service with user context
        storage_service = StorageService(user_hash=user_hash)
        
        # Inject into function
        kwargs['storage_service'] = storage_service
        return await f(*args, **kwargs)
    
    return decorated_function
```

### 3. Updated Route Examples

```python
@app.route('/api/crawl', methods=['POST'])
@with_user_storage
async def crawl(storage_service: StorageService):
    """Crawl endpoint with user-aware storage."""
    # ... crawl logic ...
    
    # Save report - automatically goes to user's bucket
    report_path = await storage_service.save_report(
        content=report_content,
        filename=filename,
        format='md'
    )
    
    return jsonify({
        'success': True,
        'report_path': report_path,
        'download_url': storage_service.get_report_url(os.path.basename(report_path))
    })

@app.route('/api/reports', methods=['GET'])
@with_user_storage
async def list_reports(storage_service: StorageService):
    """List user's reports."""
    reports = await storage_service.list_user_reports()
    
    return jsonify({
        'success': True,
        'reports': reports,
        'count': len(reports)
    })
```

### 4. Migration and Admin Features

#### A. Admin Access to All Users
```python
class StorageService:
    async def list_all_users(self) -> List[str]:
        """List all user hashes (admin only)."""
        if is_running_in_cloud():
            # List GCS prefixes under users/
            bucket = self._gcs_client.bucket(self._bucket_name)
            prefixes = set()
            for blob in bucket.list_blobs(prefix='users/', delimiter='/'):
                if blob.prefix:
                    user_hash = blob.prefix.split('/')[1]
                    prefixes.add(user_hash)
            return list(prefixes)
        else:
            # List local user directories
            users_dir = os.path.join(self._storage_path, 'users')
            if os.path.exists(users_dir):
                return [d for d in os.listdir(users_dir) 
                        if os.path.isdir(os.path.join(users_dir, d))]
            return []
    
    async def get_user_storage_stats(self, user_hash: str) -> Dict[str, Any]:
        """Get storage statistics for a user."""
        # ... implementation for counting files, total size, etc.
```

#### B. Migration from Flat to Bucketed Structure
```python
async def migrate_to_user_buckets(storage_service: StorageService):
    """Migrate existing reports to user bucket structure."""
    # Move all existing reports to 'system' bucket
    system_hash = 'system'
    
    # ... migration logic ...
```

### 5. Environment Configuration Updates

#### Local Development (.env)
```bash
RUNNING_IN_CLOUD=false
STORAGE_PATH=./storage
GNOSIS_WRAITH_REPORTS_DIR=~/.gnosis-wraith/reports  # Legacy support
ENABLE_USER_BUCKETING=true
DEFAULT_USER_HASH=dev_user  # For local testing
```

#### Google Cloud Run (env vars)
```bash
RUNNING_IN_CLOUD=true
GCS_BUCKET_NAME=gnosis-wraith-storage
GOOGLE_CLOUD_PROJECT=your-project-id
ENABLE_USER_BUCKETING=true
```

### 6. Security Considerations

1. **User Hash Privacy**: Use SHA-256 to ensure user IDs cannot be reversed
2. **Access Control**: Implement checks to ensure users can only access their own buckets
3. **Rate Limiting**: Per-user rate limiting becomes easier with bucketing
4. **Storage Quotas**: Can implement per-user storage limits

### 7. Benefits

1. **Multi-tenancy**: Support multiple users with isolated storage
2. **Better Organization**: Reports are organized by user
3. **Scalability**: Easier to distribute storage across multiple buckets
4. **Privacy**: Users' reports are isolated from each other
5. **Analytics**: Can track usage per user
6. **Cleanup**: Easier to remove all data for a specific user

### 8. Implementation Steps

1. **Phase 1: Enhance StorageService**
   - Add user context support
   - Implement user bucketing methods
   - Add user listing and stats methods
   - Update error handling for multi-user scenarios

2. **Phase 2: Update Reports Module**
   - Replace direct file I/O with StorageService
   - Add user context to save operations
   - Update report listing to be user-aware

3. **Phase 3: Update App Routes**
   - Implement user hash extraction middleware
   - Add @with_user_storage decorator to relevant endpoints
   - Update download endpoints to respect user buckets
   - Add admin endpoints for cross-user access

4. **Phase 4: Migration & Testing**
   - Create migration script for existing reports
   - Unit tests for user bucketing
   - Integration tests with multiple users
   - Performance testing with many buckets

5. **Phase 5: Admin Tools**
   - User management endpoints
   - Storage analytics dashboard
   - Cleanup tools for inactive users
   - Quota management system

### 9. Example Usage After Implementation

```python
# Automatic user context from request
@app.route('/api/my-reports')
@with_user_storage
async def my_reports(storage_service: StorageService):
    # Storage service automatically uses current user's bucket
    reports = await storage_service.list_user_reports()
    return jsonify(reports)

# Explicit user context (admin endpoint)
@app.route('/api/admin/user/<user_hash>/reports')
@require_admin
async def admin_list_user_reports(user_hash: str):
    storage_service = StorageService(user_hash=user_hash)
    reports = await storage_service.list_user_reports()
    return jsonify(reports)

# Get storage stats
@app.route('/api/storage/stats')
@with_user_storage
async def my_storage_stats(storage_service: StorageService):
    stats = await storage_service.get_user_storage_stats()
    return jsonify(stats)

# Cleanup old reports (admin)
@app.route('/api/admin/cleanup', methods=['POST'])
@require_admin
async def cleanup_old_reports():
    storage_service = StorageService()
    users = await storage_service.list_all_users()
    
    cleanup_stats = []
    for user_hash in users:
        storage_service.set_user_context(user_hash)
        stats = await storage_service.cleanup_old_reports(days=30)
        cleanup_stats.append({
            'user': user_hash,
            'deleted': stats['deleted_count'],
            'freed_space': stats['freed_bytes']
        })
    
    return jsonify(cleanup_stats)
```

### 10. Future Enhancements

1. **Shared Reports**: Allow users to share reports with specific user hashes
2. **Team Buckets**: Support team/organization-level buckets
3. **Report Templates**: Per-user or per-team report templates
4. **Usage Analytics**: Track report generation patterns per user
5. **Export/Import**: Bulk export/import of user's reports
6. **Versioning**: Keep version history of reports per user

This approach provides user isolation, improves scalability, and maintains backward compatibility while preparing for multi-tenant cloud deployment.
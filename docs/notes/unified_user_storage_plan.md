# Unified User Storage Partitioning Plan

## Core Principle: Same Structure Everywhere
Local filesystem and cloud storage (GCS) must use identical paths and user partitioning.

## Storage Structure (Local & Cloud)

```
storage/                          # Root (./storage locally, gs://bucket-name/ in cloud)
├── users/                        # All user data
│   ├── anonymous/               # Unauthenticated users (shared space)
│   │   ├── reports/
│   │   ├── screenshots/
│   │   └── meta.json           # Usage stats, limits
│   │
│   └── [user_hash_12]/         # Authenticated users (SHA256(email)[:12])
│       ├── reports/
│       ├── screenshots/
│       ├── config/
│       │   ├── api_tokens.json
│       │   └── settings.json
│       └── meta.json           # User metadata, quotas
│
└── system/                      # System-wide data
    ├── cache/
    ├── logs/
    └── stats.json
```

## Implementation: Update EnhancedStorageService

### 1. Add User Context Method
```python
# In core/enhanced_storage_service.py

import hashlib
from typing import Optional

class EnhancedStorageService:
    def __init__(self):
        self._user_hash: Optional[str] = None
        # ... existing init code ...
    
    def get_user_path(self, email: Optional[str] = None) -> str:
        """Get user-specific storage path. Same logic for local and cloud."""
        if not email:
            # Try to get from current context
            try:
                from quart import g
                email = getattr(g, 'user_email', None)
            except:
                pass
        
        if email and email != 'anonymous':
            # Generate consistent hash for authenticated users
            user_hash = hashlib.sha256(email.encode()).hexdigest()[:12]
            return f"users/{user_hash}"
        else:
            # Anonymous users share a common space
            return "users/anonymous"
    
    def set_user_context(self, email: Optional[str]):
        """Set user context for this service instance."""
        self._user_email = email
        self._user_path = self.get_user_path(email)
```

### 2. Update Save Methods to Use User Paths
```python
async def save_report(self, content: str, filename: str, format: str = 'md') -> str:
    """Save report with user partitioning (same for local and cloud)."""
    user_path = self.get_user_path()
    
    if self.is_cloud_storage():
        # Cloud path: users/[hash]/reports/filename.md
        blob_path = f"{user_path}/reports/{filename}.{format}"
        return await self._save_to_gcs(content, blob_path)
    else:
        # Local path: ./storage/users/[hash]/reports/filename.md
        local_dir = os.path.join(self._storage_path, user_path, 'reports')
        os.makedirs(local_dir, exist_ok=True)
        
        file_path = os.path.join(local_dir, f"{filename}.{format}")
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(content)
        return file_path

async def save_screenshot(self, image_data: bytes, filename: str) -> str:
    """Save screenshot with user partitioning."""
    user_path = self.get_user_path()
    
    if self.is_cloud_storage():
        # Cloud path: users/[hash]/screenshots/filename.png
        blob_path = f"{user_path}/screenshots/{filename}"
        return await self._save_binary_to_gcs(image_data, blob_path)
    else:
        # Local path: ./storage/users/[hash]/screenshots/filename.png
        local_dir = os.path.join(self._storage_path, user_path, 'screenshots')
        os.makedirs(local_dir, exist_ok=True)
        
        file_path = os.path.join(local_dir, filename)
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(image_data)
        return file_path
```

### 3. Update List Methods
```python
async def list_reports(self, user_email: Optional[str] = None) -> List[dict]:
    """List reports for current user."""
    user_path = self.get_user_path(user_email)
    
    if self.is_cloud_storage():
        # List from GCS: users/[hash]/reports/
        prefix = f"{user_path}/reports/"
        blobs = self._bucket.list_blobs(prefix=prefix)
        return [self._blob_to_dict(blob) for blob in blobs]
    else:
        # List from local: ./storage/users/[hash]/reports/
        local_dir = os.path.join(self._storage_path, user_path, 'reports')
        if not os.path.exists(local_dir):
            return []
        
        reports = []
        for filename in os.listdir(local_dir):
            if filename.endswith(('.md', '.json')):
                file_path = os.path.join(local_dir, filename)
                reports.append({
                    'filename': filename,
                    'path': file_path,
                    'size': os.path.getsize(file_path),
                    'created': os.path.getctime(file_path)
                })
        return reports
```

## Integration Points

### 1. API Routes (web/routes/api.py)
```python
@api.route('/crawl', methods=['POST'])
async def crawl():
    # Get user email from session/auth
    user_email = get_current_user_email()  # From auth system
    
    # Initialize storage with user context
    storage = EnhancedStorageService()
    storage.set_user_context(user_email)
    
    # Rest of crawl logic...
    report_path = await storage.save_report(content, filename)
```

### 2. Pages Routes (web/routes/pages.py)
```python
@pages_bp.route('/reports')
@login_required
async def list_reports():
    # Get user email from session
    user_email = current_user.email if current_user.is_authenticated else None
    
    # Initialize storage with user context
    storage = EnhancedStorageService()
    reports = await storage.list_reports(user_email)
    
    return await render_template('reports.html', reports=reports)
```

### 3. Middleware for User Context
```python
# In app.py
@app.before_request
async def set_user_context():
    """Set user context for each request."""
    if hasattr(g, 'user') and g.user:
        g.user_email = g.user.email
    else:
        g.user_email = None
```

## Migration for Existing Data

### 1. Anonymous Migration Script
```python
# migrate_to_user_storage.py
import os
import shutil

def migrate_existing_storage():
    """Move existing files to anonymous user directory."""
    storage_path = "./storage"
    
    # Create new structure
    os.makedirs(f"{storage_path}/users/anonymous/reports", exist_ok=True)
    os.makedirs(f"{storage_path}/users/anonymous/screenshots", exist_ok=True)
    
    # Move existing reports
    old_reports = f"{storage_path}/reports"
    if os.path.exists(old_reports):
        for file in os.listdir(old_reports):
            shutil.move(
                os.path.join(old_reports, file),
                f"{storage_path}/users/anonymous/reports/{file}"
            )
    
    # Move existing screenshots
    old_screenshots = f"{storage_path}/screenshots"
    if os.path.exists(old_screenshots):
        for file in os.listdir(old_screenshots):
            shutil.move(
                os.path.join(old_screenshots, file),
                f"{storage_path}/users/anonymous/screenshots/{file}"
            )
    
    print("Migration complete!")
```

## Environment Configuration

### Local Development (.env)
```bash
# Storage Configuration
STORAGE_PATH=./storage
ENABLE_USER_PARTITIONING=true
DEFAULT_USER_EMAIL=anonymous  # For unauthenticated access
```

### Production (.env.production)
```bash
# Storage Configuration
STORAGE_PATH=gs://gnosis-wraith-prod
ENABLE_USER_PARTITIONING=true
GCS_BUCKET_NAME=gnosis-wraith-prod
```

## Docker Volume Updates

### docker-compose.yml
```yaml
services:
  wraith:
    volumes:
      - ./storage:/data  # Host mount for persistence
    environment:
      - GNOSIS_WRAITH_STORAGE_PATH=/data
      - ENABLE_USER_PARTITIONING=true
```

## Testing User Partitioning

### 1. Test Anonymous User
```bash
# Without auth, files should go to users/anonymous/
curl -X POST http://localhost:5678/api/crawl \
  -d '{"url": "https://example.com"}'

# Check location
ls -la ./storage/users/anonymous/reports/
```

### 2. Test Authenticated User
```bash
# With auth token (after login)
curl -X POST http://localhost:5678/api/crawl \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"url": "https://example.com"}'

# Check location (hash of user email)
ls -la ./storage/users/*/reports/
```

### 3. Verify Isolation
```bash
# User A should not see User B's files
# List reports endpoint should only return user's own files
```

## Benefits of This Approach

1. **Consistency**: Same paths locally and in cloud
2. **Security**: Users isolated by design
3. **Scalability**: Easy to distribute users across storage
4. **Migration**: Can move from local to cloud seamlessly
5. **Compliance**: User data clearly separated

## Implementation Order

1. **Phase 1**: Update EnhancedStorageService with user paths
2. **Phase 2**: Update save/list methods
3. **Phase 3**: Add middleware for user context
4. **Phase 4**: Migrate existing data to anonymous
5. **Phase 5**: Test with both local and cloud storage
6. **Phase 6**: Deploy with user partitioning enabled

This ensures identical behavior whether running locally or in the cloud, with proper user isolation from day one.

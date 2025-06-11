# Storage Service Implementation Guide

## Overview

This guide provides detailed implementation instructions for the enhanced storage service with user bucketing support for Gnosis Wraith.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Implementation Files](#implementation-files)
3. [User Hash Bucketing](#user-hash-bucketing)
4. [API Endpoints](#api-endpoints)
5. [Migration Guide](#migration-guide)
6. [Testing Strategy](#testing-strategy)
7. [Deployment Configuration](#deployment-configuration)
8. [Troubleshooting](#troubleshooting)

## Architecture Overview

### Storage Hierarchy

```
┌─────────────────────────────────────────┐
│          Application Layer              │
│  (Routes, Handlers, Business Logic)     │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│        Storage Service Layer            │
│  (Abstraction, User Context, Caching)   │
└─────────────────┬───────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
┌───────▼──────┐   ┌───────▼──────┐
│ Local Storage│   │ Cloud Storage│
│   (Dev/Test) │   │     (GCS)    │
└──────────────┘   └──────────────┘
```

### Key Components

1. **StorageService**: Core abstraction layer
2. **User Context**: Hash-based user identification
3. **Middleware**: Request-based user extraction
4. **Migration Tools**: For existing data

## Implementation Files

### 1. Core Storage Service (`server/storage_service_v2.py`)

```python
import os
import hashlib
import logging
from typing import Dict, Any, Optional, List, Union, BinaryIO
from datetime import datetime, timedelta
import aiofiles

logger = logging.getLogger(__name__)

class UserAwareStorageService:
    """Enhanced storage service with user bucketing support."""
    
    def __init__(self, user_hash: str = None):
        self._user_hash = user_hash or 'system'
        self._initialize_backend()
    
    @staticmethod
    def generate_user_hash(user_id: str = None, request_headers: dict = None) -> str:
        """Generate consistent user hash for bucketing."""
        if user_id:
            return hashlib.sha256(user_id.encode()).hexdigest()[:12]
        elif request_headers:
            # Anonymous user identification
            ip = request_headers.get('X-Forwarded-For', 
                                   request_headers.get('Remote-Addr', 'unknown'))
            user_agent = request_headers.get('User-Agent', 'unknown')
            identity = f"{ip}:{user_agent}"
            return hashlib.sha256(identity.encode()).hexdigest()[:12]
        else:
            return 'anonymous'
    
    def _get_user_storage_path(self, resource_type: str) -> str:
        """Get user-specific storage path."""
        if self._is_cloud:
            return f"users/{self._user_hash}/{resource_type}"
        else:
            path = os.path.join(self._base_path, 'users', self._user_hash, resource_type)
            os.makedirs(path, exist_ok=True)
            return path
```

### 2. Middleware for User Context (`server/middleware.py`)

```python
from functools import wraps
from flask import request, g
from server.storage_service_v2 import UserAwareStorageService

def extract_user_context():
    """Extract user context from request."""
    # Check for authenticated user
    user_id = None
    if hasattr(g, 'user') and g.user:
        user_id = g.user.id
    
    # Generate user hash
    user_hash = UserAwareStorageService.generate_user_hash(
        user_id=user_id,
        request_headers=dict(request.headers) if not user_id else None
    )
    
    return user_hash

def with_user_storage(f):
    """Decorator to inject user-aware storage service."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_hash = extract_user_context()
        storage_service = UserAwareStorageService(user_hash=user_hash)
        return f(*args, storage_service=storage_service, **kwargs)
    return decorated_function
```

### 3. Updated Routes (`app.py` modifications)

```python
from server.middleware import with_user_storage

@app.route('/api/crawl', methods=['POST'])
@with_user_storage
async def crawl_endpoint(storage_service):
    """Crawl endpoint with user isolation."""
    data = request.get_json()
    
    # Perform crawl
    results = await perform_crawl(data['url'])
    
    # Save report to user's bucket
    report_path = await storage_service.save_report(
        content=results['content'],
        filename=f"crawl_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        format='md'
    )
    
    return jsonify({
        'success': True,
        'report_url': storage_service.get_report_url(report_path)
    })

@app.route('/api/reports')
@with_user_storage
async def list_user_reports(storage_service):
    """List reports for current user."""
    reports = await storage_service.list_reports()
    return jsonify(reports)
```

## User Hash Bucketing

### Implementation Details

1. **Hash Generation Algorithm**
   - SHA-256 with 12-character prefix
   - Ensures even distribution
   - Privacy-preserving (non-reversible)

2. **Bucket Structure**
   ```
   users/
   ├── a1b2c3d4e5f6/     # User bucket
   │   ├── reports/      # User's reports
   │   ├── screenshots/  # User's screenshots
   │   └── metadata.json # User metadata
   └── system/           # System/shared resources
   ```

3. **Anonymous User Handling**
   - IP + User-Agent combination
   - Consistent across sessions
   - Configurable retention policy

### Code Example

```python
# User identification flow
def identify_user(request):
    # 1. Check for authenticated user
    if request.user.is_authenticated:
        return UserAwareStorageService.generate_user_hash(
            user_id=str(request.user.id)
        )
    
    # 2. Check for session-based identification
    if 'user_hash' in request.session:
        return request.session['user_hash']
    
    # 3. Generate anonymous hash
    user_hash = UserAwareStorageService.generate_user_hash(
        request_headers=dict(request.headers)
    )
    
    # Store in session for consistency
    request.session['user_hash'] = user_hash
    return user_hash
```

## API Endpoints

### User Reports

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/reports` | GET | List user's reports | No* |
| `/api/reports/<id>` | GET | Get specific report | No* |
| `/api/reports/<id>` | DELETE | Delete report | No* |
| `/api/reports/stats` | GET | Get storage stats | No* |

*Uses user hash from request context

### Admin Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/admin/users` | GET | List all user hashes | Yes |
| `/api/admin/users/<hash>/reports` | GET | List user's reports | Yes |
| `/api/admin/users/<hash>/stats` | GET | Get user stats | Yes |
| `/api/admin/cleanup` | POST | Clean old reports | Yes |

## Migration Guide

### Step 1: Backup Existing Data

```bash
# Backup current reports
cp -r ~/.gnosis-wraith/reports ~/.gnosis-wraith/reports.backup

# Or use the backup script
python scripts/backup_reports.py
```

### Step 2: Run Migration Script

```python
# scripts/migrate_to_user_buckets.py
import asyncio
from server.storage_service_v2 import UserAwareStorageService

async def migrate_reports():
    """Migrate existing reports to user bucket structure."""
    storage = UserAwareStorageService(user_hash='migrated')
    
    # Get all existing reports
    old_reports_dir = os.path.expanduser('~/.gnosis-wraith/reports')
    
    for filename in os.listdir(old_reports_dir):
        if filename.endswith(('.md', '.json', '.html')):
            # Read old report
            with open(os.path.join(old_reports_dir, filename), 'r') as f:
                content = f.read()
            
            # Save to new structure
            await storage.save_report(
                content=content,
                filename=os.path.splitext(filename)[0],
                format=filename.split('.')[-1]
            )
            
            print(f"Migrated: {filename}")

if __name__ == "__main__":
    asyncio.run(migrate_reports())
```

### Step 3: Verify Migration

```python
# Verify migration success
python scripts/verify_migration.py

# Check report counts
python scripts/count_reports.py
```

## Testing Strategy

### Unit Tests

```python
# tests/test_user_storage.py
import pytest
from server.storage_service_v2 import UserAwareStorageService

@pytest.mark.asyncio
async def test_user_isolation():
    """Test that users cannot access each other's reports."""
    # Create two storage instances with different users
    storage1 = UserAwareStorageService(user_hash='user1')
    storage2 = UserAwareStorageService(user_hash='user2')
    
    # Save report as user1
    await storage1.save_report('User 1 content', 'test_report', 'md')
    
    # Verify user2 cannot see it
    user2_reports = await storage2.list_reports()
    assert len(user2_reports) == 0
    
    # Verify user1 can see it
    user1_reports = await storage1.list_reports()
    assert len(user1_reports) == 1
```

### Integration Tests

```python
# tests/test_integration.py
def test_full_flow(client):
    """Test complete user flow."""
    # 1. Crawl as anonymous user
    response = client.post('/api/crawl', json={
        'url': 'https://example.com'
    })
    assert response.status_code == 200
    
    # 2. List reports (should see the one just created)
    response = client.get('/api/reports')
    reports = response.json()
    assert len(reports) == 1
    
    # 3. Different session should not see reports
    client.cookie_jar.clear()
    response = client.get('/api/reports')
    reports = response.json()
    assert len(reports) == 0
```

## Deployment Configuration

### Local Development

```bash
# .env.local
RUNNING_IN_CLOUD=false
STORAGE_PATH=./storage
ENABLE_USER_BUCKETING=true
DEFAULT_USER_HASH=dev_user
LOG_LEVEL=DEBUG
```

### Google Cloud Run

```yaml
# cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/gnosis-wraith', '.']
    env:
      - 'RUNNING_IN_CLOUD=true'
      - 'GCS_BUCKET_NAME=gnosis-wraith-storage'
      - 'ENABLE_USER_BUCKETING=true'
```

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `RUNNING_IN_CLOUD` | Cloud environment flag | false | No |
| `GCS_BUCKET_NAME` | GCS bucket name | - | Yes (cloud) |
| `STORAGE_PATH` | Local storage path | ./storage | No |
| `ENABLE_USER_BUCKETING` | Enable user isolation | true | No |
| `USER_RETENTION_DAYS` | Days to keep anonymous data | 30 | No |
| `MAX_USER_STORAGE_MB` | Per-user storage limit | 100 | No |

## Troubleshooting

### Common Issues

1. **Permission Denied Errors**
   ```bash
   # Fix local permissions
   chmod -R 755 ~/.gnosis-wraith/storage
   ```

2. **GCS Authentication Issues**
   ```bash
   # Set up application default credentials
   gcloud auth application-default login
   ```

3. **User Hash Consistency**
   - Ensure session middleware is properly configured
   - Check cookie settings for cross-domain issues

### Debug Mode

Enable detailed logging:

```python
# In your app configuration
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('storage_service')
logger.setLevel(logging.DEBUG)
```

### Health Check Endpoint

```python
@app.route('/api/storage/health')
def storage_health():
    """Check storage service health."""
    try:
        storage = UserAwareStorageService()
        
        # Test write
        test_path = storage._get_user_storage_path('health')
        test_file = os.path.join(test_path, 'health_check.txt')
        
        with open(test_file, 'w') as f:
            f.write(str(datetime.now()))
        
        # Test read
        with open(test_file, 'r') as f:
            content = f.read()
        
        # Clean up
        os.remove(test_file)
        
        return jsonify({
            'status': 'healthy',
            'storage_type': 'cloud' if storage._is_cloud else 'local',
            'timestamp': content
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500
```

## Best Practices

1. **Always use the storage service** - Never write directly to filesystem
2. **Handle user context properly** - Use middleware consistently
3. **Implement retention policies** - Clean up old anonymous user data
4. **Monitor storage usage** - Set up alerts for quota limits
5. **Test user isolation** - Regularly verify bucket separation

## Next Steps

1. Implement authentication system if not already present
2. Add storage quota management
3. Set up monitoring and alerts
4. Create admin dashboard for user management
5. Implement data export/import features

This implementation provides a robust, scalable storage solution with proper user isolation and cloud readiness.
# Unified User Storage Plan (Revised) - NDB + Storage Hybrid

## Core Architecture: NDB for Users, Storage for Content

### Why This Approach?
- **NDB**: User profiles, auth, tokens, metadata (already implemented!)
- **Storage**: Reports, screenshots, large files (bulk data)
- **Best of both**: Database for structured data, filesystem for files

## User Model in NDB

```python
# core/models/user.py (already exists, just needs storage_hash)
from google.cloud import ndb
from core.models.base import BaseModel
import hashlib

class User(BaseModel):
    # Existing fields
    email = ndb.StringProperty(required=True)
    uid = ndb.StringProperty(required=True)
    login_token = ndb.StringProperty()
    token_timestamp = ndb.DateTimeProperty()
    
    # Add storage-related fields
    storage_hash = ndb.ComputedProperty(
        lambda self: hashlib.sha256(self.email.encode()).hexdigest()[:12]
    )
    
    # Metadata for user management
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    last_login = ndb.DateTimeProperty()
    last_crawl = ndb.DateTimeProperty()
    
    # Usage tracking
    crawl_count = ndb.IntegerProperty(default=0)
    total_storage_bytes = ndb.IntegerProperty(default=0)
    
    # API tokens stored in NDB (not filesystem)
    api_tokens = ndb.JsonProperty(default=[])  # List of {token, name, created}
    
    # Settings/preferences
    settings = ndb.JsonProperty(default={})
    
    @classmethod
    def get_or_create_anonymous(cls):
        """Get or create the anonymous user."""
        anon = cls.query(cls.email == "anonymous@system").get()
        if not anon:
            anon = cls(
                email="anonymous@system",
                uid="anonymous",
                # storage_hash will be computed as hash of "anonymous@system"
            )
            anon.put()
        return anon
```

## Storage Structure (Simplified)

```
storage/                          # Root (./storage locally, gs://bucket/ in cloud)
├── users/                        
│   ├── anonymous/               # Hash of "anonymous@system"
│   │   ├── reports/
│   │   └── screenshots/
│   │
│   └── [user.storage_hash]/     # From NDB user.storage_hash
│       ├── reports/
│       └── screenshots/
│
└── system/                      # System-wide data
    ├── cache/
    └── logs/
```

## Enhanced Storage Service Integration

```python
# core/enhanced_storage_service.py

from typing import Optional
from core.models.user import User
from google.cloud import ndb

class EnhancedStorageService:
    def __init__(self, user: Optional[User] = None):
        self._user = user
        self._storage_path = os.environ.get('GNOSIS_WRAITH_STORAGE_PATH', '/data')
        
    def set_user(self, user: User):
        """Set user context from NDB model."""
        self._user = user
    
    def get_user_path(self) -> str:
        """Get user-specific storage path from NDB user."""
        if self._user and self._user.storage_hash:
            return f"users/{self._user.storage_hash}"
        else:
            # Fallback to anonymous
            anon = User.get_or_create_anonymous()
            return f"users/{anon.storage_hash}"
    
    async def save_report(self, content: str, filename: str, format: str = 'md') -> str:
        """Save report and update user metadata in NDB."""
        user_path = self.get_user_path()
        
        # Save to storage (local or cloud)
        if self.is_cloud_storage():
            blob_path = f"{user_path}/reports/{filename}.{format}"
            url = await self._save_to_gcs(content, blob_path)
        else:
            local_dir = os.path.join(self._storage_path, user_path, 'reports')
            os.makedirs(local_dir, exist_ok=True)
            
            file_path = os.path.join(local_dir, f"{filename}.{format}")
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            url = file_path
        
        # Update user metadata in NDB
        if self._user:
            self._user.last_crawl = datetime.utcnow()
            self._user.crawl_count += 1
            self._user.total_storage_bytes += len(content.encode('utf-8'))
            self._user.put()
        
        return url
    
    async def list_user_reports(self) -> List[dict]:
        """List reports for the current user."""
        user_path = self.get_user_path()
        
        if self.is_cloud_storage():
            prefix = f"{user_path}/reports/"
            blobs = self._bucket.list_blobs(prefix=prefix)
            return [self._blob_to_dict(blob) for blob in blobs]
        else:
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

## API Integration with NDB

```python
# web/routes/api.py

from core.models.user import User
from core.lib.ndb_local import ndb_context_manager

@api.route('/crawl', methods=['POST'])
async def crawl():
    # Get current user from auth/session
    with ndb_context_manager():
        if current_user.is_authenticated:
            user = User.get_by_uid(current_user.uid)
        else:
            user = User.get_or_create_anonymous()
        
        # Initialize storage with NDB user
        storage = EnhancedStorageService(user=user)
        
        # Perform crawl and save
        content = await perform_crawl(...)
        report_path = await storage.save_report(content, filename)
        
        # User metadata already updated in save_report
        
    return jsonify({
        'success': True,
        'report_path': report_path,
        'user': user.email
    })
```

## Pages Routes with NDB

```python
# web/routes/pages.py

from core.models.user import User
from flask_login import current_user

@pages_bp.route('/reports')
@login_required
async def list_reports():
    with ndb_context_manager():
        # Get user from NDB
        user = User.get_by_uid(current_user.uid)
        
        # Get their reports from storage
        storage = EnhancedStorageService(user=user)
        reports = await storage.list_user_reports()
        
        # Add user metadata from NDB
        user_data = {
            'email': user.email,
            'crawl_count': user.crawl_count,
            'last_crawl': user.last_crawl,
            'storage_used': user.total_storage_bytes
        }
        
    return await render_template('reports.html', 
                                reports=reports,
                                user=user_data)
```

## Auth Integration Updates

```python
# web/routes/auth.py

@auth.route('/login', methods=['POST'])
async def login_post():
    email = request.form.get('email')
    
    with ndb_context_manager():
        # Get or create user in NDB
        user = User.query(User.email == email).get()
        if not user:
            # Create new user
            user = User(
                email=email,
                uid=str(uuid.uuid4()),
                created_at=datetime.utcnow()
            )
            user.put()
        
        # Generate login token
        token = random_string(6)
        user.login_token = token
        user.token_timestamp = datetime.utcnow()
        user.put()
        
        # Send email with token
        email_user(email, token)
    
    return redirect(url_for('auth.token'))
```

## Migration Script

```python
# scripts/migrate_to_ndb_storage.py

from core.models.user import User
from core.lib.ndb_local import ndb_context_manager
import os
import shutil

def migrate_existing_storage():
    """Migrate existing files and create NDB records."""
    
    with ndb_context_manager():
        # 1. Create anonymous user in NDB
        anon = User.get_or_create_anonymous()
        print(f"Anonymous user hash: {anon.storage_hash}")
        
        # 2. Move existing files to anonymous directory
        old_reports = "./storage/reports"
        old_screenshots = "./storage/screenshots"
        
        new_anon_path = f"./storage/users/{anon.storage_hash}"
        os.makedirs(f"{new_anon_path}/reports", exist_ok=True)
        os.makedirs(f"{new_anon_path}/screenshots", exist_ok=True)
        
        # Move reports
        if os.path.exists(old_reports):
            for file in os.listdir(old_reports):
                shutil.move(
                    os.path.join(old_reports, file),
                    f"{new_anon_path}/reports/{file}"
                )
                anon.crawl_count += 1
            
        # Move screenshots  
        if os.path.exists(old_screenshots):
            for file in os.listdir(old_screenshots):
                shutil.move(
                    os.path.join(old_screenshots, file),
                    f"{new_anon_path}/screenshots/{file}"
                )
        
        # Update anonymous user stats
        anon.put()
        print(f"Migrated {anon.crawl_count} reports to anonymous user")

if __name__ == "__main__":
    migrate_existing_storage()
```

## Environment Configuration

```bash
# .env (local development)
USE_LOCAL_DATASTORE=true
LOCAL_DATASTORE_PATH=./local_datastore
STORAGE_PATH=./storage

# .env.production (Google Cloud)
USE_LOCAL_DATASTORE=false
STORAGE_PATH=gs://gnosis-wraith-prod
GOOGLE_CLOUD_PROJECT=your-project-id
```

## Testing the Hybrid Approach

```python
# tests/test_ndb_storage.py

async def test_user_storage_isolation():
    """Test that users have isolated storage."""
    with ndb_context_manager():
        # Create two users
        user1 = User(email="user1@test.com", uid="uid1")
        user1.put()
        
        user2 = User(email="user2@test.com", uid="uid2") 
        user2.put()
        
        # Verify different storage hashes
        assert user1.storage_hash != user2.storage_hash
        
        # Save reports for each
        storage1 = EnhancedStorageService(user=user1)
        await storage1.save_report("User 1 content", "report1")
        
        storage2 = EnhancedStorageService(user=user2)
        await storage2.save_report("User 2 content", "report2")
        
        # List reports - should be isolated
        reports1 = await storage1.list_user_reports()
        reports2 = await storage2.list_user_reports()
        
        assert len(reports1) == 1
        assert len(reports2) == 1
        assert reports1[0]['filename'] != reports2[0]['filename']
```

## Benefits of NDB + Storage Hybrid

1. **Atomic Operations**: User updates, token rotation in NDB
2. **Fast Queries**: Find users, check quotas, analytics
3. **Bulk Storage**: Reports and screenshots in filesystem/GCS  
4. **Already Built**: Leverage existing NDB implementation
5. **Scale Ready**: NDB handles millions of users
6. **Clean Separation**: Structured data vs files

## Implementation Steps

1. **Add storage_hash to User model** ✓
2. **Update EnhancedStorageService to use NDB user** ✓
3. **Modify API routes to get user from NDB** ✓
4. **Run migration script for existing files** ✓
5. **Test user isolation and storage paths** ✓
6. **Deploy with NDB enabled** ✓

This approach leverages your existing NDB work while keeping bulk content in storage - the best architectural choice for Gnosis Wraith!

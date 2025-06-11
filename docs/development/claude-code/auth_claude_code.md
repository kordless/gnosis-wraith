# Authentication System Implementation Plan - Gnosis Wraith

## Current State (What Was Created)

Files were mistakenly created in `gnosis_wraith/server/` but should be in `server/`:

### Created Files (Wrong Location):
- `gnosis_wraith/server/models/base.py`
- `gnosis_wraith/server/models/user.py`
- `gnosis_wraith/server/models/__init__.py`
- `gnosis_wraith/server/lib/ndb_local.py`
- `gnosis_wraith/server/storage/user_storage.py`
- `gnosis_wraith/server/storage/__init__.py`
- `gnosis_wraith/server/templates/auth/login.html`
- `gnosis_wraith/server/templates/auth/token.html`

## What Should Be (Correct Structure)

### 1. Move Files to Correct Locations:
```
gnosis-wraith/
├── server/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py          # BaseModel with JSON storage
│   │   └── user.py          # User model
│   ├── lib/
│   │   ├── util.py          # Already exists
│   │   └── ndb_local.py     # Local JSON datastore
│   ├── routes/
│   │   └── auth.py          # Already exists
│   ├── templates/
│   │   └── auth/
│   │       ├── login.html   # Login page
│   │       └── token.html   # Token entry page
│   ├── storage_service.py          # Existing base storage
│   └── enhanced_storage_service.py # THIS is where user bucketing goes
```

### 2. Storage Consolidation

**Don't create a separate user_storage.py!** Instead, update `enhanced_storage_service.py` to:

1. Add user context from `current_user` (Flask-Login)
2. Modify save methods to use user buckets automatically
3. Add the SHA256(email) hash generation

**Example integration:**
```python
# In enhanced_storage_service.py
from flask_login import current_user
import hashlib

class EnhancedStorageService:
    def __init__(self):
        # ... existing init ...
        
    def _get_user_hash(self) -> str:
        """Get current user's storage hash"""
        if hasattr(current_user, 'email') and current_user.is_authenticated:
            return hashlib.sha256(current_user.email.encode()).hexdigest()[:12]
        return 'anonymous'
    
    async def save_report(self, content: str, filename: str, format: str = 'md') -> str:
        """Save report with automatic user bucketing"""
        user_hash = self._get_user_hash()
        full_filename = f"{filename}.{format}"
        
        if is_running_in_cloud():
            # Save to GCS: users/{user_hash}/reports/{filename}
            return await self.save_file(content, f'users/{user_hash}/reports', full_filename)
        else:
            # Save to local: storage/users/{user_hash}/reports/{filename}
            user_reports_dir = os.path.join(self._storage_path, 'users', user_hash, 'reports')
            os.makedirs(user_reports_dir, exist_ok=True)
            # ... rest of save logic
```

### 3. Implementation Steps

1. **Move all files** from `gnosis_wraith/server/` to `server/`
2. **Delete** the separate `storage/user_storage.py` files
3. **Update** `enhanced_storage_service.py` to:
   - Import `current_user` from flask_login
   - Add `_get_user_hash()` method
   - Modify all save/list/get methods to use user buckets
   - Keep backward compatibility for non-authenticated requests
4. **Update imports** in moved files to use correct paths
5. **Test** the authentication flow with the consolidated storage

### 4. Environment Variables

```bash
# Local Development
USE_LOCAL_DATASTORE=true
LOCAL_DATASTORE_PATH=./local_datastore

# Email (SendGrid)
SENDGRID_API_KEY=your-key-here

# SMS (Twilio)
TWILIO_ACCOUNT_SID=your-sid-here
TWILIO_AUTH_TOKEN=your-token-here
TWILIO_NUMBER=+1234567890

# Storage (existing)
STORAGE_PATH=./storage
GNOSIS_WRAITH_REPORTS_DIR=~/.gnosis-wraith/reports
RUNNING_IN_CLOUD=false
GCS_BUCKET_NAME=gnosis-wraith-storage

# App Config
APP_DOMAIN=localhost:5678
BRAND=Gnosis Wraith
SECRET_KEY=generate-random-key
DEV=True
```

### 5. Key Changes from Original Plan

1. **No separate user storage service** - User bucketing is integrated into `EnhancedStorageService`
2. **Automatic user context** - Uses `current_user` from Flask-Login, no need to pass email around
3. **Single storage service** - Everything goes through `EnhancedStorageService`
4. **Simpler imports** - No complex storage package, just use the enhanced service

### 6. Auth Route Updates Needed

Update `server/routes/auth.py` to:
1. Import from `server.models.user` instead of SlothAI
2. Use the new User model with local JSON storage
3. Ensure Flask-Login is properly configured
4. Remove references to Pipeline, Node, Template models

### 7. Testing Checklist

- [ ] Move all files to correct locations
- [ ] Update EnhancedStorageService with user bucketing
- [ ] Configure environment variables
- [ ] Test user registration/login flow
- [ ] Verify user bucket creation on first save
- [ ] Check that different users have isolated storage
- [ ] Test anonymous user storage (should use 'anonymous' bucket)

## Summary

The main consolidation tasks are:
1. **Move files** from `gnosis_wraith/server/` to `server/`
2. **Delete** separate user_storage files
3. **Update** `enhanced_storage_service.py` to handle user bucketing internally
4. **Fix imports** throughout
5. **Test** the complete flow

This keeps everything simple with one storage service that automatically handles user isolation based on the logged-in user.

NOTE
● Phase 2 is complete! All imports have been updated:
  - Updated app.py with correct imports and Flask/Quart configuration
  - Fixed all core module imports (server.* → core.*)
  - Fixed all web route imports (server.* → core.*)
  - Fixed blueprint imports
  - Config paths are already correctly set

  The app structure is now:
  - /core/ - Processing engine (crawler, reports, storage, etc.)     
  - /web/ - Web interface (routes, templates, static files)
  - /app.py - Main application entry point

  Note: The auth.py file uses Flask instead of Quart, which will need to be addressed in Phase      
  3 along with the auth integration.

# Gnosis Wraith Restructuring Plan - Phase 3: Auth and Storage Integration

## Overview
This document outlines Phase 3 - integrating authentication and user-based storage after the directory restructure.

## Phase 3: Authentication and Storage Integration

### Step 1: Update enhanced_storage_service.py
Add user bucketing to the existing EnhancedStorageService:

```python
# At the top of /core/enhanced_storage_service.py
from flask_login import current_user
import hashlib

# Add to EnhancedStorageService class:
def _get_user_hash(self) -> str:
    """Get current user's storage hash from logged in user"""
    try:
        if hasattr(current_user, 'email') and current_user.is_authenticated:
            return hashlib.sha256(current_user.email.encode()).hexdigest()[:12]
    except:
        pass
    return 'anonymous'

# Update save_report method:
async def save_report(self, content: str, filename: str, format: str = 'md') -> str:
    user_hash = self._get_user_hash()
    full_filename = f"{filename}.{format}"
    
    if is_running_in_cloud():
        # GCS path with user bucket
        return await self.save_file(content, f'users/{user_hash}/reports', full_filename)
    else:
        # Local path with user bucket
        user_reports_dir = os.path.join(self._reports_dir, 'users', user_hash)
        os.makedirs(user_reports_dir, exist_ok=True)
        report_path = os.path.join(user_reports_dir, full_filename)
        # ... rest of save logic
```

### Step 2: Set Up Flask-Login
In app.py:

```python
from flask_login import LoginManager, login_required
from core.models.user import User

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_uid(user_id)
```

### Step 3: Update Auth Routes
In /web/routes/auth.py:

```python
# Update imports
from core.models.user import User
from core.lib.util import email_user, sms_user, generate_token

# Remove Transaction model usage (not implemented yet)
# Simplify to just use User model

# Update route decorators
@auth.route('/login', methods=['GET'])
async def login():
    # Render login template
    return await render_template('auth/login.html', 
                               config=app.config,
                               brand=get_brand(app))

# Update all User model calls to use new methods
user = User.get_by_email(email)  # This works with our JSON model
```

### Step 4: Update Util Functions
In /core/lib/util.py:

```python
# Make sure these functions work standalone
def email_user(email, subject="subject", html_content="content"):
    """Send email via SendGrid"""
    if os.getenv('DEV', 'True') == 'True':
        print(f"DEV MODE - Email to {email}: {subject}")
        return {'status': 'success', 'message': 'dev mode'}
    
    # SendGrid implementation
    # ...

def sms_user(phone_e164, message="Message"):
    """Send SMS via Twilio"""
    if os.getenv('DEV', 'True') == 'True':
        print(f"DEV MODE - SMS to {phone_e164}: {message}")
        return {'status': 'success', 'message': 'dev mode'}
    
    # Twilio implementation
    # ...
```

### Step 5: Protected Routes
Add authentication to existing routes:

```python
# In /web/routes/pages.py
@pages.route('/crawl')
@login_required  # Add this decorator
async def crawl():
    # Existing crawl logic
    # Storage will automatically use logged-in user's bucket
    
# In /web/routes/api.py
@api.route('/api/crawl', methods=['POST'])
@login_required  # Add this decorator
async def api_crawl():
    # Existing API logic
```

### Step 6: Environment Variables
Create .env file:

```bash
# App Settings
USE_LOCAL_DATASTORE=true
LOCAL_DATASTORE_PATH=./local_datastore
DEV=True
SECRET_KEY=your-secret-key-here
APP_DOMAIN=localhost:5678

# Email
SENDGRID_API_KEY=your-sendgrid-key

# SMS  
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-auth
TWILIO_NUMBER=+1234567890

# Brand
BRAND=Gnosis Wraith
BRAND_FAVICON=/static/images/favicon.ico
```

### Step 7: Test Auth Flow

1. **Start app**: `python app.py`
2. **Visit**: http://localhost:5678/login
3. **Enter email**: Check console for token (DEV mode)
4. **Enter token**: Should log in
5. **Test protected route**: http://localhost:5678/crawl
6. **Check storage**: Look for user bucket in storage/users/{hash}/

## Migration Notes

- Existing reports stay in old location
- New reports go to user buckets
- Anonymous users use 'anonymous' bucket
- Can migrate old reports manually if needed

## Security Considerations

1. **Session secret**: Set strong SECRET_KEY
2. **Token rotation**: Tokens rotate after use
3. **HTTPS only**: Enforce in production
4. **Rate limiting**: Add to prevent brute force

## Next Steps

1. Test complete auth flow
2. Configure SendGrid/Twilio
3. Add UI for login/logout
4. Test user storage isolation

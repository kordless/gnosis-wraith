# Auth System Fix Instructions for Claude Code

## Quick Summary
The auth system is broken after restructuring. Login redirects back to itself, logout hits wrong URL, and styling doesn't match. Here's what to fix:

## 1. Fix Logout URL (EASY - DO THIS FIRST)

In `web/static/js/components/profile-settings-modal.js` line 66:
```javascript
// WRONG:
const response = await fetch('/api/logout', {

// CORRECT:
const response = await fetch('/auth/logout', {
```

## 2. Fix Missing Model Imports (MAIN ISSUE)

The auth system can't find User and Transaction models. Check if these files exist:
- `/app/core/models/user.py`
- `/app/core/lib/util.py`

If they DON'T exist, create this stub file at `core/models/user.py`:

```python
"""Temporary stub models for auth system"""
import random
import string
import datetime

def generate_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=40))

class User:
    def __init__(self):
        self.email = None
        self.mail_token = generate_token()
        self.mail_confirm = False
        self.mail_tries = 0
        self.phone_code = None
        self.updated = datetime.datetime.utcnow()
    
    @staticmethod
    def get_by_email(email):
        return None  # Always return None = new user
    
    @staticmethod
    def create(email):
        user = User()
        user.email = email
        return user
    
    def put(self):
        pass  # No-op for now
    
    def has_phone(self):
        return False

class Transaction:
    @staticmethod
    def create(uid, tid):
        return Transaction()
    
    @staticmethod
    def query():
        class Query:
            def filter(self, *args):
                class Filter:
                    def get(self):
                        return None  # No transaction found
                return Filter()
        return Query()
    
    def delete(self):
        pass
```

And create `core/lib/util.py`:

```python
"""Utility functions for auth"""
import random
import string

def random_string(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_token():
    return random_string(40)

def random_number(digits):
    return ''.join(random.choices(string.digits, k=digits))

def email_user(email, subject, html_content):
    print(f"EMAIL WOULD BE SENT TO: {email}")
    print(f"SUBJECT: {subject}")
    print(f"TOKEN IS IN THE EMAIL CONTENT")
    return True

def sms_user(phone, message):
    print(f"SMS WOULD BE SENT TO: {phone}")
    print(f"MESSAGE: {message}")
    return True
```

## 3. Add DEV Environment Variable

In `docker-compose.yml`, add to the wraith service:
```yaml
environment:
  - DEV=True
```

Or when running Docker:
```bash
docker run -e DEV=True ...
```

## 4. Debug Login Redirect

Add this to the TOP of `login_post()` in `web/routes/auth.py`:

```python
@auth.route('/login', methods=['POST'])
async def login_post():
    print("DEBUG: Login POST received")
    try:
        # Test imports first
        try:
            from core.models.user import User, Transaction
            print("DEBUG: Models imported successfully")
        except Exception as e:
            print(f"DEBUG: Model import failed: {e}")
            await flash("System configuration error")
            return redirect(url_for('auth.login'))
        
        try:
            from core.lib.util import random_string, email_user, generate_token
            print("DEBUG: Utils imported successfully")
        except Exception as e:
            print(f"DEBUG: Utils import failed: {e}")
            await flash("System configuration error")
            return redirect(url_for('auth.login'))
        
        # Rest of the function...
```

## 5. Fix Login Page Styling (OPTIONAL)

In `web/templates/auth/login.html`:

Change line ~11 from:
```css
background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
```

To:
```css
background: #111827; /* Match main app bg-gray-900 */
```

Change line ~31 from:
```html
<h2 class="text-3xl font-bold text-white">
```

To:
```html
<h2 class="text-3xl font-bold text-green-400">
```

## Test Order:
1. Fix logout URL first (easy win)
2. Check Docker logs for import errors
3. Create stub model files if needed
4. Add DEV=True to see login tokens
5. Test login flow

The main issue is missing model files after restructuring. Creating stubs will get auth working temporarily.
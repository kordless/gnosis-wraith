# Gnosis Wraith Authentication System - Implementation Status & Thoughts

## How the Login System Works

The authentication system implements a **passwordless login flow**:

1. **User enters email** at `/auth/login`
   - Anti-bot protection: Hidden password field (honeypot)
   - Transaction ID created for form submission tracking

2. **Email with magic link/token sent**
   - 6-digit token generated: `generate_token()` creates URL-safe token
   - Email sent via SendGrid (or printed to console in DEV mode)
   - User redirected to `/auth/token` to enter the code

3. **Token verification**
   - User enters the 6-digit code
   - Token is verified and rotated after use (one-time use)
   - Session created with `user_uid` and `user_email`

4. **Optional 2FA with SMS** (if phone number is set)
   - Additional SMS code sent via Twilio
   - User enters code at `/auth/tfa`

## Configuration & Environment Variables

### Where Config Goes
The system uses **environment variables** loaded from `.env` file:

```bash
# Current .env location: /mnt/c/Users/kord/Code/gnosis/gnosis-wraith/.env

# Core Settings
DEV=True                    # Dev mode - prints emails/SMS to console
SECRET_KEY=your-secret-key  # Session encryption key
APP_DOMAIN=localhost:5678   # Used in email "from" address

# Email Service (SendGrid)
SENDGRID_API_KEY=your-key   # Get from sendgrid.com

# SMS Service (Twilio)  
TWILIO_ACCOUNT_SID=your-sid
TWILIO_AUTH_TOKEN=your-auth
TWILIO_NUMBER=+1234567890   # Your Twilio phone number
```

### For Google Cloud Run
Environment variables are set via:
- Cloud Console UI (easiest)
- `gcloud run deploy --set-env-vars`
- Secret Manager for sensitive values

## Service Configuration Status

### Email (SendGrid)
- **Status**: Code is ready but needs API key
- **Dev Mode**: Currently prints to console when `DEV=True`
- **To Enable**: 
  1. Sign up at sendgrid.com
  2. Get API key
  3. Add to .env: `SENDGRID_API_KEY=your-key`
  4. Set `DEV=False`

### SMS (Twilio)
- **Status**: Code is ready but needs credentials
- **Dev Mode**: Currently prints to console when `DEV=True`
- **To Enable**:
  1. Sign up at twilio.com
  2. Get Account SID, Auth Token, and phone number
  3. Add all three to .env
  4. Set `DEV=False`

## Security Analysis

### Session Security
- **Session Storage**: Server-side sessions using Quart's session management
- **Session Cookie**: Encrypted with `SECRET_KEY`
- **Token**: Uses `secrets.token_urlsafe()` - cryptographically secure
- **Token Rotation**: Tokens are single-use and rotated after verification

### Potential Issues
1. **SECRET_KEY**: Currently using default in code - MUST change for production
2. **HTTPS**: Required for production (cookies need `secure` flag)
3. **Session Timeout**: Not currently implemented - sessions persist
4. **Rate Limiting**: Not implemented - could allow brute force attempts

## Database Status

### User Model
- **Status**: ✅ Fully implemented with JSON storage
- **Location**: `core/models/user.py`
- **Storage**: Local JSON files in `./local_datastore/`
- **Features**:
  - Create user with email
  - Store/verify tokens
  - Track login attempts
  - Optional phone for 2FA

### Create User Flow
```python
# User creation happens automatically on first login:
1. User enters email
2. System checks if user exists: User.get_by_email(email)
3. If not, creates new user: User.create(email)
4. Sends token to email
```

### User Storage
- **Local Development**: JSON files in `./local_datastore/User/`
- **Production**: Can use Google Cloud Datastore (code supports both)
- **User Bucketing**: Storage service updated to use user-specific directories

## API Token Authentication

For API endpoints like `/api/crawl`:
1. User has `api_token` field in User model
2. Could implement Bearer token auth:
   ```python
   Authorization: Bearer <user.api_token>
   ```
3. Currently uses session-based auth (cookie)

## What Still Needs Work

1. **API Token Auth**: Currently using session cookies, not API tokens
2. **Token in Headers**: Need to implement Bearer token validation
3. **Rate Limiting**: Prevent brute force attacks
4. **Session Timeout**: Auto-logout after inactivity
5. **Password Reset Flow**: Currently no way to reset if email is inaccessible

## Recommendations

### For Quick Testing
```bash
# In .env, just use:
DEV=True
SECRET_KEY=change-this-in-production
APP_DOMAIN=localhost:5678
```
This will print all emails/SMS to console for testing.

### For Production
1. Use Secret Manager for sensitive values
2. Set up real SendGrid account (free tier available)
3. Skip Twilio if you don't need 2FA
4. Use HTTPS (Cloud Run provides this)
5. Change SECRET_KEY to something secure:
   ```python
   import secrets
   print(secrets.token_urlsafe(32))
   ```

### For API Authentication
Consider implementing a middleware that checks for API token in headers:
```python
def api_auth_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            user = User.get_by_api_token(token)
            if user:
                request.current_user = user
                return await func(*args, **kwargs)
        return {'error': 'Unauthorized'}, 401
    return wrapper
```

## Summary

The authentication system is **functionally complete** but needs:
1. Real email/SMS service credentials (or stay in DEV mode)
2. Production SECRET_KEY
3. API token authentication for programmatic access
4. Security hardening (rate limits, timeouts)

The passwordless email flow is modern and secure, avoiding password storage entirely. The system is ready for testing in DEV mode without any external services.
# Authentication Usage Guide

## Overview

The Gnosis Wraith auth system supports multiple authentication methods:
1. **Session-based** (web login)
2. **API Token** (programmatic access)

## Using @login_required Decorator

To protect any API endpoint, simply add the `@login_required` decorator:

```python
from auth import login_required, api_token_optional

@api_bp.route('/your-endpoint', methods=['GET', 'POST'])
@login_required
async def your_protected_endpoint():
    # Access user info from request
    user_email = getattr(request, 'user_email', None)
    user_uid = getattr(request, 'user_uid', None)
    auth_method = getattr(request, 'auth_method', None)  # 'session' or 'api_token'
    
    # Your endpoint logic here
    return jsonify({"success": True, "user": user_email})
```

## API Token Authentication Methods

### 1. Authorization Header (Recommended)
```bash
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
     -X POST https://your-domain.com/api/v2/md \
     -d '{"url": "https://example.com"}'
```

### 2. X-API-Token Header
```bash
curl -H "X-API-Token: YOUR_API_TOKEN" \
     -X POST https://your-domain.com/api/v2/md \
     -d '{"url": "https://example.com"}'
```

### 3. JSON Body (POST only)
```bash
curl -X POST https://your-domain.com/api/v2/md \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://example.com",
       "api_token": "YOUR_API_TOKEN"
     }'
```

## Token Management Endpoints

- **Generate Token**: `POST /api/token/generate` (requires session auth)
- **Token Info**: `GET /api/token/info`
- **Reset Token**: `POST /token_reset`

## Request Attributes

When a request is authenticated, these attributes are added to the request object:

- `request.user_email` - User's email address
- `request.user_uid` - User's unique ID
- `request.auth_method` - Either 'session' or 'api_token'

## Optional Authentication

Use `@api_token_optional` when you want to identify users if authenticated but don't require it:

```python
@api_bp.route('/public-endpoint')
@api_token_optional
async def public_endpoint():
    if hasattr(request, 'user_email'):
        # User is authenticated
        return jsonify({"message": f"Hello {request.user_email}"})
    else:
        # Anonymous user
        return jsonify({"message": "Hello anonymous"})
```

## Error Handling

When authentication fails:
- **API endpoints** (or requests with `Accept: application/json`): Returns 401 JSON error
- **Web pages**: Redirects to login page

Example error response:
```json
{
  "success": false,
  "error": "Authentication required",
  "auth_methods": ["session", "api_token"],
  "login_url": "https://your-domain.com/auth/login"
}
```

## Implementation Notes

1. The auth system checks authentication in this order:
   - Session cookie (for web users)
   - Authorization header (Bearer token)
   - X-API-Token header
   - JSON body api_token field (POST only)

2. API tokens are validated against the User model's `api_token` field

3. Last login time is automatically updated when using API tokens

4. Failed authentication returns appropriate error messages without revealing whether a token exists

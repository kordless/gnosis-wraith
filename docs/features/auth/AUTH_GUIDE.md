# Gnosis Wraith Authentication Guide

## Overview

Gnosis Wraith supports two authentication methods:
1. **Session-based authentication** - For web interface users
2. **API token authentication** - For programmatic access

Both methods work with all API endpoints (v1 and v2).

## Session Authentication

Session authentication is automatically handled when you log in through the web interface:

1. Navigate to `/auth/login`
2. Enter your email address
3. Check your email for the login token
4. Enter the token on the verification page
5. You're now authenticated with a session cookie

Session authentication is best for:
- Browser-based access
- Interactive usage
- Web interface features

## API Token Authentication

API tokens allow programmatic access to all API endpoints without needing to manage sessions.

### Obtaining an API Token

#### Via Web Interface:
1. Log in to the web interface
2. Navigate to your profile settings
3. Click "Generate API Token" or "Reset Token"
4. Copy and securely store your token

#### Via API (requires session auth):
```bash
curl -X POST https://your-domain.com/auth/api/token/generate \
     -H "Cookie: session=YOUR_SESSION_COOKIE"
```

### Using API Tokens

You can provide your API token in three ways:

#### 1. Authorization Header (Recommended)
```bash
curl -X POST https://your-domain.com/api/v2/md \
     -H "Authorization: Bearer YOUR_API_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com"}'
```

#### 2. X-API-Token Header
```bash
curl -X POST https://your-domain.com/api/v2/md \
     -H "X-API-Token: YOUR_API_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com"}'
```

#### 3. Request Body (POST requests only)
```bash
curl -X POST https://your-domain.com/api/v2/md \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://example.com",
       "api_token": "YOUR_API_TOKEN"
     }'
```

### Python Example

```python
import requests

# Using Authorization header
headers = {
    "Authorization": "Bearer YOUR_API_TOKEN",
    "Content-Type": "application/json"
}

response = requests.post(
    "https://your-domain.com/api/v2/md",
    headers=headers,
    json={"url": "https://example.com"}
)

print(response.json())
```

### JavaScript Example

```javascript
// Using fetch with Authorization header
const response = await fetch('https://your-domain.com/api/v2/md', {
    method: 'POST',
    headers: {
        'Authorization': 'Bearer YOUR_API_TOKEN',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        url: 'https://example.com'
    })
});

const data = await response.json();
console.log(data);
```

## API Token Management

### Get Token Information
Check details about the current token:

```bash
curl -X GET https://your-domain.com/auth/api/token/info \
     -H "Authorization: Bearer YOUR_API_TOKEN"
```

Response:
```json
{
  "success": true,
  "user": {
    "email": "user@example.com",
    "name": "John Doe",
    "account_type": "free",
    "active": true,
    "crawl_count": 42,
    "created": "2025-01-01T00:00:00",
    "last_login": "2025-01-10T12:34:56"
  },
  "auth_method": "api_token"
}
```

### Reset Token
Generate a new token (invalidates the old one):

```bash
curl -X POST https://your-domain.com/auth/token_reset \
     -H "Authorization: Bearer YOUR_API_TOKEN"
```

Response:
```json
{
  "status": "Token reset successfully.",
  "new_token": "YOUR_NEW_API_TOKEN"
}
```

## Security Best Practices

1. **Keep tokens secure**: Treat API tokens like passwords
2. **Use HTTPS**: Always use encrypted connections
3. **Rotate tokens**: Periodically generate new tokens
4. **Limit scope**: Use session auth for sensitive operations
5. **Monitor usage**: Check your token info regularly

## Error Handling

### Authentication Failed
```json
{
  "success": false,
  "error": "Authentication required",
  "auth_methods": ["session", "api_token"],
  "login_url": "https://your-domain.com/auth/login"
}
```

### Invalid Token
```json
{
  "success": false,
  "error": "Invalid or expired token"
}
```

### Inactive Account
```json
{
  "success": false,
  "error": "Account is inactive"
}
```

## Rate Limiting

API token requests may be subject to rate limiting:
- Default: 1000 requests per hour per token
- Configurable per account type
- 429 status code when limit exceeded

## Browser Extension

The browser extension can use API tokens:

1. Open extension settings
2. Enter your API token
3. The extension will include it in all requests

## Troubleshooting

### Token Not Working
1. Check token hasn't been reset
2. Verify correct header format
3. Ensure account is active
4. Try regenerating token

### Session Expired
1. Log in again via web interface
2. Or switch to API token auth

### Mixed Authentication
- Don't send both session cookies and API tokens
- API token takes precedence if both present

## Migration from Session-Only

If upgrading from session-only auth:

1. Log in via web interface
2. Generate API token
3. Update your scripts/apps
4. Test thoroughly
5. Keep session auth as backup

## Example Use Cases

### Automated Crawling Script
```python
import requests
import time

API_TOKEN = "YOUR_API_TOKEN"
BASE_URL = "https://your-domain.com"

urls_to_crawl = [
    "https://example1.com",
    "https://example2.com",
    "https://example3.com"
]

for url in urls_to_crawl:
    response = requests.post(
        f"{BASE_URL}/api/v2/md",
        headers={"Authorization": f"Bearer {API_TOKEN}"},
        json={"url": url}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"Crawled {url}: {data['stats']['word_count']} words")
    else:
        print(f"Failed to crawl {url}: {response.status_code}")
    
    time.sleep(1)  # Be nice to the server
```

### CI/CD Integration
```yaml
# GitHub Actions example
steps:
  - name: Crawl documentation
    env:
      WRAITH_API_TOKEN: ${{ secrets.WRAITH_API_TOKEN }}
    run: |
      curl -X POST https://your-domain.com/api/v2/pdf \
        -H "Authorization: Bearer $WRAITH_API_TOKEN" \
        -d '{"url": "https://docs.example.com"}' \
        --output docs.pdf
```

This authentication system provides flexibility for both interactive users and automated systems while maintaining security.

# API Token Backend Implementation for Claude Code

The UI is now ready for API token management. We need these backend endpoints in `web/routes/auth.py`:

## 1. Check Existing Token
```python
@auth.route('/token/check', methods=['GET'])
@login_required
async def check_token():
    """Check if user has an API token"""
    user = get_current_user()  # Get from session
    
    if user.api_token:
        # Return preview (first 8 chars) for security
        return {
            'has_token': True,
            'token_preview': user.api_token[:8] + '...' if len(user.api_token) > 8 else user.api_token
        }
    return {'has_token': False}
```

## 2. Generate/Regenerate Token
```python
@auth.route('/token/regenerate', methods=['POST'])
@login_required
async def regenerate_token():
    """Generate new API token for user"""
    user = get_current_user()  # Get from session
    
    # Generate secure random token
    import secrets
    new_token = 'wraith_' + secrets.token_urlsafe(32)
    
    # Update user model
    user.api_token = new_token
    user.put()  # Save to NDB
    
    return {'token': new_token}
```

## Current UI Implementation:
- ProfileSettingsModal now has full token management UI
- Shows/hides token with blur effect
- Generate button for new users
- Regenerate with confirmation for existing tokens
- Copy to clipboard functionality
- Usage instructions shown

## Token Validation:
The existing `api_token_optional` decorator should check:
1. `Authorization: Bearer TOKEN` header
2. Validate against user.api_token field
3. Set request context with authenticated user

Please implement these endpoints so the UI can work properly!
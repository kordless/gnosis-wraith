# Updated Authentication Module for Multi-Token Support

## Key Changes Needed

### 1. Update auth.py login_required decorator

```python
def login_required(func):
    """Decorator to require authentication via session or API token"""
    from functools import wraps
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # First check session authentication
        if 'user_uid' in session:
            request.user_email = session.get('user_email')
            return await func(*args, **kwargs)
        
        # Check for API token authentication
        auth_header = request.headers.get('Authorization')
        api_token = None
        
        # Extract token from various sources
        if auth_header and auth_header.startswith('Bearer '):
            api_token = auth_header.split(' ', 1)[1]
        
        if not api_token:
            api_token = request.headers.get('X-API-Token')
        
        if not api_token and request.method == 'POST':
            try:
                data = await request.get_json(force=True, silent=True)
                if data and isinstance(data, dict):
                    api_token = data.get('api_token')
            except:
                pass
        
        # Validate token - try new system first
        if api_token:
            # Import here to avoid circular imports
            from core.models.api_token import ApiToken
            from core.models.user import User
            
            # Try new token system
            token_obj = ApiToken.get_by_token(api_token)
            if token_obj and token_obj.is_valid():
                # Record usage
                ip = request.headers.get('X-Forwarded-For', request.remote_addr)
                ua = request.headers.get('User-Agent', '')
                token_obj.record_usage(ip_address=ip, user_agent=ua)
                
                # Get user
                user = User.get_by_email(token_obj.user_email)
                if user and user.active:
                    request.user_email = user.email
                    request.user_uid = user.uid
                    request.auth_method = 'api_token_v2'
                    request.token_scopes = json.loads(token_obj.scopes or '[]')
                    return await func(*args, **kwargs)
            
            # Fall back to legacy single token system
            user = User.get_by_api_token(api_token)
            if user and user.active:
                request.user_email = user.email
                request.user_uid = user.uid
                request.auth_method = 'api_token_legacy'
                request.token_scopes = ['all']  # Legacy tokens have full access
                
                # Update last activity
                user.last_login = datetime.datetime.utcnow()
                user.put()
                
                return await func(*args, **kwargs)
        
        # No valid authentication found
        if request.path.startswith('/api/') or request.headers.get('Accept') == 'application/json':
            return jsonify({
                "success": False,
                "error": "Authentication required",
                "auth_methods": ["session", "api_token"],
                "login_url": url_for('auth.login', _external=True)
            }), 401
        else:
            await flash("Please log in to access this page.")
            return redirect(url_for('auth.login', next=request.url))
    
    return wrapper
```

### 2. New Token Management Endpoints

```python
# In auth.py, add these new endpoints:

@auth.route('/api/tokens', methods=['GET'])
@login_required
async def list_api_tokens():
    """List all API tokens for current user"""
    from core.models.api_token import ApiToken
    
    user = await get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    tokens = ApiToken.get_user_tokens(user.email)
    
    return jsonify({
        'success': True,
        'tokens': [t.to_safe_dict() for t in tokens],
        'count': len(tokens)
    })


@auth.route('/api/tokens', methods=['POST'])
@login_required
async def create_api_token():
    """Create a new API token"""
    from core.models.api_token import ApiToken
    
    # Must be session authenticated to create tokens
    if hasattr(request, 'auth_method') and 'api_token' in request.auth_method:
        return jsonify({
            'success': False,
            'error': 'Cannot create tokens using API token authentication. Please log in via web interface.'
        }), 403
    
    user = await get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = await request.get_json()
    
    # Validate input
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Token name is required'}), 400
    
    # Create token
    try:
        token_info = ApiToken.create_for_user(
            user_email=user.email,
            name=name,
            description=data.get('description'),
            expires_days=data.get('expires_days', 365),
            scopes=data.get('scopes', ['read', 'write'])
        )
        
        return jsonify({
            'success': True,
            **token_info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth.route('/api/tokens/<token_id>', methods=['DELETE'])
@login_required
async def revoke_api_token(token_id):
    """Revoke a specific API token"""
    from core.models.api_token import ApiToken
    
    user = await get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    token = ApiToken.get_by_id(token_id)
    
    if not token:
        return jsonify({'error': 'Token not found'}), 404
    
    if token.user_email != user.email:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Revoke the token
    token.revoke()
    
    return jsonify({
        'success': True,
        'message': 'Token revoked successfully'
    })


@auth.route('/api/tokens/<token_id>', methods=['GET'])
@login_required
async def get_api_token_details(token_id):
    """Get details about a specific token"""
    from core.models.api_token import ApiToken
    
    user = await get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    token = ApiToken.get_by_id(token_id)
    
    if not token:
        return jsonify({'error': 'Token not found'}), 404
    
    if token.user_email != user.email:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({
        'success': True,
        'token': token.to_safe_dict()
    })


# Migration endpoint for existing users
@auth.route('/api/tokens/migrate', methods=['POST'])
@login_required
async def migrate_to_multi_token():
    """Migrate legacy single token to new system"""
    from core.models.api_token import ApiToken
    
    user = await get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Check if user has legacy token
    if not user.api_token:
        return jsonify({
            'success': False,
            'error': 'No legacy token to migrate'
        }), 400
    
    # Check if already migrated
    existing_tokens = ApiToken.get_user_tokens(user.email)
    if any(t.name == "Legacy Token (Migrated)" for t in existing_tokens):
        return jsonify({
            'success': False,
            'error': 'Legacy token already migrated'
        }), 400
    
    # Create new token entry for legacy token
    # Note: We can't show the actual token since we only have it stored
    token_obj = ApiToken()
    token_obj.token_id = random_string(17)
    token_obj.token_hash = ApiToken._hash_token(user.api_token)
    token_obj.user_email = user.email
    token_obj.name = "Legacy Token (Migrated)"
    token_obj.description = "Automatically migrated from single-token system"
    token_obj.created = user.created or datetime.datetime.utcnow()
    token_obj.scopes = json.dumps(["all"])  # Full access for legacy
    token_obj.active = True
    token_obj.put()
    
    # Update token index
    ApiToken._update_token_index(user.api_token, user.email)
    
    return jsonify({
        'success': True,
        'message': 'Legacy token migrated successfully',
        'token_id': token_obj.token_id
    })
```

### 3. Scope-based Authorization Decorator

```python
def require_scope(required_scope):
    """Decorator to require specific token scope"""
    def decorator(func):
        from functools import wraps
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Check if user is authenticated
            if not hasattr(request, 'user_email'):
                return jsonify({'error': 'Authentication required'}), 401
            
            # Session auth has all scopes
            if not hasattr(request, 'auth_method') or request.auth_method == 'session':
                return await func(*args, **kwargs)
            
            # Check token scopes
            scopes = getattr(request, 'token_scopes', [])
            if required_scope not in scopes and 'all' not in scopes:
                return jsonify({
                    'error': 'Insufficient permissions',
                    'required_scope': required_scope,
                    'token_scopes': scopes
                }), 403
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# Example usage:
@auth.route('/api/admin/users')
@login_required
@require_scope('admin')
async def admin_list_users():
    """Admin endpoint that requires 'admin' scope"""
    # ... implementation
```

### 4. Update User Model Methods

Add these methods to the User model:

```python
def get_all_tokens(self):
    """Get all tokens for this user (both legacy and new)"""
    from core.models.api_token import ApiToken
    
    tokens = []
    
    # Add legacy token if exists
    if self.api_token:
        tokens.append({
            'token_id': 'legacy',
            'name': 'Legacy API Token',
            'type': 'legacy',
            'active': True,
            'created': self.created.isoformat() if self.created else None
        })
    
    # Add new tokens
    new_tokens = ApiToken.get_user_tokens(self.email)
    for token in new_tokens:
        token_dict = token.to_safe_dict()
        token_dict['type'] = 'v2'
        tokens.append(token_dict)
    
    return tokens

def revoke_all_tokens(self):
    """Revoke all tokens for this user"""
    from core.models.api_token import ApiToken
    
    # Clear legacy token
    if self.api_token:
        self.api_token = None
        self.put()
    
    # Revoke all new tokens
    tokens = ApiToken.get_user_tokens(self.email)
    for token in tokens:
        token.revoke()
```

## Testing the Implementation

```python
# Test script
async def test_multi_token():
    from core.models.user import User
    from core.models.api_token import ApiToken
    
    # Create test user
    user = User.create("test@example.com")
    
    # Create multiple tokens
    token1 = ApiToken.create_for_user(
        user.email,
        name="Production API",
        description="For production app",
        scopes=["read", "write"]
    )
    
    token2 = ApiToken.create_for_user(
        user.email,
        name="Development API",
        description="For local development",
        expires_days=30,
        scopes=["read"]
    )
    
    token3 = ApiToken.create_for_user(
        user.email,
        name="CI/CD Pipeline",
        description="For automated testing",
        expires_days=7,
        scopes=["read", "write", "admin"]
    )
    
    print(f"Created tokens:")
    print(f"1. {token1['name']}: {token1['token'][:10]}...")
    print(f"2. {token2['name']}: {token2['token'][:10]}...")
    print(f"3. {token3['name']}: {token3['token'][:10]}...")
    
    # Test token lookup
    found_token = ApiToken.get_by_token(token1['token'])
    assert found_token is not None
    assert found_token.name == "Production API"
    
    # Test token usage
    found_token.record_usage("192.168.1.1", "Mozilla/5.0")
    assert found_token.usage_count == 1
    
    # List all tokens
    all_tokens = ApiToken.get_user_tokens(user.email)
    assert len(all_tokens) == 3
    
    # Revoke a token
    all_tokens[0].revoke()
    assert not all_tokens[0].is_valid()
    
    print("All tests passed!")
```
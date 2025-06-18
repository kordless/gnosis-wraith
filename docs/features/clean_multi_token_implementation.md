# Clean Multi-Token Authentication Implementation

## Updated login_required decorator

```python
def login_required(func):
    """Decorator to require authentication via session or API token"""
    from functools import wraps
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # First check session authentication
        if 'user_uid' in session:
            request.user_email = session.get('user_email')
            request.auth_method = 'session'
            request.token_scopes = ['all']  # Session has full access
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
        
        # Validate token using new system
        if api_token:
            from core.models.api_token import ApiToken
            from core.models.user import User
            
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
                    request.auth_method = 'api_token'
                    request.token_scopes = json.loads(token_obj.scopes or '[]')
                    request.token_id = token_obj.token_id
                    return await func(*args, **kwargs)
        
        # No valid authentication found
        if request.path.startswith('/api/') or request.headers.get('Accept') == 'application/json':
            return jsonify({
                "success": False,
                "error": "Authentication required",
                "auth_methods": ["session", "api_token"]
            }), 401
        else:
            await flash("Please log in to access this page.")
            return redirect(url_for('auth.login', next=request.url))
    
    return wrapper
```

## New Token Management Endpoints

```python
@auth.route('/api/tokens', methods=['GET'])
@login_required
async def list_api_tokens():
    """List all API tokens for current user"""
    from core.models.api_token import ApiToken
    
    user = await get_current_user()
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
    if request.auth_method == 'api_token':
        return jsonify({
            'success': False,
            'error': 'Cannot create tokens using API token authentication. Please log in via web.'
        }), 403
    
    user = await get_current_user()
    data = await request.get_json()
    
    # Validate input
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Token name is required'}), 400
    
    # Create token
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


@auth.route('/api/tokens/<token_id>', methods=['DELETE'])
@login_required
async def revoke_api_token(token_id):
    """Revoke a specific API token"""
    from core.models.api_token import ApiToken
    
    user = await get_current_user()
    token = ApiToken.get_by_id(token_id)
    
    if not token:
        return jsonify({'error': 'Token not found'}), 404
    
    if token.user_email != user.email:
        return jsonify({'error': 'Unauthorized'}), 403
    
    token.revoke()
    
    return jsonify({
        'success': True,
        'message': 'Token revoked successfully'
    })


# Remove all old token endpoints
# DELETE: /auth/token/regenerate
# DELETE: /auth/token/check
# DELETE: /auth/token_reset
# DELETE: /auth/api/token/generate
```

## Scope-based Authorization

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
            if request.auth_method == 'session':
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
```

## Updated UI Component

```javascript
class ApiTokenManager extends React.Component {
    state = {
        tokens: [],
        showCreateForm: false,
        newToken: {
            name: '',
            description: '',
            expires_days: 365,
            scopes: ['read', 'write']
        },
        createdToken: null,
        loading: false
    }
    
    componentDidMount() {
        this.loadTokens();
    }
    
    async loadTokens() {
        this.setState({ loading: true });
        try {
            const response = await fetch('/api/tokens');
            const data = await response.json();
            this.setState({ tokens: data.tokens });
        } catch (error) {
            console.error('Failed to load tokens:', error);
        } finally {
            this.setState({ loading: false });
        }
    }
    
    async createToken() {
        const { newToken } = this.state;
        
        try {
            const response = await fetch('/api/tokens', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newToken)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.setState({ 
                    createdToken: result.token,
                    showCreateForm: false,
                    newToken: {
                        name: '',
                        description: '',
                        expires_days: 365,
                        scopes: ['read', 'write']
                    }
                });
                this.loadTokens();
            }
        } catch (error) {
            console.error('Failed to create token:', error);
        }
    }
    
    async revokeToken(tokenId) {
        if (!confirm('Are you sure you want to revoke this token?')) return;
        
        try {
            const response = await fetch(`/api/tokens/${tokenId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                this.loadTokens();
            }
        } catch (error) {
            console.error('Failed to revoke token:', error);
        }
    }
    
    render() {
        const { tokens, showCreateForm, newToken, createdToken, loading } = this.state;
        
        return (
            <div className="api-token-manager">
                <div className="header">
                    <h3>API Tokens</h3>
                    <button 
                        onClick={() => this.setState({ showCreateForm: true })}
                        className="btn-primary"
                    >
                        Create New Token
                    </button>
                </div>
                
                {/* Show created token once */}
                {createdToken && (
                    <div className="alert alert-success">
                        <h4>Token Created Successfully!</h4>
                        <p>Copy this token now - you won't see it again:</p>
                        <code className="token-display">{createdToken}</code>
                        <button 
                            onClick={() => {
                                navigator.clipboard.writeText(createdToken);
                                this.setState({ createdToken: null });
                            }}
                        >
                            Copy & Close
                        </button>
                    </div>
                )}
                
                {/* Create form */}
                {showCreateForm && (
                    <div className="create-form">
                        <input
                            type="text"
                            placeholder="Token name (e.g., Production API)"
                            value={newToken.name}
                            onChange={e => this.setState({
                                newToken: { ...newToken, name: e.target.value }
                            })}
                        />
                        <textarea
                            placeholder="Description (optional)"
                            value={newToken.description}
                            onChange={e => this.setState({
                                newToken: { ...newToken, description: e.target.value }
                            })}
                        />
                        <select
                            value={newToken.expires_days}
                            onChange={e => this.setState({
                                newToken: { ...newToken, expires_days: parseInt(e.target.value) }
                            })}
                        >
                            <option value="7">Expires in 7 days</option>
                            <option value="30">Expires in 30 days</option>
                            <option value="90">Expires in 90 days</option>
                            <option value="365">Expires in 1 year</option>
                            <option value="0">Never expires</option>
                        </select>
                        <div className="scopes">
                            <label>
                                <input
                                    type="checkbox"
                                    checked={newToken.scopes.includes('read')}
                                    onChange={e => {
                                        const scopes = e.target.checked 
                                            ? [...newToken.scopes, 'read']
                                            : newToken.scopes.filter(s => s !== 'read');
                                        this.setState({ newToken: { ...newToken, scopes } });
                                    }}
                                />
                                Read Access
                            </label>
                            <label>
                                <input
                                    type="checkbox"
                                    checked={newToken.scopes.includes('write')}
                                    onChange={e => {
                                        const scopes = e.target.checked 
                                            ? [...newToken.scopes, 'write']
                                            : newToken.scopes.filter(s => s !== 'write');
                                        this.setState({ newToken: { ...newToken, scopes } });
                                    }}
                                />
                                Write Access
                            </label>
                        </div>
                        <div className="form-actions">
                            <button onClick={() => this.createToken()}>Create</button>
                            <button onClick={() => this.setState({ showCreateForm: false })}>
                                Cancel
                            </button>
                        </div>
                    </div>
                )}
                
                {/* Token list */}
                <div className="token-list">
                    {loading ? (
                        <p>Loading...</p>
                    ) : tokens.length === 0 ? (
                        <p>No API tokens yet. Create one to get started.</p>
                    ) : (
                        tokens.map(token => (
                            <div key={token.token_id} className="token-item">
                                <div className="token-info">
                                    <h4>{token.name}</h4>
                                    {token.description && <p>{token.description}</p>}
                                    <div className="token-meta">
                                        <span>Created: {new Date(token.created).toLocaleDateString()}</span>
                                        <span>Last used: {token.last_used ? new Date(token.last_used).toLocaleDateString() : 'Never'}</span>
                                        <span>Uses: {token.usage_count}</span>
                                        {token.expires && <span>Expires: {new Date(token.expires).toLocaleDateString()}</span>}
                                    </div>
                                    <div className="token-scopes">
                                        {token.scopes.map(scope => (
                                            <span key={scope} className="scope-badge">{scope}</span>
                                        ))}
                                    </div>
                                </div>
                                <button 
                                    className="btn-danger"
                                    onClick={() => this.revokeToken(token.token_id)}
                                >
                                    Revoke
                                </button>
                            </div>
                        ))
                    )}
                </div>
            </div>
        );
    }
}
```

## Database Migration Script

```python
# migration/migrate_to_multi_token.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models.user import User
from core.models.api_token import ApiToken

def migrate_users():
    """Remove api_token field from all users"""
    all_users = User._load_all()
    
    for email, user_data in all_users.items():
        if 'api_token' in user_data:
            del user_data['api_token']
            print(f"Removed api_token from {email}")
    
    User._save_all(all_users)
    print(f"Migration complete. Updated {len(all_users)} users.")

if __name__ == "__main__":
    migrate_users()
```
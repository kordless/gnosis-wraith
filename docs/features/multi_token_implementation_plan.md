# Multiple API Tokens Implementation Plan

## Current State Analysis

### Current Token System
1. **Single Token Storage**: Each user has one `api_token` field (StringProperty)
2. **Token Generation**: Uses `generate_token()` which creates a 30-character URL-safe token
3. **Token Lookup**: `User.get_by_api_token()` searches through all users linearly in JSON storage
4. **Token Authentication**: Checks Bearer token in headers or X-API-Token

### Storage Architecture
- Local JSON storage in `storage/models/User.json`
- Each user is stored with email as the key
- No relational capabilities for one-to-many relationships

## Implementation Plan for Multiple Tokens

### Option 1: Embedded Token List (Quick Implementation)
Store tokens as a JSON array within the user record.

```python
class User(BaseModel):
    # Change from single token to list
    api_tokens = StringProperty(default="[]")  # JSON string of token objects
    
    def add_api_token(self, name=None, expires_days=None):
        """Add a new API token"""
        tokens = json.loads(self.api_tokens or "[]")
        new_token = {
            'token': generate_token(),
            'name': name or f"Token {len(tokens) + 1}",
            'created': datetime.utcnow().isoformat(),
            'last_used': None,
            'expires': (datetime.utcnow() + timedelta(days=expires_days)).isoformat() if expires_days else None,
            'active': True
        }
        tokens.append(new_token)
        self.api_tokens = json.dumps(tokens)
        self.put()
        return new_token
```

**Pros:**
- Minimal changes to existing structure
- Works with current JSON storage
- Easy to implement

**Cons:**
- Token lookup becomes O(n*m) where n=users, m=tokens
- Limited to JSON string size limits
- No efficient indexing

### Option 2: Separate Token Model (Recommended)
Create a new `ApiToken` model with proper relationships.

```python
class ApiToken(BaseModel):
    """API Token model for multi-token support"""
    
    # Token identification
    token_id = StringProperty()  # Unique ID
    token = StringProperty()     # The actual token
    user_email = StringProperty()  # Foreign key to User
    
    # Token metadata
    name = StringProperty()
    description = StringProperty()
    
    # Permissions/Scopes
    scopes = StringProperty(default="[]")  # JSON array of permissions
    
    # Lifecycle
    created = DateTimeProperty()
    expires = DateTimeProperty()
    last_used = DateTimeProperty()
    active = BooleanProperty(default=True)
    
    # Usage tracking
    usage_count = IntegerProperty(default=0)
    
    @classmethod
    def create_for_user(cls, user_email, name=None, expires_days=None, scopes=None):
        """Create a new token for a user"""
        token = cls()
        token.token_id = random_string(17)
        token.token = generate_token(40)  # Longer for uniqueness
        token.user_email = user_email
        token.name = name or f"API Token {datetime.utcnow().strftime('%Y%m%d')}"
        token.created = datetime.utcnow()
        if expires_days:
            token.expires = datetime.utcnow() + timedelta(days=expires_days)
        token.scopes = json.dumps(scopes or ["read", "write"])
        token.put()
        return token
```

### Option 3: Hybrid Approach (Best for Migration)
Keep backward compatibility while adding new system.

```python
class User(BaseModel):
    # Keep existing for backward compatibility
    api_token = StringProperty()  # Legacy single token
    
    # Add reference to active tokens
    active_token_count = IntegerProperty(default=0)
    
    def get_tokens(self):
        """Get all tokens for this user"""
        return ApiToken.query().filter(('user_email', '==', self.email)).fetch()
    
    def migrate_to_multi_token(self):
        """Migrate existing single token to new system"""
        if self.api_token and self.active_token_count == 0:
            ApiToken.create_for_user(
                self.email, 
                name="Legacy Token (Migrated)",
                scopes=["all"]  # Full access for legacy tokens
            )
            self.active_token_count = 1
            self.put()
```

## Implementation Steps

### Phase 1: Database Schema Changes
1. Create `ApiToken` model class
2. Update storage to handle new model
3. Create migration script for existing tokens

### Phase 2: Authentication Updates
```python
def get_user_from_token(token_string):
    """Updated authentication to check both systems"""
    # First try new token system
    token = ApiToken.get_by_token(token_string)
    if token and token.active:
        # Update usage
        token.last_used = datetime.utcnow()
        token.usage_count += 1
        token.put()
        return User.get_by_email(token.user_email)
    
    # Fall back to legacy system
    return User.get_by_api_token(token_string)
```

### Phase 3: API Endpoints
```python
# Token management endpoints
@auth.route('/api/tokens', methods=['GET'])
@login_required
async def list_tokens():
    """List all tokens for current user"""
    user = await get_current_user()
    tokens = ApiToken.query().filter(('user_email', '==', user.email)).fetch()
    return jsonify({
        'tokens': [t.to_safe_dict() for t in tokens]
    })

@auth.route('/api/tokens', methods=['POST'])
@login_required
async def create_token():
    """Create a new API token"""
    data = await request.get_json()
    user = await get_current_user()
    
    token = ApiToken.create_for_user(
        user.email,
        name=data.get('name'),
        expires_days=data.get('expires_days', 365),
        scopes=data.get('scopes', ['read', 'write'])
    )
    
    return jsonify({
        'token': token.token,  # Only shown once!
        'token_id': token.token_id,
        'name': token.name,
        'expires': token.expires.isoformat() if token.expires else None
    })

@auth.route('/api/tokens/<token_id>', methods=['DELETE'])
@login_required
async def revoke_token(token_id):
    """Revoke a specific token"""
    user = await get_current_user()
    token = ApiToken.get_by_id(token_id)
    
    if token and token.user_email == user.email:
        token.active = False
        token.put()
        return jsonify({'success': True})
    
    return jsonify({'error': 'Token not found'}), 404
```

### Phase 4: UI Updates
```javascript
// Token management component
class TokenManager extends React.Component {
    state = {
        tokens: [],
        showCreateForm: false,
        newTokenName: '',
        newTokenExpires: 365,
        createdToken: null
    }
    
    async loadTokens() {
        const response = await fetch('/api/tokens');
        const data = await response.json();
        this.setState({ tokens: data.tokens });
    }
    
    async createToken() {
        const response = await fetch('/api/tokens', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: this.state.newTokenName,
                expires_days: this.state.newTokenExpires
            })
        });
        
        const token = await response.json();
        this.setState({ 
            createdToken: token.token,
            showCreateForm: false 
        });
        this.loadTokens();
    }
    
    render() {
        return (
            <div className="token-manager">
                <h3>API Tokens</h3>
                
                {/* Token list */}
                <div className="token-list">
                    {this.state.tokens.map(token => (
                        <div key={token.token_id} className="token-item">
                            <span>{token.name}</span>
                            <span>Last used: {token.last_used || 'Never'}</span>
                            <button onClick={() => this.revokeToken(token.token_id)}>
                                Revoke
                            </button>
                        </div>
                    ))}
                </div>
                
                {/* Create token form */}
                {this.state.showCreateForm && (
                    <div className="create-token-form">
                        <input 
                            placeholder="Token name"
                            value={this.state.newTokenName}
                            onChange={e => this.setState({newTokenName: e.target.value})}
                        />
                        <button onClick={() => this.createToken()}>
                            Create Token
                        </button>
                    </div>
                )}
            </div>
        );
    }
}
```

## Security Considerations

1. **Token Storage**: Never store tokens in plain text after creation
2. **Token Display**: Only show full token once during creation
3. **Token Rotation**: Implement automatic expiration and rotation
4. **Scoping**: Implement permission scopes for fine-grained access control
5. **Audit Trail**: Log all token usage for security monitoring

## Migration Strategy

1. **Phase 1**: Deploy new code with backward compatibility
2. **Phase 2**: Migrate existing tokens to new system
3. **Phase 3**: Update all clients to use new token format
4. **Phase 4**: Deprecate old single-token system

## Performance Optimizations

1. **Token Index**: Create separate index file for fast token lookups
```python
# storage/models/TokenIndex.json
{
    "token_hash": "user_email",
    "abc123...": "user@example.com",
    "def456...": "user@example.com"
}
```

2. **Caching**: Cache token validations in memory with TTL
3. **Batch Operations**: Support bulk token operations

## Timeline Estimate

- **Week 1**: Implement ApiToken model and storage
- **Week 2**: Update authentication system
- **Week 3**: Create API endpoints
- **Week 4**: Build UI components
- **Week 5**: Testing and migration scripts
- **Week 6**: Deployment and monitoring

## Benefits

1. **Better Security**: Tokens can be scoped and rotated independently
2. **Improved UX**: Users can manage multiple integrations
3. **Audit Trail**: Track usage per token
4. **Compliance**: Meet enterprise requirements for token management
5. **Future-Proof**: Support OAuth2-style flows later
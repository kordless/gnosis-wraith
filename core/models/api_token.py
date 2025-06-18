"""
API Token model for multi-token support in Gnosis Wraith
"""
import os
import json
import datetime
from typing import Optional, List, Dict

if os.getenv('RUNNING_IN_CLOUD', 'false').lower() != 'true':
    from .base import BaseModel, ndb_context_manager
    from .base import StringProperty, BooleanProperty, IntegerProperty, DateTimeProperty
else:
    from google.cloud import ndb
    from .base import ndb_context_manager
    
    class BaseModel(ndb.Model):
        pass
    
    StringProperty = ndb.StringProperty
    BooleanProperty = ndb.BooleanProperty
    IntegerProperty = ndb.IntegerProperty
    DateTimeProperty = ndb.DateTimeProperty

from core.lib.util import random_string, generate_token


class ApiToken(BaseModel):
    """API Token model"""
    
    # Token identification
    token_id = StringProperty()      # Unique token ID
    token_hash = StringProperty()    # SHA256 hash of the actual token
    token_display = StringProperty() # Masked version for display (e.g., gwt_abc...xyz)
    user_email = StringProperty()    # User this token belongs to
    
    # Token metadata
    name = StringProperty()          # User-friendly name
    description = StringProperty()   # Optional description
    
    # Permissions
    scopes = StringProperty(default='["read", "write"]')
    
    # Lifecycle
    created = DateTimeProperty()
    expires = DateTimeProperty()     
    last_used = DateTimeProperty()
    active = BooleanProperty(default=True)
    
    # Usage tracking
    usage_count = IntegerProperty(default=0)
    last_ip = StringProperty()       
    last_user_agent = StringProperty()
    
    @staticmethod
    def _hash_token(token: str) -> str:
        """Hash a token for secure storage"""
        import hashlib
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    def _mask_token(token: str) -> str:
        """Create a masked version of token for display"""
        if len(token) < 12:
            return token  # Too short to mask effectively
        # Show first 8 and last 4 characters
        return f"{token[:8]}...{token[-4:]}"
    
    @classmethod
    @ndb_context_manager
    def create_for_user(cls, user_email: str, name: str = None, 
                       description: str = None, expires_days: int = None,
                       scopes: List[str] = None) -> Dict[str, any]:
        """Create a new API token for a user"""
        # Generate token
        raw_token = generate_token(40)
        
        # Create token object
        token = cls()
        token.token_id = random_string(17)
        token.token_hash = cls._hash_token(raw_token)
        token.token_display = cls._mask_token(raw_token)
        token.user_email = user_email
        token.name = name or f"API Token {datetime.datetime.utcnow().strftime('%Y-%m-%d')}"
        token.description = description
        token.created = datetime.datetime.utcnow()
        
        if expires_days:
            token.expires = datetime.datetime.utcnow() + datetime.timedelta(days=expires_days)
        
        token.scopes = json.dumps(scopes or ["read", "write"])
        token.active = True
        
        # Save to datastore
        token.put()
        
        # Update token index for fast lookups
        cls._update_token_index(raw_token, user_email)
        
        return {
            'token': raw_token,
            'token_id': token.token_id,
            'name': token.name,
            'expires': token.expires.isoformat() if token.expires else None
        }
    
    @classmethod
    def _update_token_index(cls, token: str, user_email: str):
        """Update the token index for O(1) lookups"""
        index_path = os.path.join(cls._get_storage_dir(), 'TokenIndex.json')
        
        try:
            with open(index_path, 'r') as f:
                index = json.load(f)
        except:
            index = {}
        
        token_hash = cls._hash_token(token)
        index[token_hash] = user_email
        
        with open(index_path, 'w') as f:
            json.dump(index, f, indent=2)
    
    @classmethod
    @ndb_context_manager
    def get_by_token(cls, raw_token: str) -> Optional['ApiToken']:
        """Get token object by raw token string"""
        token_hash = cls._hash_token(raw_token)
        
        # Check index for user email
        index_path = os.path.join(cls._get_storage_dir(), 'TokenIndex.json')
        try:
            with open(index_path, 'r') as f:
                index = json.load(f)
            user_email = index.get(token_hash)
            if not user_email:
                return None
        except:
            return None
        
        # Find the specific token
        all_tokens = cls.query().filter(('user_email', '==', user_email)).fetch()
        for token in all_tokens:
            if token.token_hash == token_hash:
                return token
        
        return None
    
    @classmethod
    @ndb_context_manager
    def get_user_tokens(cls, user_email: str) -> List['ApiToken']:
        """Get all tokens for a user"""
        return cls.query().filter(('user_email', '==', user_email)).fetch()
    
    @classmethod
    @ndb_context_manager
    def get_by_id(cls, token_id: str) -> Optional['ApiToken']:
        """Get token by its ID"""
        return cls.query().filter(('token_id', '==', token_id)).get()
    
    def record_usage(self, ip_address: str = None, user_agent: str = None):
        """Record token usage"""
        self.last_used = datetime.datetime.utcnow()
        self.usage_count += 1
        if ip_address:
            self.last_ip = ip_address
        if user_agent:
            self.last_user_agent = user_agent
        self.put()
    
    def revoke(self):
        """Revoke this token"""
        self.active = False
        self.put()
        
        # Remove from index
        index_path = os.path.join(self._get_storage_dir(), 'TokenIndex.json')
        try:
            with open(index_path, 'r') as f:
                index = json.load(f)
            if self.token_hash in index:
                del index[self.token_hash]
                with open(index_path, 'w') as f:
                    json.dump(index, f, indent=2)
        except:
            pass
    
    def is_valid(self) -> bool:
        """Check if token is valid"""
        if not self.active:
            return False
        
        if self.expires and self.expires < datetime.datetime.utcnow():
            return False
        
        return True
    
    def has_scope(self, required_scope: str) -> bool:
        """Check if token has a specific scope"""
        scopes = json.loads(self.scopes or '[]')
        return required_scope in scopes or 'all' in scopes
    
    def to_safe_dict(self) -> dict:
        """Convert to dict without exposing sensitive data"""
        # Handle datetime fields that might be strings
        def format_datetime(dt):
            if dt is None:
                return None
            if isinstance(dt, str):
                return dt  # Already formatted
            if hasattr(dt, 'isoformat'):
                return dt.isoformat()
            return str(dt)
            
        return {
            'token_id': self.token_id,
            'name': self.name,
            'description': self.description,
            'token_display': self.token_display,  # Masked token for UI display
            'created': format_datetime(self.created),
            'expires': format_datetime(self.expires),
            'last_used': format_datetime(self.last_used),
            'active': self.active,
            'usage_count': self.usage_count,
            'scopes': json.loads(self.scopes or '[]')
        }

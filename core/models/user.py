"""
User model for Gnosis Wraith authentication system
Implements passwordless authentication with email and SMS 2FA

This is adapted from the SlothAI/MittaAI authentication system
with support for both local JSON storage and Google Cloud Datastore
"""
import os
import datetime
from typing import Optional

# Import based on environment
if os.getenv('USE_LOCAL_DATASTORE', 'true').lower() == 'true':
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

# Import utilities
from core.lib.util import random_name, random_string, generate_token


class User(BaseModel):
    """
    User model with passwordless authentication
    
    Authentication flow:
    1. User enters email
    2. System sends login link with mail_token
    3. Optional: SMS verification with phone_code
    4. User is authenticated with api_token for API access
    """
    
    # User identification
    uid = StringProperty()  # Unique user ID (17 char random)
    name = StringProperty()  # Display name (3-word random)
    email = StringProperty()  # Email address (primary identifier)
    
    # Authentication tokens
    mail_token = StringProperty()  # Email verification token
    mail_confirm = BooleanProperty(default=False)  # Email confirmed
    mail_tries = IntegerProperty(default=0)  # Email send attempts
    
    # Phone/SMS authentication
    phone = StringProperty(default="+1")  # Phone number in E.164 format
    phone_code = StringProperty()  # 6-digit SMS verification code
    failed_2fa_attempts = IntegerProperty(default=0)  # Failed 2FA attempts
    
    # Account status
    authenticated = BooleanProperty(default=False)  # Currently logged in
    active = BooleanProperty(default=True)  # Account active
    account_type = StringProperty(default="free")  # "free" or "paid"
    admin = BooleanProperty(default=False)  # Admin privileges
    
    # Timestamps
    created = DateTimeProperty()  # Account creation
    updated = DateTimeProperty()  # Last update
    expires = DateTimeProperty()  # Account expiration (for trials)
    last_login = DateTimeProperty()  # Last successful login
    last_crawl = DateTimeProperty()  # Last crawl performed
    
    # Usage tracking
    crawl_count = IntegerProperty(default=0)  # Total crawls performed
    total_storage_bytes = IntegerProperty(default=0)  # Total storage used
    
    # API tokens stored in NDB (not filesystem)
    # api_tokens = JsonProperty(default=[])  # List of {token, name, created}
    # Note: JsonProperty not available in local datastore, using StringProperty for now
    
    # Settings/preferences
    # settings = JsonProperty(default={})
    # Note: JsonProperty not available in local datastore, using StringProperty for now
    
    # Flask-Login required methods
    def is_active(self):
        return self.active
    
    def get_id(self):
        return self.uid
    
    def is_authenticated(self):
        return self.authenticated
    
    def is_anonymous(self):
        return False
    
    def has_phone(self):
        return self.phone and self.phone != "+1"
    
    @classmethod
    @ndb_context_manager
    def create(cls, email: str, phone: str = "+1") -> 'User':
        """
        Create a new user with email
        
        Args:
            email: User's email address
            phone: Optional phone number for 2FA
            
        Returns:
            User instance
        """
        # Check if user already exists
        existing = cls.get_by_email(email)
        if existing:
            return existing
        
        # Generate unique identifiers
        uid = random_string(size=17)
        name = random_name(3)  # 3-word random name
        
        # Create user instance
        user = cls()
        user.uid = uid
        user.name = name
        user.email = email
        user.phone = phone
        user.phone_code = generate_token()
        user.mail_token = generate_token()
        user.created = datetime.datetime.utcnow()
        user.updated = datetime.datetime.utcnow()
        user.expires = datetime.datetime.utcnow() + datetime.timedelta(days=30)
        user.account_type = "free"
        user.authenticated = False
        user.active = True
        user.admin = False
        user.mail_confirm = False
        user.mail_tries = 0
        user.failed_2fa_attempts = 0
        
        # Save to datastore
        user.put()
        
        return user
    
    @classmethod
    @ndb_context_manager
    def get_by_email(cls, email: str) -> Optional['User']:
        """Get user by email address"""
        if os.getenv('USE_LOCAL_DATASTORE', 'true').lower() == 'true':
            # For local storage, email is the key
            all_users = cls._load_all()
            if email in all_users:
                user = cls()
                for k, v in all_users[email].items():
                    if k in ['created', 'updated', 'expires'] and v:
                        # Convert ISO format back to datetime
                        setattr(user, k, datetime.datetime.fromisoformat(v))
                    else:
                        setattr(user, k, v)
                return user
            return None
        else:
            # Google Cloud Datastore query
            return cls.query(cls.email == email).get()
    
    @classmethod
    @ndb_context_manager
    def get_by_uid(cls, uid: str) -> Optional['User']:
        """Get user by unique ID"""
        if os.getenv('USE_LOCAL_DATASTORE', 'true').lower() == 'true':
            # For local storage, manually search through users
            all_users = cls._load_all()
            for key, user_data in all_users.items():
                if user_data.get('uid') == uid:
                    user = cls()
                    for k, v in user_data.items():
                        if k == 'created' or k == 'updated':
                            # Convert string dates back to datetime
                            try:
                                setattr(user, k, datetime.datetime.fromisoformat(v))
                            except:
                                setattr(user, k, v)
                        else:
                            setattr(user, k, v)
                    return user
            return None
        else:
            return cls.query(cls.uid == uid).get()
    
    @classmethod
    @ndb_context_manager
    def get_by_mail_token(cls, mail_token: str) -> Optional['User']:
        """Get user by email verification token"""
        if os.getenv('USE_LOCAL_DATASTORE', 'true').lower() == 'true':
            # For local storage, manually search through users
            all_users = cls._load_all()
            for key, user_data in all_users.items():
                if user_data.get('mail_token') == mail_token:
                    user = cls()
                    for k, v in user_data.items():
                        if k == 'created' or k == 'updated':
                            # Convert string dates back to datetime
                            try:
                                setattr(user, k, datetime.datetime.fromisoformat(v))
                            except:
                                setattr(user, k, v)
                        else:
                            setattr(user, k, v)
                    return user
            return None
        else:
            return cls.query(cls.mail_token == mail_token).get()
    
    
    @classmethod
    @ndb_context_manager
    def authenticate(cls, uid: str) -> Optional['User']:
        """Mark user as authenticated"""
        user = cls.get_by_uid(uid)
        if user:
            user.authenticated = True
            user.updated = datetime.datetime.utcnow()
            user.put()
        return user
    
    
    @classmethod
    @ndb_context_manager
    def rotate_mail_token(cls, uid: str) -> Optional['User']:
        """Rotate email verification token after use"""
        user = cls.get_by_uid(uid)
        if user:
            user.mail_token = generate_token()
            user.mail_confirm = True
            user.mail_tries = 0
            user.updated = datetime.datetime.utcnow()
            user.put()
        return user
    
    @classmethod
    @ndb_context_manager
    def update_phone(cls, uid: str, phone: str) -> Optional['User']:
        """Update user's phone number and generate new code"""
        user = cls.get_by_uid(uid)
        if user:
            user.phone = phone
            user.phone_code = random_string(size=6, chars='0123456789')  # 6-digit code
            user.updated = datetime.datetime.utcnow()
            user.put()
        return user
    
    @classmethod
    @ndb_context_manager
    def increment_mail_tries(cls, uid: str) -> Optional['User']:
        """Increment email send attempts"""
        user = cls.get_by_uid(uid)
        if user:
            user.mail_tries += 1
            user.updated = datetime.datetime.utcnow()
            user.put()
        return user
    
    @classmethod
    @ndb_context_manager
    def remove_by_uid(cls, uid: str) -> bool:
        """Delete user by UID"""
        user = cls.get_by_uid(uid)
        if user:
            user.delete()
            return True
        return False
    
    def get_storage_hash(self) -> str:
        """
        Get SHA256 hash of email for storage bucket naming
        Used for organizing user files in storage
        """
        import hashlib
        return hashlib.sha256(self.email.encode()).hexdigest()[:12]
    
    @classmethod
    @ndb_context_manager
    def get_or_create_anonymous(cls) -> 'User':
        """Get or create the anonymous user for unauthenticated access."""
        anon = cls.get_by_email("anonymous@system")
        if not anon:
            anon = cls()
            anon.uid = "anonymous"
            anon.name = "Anonymous User"
            anon.email = "anonymous@system"
            anon.phone = "+1"
            anon.phone_code = "000000"
            anon.mail_token = "anonymous"
            anon.created = datetime.datetime.utcnow()
            anon.updated = datetime.datetime.utcnow()
            anon.expires = datetime.datetime.utcnow() + datetime.timedelta(days=36500)  # 100 years
            anon.account_type = "free"
            anon.authenticated = False
            anon.active = True
            anon.admin = False
            anon.mail_confirm = True
            anon.mail_tries = 0
            anon.failed_2fa_attempts = 0
            anon.crawl_count = 0
            anon.total_storage_bytes = 0
            anon.put()
        return anon
    
    def __repr__(self):
        return f"<User {self.email} ({self.uid})>"


class Transaction(BaseModel):
    """
    Transaction model for anti-bot protection
    Tracks form submissions with unique IDs
    """
    uid = StringProperty()  # User ID (or "anonymous")
    tid = StringProperty()  # Transaction ID
    created = DateTimeProperty()
    
    @classmethod
    @ndb_context_manager
    def create(cls, uid: str, tid: str) -> 'Transaction':
        """
        Create a new transaction for anti-bot protection
        
        Args:
            uid: User ID or "anonymous"
            tid: Transaction ID (random string)
            
        Returns:
            Transaction instance
        """
        transaction = cls()
        transaction.uid = uid
        transaction.tid = tid
        transaction.created = datetime.datetime.utcnow()
        transaction.put()
        return transaction
    
    @classmethod
    @ndb_context_manager
    def query(cls):
        """Query all transactions"""
        if os.getenv('USE_LOCAL_DATASTORE', 'true').lower() == 'true':
            # For local storage, return a LocalQuery that can actually find transactions
            from core.models.base import LocalQuery
            return LocalQuery(cls)
        else:
            return super().query()
    
    def delete(self):
        """Delete this transaction"""
        # For local storage, this would need to be implemented
        # For now, we'll just pass
        pass


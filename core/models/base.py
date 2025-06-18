"""
Base model functionality and context managers for NDB-style models
This provides a lightweight JSON-based implementation for local development
"""
import json
import os
from pathlib import Path
from datetime import datetime
import threading

# Thread-local storage for context management
_local = threading.local()

class LocalContext:
    """Context manager for local datastore operations"""
    def __enter__(self):
        _local.in_context = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        _local.in_context = False

class LocalClient:
    """Mimics ndb.Client for local development"""
    def context(self):
        return LocalContext()

# Create a context manager decorator
def ndb_context_manager(func):
    """
    Decorator that ensures function runs within an NDB context
    For local development, this just ensures thread safety
    """
    def wrapper(*args, **kwargs):
        # Check if we're using local or real NDB
        if os.getenv('RUNNING_IN_CLOUD', 'false').lower() != 'true':
            with LocalClient().context():
                result = func(*args, **kwargs)
        else:
            # Real Google Cloud NDB
            from google.cloud import ndb
            with ndb.Client().context():
                result = func(*args, **kwargs)
        return result
    return wrapper

class LocalQuery:
    """Simple query implementation for local JSON storage"""
    def __init__(self, model_class, filters=None):
        self.model_class = model_class
        self.filters = filters or []
    
    def filter(self, *conditions):
        """Add filter conditions"""
        new_query = LocalQuery(self.model_class, self.filters[:])
        new_query.filters.extend(conditions)
        return new_query
    
    def get(self):
        """Get first matching entity"""
        results = self.fetch(limit=1)
        return results[0] if results else None
    
    def fetch(self, limit=None):
        """Fetch all matching entities"""
        # Load all entities from JSON
        storage_path = self.model_class._get_storage_path()
        if not os.path.exists(storage_path):
            return []
        
        with open(storage_path, 'r') as f:
            all_data = json.load(f)
        
        # Apply filters
        results = []
        for key, data in all_data.items():
            match = True
            for condition in self.filters:
                # Simple equality check for now
                # Format: (property, operator, value)
                if len(condition) == 3:
                    prop, op, value = condition
                    if op == '==' and data.get(prop) != value:
                        match = False
                        break
            if match:
                # Convert dict to model instance
                instance = self.model_class()
                # Set internal storage attributes for property descriptors
                for k, v in data.items():
                    if hasattr(instance.__class__, k):
                        prop = getattr(instance.__class__, k)
                        if isinstance(prop, (StringProperty, BooleanProperty, IntegerProperty, DateTimeProperty, JsonProperty)):
                            # Use the property descriptor setter
                            setattr(instance, k, v)
                        else:
                            # Regular attribute
                            setattr(instance, k, v)
                    else:
                        # Dynamic attribute not defined in class
                        setattr(instance, k, v)
                results.append(instance)
        
        if limit:
            results = results[:limit]
        
        return results

class BaseModel:
    """Base class for all local datastore models"""
    
    @classmethod
    def _get_storage_dir(cls):
        """Get storage directory for this model"""
        # Use the unified storage path from environment or default
        base_path = os.getenv('STORAGE_PATH', os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'storage'))
        model_dir = os.path.join(base_path, 'models')
        Path(model_dir).mkdir(parents=True, exist_ok=True)
        return model_dir
    
    @classmethod
    def _get_storage_path(cls):
        """Get JSON file path for this model"""
        model_dir = cls._get_storage_dir()
        return os.path.join(model_dir, f'{cls.__name__}.json')
    
    @classmethod
    def _load_all(cls):
        """Load all entities from storage"""
        storage_path = cls._get_storage_path()
        if not os.path.exists(storage_path):
            return {}
        with open(storage_path, 'r') as f:
            return json.load(f)
    
    @classmethod
    def _save_all(cls, data):
        """Save all entities to storage"""
        storage_path = cls._get_storage_path()
        with open(storage_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def put(self):
        """Save this entity to storage"""
        # Get primary key (email for User, tid for Transaction, token_id for ApiToken, or uid as fallback)
        key = getattr(self, 'email', None) or getattr(self, 'tid', None) or getattr(self, 'token_id', None) or getattr(self, 'uid', None)
        if not key:
            raise ValueError("Entity must have email, tid, token_id, or uid")
        
        # Load existing data
        all_data = self._load_all()
        
        # Convert instance to dict
        entity_data = {}
        
        # First, handle all property descriptors
        for attr_name in dir(self.__class__):
            if not attr_name.startswith('_'):
                attr = getattr(self.__class__, attr_name)
                if isinstance(attr, (StringProperty, BooleanProperty, IntegerProperty, DateTimeProperty, JsonProperty)):
                    # Get the actual value using the descriptor
                    value = getattr(self, attr_name)
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    entity_data[attr_name] = value
        
        # Then handle any additional attributes that were set dynamically
        for attr_name in dir(self):
            if not attr_name.startswith('_') and not callable(getattr(self, attr_name)):
                # Skip if already handled by property descriptor
                if attr_name not in entity_data:
                    value = getattr(self, attr_name)
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    entity_data[attr_name] = value
        
        # Save
        all_data[key] = entity_data
        self._save_all(all_data)
        
        return self
    
    @classmethod
    def query(cls, *filters):
        """Create a query for this model"""
        return LocalQuery(cls, list(filters))
    
    def to_dict(self):
        """Convert entity to dictionary"""
        result = {}
        
        # First, handle all property descriptors
        for attr_name in dir(self.__class__):
            if not attr_name.startswith('_'):
                attr = getattr(self.__class__, attr_name)
                if isinstance(attr, (StringProperty, BooleanProperty, IntegerProperty, DateTimeProperty, JsonProperty)):
                    # Get the actual value using the descriptor
                    value = getattr(self, attr_name)
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    result[attr_name] = value
        
        # Then handle any additional attributes that were set dynamically
        for attr_name in dir(self):
            if not attr_name.startswith('_') and not callable(getattr(self, attr_name)):
                # Skip if already handled by property descriptor
                if attr_name not in result:
                    value = getattr(self, attr_name)
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    result[attr_name] = value
        
        return result
    
    def delete(self):
        """Delete this entity"""
        key = getattr(self, 'email', None) or getattr(self, 'tid', None) or getattr(self, 'token_id', None) or getattr(self, 'uid', None)
        if not key:
            return False
        
        all_data = self._load_all()
        if key in all_data:
            del all_data[key]
            self._save_all(all_data)
            return True
        return False

# Property types for compatibility
class StringProperty:
    def __init__(self, default=None):
        self.default = default
        self.name = None
    
    def __set_name__(self, owner, name):
        self.name = f"_{name}"
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.name, self.default)
    
    def __set__(self, obj, value):
        # Handle corrupted data from old property object strings
        if isinstance(value, str) and '<core.models.base.' in value and 'Property object at' in value:
            value = self.default
        setattr(obj, self.name, value)

class BooleanProperty:
    def __init__(self, default=False):
        self.default = default
        self.name = None
    
    def __set_name__(self, owner, name):
        self.name = f"_{name}"
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.name, self.default)
    
    def __set__(self, obj, value):
        setattr(obj, self.name, bool(value) if value is not None else self.default)

class IntegerProperty:
    def __init__(self, default=0):
        self.default = default
        self.name = None
    
    def __set_name__(self, owner, name):
        self.name = f"_{name}"
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.name, self.default)
    
    def __set__(self, obj, value):
        # Handle corrupted data from old property object strings
        if isinstance(value, str) and '<core.models.base.' in value and 'Property object at' in value:
            value = self.default
        else:
            try:
                value = int(value) if value is not None else self.default
            except (ValueError, TypeError):
                value = self.default
        setattr(obj, self.name, value)

class DateTimeProperty:
    def __init__(self, default=None):
        self.default = default
        self.name = None
    
    def __set_name__(self, owner, name):
        self.name = f"_{name}"
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        value = getattr(obj, self.name, self.default)
        # Convert string back to datetime if needed
        if isinstance(value, str) and value:
            try:
                return datetime.fromisoformat(value)
            except:
                return value
        return value
    
    def __set__(self, obj, value):
        # Handle corrupted data from old property object strings
        if isinstance(value, str) and '<core.models.base.' in value and 'Property object at' in value:
            value = self.default
        # Store as string if datetime
        elif isinstance(value, datetime):
            value = value.isoformat()
        setattr(obj, self.name, value)

class JsonProperty:
    def __init__(self, default=None):
        self.default = default or {}
        self.name = None
    
    def __set_name__(self, owner, name):
        self.name = f"_{name}"
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        value = getattr(obj, self.name, self.default)
        # Parse JSON string if needed
        if isinstance(value, str):
            try:
                return json.loads(value)
            except:
                return value
        return value
    
    def __set__(self, obj, value):
        # Store as JSON string if dict/list
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        setattr(obj, self.name, value)

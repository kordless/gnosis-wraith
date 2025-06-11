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
        if os.getenv('USE_LOCAL_DATASTORE', 'true').lower() == 'true':
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
                for k, v in data.items():
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
        base_path = os.getenv('LOCAL_DATASTORE_PATH', './local_datastore')
        model_dir = os.path.join(base_path, cls.__name__.lower())
        Path(model_dir).mkdir(parents=True, exist_ok=True)
        return model_dir
    
    @classmethod
    def _get_storage_path(cls):
        """Get JSON file path for this model"""
        return os.path.join(cls._get_storage_dir(), 'data.json')
    
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
        # Get primary key (email for User, tid for Transaction, or uid as fallback)
        key = getattr(self, 'email', None) or getattr(self, 'tid', None) or getattr(self, 'uid', None)
        if not key:
            raise ValueError("Entity must have email, tid, or uid")
        
        # Load existing data
        all_data = self._load_all()
        
        # Convert instance to dict
        entity_data = {}
        for attr in dir(self):
            if not attr.startswith('_') and not callable(getattr(self, attr)):
                value = getattr(self, attr)
                if isinstance(value, datetime):
                    value = value.isoformat()
                entity_data[attr] = value
        
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
        for attr in dir(self):
            if not attr.startswith('_') and not callable(getattr(self, attr)):
                value = getattr(self, attr)
                if isinstance(value, datetime):
                    value = value.isoformat()
                result[attr] = value
        return result
    
    def delete(self):
        """Delete this entity"""
        key = getattr(self, 'email', None) or getattr(self, 'uid', None)
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

class BooleanProperty:
    def __init__(self, default=False):
        self.default = default

class IntegerProperty:
    def __init__(self, default=0):
        self.default = default

class DateTimeProperty:
    def __init__(self, default=None):
        self.default = default

class JsonProperty:
    def __init__(self, default=None):
        self.default = default or {}

# TODO: Implement these property types for validation and type conversion
# For now, they're just markers for documentation purposes

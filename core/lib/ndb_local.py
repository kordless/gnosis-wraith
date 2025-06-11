"""
Local NDB implementation for development
Provides a JSON-based datastore that mimics Google Cloud NDB

This allows local development without Google Cloud dependencies
while maintaining the same API interface
"""
import os
import json
from pathlib import Path
from typing import Any, List, Optional

# Re-export everything from models.base for convenience
from ..models.base import (
    BaseModel,
    LocalClient,
    LocalContext,
    LocalQuery,
    ndb_context_manager,
    StringProperty,
    BooleanProperty,
    IntegerProperty,
    DateTimeProperty,
    JsonProperty
)

# Additional query operators for compatibility
class QueryOperator:
    """Operators for query filters"""
    EQ = '=='
    NE = '!='
    LT = '<'
    LE = '<='
    GT = '>'
    GE = '>='
    IN = 'in'
    
    @staticmethod
    def evaluate(value1: Any, operator: str, value2: Any) -> bool:
        """Evaluate a query condition"""
        if operator == QueryOperator.EQ:
            return value1 == value2
        elif operator == QueryOperator.NE:
            return value1 != value2
        elif operator == QueryOperator.LT:
            return value1 < value2
        elif operator == QueryOperator.LE:
            return value1 <= value2
        elif operator == QueryOperator.GT:
            return value1 > value2
        elif operator == QueryOperator.GE:
            return value1 >= value2
        elif operator == QueryOperator.IN:
            return value1 in value2
        else:
            raise ValueError(f"Unknown operator: {operator}")


def AND(*conditions):
    """Combine multiple query conditions with AND logic"""
    return ('AND', conditions)


def OR(*conditions):
    """Combine multiple query conditions with OR logic"""
    return ('OR', conditions)


class LocalDatastore:
    """
    Main interface for local JSON-based datastore
    Manages all model storage and queries
    """
    
    def __init__(self, base_path: str = None):
        self.base_path = base_path or os.getenv('LOCAL_DATASTORE_PATH', './local_datastore')
        Path(self.base_path).mkdir(parents=True, exist_ok=True)
    
    def clear_all(self):
        """Clear all data (useful for testing)"""
        import shutil
        if os.path.exists(self.base_path):
            shutil.rmtree(self.base_path)
        Path(self.base_path).mkdir(parents=True, exist_ok=True)
    
    def export_all(self) -> dict:
        """Export all data as a dictionary"""
        result = {}
        for model_dir in os.listdir(self.base_path):
            model_path = os.path.join(self.base_path, model_dir)
            if os.path.isdir(model_path):
                data_file = os.path.join(model_path, 'data.json')
                if os.path.exists(data_file):
                    with open(data_file, 'r') as f:
                        result[model_dir] = json.load(f)
        return result
    
    def import_all(self, data: dict):
        """Import data from a dictionary"""
        for model_name, model_data in data.items():
            model_dir = os.path.join(self.base_path, model_name)
            Path(model_dir).mkdir(parents=True, exist_ok=True)
            data_file = os.path.join(model_dir, 'data.json')
            with open(data_file, 'w') as f:
                json.dump(model_data, f, indent=2)


# Global instance
_datastore = LocalDatastore()


def get_datastore() -> LocalDatastore:
    """Get the global datastore instance"""
    return _datastore


# Development utilities
def reset_datastore():
    """Reset all data in local datastore"""
    _datastore.clear_all()
    print("Local datastore cleared")


def backup_datastore(filename: str = 'datastore_backup.json'):
    """Backup all datastore data to a file"""
    data = _datastore.export_all()
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Datastore backed up to {filename}")


def restore_datastore(filename: str = 'datastore_backup.json'):
    """Restore datastore from a backup file"""
    if not os.path.exists(filename):
        print(f"Backup file {filename} not found")
        return
    
    with open(filename, 'r') as f:
        data = json.load(f)
    
    _datastore.import_all(data)
    print(f"Datastore restored from {filename}")


# Make it easy to switch between local and cloud
def is_local_mode() -> bool:
    """Check if running in local datastore mode"""
    return os.getenv('USE_LOCAL_DATASTORE', 'true').lower() == 'true'


# Example usage for testing
if __name__ == '__main__':
    # Test the local datastore
    print(f"Local datastore mode: {is_local_mode()}")
    print(f"Datastore path: {_datastore.base_path}")
    
    # You can test model operations here
    # from .user import User
    # user = User.create(email="test@example.com")
    # print(f"Created user: {user}")

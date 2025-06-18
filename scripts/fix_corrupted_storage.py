#!/usr/bin/env python3
"""
Script to fix corrupted property data in storage JSON files
"""
import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def fix_corrupted_json(file_path):
    """Fix corrupted property object strings in JSON file"""
    if not os.path.exists(file_path):
        return False
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    fixed = False
    for key, entity in data.items():
        for attr, value in list(entity.items()):
            if isinstance(value, str) and '<core.models.base.' in value and 'Property object at' in value:
                # Replace corrupted property object strings with appropriate defaults
                if 'IntegerProperty' in value:
                    entity[attr] = 0
                elif 'BooleanProperty' in value:
                    entity[attr] = False
                elif 'StringProperty' in value:
                    entity[attr] = None
                elif 'DateTimeProperty' in value:
                    entity[attr] = None
                elif 'JsonProperty' in value:
                    entity[attr] = '[]'
                fixed = True
                print(f"Fixed {file_path} - {key}.{attr}")
    
    if fixed:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Updated {file_path}")
    
    return fixed

if __name__ == '__main__':
    storage_path = os.environ.get('STORAGE_PATH', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'storage'))
    models_dir = os.path.join(storage_path, 'models')
    
    # Fix all JSON files in models directory
    for filename in os.listdir(models_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(models_dir, filename)
            fix_corrupted_json(file_path)
    
    print("Done fixing corrupted storage files")
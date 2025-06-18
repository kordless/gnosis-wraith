"""
Storage Service for Gnosis Wraith

Handles all storage operations:
- NDB models (local JSON storage / remote Google Datastore)
- File storage (screenshots, markdown reports, JSON crawl data, etc.)
- User-partitioned storage using hash bucketing

Storage Structure:
- Local Development:
    storage/
    ├── models/              # NDB model data
    │   ├── User.json
    │   └── Transaction.json
    └── users/               # User file storage
        └── {user_hash}/
            └── files...
            
- Production (Cloud):
    - NDB models go to Google Datastore (not file storage)
    - Files go to GCS bucket under users/{user_hash}/
"""

import os
import io
import json
import hashlib
import logging
import traceback
from typing import Dict, Any, Optional, Union, BinaryIO, List
from pathlib import Path
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import GCS
try:
    from google.cloud import storage
    GCS_AVAILABLE = True
except ImportError:
    logger.warning("Could not import GCS. Cloud storage will not be available.")
    GCS_AVAILABLE = False


def is_running_in_cloud():
    """Detect if running in Google Cloud environment."""
    return os.environ.get('RUNNING_IN_CLOUD', '').lower() == 'true'


def get_storage_config():
    """
    Get current storage configuration.
    
    Returns:
        dict: Configuration details including:
            - ndb_mode: 'local' or 'cloud'
            - file_storage: 'local' or 'gcs'
            - storage_path: Base storage directory
            - models_path: Path for local NDB models
            - users_path: Path for user files
    """
    is_cloud = is_running_in_cloud()
    storage_path = os.environ.get('STORAGE_PATH', 
                                  os.path.join(os.path.dirname(os.path.dirname(__file__)), 'storage'))
    
    return {
        'ndb_mode': 'cloud' if is_cloud else 'local',
        'file_storage': 'gcs' if is_cloud else 'local',
        'storage_path': storage_path,
        'models_path': os.path.join(storage_path, 'models') if not is_cloud else None,
        'users_path': os.path.join(storage_path, 'users'),
        'environment': {
            'RUNNING_IN_CLOUD': os.environ.get('RUNNING_IN_CLOUD', 'false'),
            'STORAGE_PATH': storage_path,
            'GCS_BUCKET_NAME': os.environ.get('GCS_BUCKET_NAME', 'gnosis-wraith-storage')
        }
    }



class StorageService:
    """
    Storage service that handles both NDB and file storage operations.
    """
    
    def __init__(self, user_email: Optional[str] = None):
        """Initialize the storage service based on environment."""
        self._gcs_client = None
        self._bucket_name = os.environ.get('GCS_BUCKET_NAME', 'gnosis-wraith-storage')
        self._storage_path = os.environ.get('STORAGE_PATH', 
                                            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'storage'))
        self._user_email = user_email
        self._user_hash = self._compute_user_hash(user_email)
        
        # Initialize based on environment
        if is_running_in_cloud() and GCS_AVAILABLE:
            self._init_gcs()
        else:
            # Ensure local directories exist
            self._ensure_local_dirs()
    
    def _init_gcs(self):
        """Initialize Google Cloud Storage client."""
        try:
            self._gcs_client = storage.Client()
            # Check if bucket exists
            try:
                bucket = self._gcs_client.get_bucket(self._bucket_name)
            except Exception:
                bucket = self._gcs_client.create_bucket(self._bucket_name)
                logger.info(f"Created GCS bucket: {self._bucket_name}")
            
            logger.info(f"GCS client initialized for bucket {self._bucket_name}")
        except Exception as e:
            logger.error(f"Failed to initialize GCS: {str(e)}")
            raise
    
    def _ensure_local_dirs(self):
        """Ensure all required local directories exist."""
        # Only create the base storage directory
        # User directories will be created on demand
        os.makedirs(self._storage_path, exist_ok=True)
        logger.debug(f"Ensured storage directory exists: {self._storage_path}")
    
    def _compute_user_hash(self, email: Optional[str]) -> str:
        """Compute a consistent hash for user bucketing."""
        if not email:
            # Anonymous user hash
            email = "anonymous@gnosis-wraith.local"
        
        return hashlib.sha256(email.encode()).hexdigest()[:12]
    
    def set_user_email(self, email: Optional[str]):
        """Update the user email and recompute hash."""
        self._user_email = email
        self._user_hash = self._compute_user_hash(email)
        logger.info(f"User context updated: email={email}, hash={self._user_hash}")
    
    def get_user_path(self) -> str:
        """Get the user-specific storage path."""
        return f"users/{self._user_hash}"
    
    def get_models_path(self) -> str:
        """Get the path for local NDB model storage."""
        return os.path.join(self._storage_path, "models")
    
    # File operations
    async def save_file(self, content: Union[bytes, str], filename: str) -> str:
        """
        Save a file to user-partitioned storage.
        
        Args:
            content: File content (bytes or string)
            filename: Filename to save
            
        Returns:
            Full path where file was saved
        """
        # Convert string to bytes if needed
        if isinstance(content, str):
            content = content.encode('utf-8')
        
        user_path = self.get_user_path()
        full_path = f"{user_path}/{filename}"
        
        if is_running_in_cloud() and self._gcs_client:
            # Save to GCS
            bucket = self._gcs_client.bucket(self._bucket_name)
            blob = bucket.blob(full_path)
            blob.upload_from_string(content)
            logger.info(f"Saved file to GCS: {full_path}")
            return full_path
        else:
            # Save to local storage
            local_path = os.path.join(self._storage_path, user_path)
            os.makedirs(local_path, exist_ok=True)
            
            file_path = os.path.join(local_path, filename)
            
            # Handle binary vs text mode
            mode = 'wb' if isinstance(content, bytes) else 'w'
            with open(file_path, mode) as f:
                f.write(content)
            
            logger.info(f"Saved file locally: {file_path}")
            return file_path
    
    async def get_file(self, filename: str) -> bytes:
        """
        Retrieve a file from user-partitioned storage.
        
        Args:
            filename: Filename to retrieve
            
        Returns:
            File content as bytes
        """
        user_path = self.get_user_path()
        full_path = f"{user_path}/{filename}"
        
        if is_running_in_cloud() and self._gcs_client:
            # Get from GCS
            bucket = self._gcs_client.bucket(self._bucket_name)
            blob = bucket.blob(full_path)
            
            if not blob.exists():
                raise FileNotFoundError(f"File not found: {filename}")
            
            content = blob.download_as_bytes()
            logger.info(f"Retrieved file from GCS: {full_path}")
            return content
        else:
            # Get from local storage
            file_path = os.path.join(self._storage_path, user_path, filename)
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {filename}")
            
            with open(file_path, 'rb') as f:
                content = f.read()
            
            logger.info(f"Retrieved file locally: {file_path}")
            return content
    
    async def delete_file(self, filename: str) -> bool:
        """
        Delete a file from user-partitioned storage.
        
        Args:
            filename: Filename to delete
            
        Returns:
            True if deletion was successful
        """
        user_path = self.get_user_path()
        full_path = f"{user_path}/{filename}"
        
        if is_running_in_cloud() and self._gcs_client:
            # Delete from GCS
            bucket = self._gcs_client.bucket(self._bucket_name)
            blob = bucket.blob(full_path)
            
            if blob.exists():
                blob.delete()
                logger.info(f"Deleted file from GCS: {full_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {full_path}")
                return False
        else:
            # Delete from local storage
            file_path = os.path.join(self._storage_path, user_path, filename)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file locally: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False
    
    async def list_files(self, prefix: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List files in user-partitioned storage.
        
        Args:
            prefix: Optional prefix to filter files
            
        Returns:
            List of file metadata
        """
        user_path = self.get_user_path()
        search_path = f"{user_path}/{prefix}" if prefix else user_path
        
        files = []
        
        if is_running_in_cloud() and self._gcs_client:
            # List from GCS
            bucket = self._gcs_client.bucket(self._bucket_name)
            blobs = bucket.list_blobs(prefix=search_path)
            
            for blob in blobs:
                # Extract filename from full path
                filename = blob.name.replace(f"{user_path}/", "")
                files.append({
                    'filename': filename,
                    'size': blob.size,
                    'created': blob.time_created,
                    'modified': blob.updated,
                    'content_type': blob.content_type
                })
        else:
            # List from local storage
            local_path = os.path.join(self._storage_path, user_path)
            if not os.path.exists(local_path):
                return files
            
            for root, dirs, filenames in os.walk(local_path):
                for filename in filenames:
                    if prefix and not filename.startswith(prefix):
                        continue
                    
                    file_path = os.path.join(root, filename)
                    # Get relative path from user directory
                    rel_path = os.path.relpath(file_path, local_path).replace('\\', '/')
                    stat = os.stat(file_path)
                    
                    files.append({
                        'filename': rel_path,
                        'size': stat.st_size,
                        'created': datetime.fromtimestamp(stat.st_ctime),
                        'modified': datetime.fromtimestamp(stat.st_mtime),
                        'content_type': self._guess_content_type(filename)
                    })
        
        return files
    
    def get_file_url(self, filename: str, expiry_hours: int = 24) -> str:
        """
        Get a URL for accessing a file.
        
        Args:
            filename: Filename
            expiry_hours: Hours until URL expires (for signed URLs)
            
        Returns:
            URL for accessing the file
        """
        user_path = self.get_user_path()
        full_path = f"{user_path}/{filename}"
        
        if is_running_in_cloud() and self._gcs_client:
            # Generate signed URL for GCS
            bucket = self._gcs_client.bucket(self._bucket_name)
            blob = bucket.blob(full_path)
            
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(hours=expiry_hours),
                method="GET",
            )
            return url
        else:
            # Return local serving URL
            # This assumes the web server is set up to serve from /storage
            return f"/storage/{self._user_hash}/{filename}"
    
    def _guess_content_type(self, filename: str) -> str:
        """Guess content type from filename."""
        ext = filename.lower().split('.')[-1]
        content_types = {
            'json': 'application/json',
            'md': 'text/markdown',
            'html': 'text/html',
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'pdf': 'application/pdf',
            'gz': 'application/gzip',
            'tar': 'application/x-tar',
        }
        return content_types.get(ext, 'application/octet-stream')
    
    # Convenience methods for specific file types
    async def save_screenshot(self, content: bytes, url: str) -> Dict[str, str]:
        """Save a screenshot and return its metadata."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_url = hashlib.md5(url.encode()).hexdigest()[:8]
        filename = f"screenshot_{timestamp}_{safe_url}.png"
        
        path = await self.save_file(content, filename)
        url = self.get_file_url(filename)
        
        return {
            'filename': filename,
            'path': path,
            'url': url
        }
    
    async def save_report(self, content: str, url: str, format: str = 'md') -> Dict[str, str]:
        """Save a report (markdown/json) and return its metadata."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_url = hashlib.md5(url.encode()).hexdigest()[:8]
        filename = f"report_{timestamp}_{safe_url}.{format}"
        
        path = await self.save_file(content, filename)
        url = self.get_file_url(filename)
        
        return {
            'filename': filename,
            'path': path,
            'url': url
        }
    
    async def save_crawl_data(self, data: Dict[str, Any], url: str) -> Dict[str, str]:
        """Save crawl data as JSON and return its metadata."""
        content = json.dumps(data, indent=2)
        return await self.save_report(content, url, format='json')


# Singleton instance
_storage_instance = None

def get_storage_service(user_email: Optional[str] = None) -> StorageService:
    """Get or create a storage service instance."""
    global _storage_instance
    if _storage_instance is None or (user_email and _storage_instance._user_email != user_email):
        _storage_instance = StorageService(user_email)
    return _storage_instance

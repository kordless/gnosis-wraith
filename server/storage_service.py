"""
Storage Service for Gnosis Wraith

Abstracts storage operations between Google Cloud Storage (cloud) and local filesystem (development).
"""

import os
import io
import uuid
import logging
import traceback
from typing import Dict, Any, Optional, Union, BinaryIO
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import GCS
try:
    from google.cloud import storage
except ImportError:
    logger.warning("Could not import GCS. Cloud storage will not be available.")

def is_running_in_cloud():
    """Detect if running in Google Cloud environment."""
    return os.environ.get('RUNNING_IN_CLOUD', '').lower() == 'true'

class StorageService:
    """
    Abstract storage operations between Google Cloud Storage and local filesystem.
    """
    
    def __init__(self):
        """Initialize the storage service based on environment."""
        self._gcs_client = None
        self._storage_path = os.environ.get('STORAGE_PATH', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'storage'))
        self._bucket_name = os.environ.get('GCS_BUCKET_NAME', 'gnosis-wraith-storage')
        
        # Ensure local storage path exists
        if not is_running_in_cloud():
            os.makedirs(self._storage_path, exist_ok=True)
            os.makedirs(os.path.join(self._storage_path, 'uploads'), exist_ok=True)
            os.makedirs(os.path.join(self._storage_path, 'reports'), exist_ok=True)
            os.makedirs(os.path.join(self._storage_path, 'screenshots'), exist_ok=True)
        else:
            self._init_gcs()
            
    def _init_gcs(self):
        """Initialize Google Cloud Storage client."""
        try:
            self._gcs_client = storage.Client()
            # Check if bucket exists and create if not
            try:
                bucket = self._gcs_client.get_bucket(self._bucket_name)
            except Exception:
                bucket = self._gcs_client.create_bucket(self._bucket_name)
                logger.info(f"Created GCS bucket: {self._bucket_name}")
            
            logger.info(f"GCS client initialized for bucket {self._bucket_name}")
        except Exception as e:
            logger.error(f"Failed to initialize GCS: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    async def save_file(self, file_data: Union[bytes, BinaryIO, str], folder: str, filename: Optional[str] = None) -> str:
        """
        Save a file to storage and return its path.
        
        Args:
            file_data: The file content as bytes or a file-like object
            folder: Folder to store in (e.g., 'uploads', 'reports')
            filename: Optional filename, will generate UUID if not provided
            
        Returns:
            path: The path to the saved file (GCS path or local path)
        """
        try:
            logger.info(f"save_file called with type: {type(file_data)}, folder: {folder}, filename: {filename}")
            
            if filename is None:
                filename = f"{uuid.uuid4().hex}{self._get_extension(file_data)}"
            
            if is_running_in_cloud():
                # Cloud storage logic...
                if self._gcs_client:
                    bucket = self._gcs_client.bucket(self._bucket_name)
                    blob_path = f"{folder}/{filename}"
                    blob = bucket.blob(blob_path)
                    
                    if isinstance(file_data, str):
                        # Handle string content
                        blob.upload_from_string(file_data)
                    elif isinstance(file_data, bytes):
                        # Handle bytes content
                        blob.upload_from_string(file_data, content_type=self._get_content_type(filename))
                    else:
                        # Handle file-like object
                        blob.upload_from_file(file_data)
                    
                    logger.info(f"Saved file to GCS: {blob_path}")
                    return blob_path
            else:
                # Local filesystem storage
                folder_path = os.path.join(self._storage_path, folder)
                os.makedirs(folder_path, exist_ok=True)
                
                file_path = os.path.join(folder_path, filename)
                logger.info(f"Preparing to save file to: {file_path}")
                
                if isinstance(file_data, str):
                    # Handle string content
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(file_data)
                    logger.info(f"Saved string data to {file_path}")
                elif isinstance(file_data, bytes):
                    # Handle bytes content - directly write to file
                    logger.info(f"Writing {len(file_data)} bytes to {file_path}")
                    with open(file_path, 'wb') as f:
                        f.write(file_data)
                    logger.info(f"Saved binary data ({len(file_data)} bytes) to {file_path}")
                else:
                    # Log details about the file-like object
                    has_read = hasattr(file_data, 'read')
                    has_seek = hasattr(file_data, 'seek')
                    has_tell = hasattr(file_data, 'tell')
                    logger.info(f"File-like object properties: has_read={has_read}, has_seek={has_seek}, has_tell={has_tell}")
                    
                    # Handle file-like object
                    with open(file_path, 'wb') as f:
                        if has_read:
                            # Try to seek to beginning if possible
                            if has_seek:
                                try:
                                    file_data.seek(0)
                                    logger.info("Seeked to beginning of file")
                                except Exception as e:
                                    logger.warning(f"Could not seek to beginning: {str(e)}")
                            
                            # Read in chunks
                            chunk_size = 8192  # 8KB chunks
                            total_written = 0
                            try:
                                chunk = file_data.read(chunk_size)
                                while chunk:
                                    if isinstance(chunk, str):
                                        chunk = chunk.encode('utf-8')
                                    f.write(chunk)
                                    total_written += len(chunk)
                                    chunk = file_data.read(chunk_size)
                                logger.info(f"Wrote {total_written} bytes in chunks")
                            except Exception as e:
                                logger.error(f"Error reading from file-like object: {str(e)}")
                                logger.error(traceback.format_exc())
                                raise
                        else:
                            # Try to convert to string or bytes
                            logger.warning(f"Object doesn't have .read() method: {type(file_data)}")
                            if hasattr(file_data, '__str__'):
                                data_str = str(file_data)
                                f.write(data_str.encode('utf-8'))
                                logger.info(f"Converted to string and wrote {len(data_str)} bytes")
                            else:
                                raise ValueError(f"Cannot handle data type: {type(file_data)}")
                
                logger.info(f"Successfully saved file to: {file_path}")
                return f"{folder}/{filename}"
        except Exception as e:
            logger.error(f"Error in save_file: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    async def get_file(self, file_path: str) -> bytes:
        """
        Retrieve a file from storage.
        
        Args:
            file_path: The path to the file
            
        Returns:
            The file content as bytes
        """
        try:
            if is_running_in_cloud():
                # Cloud storage retrieval...
                if self._gcs_client:
                    try:
                        bucket = self._gcs_client.bucket(self._bucket_name)
                        blob = bucket.blob(file_path)
                        return blob.download_as_bytes()
                    except Exception as e:
                        logger.error(f"Error getting file from GCS: {str(e)}")
                        logger.error(traceback.format_exc())
                        raise
            else:
                # Local filesystem retrieval
                try:
                    # If file_path is already absolute, use it as is
                    if os.path.isabs(file_path):
                        full_path = file_path
                    else:
                        # Otherwise, join with storage path
                        full_path = os.path.join(self._storage_path, file_path)
                    
                    logger.info(f"Getting file from: {full_path}")
                    with open(full_path, 'rb') as f:
                        data = f.read()
                    logger.info(f"Read {len(data)} bytes from {full_path}")
                    return data
                except Exception as e:
                    logger.error(f"Error getting file from local storage: {str(e)}")
                    logger.error(traceback.format_exc())
                    raise
        except Exception as e:
            logger.error(f"Error in get_file: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    async def get_file_as_string(self, file_path: str, encoding: str = 'utf-8') -> str:
        """
        Retrieve a file from storage as a string.
        
        Args:
            file_path: The path to the file
            encoding: Text encoding to use (default: utf-8)
            
        Returns:
            The file content as string
        """
        try:
            content = await self.get_file(file_path)
            return content.decode(encoding)
        except Exception as e:
            logger.error(f"Error in get_file_as_string: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from storage.
        
        Args:
            file_path: The path to the file
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            if is_running_in_cloud():
                # Cloud storage deletion...
                if self._gcs_client:
                    try:
                        bucket = self._gcs_client.bucket(self._bucket_name)
                        blob = bucket.blob(file_path)
                        blob.delete()
                        logger.info(f"Deleted file from GCS: {file_path}")
                        return True
                    except Exception as e:
                        logger.error(f"Error deleting file from GCS: {str(e)}")
                        return False
            else:
                # Local filesystem deletion
                try:
                    # If file_path is already absolute, use it as is
                    if os.path.isabs(file_path):
                        full_path = file_path
                    else:
                        # Otherwise, join with storage path
                        full_path = os.path.join(self._storage_path, file_path)
                    
                    os.remove(full_path)
                    logger.info(f"Deleted file from local storage: {full_path}")
                    return True
                except Exception as e:
                    logger.error(f"Error deleting file from local storage: {str(e)}")
                    return False
        except Exception as e:
            logger.error(f"Error in delete_file: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def get_public_url(self, file_path: str) -> str:
        """
        Get a public URL for accessing the file.
        
        Args:
            file_path: The path to the file
            
        Returns:
            A URL for accessing the file
        """
        if is_running_in_cloud():
            # Get GCS URL
            if self._gcs_client:
                bucket = self._gcs_client.bucket(self._bucket_name)
                blob = bucket.blob(file_path)
                return blob.public_url
        
        # For local development, just return the relative path
        # The app will serve it via a route handler
        return file_path
    
    def _get_extension(self, file_data: Union[bytes, BinaryIO, str]) -> str:
        """Infer file extension if possible, otherwise return empty string."""
        if isinstance(file_data, str):
            return '.txt'
        # For screenshots, use .png by default
        return '.png'
    
    def _get_content_type(self, filename: str) -> str:
        """Infer content type from filename."""
        ext = os.path.splitext(filename)[1].lower()
        
        content_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.txt': 'text/plain',
            '.html': 'text/html',
            '.md': 'text/markdown',
            '.json': 'application/json',
            '.pdf': 'application/pdf'
        }
        
        return content_types.get(ext, 'application/octet-stream')

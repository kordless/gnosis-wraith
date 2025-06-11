"""
Enhanced Storage Service for Gnosis Wraith

This module extends the existing storage service to properly handle report storage
in both local and cloud environments.
"""

import os
import io
import uuid
import logging
import traceback
import aiofiles
import hashlib
from typing import Dict, Any, Optional, Union, BinaryIO, List
from pathlib import Path
from datetime import datetime, timedelta
from quart import session
from core.models.user import User
import datetime as dt

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


class EnhancedStorageService:
    """
    Enhanced storage service that properly abstracts between local and cloud storage.
    """
    
    def __init__(self, user: Optional[User] = None):
        """Initialize the storage service based on environment."""
        self._gcs_client = None
        self._storage_path = os.environ.get('STORAGE_PATH', 
                                            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'storage'))
        self._bucket_name = os.environ.get('GCS_BUCKET_NAME', 'gnosis-wraith-storage')
        self._reports_dir = os.environ.get('GNOSIS_WRAITH_REPORTS_DIR', 
                                           os.path.join(os.path.expanduser("~"), ".gnosis-wraith/reports"))
        self._user = user  # NDB User model
        self._user_email = user.email if user else None
        self._user_path = None
        self._enable_user_partitioning = os.environ.get('ENABLE_USER_PARTITIONING', 'false').lower() == 'true'
        
        # Initialize based on environment
        if is_running_in_cloud():
            if GCS_AVAILABLE:
                self._init_gcs()
            else:
                raise RuntimeError("Running in cloud mode but GCS is not available")
        else:
            # Ensure local directories exist
            self._ensure_local_dirs()
    
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
    
    def set_user(self, user: User):
        """Set user context from NDB model."""
        self._user = user
        self._user_email = user.email if user else None
        self._user_path = self.get_user_path()
        logger.info(f"User context set from NDB: email={self._user_email}, path={self._user_path}")
    
    def get_user_path(self) -> str:
        """Get user-specific storage path from NDB user."""
        if not self._enable_user_partitioning:
            return ""  # No user partitioning, use root paths
        
        if self._user and hasattr(self._user, 'get_storage_hash'):
            # Use storage hash from NDB user model
            return f"users/{self._user.get_storage_hash()}"
        else:
            # Fallback to anonymous - get or create anonymous user
            from core.models.user import User
            anon = User.get_or_create_anonymous()
            return f"users/{anon.get_storage_hash()}"
    
    def set_user_context(self, email: Optional[str]):
        """Legacy method - kept for backwards compatibility."""
        # Try to find user by email
        if email:
            from core.models.user import User
            user = User.get_by_email(email)
            if user:
                self.set_user(user)
            else:
                logger.warning(f"User not found for email: {email}")
        else:
            self._user_email = email
            self._user_path = self.get_user_path()
            logger.info(f"User context set: email={email}, path={self._user_path}")
    
    def _ensure_local_dirs(self):
        """Ensure all required local directories exist."""
        dirs_to_create = [
            self._storage_path,
            os.path.join(self._storage_path, 'uploads'),
            os.path.join(self._storage_path, 'reports'),
            os.path.join(self._storage_path, 'screenshots'),
            self._reports_dir,
            os.path.dirname(self._reports_dir)  # Ensure parent dir exists
        ]
        
        for dir_path in dirs_to_create:
            os.makedirs(dir_path, exist_ok=True)
            logger.debug(f"Ensured directory exists: {dir_path}")
    
    def _get_user_hash(self) -> str:
        """Get current user's storage hash from NDB user."""
        if self._user and hasattr(self._user, 'get_storage_hash'):
            return self._user.get_storage_hash()
        
        # Fallback to session check
        try:
            if 'user_email' in session:
                email = session['user_email']
                return hashlib.sha256(email.encode()).hexdigest()[:12]
        except Exception as e:
            logger.debug(f"Could not get user hash: {e}")
        
        # Default to anonymous hash
        from core.models.user import User
        anon = User.get_or_create_anonymous()
        return anon.get_storage_hash()
    
    # Report-specific methods
    async def save_report(self, content: str, filename: str, format: str = 'md') -> str:
        """
        Save a report (markdown, JSON, or HTML) using appropriate storage backend.
        Also updates user metadata in NDB.
        
        Args:
            content: The report content as string
            filename: Base filename without extension
            format: File format ('md', 'json', 'html')
            
        Returns:
            Path or identifier for the saved report
        """
        user_hash = self._get_user_hash()
        full_filename = f"{filename}.{format}"
        
        if is_running_in_cloud():
            # Save to GCS bucket under users/{hash}/reports/ prefix
            report_path = await self.save_file(content, f'users/{user_hash}/reports', full_filename)
        else:
            # Save to local reports directory with user bucket
            user_reports_dir = os.path.join(self._reports_dir, 'users', user_hash)
            os.makedirs(user_reports_dir, exist_ok=True)
            
            report_path = os.path.join(user_reports_dir, full_filename)
            
            # Write file
            async with aiofiles.open(report_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            logger.info(f"Saved report to user storage: {report_path}")
        
        # Update user metadata in NDB if we have a user
        if self._user:
            try:
                self._user.last_crawl = dt.datetime.utcnow()
                self._user.crawl_count = (self._user.crawl_count or 0) + 1
                self._user.total_storage_bytes = (self._user.total_storage_bytes or 0) + len(content.encode('utf-8'))
                self._user.updated = dt.datetime.utcnow()
                self._user.put()
                logger.info(f"Updated user metadata in NDB: crawl_count={self._user.crawl_count}")
            except Exception as e:
                logger.error(f"Failed to update user metadata in NDB: {str(e)}")
                # Continue anyway - report is saved
        
        return report_path
    
    async def get_report(self, filename: str) -> str:
        """
        Retrieve a report from storage.
        
        Args:
            filename: The report filename (with extension)
            
        Returns:
            The report content as string
        """
        user_hash = self._get_user_hash()
        
        if is_running_in_cloud():
            # Get from GCS with user bucket
            content_bytes = await self.get_file(f"users/{user_hash}/reports/{filename}")
            return content_bytes.decode('utf-8')
        else:
            # Get from local storage with user bucket
            user_reports_dir = os.path.join(self._reports_dir, 'users', user_hash)
            report_path = os.path.join(user_reports_dir, filename)
            
            if not os.path.exists(report_path):
                raise FileNotFoundError(f"Report not found: {filename}")
            
            async with aiofiles.open(report_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            return content
    
    async def list_reports(self, format: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all reports in storage for the current user.
        
        Args:
            format: Optional filter by format ('md', 'json', 'html')
            
        Returns:
            List of report metadata dictionaries
        """
        user_hash = self._get_user_hash()
        reports = []
        
        if is_running_in_cloud():
            # List from GCS with user bucket
            bucket = self._gcs_client.bucket(self._bucket_name)
            blobs = bucket.list_blobs(prefix=f'users/{user_hash}/reports/')
            
            for blob in blobs:
                if format and not blob.name.endswith(f'.{format}'):
                    continue
                
                reports.append({
                    'filename': os.path.basename(blob.name),
                    'path': blob.name,
                    'size': blob.size,
                    'created': blob.time_created,
                    'modified': blob.updated,
                    'url': self.get_public_url(blob.name)
                })
        else:
            # List from local storage with user bucket
            user_reports_dir = os.path.join(self._reports_dir, 'users', user_hash)
            if not os.path.exists(user_reports_dir):
                return reports
            
            for filename in os.listdir(user_reports_dir):
                if format and not filename.endswith(f'.{format}'):
                    continue
                
                file_path = os.path.join(user_reports_dir, filename)
                stat = os.stat(file_path)
                
                reports.append({
                    'filename': filename,
                    'path': file_path,
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_ctime),
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'url': f"/reports/{filename}"  # Local serving URL
                })
        
        # Sort by modified date, newest first
        reports.sort(key=lambda x: x['modified'], reverse=True)
        return reports
    
    async def delete_report(self, filename: str) -> bool:
        """
        Delete a report from storage.
        
        Args:
            filename: The report filename
            
        Returns:
            True if deletion was successful
        """
        if is_running_in_cloud():
            return await self.delete_file(f"reports/{filename}")
        else:
            report_path = os.path.join(self._reports_dir, filename)
            
            if os.path.exists(report_path):
                os.remove(report_path)
                logger.info(f"Deleted report: {filename}")
                return True
            else:
                logger.warning(f"Report not found for deletion: {filename}")
                return False
    
    def get_report_url(self, filename: str, signed: bool = True, expiry_hours: int = 24) -> str:
        """
        Get a URL for accessing a report.
        
        Args:
            filename: The report filename
            signed: Whether to generate a signed URL (for cloud storage)
            expiry_hours: Hours until signed URL expires
            
        Returns:
            URL for accessing the report
        """
        if is_running_in_cloud():
            blob_path = f"reports/{filename}"
            
            if signed and self._gcs_client:
                # Generate signed URL
                bucket = self._gcs_client.bucket(self._bucket_name)
                blob = bucket.blob(blob_path)
                
                url = blob.generate_signed_url(
                    version="v4",
                    expiration=timedelta(hours=expiry_hours),
                    method="GET",
                )
                return url
            else:
                # Return public URL
                return self.get_public_url(blob_path)
        else:
            # Return local serving URL
            return f"/reports/{filename}"
    
    # Existing methods from original StorageService
    async def save_file(self, file_data: Union[bytes, BinaryIO, str], 
                        folder: str, filename: Optional[str] = None) -> str:
        """Save a file to storage and return its path."""
        # Implementation from original storage_service.py
        # ... (keep existing implementation)
        pass
    
    async def get_file(self, file_path: str) -> bytes:
        """Retrieve a file from storage."""
        # Implementation from original storage_service.py
        # ... (keep existing implementation)
        pass
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete a file from storage."""
        # Implementation from original storage_service.py
        # ... (keep existing implementation)
        pass
    
    def get_public_url(self, file_path: str) -> str:
        """Get a public URL for accessing the file."""
        # Implementation from original storage_service.py
        # ... (keep existing implementation)
        pass


# Backward compatibility - export the enhanced service as StorageService
StorageService = EnhancedStorageService


# Utility function for migration
async def migrate_existing_reports(storage_service: EnhancedStorageService):
    """
    Migrate existing local reports to current storage backend.
    
    This is useful when moving from local development to cloud deployment.
    """
    local_reports_dir = os.path.expanduser("~/.gnosis-wraith/reports")
    
    if not os.path.exists(local_reports_dir):
        logger.info("No local reports directory found for migration")
        return
    
    migrated_count = 0
    error_count = 0
    
    for filename in os.listdir(local_reports_dir):
        if filename.endswith(('.md', '.json', '.html')):
            file_path = os.path.join(local_reports_dir, filename)
            
            try:
                # Read the file
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract base filename and extension
                base_name = os.path.splitext(filename)[0]
                extension = filename.split('.')[-1]
                
                # Save using storage service
                await storage_service.save_report(content, base_name, extension)
                migrated_count += 1
                logger.info(f"Migrated report: {filename}")
                
            except Exception as e:
                error_count += 1
                logger.error(f"Failed to migrate {filename}: {str(e)}")
    
    logger.info(f"Migration complete. Migrated: {migrated_count}, Errors: {error_count}")


# Example usage in a route handler
"""
# In your Flask/FastAPI route:

@app.route('/api/save-report', methods=['POST'])
async def save_report():
    storage_service = StorageService()
    
    # Generate report content
    report_content = generate_markdown_report(title, crawl_results)
    
    # Save report
    report_path = await storage_service.save_report(
        content=report_content,
        filename=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        format="md"
    )
    
    # Get download URL
    download_url = storage_service.get_report_url(
        os.path.basename(report_path),
        signed=True,
        expiry_hours=24
    )
    
    return jsonify({
        'success': True,
        'report_path': report_path,
        'download_url': download_url
    })
"""

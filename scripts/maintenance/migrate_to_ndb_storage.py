#!/usr/bin/env python3
"""
Migration script for moving to NDB + Storage hybrid approach.

This script will:
1. Create anonymous user in NDB
2. Move existing reports and screenshots to anonymous user directory
3. Update the storage structure to match the new user-based organization
"""

import os
import shutil
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def migrate_to_ndb_storage():
    """Migrate existing files and create NDB records."""
    
    # Import models and context manager
    from core.models.user import User
    from core.lib.ndb_local import ndb_context_manager
    
    logger.info("Starting migration to NDB + Storage hybrid system")
    
    with ndb_context_manager():
        # 1. Create anonymous user in NDB
        logger.info("Creating anonymous user in NDB...")
        anon = User.get_or_create_anonymous()
        anon_hash = anon.get_storage_hash()
        logger.info(f"Anonymous user created with hash: {anon_hash}")
        
        # 2. Determine storage paths
        storage_path = os.environ.get('GNOSIS_WRAITH_STORAGE_PATH', './storage')
        
        # Create new directory structure
        new_anon_path = os.path.join(storage_path, 'users', anon_hash)
        new_anon_reports = os.path.join(new_anon_path, 'reports')
        new_anon_screenshots = os.path.join(new_anon_path, 'screenshots')
        
        os.makedirs(new_anon_reports, exist_ok=True)
        os.makedirs(new_anon_screenshots, exist_ok=True)
        logger.info(f"Created anonymous user directories at {new_anon_path}")
        
        # 3. Move existing reports
        old_reports = os.path.join(storage_path, 'reports')
        if os.path.exists(old_reports) and os.path.isdir(old_reports):
            logger.info(f"Migrating reports from {old_reports}")
            
            report_count = 0
            for filename in os.listdir(old_reports):
                if filename.endswith(('.md', '.json', '.html')):
                    src_path = os.path.join(old_reports, filename)
                    dst_path = os.path.join(new_anon_reports, filename)
                    
                    if os.path.exists(dst_path):
                        logger.warning(f"File already exists in destination: {filename}")
                        continue
                    
                    try:
                        shutil.move(src_path, dst_path)
                        report_count += 1
                        logger.info(f"Moved report: {filename}")
                        
                        # Update anonymous user stats
                        if filename.endswith('.md'):
                            anon.crawl_count = (anon.crawl_count or 0) + 1
                            # Estimate storage (we don't have exact size right now)
                            file_size = os.path.getsize(dst_path)
                            anon.total_storage_bytes = (anon.total_storage_bytes or 0) + file_size
                    except Exception as e:
                        logger.error(f"Failed to move {filename}: {str(e)}")
            
            logger.info(f"Moved {report_count} report files")
            
            # Remove old reports directory if empty
            try:
                if not os.listdir(old_reports):
                    os.rmdir(old_reports)
                    logger.info("Removed empty old reports directory")
            except Exception as e:
                logger.warning(f"Could not remove old reports directory: {str(e)}")
        else:
            logger.info("No old reports directory found")
        
        # 4. Move existing screenshots
        old_screenshots = os.path.join(storage_path, 'screenshots')
        if os.path.exists(old_screenshots) and os.path.isdir(old_screenshots):
            logger.info(f"Migrating screenshots from {old_screenshots}")
            
            screenshot_count = 0
            for filename in os.listdir(old_screenshots):
                if filename.endswith(('.png', '.jpg', '.jpeg')):
                    src_path = os.path.join(old_screenshots, filename)
                    dst_path = os.path.join(new_anon_screenshots, filename)
                    
                    if os.path.exists(dst_path):
                        logger.warning(f"File already exists in destination: {filename}")
                        continue
                    
                    try:
                        shutil.move(src_path, dst_path)
                        screenshot_count += 1
                        logger.info(f"Moved screenshot: {filename}")
                        
                        # Update storage size
                        file_size = os.path.getsize(dst_path)
                        anon.total_storage_bytes = (anon.total_storage_bytes or 0) + file_size
                    except Exception as e:
                        logger.error(f"Failed to move {filename}: {str(e)}")
            
            logger.info(f"Moved {screenshot_count} screenshot files")
            
            # Remove old screenshots directory if empty
            try:
                if not os.listdir(old_screenshots):
                    os.rmdir(old_screenshots)
                    logger.info("Removed empty old screenshots directory")
            except Exception as e:
                logger.warning(f"Could not remove old screenshots directory: {str(e)}")
        else:
            logger.info("No old screenshots directory found")
        
        # 5. Update anonymous user stats in NDB
        anon.put()
        logger.info(f"Updated anonymous user stats: crawl_count={anon.crawl_count}, storage_bytes={anon.total_storage_bytes}")
        
        # 6. Create system directory for future use
        system_dir = os.path.join(storage_path, 'system')
        os.makedirs(system_dir, exist_ok=True)
        logger.info("Created system directory")
        
        # 7. Create migration marker file
        marker_file = os.path.join(system_dir, 'ndb_migration_completed.txt')
        with open(marker_file, 'w') as f:
            import datetime
            f.write(f"NDB + Storage hybrid migration completed at {datetime.datetime.now()}\n")
            f.write(f"Anonymous user hash: {anon_hash}\n")
            f.write(f"Reports migrated: {report_count}\n")
            f.write(f"Screenshots migrated: {screenshot_count}\n")
        
        logger.info("Migration completed successfully!")
        logger.info(f"Anonymous user storage is at: users/{anon_hash}/")
        
        return True

def check_if_migration_needed():
    """Check if migration has already been performed."""
    storage_path = os.environ.get('GNOSIS_WRAITH_STORAGE_PATH', './storage')
    marker_file = os.path.join(storage_path, 'system', 'ndb_migration_completed.txt')
    
    if os.path.exists(marker_file):
        logger.info("NDB migration has already been completed")
        with open(marker_file, 'r') as f:
            logger.info(f"Previous migration info:\n{f.read()}")
        return False
    
    # Check if old structure exists
    old_reports = os.path.join(storage_path, 'reports')
    old_screenshots = os.path.join(storage_path, 'screenshots')
    
    if os.path.exists(old_reports) or os.path.exists(old_screenshots):
        return True
    
    logger.info("No migration needed - old directories not found")
    return False

if __name__ == "__main__":
    # Set environment variable for local datastore if not set
    if 'USE_LOCAL_DATASTORE' not in os.environ:
        os.environ['USE_LOCAL_DATASTORE'] = 'true'
    
    # Set storage path if not set
    if 'GNOSIS_WRAITH_STORAGE_PATH' not in os.environ:
        os.environ['GNOSIS_WRAITH_STORAGE_PATH'] = './storage'
    
    try:
        if check_if_migration_needed():
            logger.info("Migration needed - starting NDB migration process")
            success = migrate_to_ndb_storage()
            if success:
                logger.info("Migration completed successfully!")
                sys.exit(0)
            else:
                logger.error("Migration failed!")
                sys.exit(1)
        else:
            logger.info("No migration needed")
            sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error during migration: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
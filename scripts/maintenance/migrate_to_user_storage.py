#!/usr/bin/env python3
"""
Migration script for moving existing reports and screenshots to user-specific directories.

This script will:
1. Move all existing reports and screenshots to the anonymous user directory
2. Create the new user-based directory structure
3. Update any file references if needed
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

def migrate_existing_storage():
    """Move existing files to anonymous user directory."""
    
    # Get storage path from environment or use default
    storage_path = os.environ.get('GNOSIS_WRAITH_STORAGE_PATH', './storage')
    
    # Check if storage path exists
    if not os.path.exists(storage_path):
        logger.error(f"Storage path does not exist: {storage_path}")
        return False
    
    logger.info(f"Starting migration for storage path: {storage_path}")
    
    # Create new user directory structure
    anonymous_dir = os.path.join(storage_path, 'users', 'anonymous')
    anonymous_reports_dir = os.path.join(anonymous_dir, 'reports')
    anonymous_screenshots_dir = os.path.join(anonymous_dir, 'screenshots')
    
    # Create directories
    os.makedirs(anonymous_reports_dir, exist_ok=True)
    os.makedirs(anonymous_screenshots_dir, exist_ok=True)
    logger.info(f"Created anonymous user directories")
    
    # Migrate reports
    old_reports_dir = os.path.join(storage_path, 'reports')
    if os.path.exists(old_reports_dir) and os.path.isdir(old_reports_dir):
        logger.info(f"Migrating reports from {old_reports_dir}")
        
        files_moved = 0
        for filename in os.listdir(old_reports_dir):
            if filename.endswith(('.md', '.json', '.html')):
                src_path = os.path.join(old_reports_dir, filename)
                dst_path = os.path.join(anonymous_reports_dir, filename)
                
                if os.path.exists(dst_path):
                    logger.warning(f"File already exists in destination: {filename}")
                    continue
                
                try:
                    shutil.move(src_path, dst_path)
                    files_moved += 1
                    logger.info(f"Moved report: {filename}")
                except Exception as e:
                    logger.error(f"Failed to move {filename}: {str(e)}")
        
        logger.info(f"Moved {files_moved} report files")
        
        # Remove old reports directory if empty
        try:
            if not os.listdir(old_reports_dir):
                os.rmdir(old_reports_dir)
                logger.info("Removed empty old reports directory")
        except Exception as e:
            logger.warning(f"Could not remove old reports directory: {str(e)}")
    else:
        logger.info("No old reports directory found")
    
    # Migrate screenshots
    old_screenshots_dir = os.path.join(storage_path, 'screenshots')
    if os.path.exists(old_screenshots_dir) and os.path.isdir(old_screenshots_dir):
        logger.info(f"Migrating screenshots from {old_screenshots_dir}")
        
        files_moved = 0
        for filename in os.listdir(old_screenshots_dir):
            if filename.endswith(('.png', '.jpg', '.jpeg')):
                src_path = os.path.join(old_screenshots_dir, filename)
                dst_path = os.path.join(anonymous_screenshots_dir, filename)
                
                if os.path.exists(dst_path):
                    logger.warning(f"File already exists in destination: {filename}")
                    continue
                
                try:
                    shutil.move(src_path, dst_path)
                    files_moved += 1
                    logger.info(f"Moved screenshot: {filename}")
                except Exception as e:
                    logger.error(f"Failed to move {filename}: {str(e)}")
        
        logger.info(f"Moved {files_moved} screenshot files")
        
        # Remove old screenshots directory if empty
        try:
            if not os.listdir(old_screenshots_dir):
                os.rmdir(old_screenshots_dir)
                logger.info("Removed empty old screenshots directory")
        except Exception as e:
            logger.warning(f"Could not remove old screenshots directory: {str(e)}")
    else:
        logger.info("No old screenshots directory found")
    
    # Create a system directory for future use
    system_dir = os.path.join(storage_path, 'system')
    os.makedirs(system_dir, exist_ok=True)
    logger.info("Created system directory")
    
    # Create a migration marker file
    marker_file = os.path.join(system_dir, 'migration_v1_completed.txt')
    with open(marker_file, 'w') as f:
        import datetime
        f.write(f"Migration to user-based storage completed at {datetime.datetime.now()}\n")
    
    logger.info("Migration completed successfully!")
    return True

def check_if_migration_needed():
    """Check if migration has already been performed."""
    storage_path = os.environ.get('GNOSIS_WRAITH_STORAGE_PATH', './storage')
    marker_file = os.path.join(storage_path, 'system', 'migration_v1_completed.txt')
    
    if os.path.exists(marker_file):
        logger.info("Migration has already been completed")
        return False
    
    # Check if old structure exists
    old_reports = os.path.join(storage_path, 'reports')
    old_screenshots = os.path.join(storage_path, 'screenshots')
    
    if os.path.exists(old_reports) or os.path.exists(old_screenshots):
        return True
    
    logger.info("No migration needed - old directories not found")
    return False

if __name__ == "__main__":
    try:
        if check_if_migration_needed():
            logger.info("Migration needed - starting migration process")
            success = migrate_existing_storage()
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
        sys.exit(1)
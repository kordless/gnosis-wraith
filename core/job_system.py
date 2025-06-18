"""
Gnosis Wraith Job System Integration

This module initializes the job-based processing system and integrates it with the main app.
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

def is_running_in_cloud():
    """Detect if running in Google Cloud environment."""
    return os.environ.get('RUNNING_IN_CLOUD', '').lower() == 'true'

def setup_job_system(app):
    """
    Set up the job-based processing system and register it with the main app.
    
    Args:
        app: The Quart application instance
    """
    logger.info("Setting up job-based processing system")
    
    # Register the job routes blueprint
    from core.job_routes import register_jobs_blueprint
    register_jobs_blueprint(app)
    
    # Add a scheduled cleanup task if we're running in cloud mode
    if is_running_in_cloud():
        # Import here to avoid circular imports
        from core.task_manager import TaskManager
        import asyncio
        
        async def schedule_cleanup_task():
            task_manager = TaskManager()
            
            # Schedule a daily cleanup task
            await task_manager.create_task(
                "cleanup-old-jobs",
                {"days_to_keep": 30},  # Keep jobs for 30 days
                "cleanup"  # Use a fixed ID for this system task
            )
            
            logger.info("Scheduled cleanup task")
        
        # Schedule the cleanup task asynchronously
        @app.before_serving
        async def startup():
            asyncio.create_task(schedule_cleanup_task())
    
    logger.info("Job-based processing system initialized")

def add_job_system_to_context():
    """
    Add job system components to the app context.
    This allows other parts of the app to access them.
    """
    # Import components
    from core.job_manager import JobManager
    from core.enhanced_storage_service import EnhancedStorageService
    from core.task_manager import TaskManager
    
    # Initialize components
    job_manager = JobManager()
    storage_service = EnhancedStorageService()
    task_manager = TaskManager()
    
    # Return components to be added to app context
    return {
        'job_manager': job_manager,
        'storage_service': storage_service,
        'task_manager': task_manager
    }

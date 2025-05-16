"""
Gnosis Wraith Initializers

This module provides initialization functions for various subsystems.
It is imported by app.py to set up the application components.
"""

import logging
import asyncio
from server.task_manager import TaskManager, is_running_in_cloud

logger = logging.getLogger(__name__)

def init_job_system(app):
    """
    Initialize the job-based processing system.
    
    Args:
        app: The Quart application instance
    """
    try:
        from server.job_system import setup_job_system
        setup_job_system(app)
        
        # Add a before_serving hook to start the background task processor
        @app.before_serving
        async def startup():
            """Initialize background tasks before server starts."""
            # Initialize task manager and start processor
            task_manager = await TaskManager.create()
            
            # Only start background processor in local mode
            # In cloud mode, Cloud Tasks handles this
            if not is_running_in_cloud():
                # Start the task processor in the background
                app.background_tasks.add(
                    asyncio.create_task(task_manager._process_local_tasks())
                )
                logger.info("Started background task processor for job system")
        
        logger.info("Job system initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize job system: {str(e)}")
        return False

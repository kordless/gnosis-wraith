"""
Job Manager for Gnosis Wraith

Handles job creation, retrieval, and status updates.
Works with Firestore in the cloud and Redis locally.
"""

import os
import json
import uuid
import datetime
import logging
import asyncio
from typing import Dict, Any, List, Optional, Union

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import Firestore
try:
    from google.cloud import firestore
except ImportError:
    logger.warning("Could not import Firestore. Cloud storage will not be available.")

# Try to import Redis
try:
    import redis.asyncio as aioredis
except ImportError:
    try:
        import aioredis
    except ImportError:
        logger.warning("Could not import aioredis. Local job queue will use in-memory storage.")

def is_running_in_cloud():
    """Detect if running in Google Cloud environment."""
    return os.environ.get('RUNNING_IN_CLOUD', '').lower() == 'true'

class JobManager:
    """
    Manages job creation, retrieval, and updates.
    Uses Firestore in cloud mode and Redis in local mode.
    """
    
    def __init__(self):
        """Initialize the job manager based on environment."""
        self._db_client = None
        self._redis_client = None
        self._in_memory_jobs = {}  # Fallback if Redis is not available in local mode
        
        if is_running_in_cloud():
            self._init_firestore()
        # Don't call _init_redis() here - will be called by factory method
            
    @classmethod
    async def create(cls):
        """Factory method to create and initialize JobManager."""
        instance = cls()
        if not is_running_in_cloud():
            await instance._init_redis()
        return instance
            
    def _init_firestore(self):
        """Initialize Firestore client for cloud mode."""
        try:
            self._db_client = firestore.AsyncClient()
            logger.info("Firestore client initialized for job management")
        except Exception as e:
            logger.error(f"Failed to initialize Firestore: {str(e)}")
            raise
            
    async def _init_redis(self):
        """Initialize Redis client for local mode."""
        try:
            redis_host = os.environ.get('REDIS_HOST', 'localhost')
            redis_port = int(os.environ.get('REDIS_PORT', 6379))
            
            # Support both newer Redis and older aioredis libraries
            try:
                # Try newer Redis library first
                self._redis_client = await aioredis.from_url(f'redis://{redis_host}:{redis_port}')
                logger.info(f"Redis client initialized using redis.asyncio at {redis_host}:{redis_port}")
            except (AttributeError, TypeError):
                # Fall back to older aioredis library
                try:
                    self._redis_client = await aioredis.create_redis_pool(f'redis://{redis_host}:{redis_port}')
                    logger.info(f"Redis client initialized using legacy aioredis at {redis_host}:{redis_port}")
                except AttributeError:
                    # If we're here, neither method works
                    logger.warning("Could not initialize Redis with available methods, falling back to in-memory storage")
                    self._redis_client = None
        except Exception as e:
            logger.warning(f"Failed to initialize Redis, using in-memory storage: {str(e)}")
            self._redis_client = None
    
    async def create_job(self, job_type: str, metadata: Dict[str, Any]) -> str:
        """
        Create a new job and return its ID.
        
        Args:
            job_type: Type of job (e.g., 'image-processing', 'ocr')
            metadata: Job metadata including file paths, options, etc.
            
        Returns:
            job_id: The unique ID for the created job
        """
        job_id = str(uuid.uuid4())
        created_at = datetime.datetime.now().isoformat()
        
        job_data = {
            "job_id": job_id,
            "job_type": job_type,
            "status": "pending",
            "created_at": created_at,
            "updated_at": created_at,
            "metadata": metadata
        }
        
        # Store the job based on environment
        if is_running_in_cloud():
            # Store in Firestore
            if self._db_client:
                await self._db_client.collection('jobs').document(job_id).set(job_data)
        else:
            # Store in Redis or in-memory
            if self._redis_client:
                await self._redis_client.set(
                    f"job:{job_id}", 
                    json.dumps(job_data)
                )
            else:
                # Fallback to in-memory storage
                self._in_memory_jobs[job_id] = job_data
        
        logger.info(f"Created job {job_id} of type {job_type}")
        return job_id
    
    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a job by its ID.
        
        Args:
            job_id: The ID of the job to retrieve
            
        Returns:
            The job data as a dictionary, or None if not found
        """
        if is_running_in_cloud():
            # Get from Firestore
            if self._db_client:
                doc_ref = self._db_client.collection('jobs').document(job_id)
                doc = await doc_ref.get()
                return doc.to_dict() if doc.exists else None
        else:
            # Get from Redis or in-memory
            if self._redis_client:
                job_data = await self._redis_client.get(f"job:{job_id}")
                return json.loads(job_data) if job_data else None
            else:
                # Get from in-memory storage
                return self._in_memory_jobs.get(job_id)
    
    async def update_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a job with new data.
        
        Args:
            job_id: The ID of the job to update
            updates: Dictionary of fields to update
            
        Returns:
            True if update was successful, False otherwise
        """
        # Add updated_at timestamp
        updates["updated_at"] = datetime.datetime.now().isoformat()
        
        if is_running_in_cloud():
            # Update in Firestore
            if self._db_client:
                doc_ref = self._db_client.collection('jobs').document(job_id)
                await doc_ref.update(updates)
                logger.info(f"Updated job {job_id} in Firestore")
                return True
        else:
            # Update in Redis or in-memory
            if self._redis_client:
                # Get current job data
                job_data = await self._redis_client.get(f"job:{job_id}")
                if not job_data:
                    logger.error(f"Job {job_id} not found in Redis")
                    return False
                
                # Update job data
                job_dict = json.loads(job_data)
                job_dict.update(updates)
                
                # Save updated job data
                await self._redis_client.set(f"job:{job_id}", json.dumps(job_dict))
                logger.info(f"Updated job {job_id} in Redis")
                return True
            else:
                # Update in-memory storage
                if job_id not in self._in_memory_jobs:
                    logger.error(f"Job {job_id} not found in memory")
                    return False
                
                self._in_memory_jobs[job_id].update(updates)
                logger.info(f"Updated job {job_id} in memory")
                return True
        
        return False
    
    async def list_jobs(self, status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List jobs, optionally filtered by status.
        
        Args:
            status: Optional status to filter by
            limit: Maximum number of jobs to return
            
        Returns:
            List of job data dictionaries
        """
        jobs = []
        
        if is_running_in_cloud():
            # List from Firestore
            if self._db_client:
                query = self._db_client.collection('jobs')
                if status:
                    query = query.where('status', '==', status)
                    
                query = query.limit(limit)
                docs = await query.get()
                
                jobs = [doc.to_dict() for doc in docs]
        else:
            # List from Redis or in-memory
            if self._redis_client:
                # Get all job keys
                keys = await self._redis_client.keys('job:*')
                
                # Get job data for each key
                for key in keys[:limit]:
                    job_data = await self._redis_client.get(key)
                    if job_data:
                        job_dict = json.loads(job_data)
                        if status is None or job_dict.get('status') == status:
                            jobs.append(job_dict)
            else:
                # List from in-memory storage
                jobs = list(self._in_memory_jobs.values())
                if status:
                    jobs = [job for job in jobs if job.get('status') == status]
                jobs = jobs[:limit]
        
        # Sort by creation time, newest first
        jobs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return jobs
    
    async def cleanup(self):
        """Close any open connections."""
        if not is_running_in_cloud() and self._redis_client:
            self._redis_client.close()
            await self._redis_client.wait_closed()

"""
Cloud Tasks Integration for Gnosis Wraith

Handles the creation and management of asynchronous tasks.
Provides both Google Cloud Tasks and local Redis-based task queues.
"""

import os
import json
import logging
import datetime
import asyncio
import traceback
from typing import Dict, Any, Optional, List, Union

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Class-level variable to track if the processor is running
_processor_running = False

# Try to import Cloud Tasks libraries
try:
    from google.cloud import tasks_v2
    from google.protobuf import timestamp_pb2
except ImportError:
    logger.warning("Could not import Cloud Tasks libraries. Cloud tasks will not be available.")

# Try to import Redis
try:
    import redis.asyncio as aioredis
except ImportError:
    try:
        import aioredis
    except ImportError:
        logger.warning("Could not import aioredis. Local task queue will use in-memory processing.")

def is_running_in_cloud():
    """Detect if running in Google Cloud environment."""
    return os.environ.get('RUNNING_IN_CLOUD', '').lower() == 'true'

class TaskManager:
    """
    Manages asynchronous tasks using Google Cloud Tasks in cloud mode
    and Redis in local development mode.
    """
    
    def __init__(self):
        """Initialize the task manager based on environment."""
        self._tasks_client = None
        self._redis_client = None
        self._in_memory_tasks = {}  # Fallback if Redis is not available
        self._local_tasks_running = False
        
        # Cloud Tasks configuration
        self._project = os.environ.get('GOOGLE_CLOUD_PROJECT')
        self._location = os.environ.get('CLOUD_TASKS_LOCATION', 'us-central1')
        self._queue = os.environ.get('CLOUD_TASKS_QUEUE', 'image-processing')
        self._service_url = os.environ.get('SERVICE_URL')
        self._service_account = os.environ.get('CLOUD_TASKS_SERVICE_ACCOUNT')
        
        if is_running_in_cloud():
            self._init_tasks_client()
        # Don't call _init_redis() here - will be called by factory method
    
    @classmethod
    async def create(cls):
        """Factory method to create and initialize TaskManager."""
        instance = cls()
        if not is_running_in_cloud():
            await instance._init_redis()
        return instance
    
    def _init_tasks_client(self):
        """Initialize Cloud Tasks client for cloud mode."""
        try:
            self._tasks_client = tasks_v2.CloudTasksClient()
            logger.info("Cloud Tasks client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Cloud Tasks client: {str(e)}")
            raise
    
    async def _init_redis(self):
        """Initialize Redis client for local development."""
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
            logger.warning(f"Failed to initialize Redis, using in-memory task processing: {str(e)}")
            self._redis_client = None
    
    async def create_task(self, task_type: str, task_data: Dict[str, Any], job_id: str, delay_seconds: int = 0) -> str:
        """
        Create a new task for asynchronous processing.
        
        Args:
            task_type: Type of task (e.g., 'process-image', 'generate-report')
            task_data: Data to be passed to the task handler
            job_id: ID of the associated job
            delay_seconds: Optional delay before task execution
            
        Returns:
            task_id: The ID of the created task
        """
        if is_running_in_cloud():
            return await self._create_cloud_task(task_type, task_data, job_id, delay_seconds)
        else:
            return await self._create_local_task(task_type, task_data, job_id, delay_seconds)
    
    async def _create_cloud_task(self, task_type: str, task_data: Dict[str, Any], job_id: str, delay_seconds: int = 0) -> str:
        """Create a task in Google Cloud Tasks."""
        if not self._tasks_client:
            raise ValueError("Cloud Tasks client not initialized")
        
        # Verify required environment variables
        if not self._project or not self._service_url or not self._service_account:
            raise ValueError("Missing required Cloud Tasks configuration")
        
        # Create the task path
        parent = self._tasks_client.queue_path(self._project, self._location, self._queue)
        
        # Create the task with payload
        task = {
            'http_request': {
                'http_method': tasks_v2.HttpMethod.POST,
                'url': f"{self._service_url}/tasks/{task_type}/{job_id}",
                'oidc_token': {
                    'service_account_email': self._service_account
                },
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps(task_data).encode()
            }
        }
        
        # Set schedule time if delay is specified
        if delay_seconds > 0:
            timestamp = timestamp_pb2.Timestamp()
            timestamp.FromDatetime(
                datetime.datetime.utcnow() + datetime.timedelta(seconds=delay_seconds)
            )
            task['schedule_time'] = timestamp
        
        # Submit the task
        response = self._tasks_client.create_task(request={"parent": parent, "task": task})
        
        logger.info(f"Created Cloud Task: {response.name}")
        return response.name
    
    async def _create_local_task(self, task_type: str, task_data: Dict[str, Any], job_id: str, delay_seconds: int = 0) -> str:
        """Create a task in the local Redis queue or in-memory queue."""
        # Generate a task ID
        import uuid
        task_id = str(uuid.uuid4())
        
        # Create task data structure
        task_record = {
            "task_id": task_id,
            "task_type": task_type,
            "job_id": job_id,
            "data": task_data,
            "created_at": datetime.datetime.now().isoformat(),
            "execute_at": (datetime.datetime.now() + datetime.timedelta(seconds=delay_seconds)).isoformat()
        }
        
        # Store the task based on available storage
        if self._redis_client:
            # Store in Redis
            # Use a sorted set with execute_at as score for delayed execution
            execute_at_timestamp = datetime.datetime.fromisoformat(task_record["execute_at"]).timestamp()
            
            # Store task data
            await self._redis_client.set(f"task:{task_id}", json.dumps(task_record))
            
            try:
                # This is the problematic line - fix the zadd call based on Redis version
                logger.info(f"Adding task to queue with Redis client type: {type(self._redis_client)}")
                
                # Try the newer Redis interface first
                try:
                    # New redis.asyncio style - expects mapping
                    await self._redis_client.zadd(
                        f"task_queue:{task_type}",
                        {task_id: execute_at_timestamp}
                    )
                    logger.info(f"Used new-style zadd with mapping")
                except (TypeError, AttributeError) as e:
                    logger.info(f"New-style zadd failed: {str(e)}, trying old-style")
                    # Older aioredis style - expects score, member
                    await self._redis_client.zadd(
                        f"task_queue:{task_type}",
                        execute_at_timestamp,
                        task_id
                    )
                    logger.info(f"Used old-style zadd with separate score and member")
                    
            except Exception as e:
                logger.error(f"Error adding task to Redis queue: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise
            
            logger.info(f"Created local task in Redis: {task_id}")
        else:
            # Store in memory
            self._in_memory_tasks[task_id] = task_record
            logger.info(f"Created local task in memory: {task_id}")
        
        return task_id
    
    async def _process_local_tasks(self):
        """Process tasks from Redis or in-memory queue for local development."""
        # Check if already running using module-level variable
        global _processor_running
        
        if _processor_running:
            logger.warning("Task processor already running, not starting a second instance")
            return
        
        # Mark as running
        _processor_running = True
        logger.info("Starting local task processor")
        
        try:
            while True:  # Keep running indefinitely
                try:
                    if self._redis_client:
                        # Process from Redis
                        await self._process_redis_tasks()
                    else:
                        # Process from in-memory queue
                        await self._process_in_memory_tasks()
                    
                    # Sleep before next check
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"Error in local task processor: {str(e)}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    await asyncio.sleep(5)  # Sleep longer on error
        except asyncio.CancelledError:
            # Handle shutdown gracefully
            logger.info("Background task processor is shutting down")
        finally:
            # On exit, mark as not running
            _processor_running = False
    
    async def _process_redis_tasks(self):
        """Process tasks from Redis queue."""
        # Get all task types (queue names)
        task_queues = []
        keys = await self._redis_client.keys("task_queue:*")
        for key in keys:
            if isinstance(key, bytes):
                key = key.decode('utf-8')
            task_queues.append(key.replace("task_queue:", ""))
        
        current_time = datetime.datetime.now().timestamp()
        
        for task_type in task_queues:
            # Get tasks that are ready to execute (score <= current time)
            try:
                # Handle different Redis library versions
                if hasattr(self._redis_client, 'zrangebyscore'):
                    # Legacy aioredis
                    task_ids = await self._redis_client.zrangebyscore(
                        f"task_queue:{task_type}",
                        0,  # Min score
                        current_time,  # Max score (current time)
                        0,  # Offset
                        5  # Count (process up to 5 tasks at once)
                    )
                else:
                    # Newer redis.asyncio
                    try:
                        task_ids = await self._redis_client.zrange_by_score(
                            f"task_queue:{task_type}",
                            min=0,
                            max=current_time,
                            start=0,
                            num=5
                        )
                    except (TypeError, AttributeError):
                        # Some versions of redis-py use different method names or signatures
                        task_ids = await self._redis_client.zrangebyscore(
                            f"task_queue:{task_type}",
                            min=0,
                            max=current_time,
                            start=0,
                            num=5
                        )
            except Exception as e:
                logger.error(f"Error retrieving tasks from Redis: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                continue  # Skip this queue and try the next one
            
            for task_id_bytes in task_ids:
                if isinstance(task_id_bytes, bytes):
                    task_id = task_id_bytes.decode('utf-8')
                else:
                    task_id = task_id_bytes
                
                # Get task data
                task_data = await self._redis_client.get(f"task:{task_id}")
                if not task_data:
                    # Task data not found, remove from queue
                    try:
                        if hasattr(self._redis_client, 'zrem'):
                            await self._redis_client.zrem(f"task_queue:{task_type}", task_id)
                        else:
                            await self._redis_client.zrem(f"task_queue:{task_type}", [task_id])
                    except Exception as e:
                        logger.error(f"Error removing task {task_id} from queue: {str(e)}")
                    continue
                
                # Parse task data
                if isinstance(task_data, bytes):
                    task_data = task_data.decode('utf-8')
                    
                try:
                    task = json.loads(task_data)
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing task data for {task_id}: {str(e)}")
                    continue
                
                try:
                    # Execute the task
                    logger.info(f"Executing local task from Redis: {task_id}")
                    await self._execute_local_task(task)
                    
                    # Remove from queue
                    try:
                        if hasattr(self._redis_client, 'zrem'):
                            await self._redis_client.zrem(f"task_queue:{task_type}", task_id)
                        else:
                            await self._redis_client.zrem(f"task_queue:{task_type}", [task_id])
                    except Exception as e:
                        logger.error(f"Error removing completed task {task_id} from queue: {str(e)}")
                    
                    # We could delete the task data, but keeping it allows for inspection
                    # await self._redis_client.delete(f"task:{task_id}")
                except Exception as e:
                    logger.error(f"Error executing local task {task_id}: {str(e)}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    
                    # Increment retry count and reschedule if possible
                    retry_count = task.get("retry_count", 0) + 1
                    if retry_count <= 3:  # Max retries
                        task["retry_count"] = retry_count
                        next_execution = datetime.datetime.now() + datetime.timedelta(seconds=30*retry_count)
                        task["execute_at"] = next_execution.isoformat()
                        
                        # Update task data
                        await self._redis_client.set(f"task:{task_id}", json.dumps(task))
                        
                        # Update in queue with new execution time
                        try:
                            if hasattr(self._redis_client, 'zadd'):
                                try:
                                    # Try new-style first
                                    await self._redis_client.zadd(
                                        f"task_queue:{task_type}",
                                        {task_id: next_execution.timestamp()}
                                    )
                                except (TypeError, AttributeError):
                                    # Fall back to old-style
                                    await self._redis_client.zadd(
                                        f"task_queue:{task_type}",
                                        next_execution.timestamp(),
                                        task_id
                                    )
                            else:
                                await self._redis_client.zadd(
                                    f"task_queue:{task_type}",
                                    {task_id: next_execution.timestamp()}
                                )
                        except Exception as add_error:
                            logger.error(f"Error rescheduling task {task_id}: {str(add_error)}")
                        
                        logger.info(f"Rescheduled task {task_id} for retry {retry_count}")
                    else:
                        logger.error(f"Task {task_id} failed after {retry_count} retries, giving up")
                        # Mark as failed but don't remove from queue for inspection
                        task["status"] = "failed"
                        task["error"] = str(e)
                        await self._redis_client.set(f"task:{task_id}", json.dumps(task))
    
    async def _process_in_memory_tasks(self):
        """Process tasks from in-memory queue."""
        current_time = datetime.datetime.now()
        tasks_to_execute = []
        
        # Find tasks that are ready to execute
        for task_id, task in list(self._in_memory_tasks.items()):
            execute_at = datetime.datetime.fromisoformat(task["execute_at"])
            if current_time >= execute_at and task.get("status") != "processing":
                task["status"] = "processing"
                tasks_to_execute.append(task)
        
        # Execute ready tasks
        for task in tasks_to_execute:
            try:
                logger.info(f"Executing local task from memory: {task['task_id']}")
                await self._execute_local_task(task)
                
                # Mark as completed (or remove)
                # In-memory tasks are kept for debugging
                task["status"] = "completed"
                task["completed_at"] = datetime.datetime.now().isoformat()
            except Exception as e:
                logger.error(f"Error executing in-memory task {task['task_id']}: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                
                # Increment retry count and reschedule if possible
                retry_count = task.get("retry_count", 0) + 1
                if retry_count <= 3:  # Max retries
                    task["status"] = "pending"
                    task["retry_count"] = retry_count
                    task["execute_at"] = (datetime.datetime.now() + datetime.timedelta(seconds=30*retry_count)).isoformat()
                    task["error"] = str(e)
                    logger.info(f"Rescheduled in-memory task {task['task_id']} for retry {retry_count}")
                else:
                    task["status"] = "failed"
                    task["error"] = str(e)
                    logger.error(f"In-memory task {task['task_id']} failed after {retry_count} retries, giving up")
    
    async def _execute_local_task(self, task):
        """Execute a local task by calling the appropriate task handler."""
        import aiohttp
        
        task_type = task["task_type"]
        job_id = task["job_id"]
        data = task["data"]
        
        # Determine the URL for the task handler
        task_url = f"http://localhost:5678/tasks/{task_type}/{job_id}"
        
        # Call the task handler
        async with aiohttp.ClientSession() as session:
            async with session.post(task_url, json=data) as response:
                if response.status >= 400:
                    response_text = await response.text()
                    raise ValueError(f"Task handler returned error {response.status}: {response_text}")
                
                return await response.json()
    
    async def cleanup(self):
        """Close any open connections."""
        if not is_running_in_cloud() and self._redis_client:
            if hasattr(self._redis_client, 'close'):
                self._redis_client.close()
                if hasattr(self._redis_client, 'wait_closed'):
                    await self._redis_client.wait_closed()

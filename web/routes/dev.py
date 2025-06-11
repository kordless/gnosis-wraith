"""
Development-only routes for Gnosis Wraith

This module provides endpoints for development tools like the queue monitor.
These endpoints are automatically disabled in production.
"""
import os
import functools
from datetime import datetime
from typing import Dict, Any, List

from quart import Blueprint, render_template, jsonify, request

# Only import Redis if available in dev
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from core.config import logger

# Create blueprint
dev_bp = Blueprint('dev', __name__, url_prefix='/dev')

# Environment check
IS_DEVELOPMENT = os.getenv('ENVIRONMENT', 'development') == 'development'
ENABLE_DEV_ENDPOINTS = os.getenv('ENABLE_DEV_ENDPOINTS', 'false').lower() == 'true'

def dev_only(f):
    """Decorator to ensure endpoint only works in development"""
    @functools.wraps(f)
    async def decorated_function(*args, **kwargs):
        if not IS_DEVELOPMENT or not ENABLE_DEV_ENDPOINTS:
            return jsonify({"error": "Not available in production"}), 404
        return await f(*args, **kwargs)
    return decorated_function

# Redis connection (lazy initialization)
_redis_client = None

async def get_redis():
    """Get Redis client (development only)"""
    global _redis_client
    if not REDIS_AVAILABLE:
        return None
    
    if _redis_client is None:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        _redis_client = await redis.from_url(redis_url)
    
    return _redis_client

@dev_bp.route('/queue-monitor')
@dev_only
async def queue_monitor():
    """Development queue monitor page"""
    return await render_template('dev/queue_monitor.html')

@dev_bp.route('/api/queue-status')
@dev_only
async def queue_status():
    """Get current queue status"""
    try:
        client = await get_redis()
        if not client:
            return jsonify({
                "queue_size": 0,
                "redis_available": False,
                "message": "Redis not available"
            })
        
        # Get queue size from Redis
        queue_size = await client.llen('gnosis:task_queue')
        
        # Get some stats
        processed_count = await client.get('gnosis:processed_count') or 0
        failed_count = await client.get('gnosis:failed_count') or 0
        
        return jsonify({
            "queue_size": queue_size,
            "redis_available": True,
            "processed_total": int(processed_count),
            "failed_total": int(failed_count),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Queue status error: {e}")
        return jsonify({
            "queue_size": 0,
            "redis_available": False,
            "error": str(e)
        })

@dev_bp.route('/api/process-queue', methods=['POST'])
@dev_only
async def process_queue():
    """Process one batch of queue items"""
    try:
        client = await get_redis()
        if not client:
            return jsonify({
                "processed": 0,
                "results": [],
                "error": "Redis not available"
            })
        
        # Get batch size from request or use default
        batch_size = request.args.get('batch_size', 5, type=int)
        results = []
        
        # Process batch
        for _ in range(batch_size):
            # Pop item from queue
            item = await client.lpop('gnosis:task_queue')
            if not item:
                break
            
            # Simulate processing (this is where AI pipelines will go)
            task_data = eval(item.decode('utf-8'))  # In production, use json.loads
            
            result = await process_task(task_data)
            results.append(result)
            
            # Update counters
            if result['status'] == 'success':
                await client.incr('gnosis:processed_count')
            else:
                await client.incr('gnosis:failed_count')
        
        return jsonify({
            "processed": len(results),
            "results": results,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Queue processing error: {e}")
        return jsonify({
            "processed": 0,
            "results": [],
            "error": str(e)
        }), 500

async def process_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single task - this is where agentic pipelines will be integrated
    
    Args:
        task_data: Dictionary containing task information
        
    Returns:
        Result dictionary with status and details
    """
    try:
        task_type = task_data.get('type', 'unknown')
        task_id = task_data.get('id', 'unknown')
        
        # TODO: This is where we'll integrate agentic pipelines
        # For now, simulate different task types
        
        if task_type == 'crawl':
            # Simulate crawl processing
            logger.info(f"Processing crawl task {task_id}")
            return {
                "task_id": task_id,
                "type": task_type,
                "status": "success",
                "message": "Crawl completed (simulated)"
            }
            
        elif task_type == 'ai_analysis':
            # Simulate AI analysis
            logger.info(f"Processing AI analysis task {task_id}")
            return {
                "task_id": task_id,
                "type": task_type,
                "status": "success",
                "message": "AI analysis completed (simulated)"
            }
            
        elif task_type == 'report_generation':
            # Simulate report generation
            logger.info(f"Processing report generation task {task_id}")
            return {
                "task_id": task_id,
                "type": task_type,
                "status": "success",
                "message": "Report generated (simulated)"
            }
            
        else:
            # Unknown task type
            return {
                "task_id": task_id,
                "type": task_type,
                "status": "error",
                "message": f"Unknown task type: {task_type}"
            }
            
    except Exception as e:
        logger.error(f"Task processing error: {e}")
        return {
            "task_id": task_data.get('id', 'unknown'),
            "type": task_data.get('type', 'unknown'),
            "status": "error",
            "message": str(e)
        }

@dev_bp.route('/api/add-test-task', methods=['POST'])
@dev_only
async def add_test_task():
    """Add a test task to the queue (for development testing)"""
    try:
        client = await get_redis()
        if not client:
            return jsonify({"error": "Redis not available"}), 500
        
        # Get task data from request
        data = await request.get_json()
        task_type = data.get('type', 'crawl')
        
        # Create test task
        task = {
            'id': f'test-{datetime.now().timestamp()}',
            'type': task_type,
            'created': datetime.now().isoformat(),
            'data': data.get('data', {})
        }
        
        # Add to queue
        await client.rpush('gnosis:task_queue', str(task))
        
        return jsonify({
            "success": True,
            "task": task,
            "queue_size": await client.llen('gnosis:task_queue')
        })
        
    except Exception as e:
        logger.error(f"Add test task error: {e}")
        return jsonify({"error": str(e)}), 500

@dev_bp.route('/api/clear-queue', methods=['POST'])
@dev_only
async def clear_queue():
    """Clear the task queue (development only!)"""
    try:
        client = await get_redis()
        if not client:
            return jsonify({"error": "Redis not available"}), 500
        
        # Clear queue
        await client.delete('gnosis:task_queue')
        
        # Reset counters
        await client.delete('gnosis:processed_count')
        await client.delete('gnosis:failed_count')
        
        return jsonify({
            "success": True,
            "message": "Queue cleared"
        })
        
    except Exception as e:
        logger.error(f"Clear queue error: {e}")
        return jsonify({"error": str(e)}), 500
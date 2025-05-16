"""
API Routes for Job-based Processing

This module adds the job-based API endpoints to the Gnosis Wraith application.
"""

import os
import uuid
import datetime
import logging
import io
import traceback
import asyncio
from typing import Dict, Any

from quart import Blueprint, request, jsonify

from server.job_manager import JobManager
from server.storage_service import StorageService
from server.task_manager import TaskManager
from server.config import logger

# Create Blueprint
jobs_blueprint = Blueprint('jobs', __name__, url_prefix='/api')

@jobs_blueprint.route('/upload-async', methods=['POST'])
async def api_upload_async():
    """
    API endpoint to upload images asynchronously.
    
    This immediately returns a job ID and processes in the background.
    """
    logger.info("API upload-async endpoint called")
    
    try:
        # Get files and form data
        files = await request.files
        form = await request.form
        logger.info(f"Files received: {files.keys()}, Form data: {form.keys()}")
        
        if 'image' not in files:
            return jsonify({
                "success": False,
                "error": "No image file provided"
            }), 400
        
        # Initialize services using async factory methods
        job_manager = await JobManager.create()
        storage = StorageService()  # This one doesn't need async init
        task_manager = await TaskManager.create()
        
        # Process the file
        file = files['image']
        title = form.get('title', 'Image Analysis Report')
        
        # Get original filename from the file object
        original_filename = file.filename if hasattr(file, 'filename') else "screenshot.png"
        logger.info(f"Original filename: {original_filename}")
        
        # Generate a unique filename for storage
        extension = os.path.splitext(original_filename)[1] or '.png'
        unique_filename = f"{uuid.uuid4().hex}{extension}"
        
        # Get file data SAFELY - check the type first to avoid await errors
        logger.info(f"File object type: {type(file)}")
        
        # Modified handling to check if read is awaitable or not
        if hasattr(file, 'read'):
            logger.info("File has read attribute")
            if asyncio.iscoroutinefunction(file.read):
                logger.info("File.read is a coroutine function, using await")
                file_data = await file.read()
            else:
                logger.info("File.read is not a coroutine, calling directly")
                file_data = file.read()
        else:
            # If file is already bytes or string
            logger.info(f"File does not have read attribute, using directly: {type(file)}")
            file_data = file
        
        logger.info(f"File data type: {type(file_data)}, size: {len(file_data) if hasattr(file_data, '__len__') else 'unknown'}")
        
        # Don't pass the file object, pass the raw bytes
        file_path = await storage.save_file(file_data, 'uploads', unique_filename)
        
        # Create a job for async processing
        job_metadata = {
            "file_path": file_path,
            "title": title,
            "original_filename": original_filename,  # Store the actual original filename
            "file_size": len(file_data) if hasattr(file_data, '__len__') else 0,
            "mime_type": getattr(file, 'content_type', 'application/octet-stream')
        }
        
        # Create job record
        job_id = await job_manager.create_job("image-processing", job_metadata)
        
        # Create task to process the job
        await task_manager.create_task(
            "process-image",
            {"source": "upload-api"},
            job_id
        )
        
        logger.info(f"Created job {job_id} for async image processing")
        
        # Return immediately with job ID
        return jsonify({
            "success": True,
            "job_id": job_id,
            "status": "pending"
        })
        
    except Exception as e:
        logger.error(f"API upload-async error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@jobs_blueprint.route('/jobs/<job_id>', methods=['GET'])
async def get_job_status(job_id):
    """
    API endpoint to check job status.
    
    Clients poll this endpoint to check progress.
    """
    try:
        job_manager = await JobManager.create()
        
        # Get the job
        job = await job_manager.get_job(job_id)
        if not job:
            return jsonify({
                "success": False,
                "error": f"Job {job_id} not found"
            }), 404
        
        # Basic response with job status
        response = {
            "success": True,
            "job_id": job_id,
            "status": job.get("status", "unknown"),
            "job_type": job.get("job_type"),
            "created_at": job.get("created_at"),
            "updated_at": job.get("updated_at")
        }
        
        # Add info based on status
        if job.get("status") == "completed":
            response["results"] = job.get("results", {})
            
            # Add server URLs for convenience
            if "report_path" in job.get("results", {}):
                server_url = os.environ.get('GNOSIS_WRAITH_SERVER_URL', request.host_url.rstrip('/'))
                response["report_url"] = f"{server_url}/reports/{job['results']['report_path']}"
                
            if "html_path" in job.get("results", {}):
                server_url = os.environ.get('GNOSIS_WRAITH_SERVER_URL', request.host_url.rstrip('/'))
                response["html_url"] = f"{server_url}/reports/{job['results']['html_path']}"
                
        elif job.get("status") == "failed":
            response["error"] = job.get("error", "Unknown error")
            response["failed_at"] = job.get("failed_at")
            
        elif job.get("status") == "processing":
            response["processing_started_at"] = job.get("processing_started_at")
            # Could add progress percentage or stage info here
            
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting job status for {job_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@jobs_blueprint.route('/jobs', methods=['GET'])
async def list_jobs():
    """
    API endpoint to list jobs.
    
    Can filter by status and limit results.
    """
    try:
        job_manager = await JobManager.create()
        
        # Get query parameters
        status = request.args.get('status')
        limit_str = request.args.get('limit', '100')
        
        try:
            limit = int(limit_str)
        except ValueError:
            limit = 100
        
        # Get jobs
        jobs = await job_manager.list_jobs(status, limit)
        
        # Simplify the job data for the response
        job_list = []
        for job in jobs:
            job_summary = {
                "job_id": job.get("job_id"),
                "job_type": job.get("job_type"),
                "status": job.get("status"),
                "created_at": job.get("created_at"),
                "updated_at": job.get("updated_at")
            }
            
            if job.get("status") == "completed":
                results = job.get("results", {})
                if "processing_time" in results:
                    job_summary["processing_time"] = results["processing_time"]
                    
            elif job.get("status") == "failed":
                job_summary["error"] = job.get("error", "Unknown error")
                
            job_list.append(job_summary)
        
        return jsonify({
            "success": True,
            "jobs": job_list,
            "count": len(job_list)
        })
        
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@jobs_blueprint.route('/jobs/<job_id>', methods=['DELETE'])
async def delete_job(job_id):
    """
    API endpoint to delete a job and its associated files.
    """
    try:
        job_manager = await JobManager.create()
        storage = StorageService()
        
        # Get the job
        job = await job_manager.get_job(job_id)
        if not job:
            return jsonify({
                "success": False,
                "error": f"Job {job_id} not found"
            }), 404
        
        # Delete files
        files_deleted = []
        
        # Delete input file
        file_path = job.get("metadata", {}).get("file_path")
        if file_path and await storage.delete_file(file_path):
            files_deleted.append(file_path)
        
        # Delete result files
        results = job.get("results", {})
        
        report_path = results.get("report_path")
        if report_path:
            full_report_path = os.path.join("reports", report_path)
            if await storage.delete_file(full_report_path):
                files_deleted.append(full_report_path)
        
        html_path = results.get("html_path")
        if html_path:
            full_html_path = os.path.join("reports", html_path)
            if await storage.delete_file(full_html_path):
                files_deleted.append(full_html_path)
        
        # Mark job as deleted (we don't actually delete the job record for audit trail)
        await job_manager.update_job(job_id, {
            "status": "deleted",
            "deleted_at": datetime.datetime.now().isoformat(),
            "files_deleted": files_deleted
        })
        
        return jsonify({
            "success": True,
            "job_id": job_id,
            "files_deleted": files_deleted
        })
        
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def register_jobs_blueprint(app):
    """Register the jobs blueprint with the main app."""
    app.register_blueprint(jobs_blueprint)
    
    # Also register the task handlers
    from server.task_handlers import tasks_blueprint
    app.register_blueprint(tasks_blueprint)
    
    # Add a hook to log and sanitize input parameters for debugging
    @app.before_request
    async def log_request_data():
        if request.method == 'POST' and request.path == '/api/crawl':
            try:
                data = await request.get_json(silent=True)
                if data and 'take_screenshot' in data:
                    # Ensure take_screenshot is properly processed
                    if isinstance(data['take_screenshot'], str):
                        # Convert string 'true'/'false' to boolean
                        data['take_screenshot'] = data['take_screenshot'].lower() == 'true'
                    # Log the processed value
                    logger.info(f"Request take_screenshot parameter processed to: {data['take_screenshot']}")
            except Exception as e:
                logger.error(f"Error processing request parameters: {str(e)}")
    
    logger.info("Registered job-based API endpoints and task handlers")

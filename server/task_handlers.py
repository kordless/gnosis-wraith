"""
Task Handlers for Gnosis Wraith

Implements the endpoints that process tasks initiated by Cloud Tasks.
"""

import os
import json
import datetime
import logging
import traceback
from typing import Dict, Any, Optional

from quart import Blueprint, request, jsonify

from server.job_manager import JobManager
from server.storage_service import StorageService
from server.config import logger

# Import AI models for OCR processing
from ai.models import ModelManager

# Import reporting functions
from server.reports import save_markdown_report, convert_markdown_to_html

# Create Blueprint
tasks_blueprint = Blueprint('tasks', __name__, url_prefix='/tasks')

# Task request verification
def verify_task_request(request):
    """
    Verify the task request is legitimate.
    
    In cloud mode, this checks the authentication.
    In local mode, we trust localhost requests.
    """
    from server.task_manager import is_running_in_cloud
    
    if is_running_in_cloud():
        # In cloud mode, verify the OIDC token
        # This would typically be done by Cloud Run automatically
        # but we can add extra verification if needed
        
        # Get the Authorization header
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            logger.warning("Task request missing Bearer token")
            return False
        
        # Further token validation could be implemented here
        # For Cloud Run with IAM, most validation is handled by the platform
        
        return True
    else:
        # In local mode, accept all requests (assuming they're from localhost)
        # We could add a simple token-based auth for local testing if needed
        return True

@tasks_blueprint.route('/process-image/<job_id>', methods=['POST'])
async def process_image_task(job_id):
    """Handler for processing an image asynchronously."""
    # Verify task request
    if not verify_task_request(request):
        return jsonify({"error": "Unauthorized task request"}), 403
    
    # Initialize services
    job_manager = await JobManager.create()
    storage = StorageService()
    model_manager = ModelManager()
    
    try:
        # Get the job
        job = await job_manager.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return jsonify({"error": f"Job {job_id} not found"}), 404
        
        # Record processing start time
        processing_start_time = datetime.datetime.now()
        
        # Update job status
        await job_manager.update_job(job_id, {
            "status": "processing",
            "processing_started_at": processing_start_time.isoformat()
        })
        
        # Get file path from job metadata
        file_path = job["metadata"].get("file_path")
        if not file_path:
            raise ValueError("No file path in job metadata")
        
        # Load the image data
        image_data = await storage.get_file(file_path)
        
        # Prepare a temporary local file for the OCR engine if needed
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
            temp_file.write(image_data)
            temp_file_path = temp_file.name
        
        try:
            # Extract text using OCR
            logger.info(f"Extracting text from image for job {job_id}")
            extracted_text = await model_manager.extract_text_from_image(temp_file_path)
            
            # Clean up temp file
            os.unlink(temp_file_path)
            
            # Create a result object for the report
            original_filename = job["metadata"].get("original_filename", "captured_image.png")
            image_result = {
                'url': original_filename,  # Use the original filename as the URL
                'title': job["metadata"].get("title", "Image Analysis"),
                'screenshot': file_path,  # Path to the image
                'original_filename': original_filename,  # Add original filename explicitly
                'extracted_text': extracted_text
            }
            
            # Generate markdown report
            report_title = job["metadata"].get("title", "Image Analysis Report")
            logger.info(f"Generating report for job {job_id}")
            
            report_path = await save_markdown_report(report_title, [image_result])
            
            # Convert to HTML
            html_path = await convert_markdown_to_html(report_path)
            
            # Calculate processing time
            processing_time = (datetime.datetime.now() - processing_start_time).total_seconds()
            
            # Update job with results
            await job_manager.update_job(job_id, {
                "status": "completed",
                "completed_at": datetime.datetime.now().isoformat(),
                "results": {
                    "extracted_text": extracted_text,
                    "report_path": os.path.basename(report_path),
                    "html_path": os.path.basename(html_path),
                    "processing_time": processing_time
                }
            })
            
            logger.info(f"Successfully completed image processing for job {job_id}")
            return jsonify({
                "success": True,
                "job_id": job_id,
                "status": "completed"
            })
            
        except Exception as process_error:
            # Clean up temp file if it still exists
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            raise process_error
            
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Update job with error
        await job_manager.update_job(job_id, {
            "status": "failed",
            "error": str(e),
            "failed_at": datetime.datetime.now().isoformat()
        })
        
        # Return 200 to avoid Cloud Tasks retries (we already marked the job as failed)
        return jsonify({
            "success": False,
            "job_id": job_id,
            "error": str(e),
            "status": "failed"
        }), 200

@tasks_blueprint.route('/cleanup-old-jobs', methods=['POST'])
async def cleanup_old_jobs_task():
    """Handler for cleaning up old jobs and files."""
    # Verify task request
    if not verify_task_request(request):
        return jsonify({"error": "Unauthorized task request"}), 403
    
    try:
        # Get days to keep from request (default 30 days)
        data = await request.get_json() or {}
        days_to_keep = data.get('days_to_keep', 30)
        
        # Calculate cutoff date
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_to_keep)
        cutoff_iso = cutoff_date.isoformat()
        
        # Initialize services
        job_manager = await JobManager.create()
        storage = StorageService()
        
        # Get all jobs
        all_jobs = await job_manager.list_jobs(limit=1000)  # Increase limit if needed
        
        # Find jobs older than cutoff
        old_jobs = [job for job in all_jobs if job.get('created_at', '') < cutoff_iso]
        
        # Keep track of what's deleted
        deleted_count = 0
        failed_count = 0
        
        # Delete files and jobs
        for job in old_jobs:
            job_id = job.get('job_id')
            try:
                # Get file paths
                file_path = job.get('metadata', {}).get('file_path')
                results = job.get('results', {})
                report_path = results.get('report_path')
                html_path = results.get('html_path')
                
                # Delete files
                files_deleted = []
                if file_path:
                    if await storage.delete_file(file_path):
                        files_deleted.append(file_path)
                
                if report_path:
                    report_full_path = os.path.join('reports', report_path)
                    if await storage.delete_file(report_full_path):
                        files_deleted.append(report_full_path)
                
                if html_path:
                    html_full_path = os.path.join('reports', html_path)
                    if await storage.delete_file(html_full_path):
                        files_deleted.append(html_full_path)
                
                # Update job (mark as cleaned up, don't delete the record)
                await job_manager.update_job(job_id, {
                    "status": "cleaned_up",
                    "cleaned_up_at": datetime.datetime.now().isoformat(),
                    "files_deleted": files_deleted
                })
                
                deleted_count += 1
                
            except Exception as e:
                logger.error(f"Error cleaning up job {job_id}: {str(e)}")
                failed_count += 1
        
        return jsonify({
            "success": True,
            "deleted_count": deleted_count,
            "failed_count": failed_count,
            "cutoff_date": cutoff_iso
        })
        
    except Exception as e:
        logger.error(f"Error in cleanup task: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

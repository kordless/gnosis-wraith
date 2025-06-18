# Phase 4: Task Queue System Implementation

## Overview
Implement asynchronous task processing using Cloud Run Jobs + Storage pattern for OCR, AI enhancement, and future processing needs.

## Core Architecture

### Storage-First Pattern
```
1. Crawl creates document → Save to storage
2. Create task reference → Save to queue directory  
3. Trigger job with path → Job loads from storage
4. Process & update → Save results back to storage
```

### Job Tracking (NDB)
```python
class Job(BaseModel):
    doc_path = ndb.StringProperty(required=True)
    task_path = ndb.StringProperty(required=True)
    status = ndb.StringProperty(default="queued")  # queued, processing, completed, failed
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)
    error = ndb.TextProperty()
    attempts = ndb.IntegerProperty(default=0)
```

### Directory Structure
```
storage/
└── domains/
    └── [domain_name]/
        ├── raw/          # Original crawl data
        ├── processed/    # Completed processing
        ├── screenshots/  # Image files
        └── queue/        # Task documents
            └── [task_id].json
```

### Task Document Schema
```json
{
    "task_id": "ocr_12345",
    "job_id": "job_xyz789",  // NDB job reference
    "endpoint": "/api/process/ocr",
    "doc_path": "domains/splunk_com/raw/crawl_12345.json",
    "params": {
        "screenshot_path": "domains/splunk_com/screenshots/12345.png",
        "ocr_enabled": true,
        "language": "en"
    },
    "created_at": "2025-06-04T18:30:00Z",
    "chain_next": "enhance_md_12346",  // Optional chaining
    "callback_url": null,  // Optional webhook
    "sse_client_id": null  // Optional SSE connection
}
```

## Implementation Components

### 1. Job Runner Interface
```python
# core/job_runner.py
class JobRunner(ABC):
    @abstractmethod
    def trigger_job(self, task_path: str) -> str:
        """Returns job_id"""
        pass
    
    @abstractmethod
    def get_job_status(self, job_id: str) -> dict:
        pass

# core/cloud_job_runner.py
class CloudJobRunner(JobRunner):
    """Uses Cloud Run Jobs API"""
    
# core/local_job_runner.py  
class LocalJobRunner(JobRunner):
    """Uses ProcessPoolExecutor for local dev"""
```

### 2. Task Processor
```python
# core/task_processor.py
TASK_ENDPOINTS = {
    "/api/process/ocr": process_ocr,
    "/api/process/enhance_md": enhance_markdown,
    "/api/process/ai_summary": ai_summarize,
}

async def process_task(task_path: str):
    # Load task document
    task = storage.load(task_path)
    
    # Update job status
    job = Job.get_by_id(task["job_id"])
    job.status = "processing"
    job.put()
    
    # Call appropriate handler
    handler = TASK_ENDPOINTS[task["endpoint"]]
    result = await handler(task)
    
    # Handle chaining
    if task.get("chain_next"):
        trigger_next_task(task["chain_next"])
```

### 3. Job Reaper
```python
# core/job_reaper.py
async def reap_stale_jobs():
    """Run every 5 minutes"""
    cutoff = datetime.utcnow() - timedelta(minutes=10)
    stale_jobs = Job.query(
        Job.status.IN(["queued", "processing"]),
        Job.updated_at < cutoff
    ).fetch()
    
    for job in stale_jobs:
        job.status = "failed"
        job.error = "Timeout - no update for 10 minutes"
        job.put()
```

### 4. API Updates
```python
# web/routes/api.py
@api_bp.route('/api/crawl', methods=['POST'])
async def crawl():
    # ... existing crawl logic ...
    
    # If OCR requested, create task
    if data.get('ocr_extraction'):
        task_id = f"ocr_{timestamp}_{random_string(6)}"
        task_doc = {
            "task_id": task_id,
            "endpoint": "/api/process/ocr",
            "doc_path": doc_path,
            "params": {
                "screenshot_path": screenshot_path,
                "ocr_enabled": True
            }
        }
        
        # Save task to queue
        task_path = f"{domain_path}/queue/{task_id}.json"
        storage.save(task_path, task_doc)
        
        # Trigger job
        job_id = job_runner.trigger_job(task_path)
        
        # Return immediately
        return {
            "status": "success",
            "job_id": job_id,
            "message": "Crawl complete, OCR processing queued"
        }
```

### 5. SSE Support (Optional)
```python
# web/routes/api.py
@api_bp.route('/api/jobs/<job_id>/stream')
async def stream_job_status(job_id):
    async def generate():
        while True:
            job = Job.get_by_id(job_id)
            yield f"data: {json.dumps(job.to_dict())}\n\n"
            
            if job.status in ["completed", "failed"]:
                break
                
            await asyncio.sleep(1)
    
    return Response(generate(), mimetype="text/event-stream")
```

## Processing Endpoints

### OCR Processing
```python
# core/processors/ocr_processor.py
async def process_ocr(task: dict) -> dict:
    doc = storage.load(task["doc_path"])
    screenshot_path = task["params"]["screenshot_path"]
    
    # Run OCR
    ocr_text = await model_manager.extract_text_from_image(screenshot_path)
    
    # Update document
    doc["ocr_content"] = ocr_text
    doc["ocr_processed_at"] = datetime.utcnow().isoformat()
    
    # Save to processed
    processed_path = task["doc_path"].replace("/raw/", "/processed/")
    storage.save(processed_path, doc)
    
    return {"status": "success", "processed_path": processed_path}
```

### Markdown Enhancement
```python
# core/processors/markdown_enhancer.py
async def enhance_markdown(task: dict) -> dict:
    doc = storage.load(task["doc_path"])
    
    # Use AI to enhance markdown
    enhanced = await ai_client.enhance_markdown(
        doc["markdown_content"],
        doc.get("ocr_content", "")
    )
    
    doc["enhanced_markdown"] = enhanced
    doc["enhanced_at"] = datetime.utcnow().isoformat()
    
    storage.save(task["doc_path"], doc)
    return {"status": "success"}
```

## Environment Configuration
```python
# core/config.py
if os.getenv('K_SERVICE'):  # Cloud Run
    from .cloud_job_runner import CloudJobRunner
    job_runner = CloudJobRunner()
else:  # Local
    from .local_job_runner import LocalJobRunner
    job_runner = LocalJobRunner(max_workers=4)
```

## Testing Strategy
1. Unit tests for each processor
2. Integration tests with local job runner
3. Mock Cloud Run Jobs API for cloud tests
4. Test job timeout and reaping
5. Test task chaining

## Migration Notes
- Existing crawl API remains synchronous for non-OCR requests
- OCR/AI processing becomes async with job tracking
- Backwards compatible - old clients still work

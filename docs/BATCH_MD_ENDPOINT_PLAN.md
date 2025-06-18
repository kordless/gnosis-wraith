# Batch Markdown Endpoint Implementation Plan

## Overview
Enhance the `/md` endpoint to support processing multiple URLs in parallel with immediate response and background processing.

## Goals
1. Accept both single URL and list of URLs
2. Process multiple URLs in parallel using async threads
3. Return immediate response with predictable URLs
4. Background processing with status tracking
5. Optional result collation

## API Design

### Request Format
```json
{
  "url": "https://example.com",  // Single URL (backward compatible)
  // OR
  "urls": [                       // Multiple URLs (new)
    "https://example.com/page1",
    "https://example.com/page2",
    "https://example.com/page3"
  ],
  "filter": "pruning",
  "filter_options": {...},
  "javascript_enabled": true,
  "collate": false,               // Whether to merge results into single file
  "async": true,                  // Return immediately with status URLs
  "callback_url": "https://myapp.com/webhook/batch-complete",  // Optional webhook
  "callback_headers": {           // Optional headers for callback
    "Authorization": "Bearer my-webhook-token"
  }
}
```


### Response Format (Immediate)
```json
{
  "success": true,
  "mode": "batch_async",
  "job_id": "batch_1234567890",
  "status_url": "/api/jobs/batch_1234567890",
  "results": [
    {
      "url": "https://example.com/page1",
      "status": "processing",
      "markdown_url": "/storage/users/[hash]/reports/example_com_page1_abc123.md",
      "json_url": "/storage/users/[hash]/data/example_com_page1_abc123.json"
    },
    {
      "url": "https://example.com/page2",
      "status": "processing",
      "markdown_url": "/storage/users/[hash]/reports/example_com_page2_def456.md",
      "json_url": "/storage/users/[hash]/data/example_com_page2_def456.json"
    }
  ],
  "collated_url": "/storage/users/[hash]/reports/batch_1234567890_collated.md"  // If collate=true
}
```

## Implementation Steps

### Phase 0: Test-First Development
1. **Create comprehensive test suite BEFORE making changes**
   ```python
   # tests/test_batch_markdown.py
   
   async def test_single_url_backward_compatibility():
       """Ensure single URL requests work exactly as before"""
       response = await client.post("/api/markdown", json={
           "url": "https://example.com"
       })
       assert response.status_code == 200
       assert "markdown" in response.json()
       assert "urls" not in response.json()  # No batch response
   
   async def test_batch_urls_sync_mode():
       """Test batch processing with immediate response"""
       response = await client.post("/api/markdown", json={
           "urls": ["https://example.com/1", "https://example.com/2"],
           "async": False
       })
       assert response.status_code == 200
       assert len(response.json()["results"]) == 2
       assert all(r["status"] == "completed" for r in response.json()["results"])
   
   async def test_batch_urls_async_mode():
       """Test batch processing with background jobs"""
       response = await client.post("/api/markdown", json={
           "urls": ["https://example.com/1", "https://example.com/2"],
           "async": True
       })
       assert response.status_code == 202  # Accepted
       assert "job_id" in response.json()
       assert all(r["status"] == "processing" for r in response.json()["results"])
   
   async def test_callback_webhook():
       """Test webhook callback on batch completion"""
       with mock_webhook_server() as webhook:
           response = await client.post("/api/markdown", json={
               "urls": ["https://example.com/1"],
               "async": True,
               "callback_url": webhook.url,
               "callback_headers": {"X-Test": "123"}
           })
           
           # Wait for callback
           callback_data = await webhook.wait_for_call(timeout=60)
           assert callback_data["job_id"] == response.json()["job_id"]
           assert callback_data["status"] == "completed"
           assert "stats" in callback_data
   ```

2. **Create test fixtures and mocks**
   - Mock crawler responses for predictable testing
   - Mock storage service for fast tests
   - Create test webhook server for callback testing

3. **Run existing tests to ensure no regression**
   ```bash
   pytest tests/test_api.py::test_markdown_endpoint -v
   ```

### Phase 1: URL Prediction System

## Implementation Steps

### Phase 0: Test-First Development
1. **Create comprehensive test suite BEFORE making changes**
   ```python
   # tests/test_batch_markdown.py
   
   async def test_single_url_backward_compatibility():
       """Ensure single URL requests work exactly as before"""
       response = await client.post("/api/markdown", json={
           "url": "https://example.com"
       })
       assert response.status_code == 200
       assert "markdown" in response.json()
       assert "urls" not in response.json()  # No batch response
   
   async def test_batch_urls_sync_mode():
       """Test batch processing with immediate response"""
       response = await client.post("/api/markdown", json={
           "urls": ["https://example.com/1", "https://example.com/2"],
           "async": False
       })
       assert response.status_code == 200
       assert len(response.json()["results"]) == 2
       assert all(r["status"] == "completed" for r in response.json()["results"])
   
   async def test_batch_urls_async_mode():
       """Test batch processing with background jobs"""
       response = await client.post("/api/markdown", json={
           "urls": ["https://example.com/1", "https://example.com/2"],
           "async": True
       })
       assert response.status_code == 202  # Accepted
       assert "job_id" in response.json()
       assert all(r["status"] == "processing" for r in response.json()["results"])
   
   async def test_callback_webhook():
       """Test webhook callback on batch completion"""
       with mock_webhook_server() as webhook:
           response = await client.post("/api/markdown", json={
               "urls": ["https://example.com/1"],
               "async": True,
               "callback_url": webhook.url,
               "callback_headers": {"X-Test": "123"}
           })
           
           # Wait for callback
           callback_data = await webhook.wait_for_call(timeout=60)
           assert callback_data["job_id"] == response.json()["job_id"]
           assert callback_data["status"] == "completed"
           assert "stats" in callback_data
   ```

2. **Create test fixtures and mocks**
   - Mock crawler responses for predictable testing
   - Mock storage service for fast tests
   - Create test webhook server for callback testing

3. **Run existing tests to ensure no regression**
   ```bash
   pytest tests/test_api.py::test_markdown_endpoint -v
   ```

### Phase 1: URL Prediction System

1. **Create `core/url_predictor.py`**
   ```python
   def predict_storage_urls(url, user_email, include_screenshot=False):
       """Generate predictable storage URLs before crawling"""
       # Use existing filename generation logic
       # Return dict with markdown_url, json_url, screenshot_url
   ```

2. **Pre-create placeholder files**
   ```python
   async def create_placeholder_files(urls, user_email):
       """Create empty files with 'processing' status"""
       # Create .md.processing, .json.processing files
       # These will be replaced when crawl completes
   ```

### Phase 2: Batch Processing Logic
1. **Update `/md` endpoint to detect batch mode**
   ```python
   # In markdown_extraction()
   urls = data.get('urls') or [data.get('url')]
   is_batch = len(urls) > 1
   async_mode = data.get('async', True) and is_batch
   ```

2. **Create parallel processor**
   ```python
   async def process_urls_parallel(urls, options, user_email):
       """Process multiple URLs in parallel"""
       tasks = []
       for url in urls:
           task = asyncio.create_task(
               process_single_url(url, options, user_email)
           )
           tasks.append(task)
       
       # Use asyncio.gather for parallel execution
       results = await asyncio.gather(*tasks, return_exceptions=True)
       return results
   ```

### Phase 3: Background Job System
1. **Create job tracking**
   ```python
   class BatchJob:
       job_id: str
       urls: List[str]
       status: Dict[str, str]  # url -> status mapping
       created_at: datetime
       completed_at: Optional[datetime]
       callback_url: Optional[str]
       callback_headers: Optional[Dict[str, str]]
       stats: Dict[str, Any]  # Performance metrics
   ```

2. **Integrate with existing job system**
   - Use Redis/Firestore for job storage
   - Update job status as each URL completes
   - Provide status endpoint for polling

3. **Implement callback system**
   ```python
   async def trigger_callback(job: BatchJob):
       """Send webhook when batch completes"""
       if not job.callback_url:
           return
       
       payload = {
           "job_id": job.job_id,
           "status": "completed",
           "stats": {
               "total_urls": len(job.urls),
               "successful": sum(1 for s in job.status.values() if s == "completed"),
               "failed": sum(1 for s in job.status.values() if s == "failed"),
               "total_time": (job.completed_at - job.created_at).total_seconds(),
               "average_time_per_url": job.stats.get("avg_time"),
               "total_words": job.stats.get("total_words"),
               "total_characters": job.stats.get("total_chars")
           },
           "results": [
               {
                   "url": url,
                   "status": status,
                   "markdown_url": job.results[url].get("markdown_url"),
                   "word_count": job.results[url].get("word_count"),
                   "error": job.results[url].get("error")
               }
               for url, status in job.status.items()
           ],
           "collated_url": job.collated_url if job.collate else None
       }
       
       headers = {"Content-Type": "application/json"}
       headers.update(job.callback_headers or {})
       
       async with aiohttp.ClientSession() as session:
           try:
               await session.post(
                   job.callback_url,
                   json=payload,
                   headers=headers,
                   timeout=30
               )
           except Exception as e:
               logger.error(f"Callback failed for job {job.job_id}: {e}")
   ```


### Phase 4: Collation Feature
1. **Create collation function**
   ```python
   async def collate_markdown_files(file_paths, output_path):
       """Merge multiple markdown files into one"""
       # Add headers for each source
       # Preserve citations
       # Create table of contents
   ```

2. **Trigger collation after all complete**
   ```python
   if all_complete and collate_requested:
       await collate_markdown_files(results, collated_path)
   ```

### Phase 5: Error Handling & Resilience
1. **Partial failure handling**
   - Continue processing other URLs if one fails
   - Mark individual URL status as "failed"
   - Include error details in response

2. **Timeout management**
   - Set per-URL timeout (30s default)
   - Set batch timeout (5 minutes default)
   - Clean up stale jobs

## File Changes Required

### 1. `web/routes/apis/api.py`
- Modify `markdown_extraction()` to handle URL lists
- Add batch detection logic
- Implement immediate response for async mode
- Create background task for batch processing

### 2. `core/batch_processor.py` (NEW)
- Parallel URL processing logic
- Progress tracking
- Result collation
- Error aggregation

### 3. `core/url_predictor.py` (NEW)
- Predictable URL generation
- Placeholder file creation
- Storage path management

### 4. `web/routes/apis/jobs.py`
- Add batch job status endpoint
- Provide progress updates
- Handle job cancellation

### 5. `core/storage_service.py`
- Add `create_placeholder()` method
- Add `replace_placeholder()` method
- Add `collate_files()` method

## Technical Considerations

### Concurrency Limits
- Default: 5 concurrent crawls per batch
- Configurable via environment variable
- Prevent resource exhaustion

### Rate Limiting
- Per-user batch limits (e.g., 50 URLs/minute)
- Prevent abuse while allowing legitimate use

### Progress Reporting
```json
{
  "job_id": "batch_1234567890",
  "total": 10,
  "completed": 7,
  "failed": 1,
  "processing": 2,
  "results": {...}
}
```

### Backward Compatibility
- Single URL requests work exactly as before
- No breaking changes to existing API
- New features are opt-in

## Example Usage

### Simple Batch Request
```bash
curl -X POST http://localhost:8080/api/markdown \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://docs.python.org/3/tutorial/index.html",
      "https://docs.python.org/3/tutorial/introduction.html",
      "https://docs.python.org/3/tutorial/controlflow.html"
    ],
    "filter": "pruning"
  }'
```

### With Collation
```bash
curl -X POST http://localhost:8080/api/markdown \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [...],
    "collate": true,
    "collate_options": {
      "title": "Python Tutorial Collection",
      "add_toc": true,
      "add_source_headers": true
    }
  }'
```

### With Webhook Callback
```bash
curl -X POST http://localhost:8080/api/markdown \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://docs.python.org/3/tutorial/index.html",
      "https://docs.python.org/3/tutorial/introduction.html"
    ],
    "async": true,
    "callback_url": "https://myapp.com/webhook/gnosis-complete",
    "callback_headers": {
      "Authorization": "Bearer my-webhook-secret",
      "X-Custom-Header": "value"
    }
  }'

# Immediate response:
{
  "success": true,
  "job_id": "batch_1234567890",
  "status_url": "/api/jobs/batch_1234567890",
  "results": [...]
}

# Later webhook payload to your callback_url:
{
  "job_id": "batch_1234567890",
  "status": "completed",
  "stats": {
    "total_urls": 2,
    "successful": 2,
    "failed": 0,
    "total_time": 4.5,
    "average_time_per_url": 2.25,
    "total_words": 5234,
    "total_characters": 28456
  },
  "results": [
    {
      "url": "https://docs.python.org/3/tutorial/index.html",
      "status": "completed",
      "markdown_url": "/storage/users/.../python_org_abc123.md",
      "word_count": 2156
    },
    {
      "url": "https://docs.python.org/3/tutorial/introduction.html",
      "status": "completed",
      "markdown_url": "/storage/users/.../python_org_def456.md",
      "word_count": 3078
    }
  ]
}
```


## Testing Strategy

1. **Unit Tests**
   - URL prediction accuracy
   - Parallel processing logic
   - Collation formatting

2. **Integration Tests**
   - Single URL (backward compatibility)
   - Small batch (2-3 URLs)
   - Large batch (20+ URLs)
   - Mixed success/failure scenarios

3. **Load Tests**
   - Concurrent batch requests
   - Resource usage monitoring
   - Rate limit enforcement

## Rollout Plan

1. **Phase 0**: Write comprehensive test suite (1 day)
   - All tests must pass with current single-URL implementation
   - Mock infrastructure for fast testing
   - Webhook testing framework

2. **Phase 1**: URL prediction and placeholder system (1 day)
   - Tests for URL prediction accuracy
   - Tests for placeholder creation/replacement

3. **Phase 2**: Basic batch processing (2 days)
   - Tests for parallel execution
   - Tests for error handling in batch mode

4. **Phase 3**: Async mode with job tracking (2 days)
   - Tests for job creation and status
   - Tests for callback webhooks
   - Tests for partial failures

5. **Phase 4**: Collation feature (1 day)
   - Tests for merging multiple files
   - Tests for citation preservation

6. **Phase 5**: Integration testing and optimization (2 days)
   - End-to-end tests with real crawls
   - Performance benchmarking
   - Load testing

Total estimate: 9 days of development (including test-first approach)


## Success Metrics

- Batch requests complete 3-5x faster than sequential
- 95% of predictable URLs are correct
- Job status updates within 100ms
- System handles 100 concurrent URLs without degradation
- Zero impact on single-URL performance
- Webhook callbacks delivered within 5 seconds of completion
- 99% callback delivery success rate
- All existing tests continue to pass (backward compatibility)

## Test-First Development Benefits

1. **Confidence in Changes** - Know immediately if something breaks
2. **Better API Design** - Writing tests first improves the API interface
3. **Documentation** - Tests serve as usage examples
4. **Regression Prevention** - Catch issues before production
5. **Faster Development** - Less debugging, more building

## Callback Webhook Benefits

1. **No Polling Required** - System notifies you when done
2. **Integration Friendly** - Works with Zapier, Make, n8n, etc.
3. **Performance Stats** - Get metrics on crawl performance
4. **Error Handling** - Know which URLs failed and why
5. **Workflow Automation** - Trigger next steps automatically


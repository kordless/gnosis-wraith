# Phase 2: V2 Endpoints Migration Plan

## Overview
Migrate existing /crawl endpoints to /v2 with smart hybrid sync/async support and direct function calls (not API endpoints).

## Timeline: Week 2-3 (10-14 days)

## 2.1 Core Function Extraction

### File: `core/crawl_functions.py` (NEW - Minimal file addition)

Extract core crawling functions that tools will call directly:

```python
"""
Core crawling functions for direct tool invocation.
These functions are called by MCP tools, not through HTTP endpoints.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from core.crawler import CrawlerService
from core.browser_session import session_manager
from core.storage_service import storage_service

logger = logging.getLogger("gnosis_wraith")

# Smart sync/async threshold (in seconds)
ASYNC_THRESHOLD = 3.0

async def estimate_crawl_time(url: str, options: Dict[str, Any] = None) -> float:
    """
    Estimate how long a crawl will take based on URL and options.
    
    Returns:
        Estimated time in seconds
    """
    # Base time for simple page load
    base_time = 1.5
    
    # Add time for options
    if options:
        if options.get('javascript', False):
            base_time += 2.0
        if options.get('screenshot', False):
            base_time += 1.0
        if options.get('full_content', False):
            base_time += 0.5
        if options.get('depth', 0) > 0:
            base_time *= (options['depth'] + 1)
    
    return base_time

async def crawl_url_direct(
    url: str,
    options: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Direct crawl function that tools call.
    Automatically chooses sync or async based on complexity.
    
    Args:
        url: URL to crawl
        options: Crawl options (javascript, screenshot, etc.)
        session_id: Optional browser session to reuse
        user_id: Optional user ID for storage
        
    Returns:
        Crawl results or job info
    """
    try:
        # Estimate crawl time
        estimated_time = await estimate_crawl_time(url, options)
        logger.info(f"Estimated crawl time for {url}: {estimated_time}s")
        
        # Decide sync vs async
        if estimated_time < ASYNC_THRESHOLD:
            # Synchronous crawl
            return await _crawl_sync(url, options, session_id, user_id)
        else:
            # Asynchronous job
            return await _crawl_async(url, options, session_id, user_id)
            
    except Exception as e:
        logger.error(f"Crawl error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

async def _crawl_sync(
    url: str,
    options: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Execute synchronous crawl and return results immediately."""
    
    # Get or create crawler
    crawler = CrawlerService()
    
    # Reuse session if provided
    if session_id:
        browser = await session_manager.get_session(session_id)
        if browser:
            crawler.browser = browser
    
    # Execute crawl
    result = await crawler.crawl(url, options or {})
    
    # Store result if user_id provided
    if user_id and result.get('success'):
        await storage_service.store_crawl_result(
            user_id=user_id,
            url=url,
            result=result,
            metadata={
                'sync': True,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    # Create new session if browser was created
    if crawler.browser and not session_id:
        new_session_id = f"session_{datetime.now().timestamp()}"
        await session_manager.create_session(new_session_id, crawler.browser)
        result['session_id'] = new_session_id
        result['session_data'] = {'url': url, 'state': 'ready'}
    
    return result

async def _crawl_async(
    url: str,
    options: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create async job and return job info."""
    
    # Import job system
    from core.job_system import job_manager
    
    # Create job
    job = await job_manager.create_job(
        type='crawl',
        payload={
            'url': url,
            'options': options or {},
            'session_id': session_id,
            'user_id': user_id
        }
    )
    
    return {
        "success": True,
        "async": True,
        "job_id": job['id'],
        "status": "pending",
        "check_url": f"/v2/jobs/{job['id']}",
        "estimated_time": await estimate_crawl_time(url, options),
        "message": "Crawl job created. Check status with job_id."
    }

async def get_job_status_direct(job_id: str) -> Dict[str, Any]:
    """Get job status directly."""
    from core.job_system import job_manager
    
    job = await job_manager.get_job(job_id)
    if not job:
        return {
            "success": False,
            "error": "Job not found"
        }
    
    return {
        "success": True,
        "job_id": job_id,
        "status": job['status'],
        "progress": job.get('progress', 0),
        "result": job.get('result') if job['status'] == 'completed' else None,
        "error": job.get('error') if job['status'] == 'failed' else None
    }

async def search_crawls_direct(
    query: str,
    user_id: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """Search stored crawl results."""
    
    results = await storage_service.search_crawls(
        query=query,
        user_id=user_id,
        limit=limit
    )
    
    return {
        "success": True,
        "count": len(results),
        "results": results
    }
```

## 2.2 MCP Tool Implementations

### File: `ai/tools/web_crawling.py` (NEW)

Create descriptive MCP tools that call the core functions:

```python
"""
Web crawling MCP tools with descriptive names.
These tools call core functions directly, not HTTP endpoints.
"""

from typing import Dict, Any, Optional
from ai.tools.decorators import tool
from core.crawl_functions import (
    crawl_url_direct,
    get_job_status_direct,
    search_crawls_direct,
    estimate_crawl_time
)

@tool(
    name="crawl_webpage_with_smart_execution",
    description="Crawl a webpage intelligently - automatically chooses sync (fast) or async (slow) execution based on complexity"
)
async def crawl_webpage_with_smart_execution(
    url: str,
    javascript: bool = False,
    screenshot: bool = False,
    full_content: bool = False,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Crawl a webpage with smart sync/async execution.
    
    Args:
        url: The URL to crawl
        javascript: Enable JavaScript rendering (slower)
        screenshot: Capture screenshot (slower)
        full_content: Extract all content including hidden elements
        session_id: Reuse browser session from previous crawl
        
    Returns:
        Either immediate results (sync) or job info (async)
    """
    options = {
        'javascript': javascript,
        'screenshot': screenshot,
        'full_content': full_content
    }
    
    # Remove false options to keep payload clean
    options = {k: v for k, v in options.items() if v}
    
    return await crawl_url_direct(
        url=url,
        options=options,
        session_id=session_id
    )

@tool(
    name="crawl_website_with_depth_control",
    description="Crawl multiple pages from a website following links to specified depth"
)
async def crawl_website_with_depth_control(
    url: str,
    depth: int = 1,
    max_pages: int = 10,
    follow_pattern: Optional[str] = None,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Crawl a website with depth control.
    
    Args:
        url: Starting URL
        depth: How many levels deep to follow links (1-3)
        max_pages: Maximum number of pages to crawl
        follow_pattern: Regex pattern for URLs to follow
        session_id: Reuse browser session
        
    Returns:
        Job info (always async due to complexity)
    """
    options = {
        'depth': min(depth, 3),  # Cap at 3 for safety
        'max_pages': min(max_pages, 50),  # Cap at 50
        'follow_pattern': follow_pattern,
        'javascript': True  # Usually needed for modern sites
    }
    
    return await crawl_url_direct(
        url=url,
        options=options,
        session_id=session_id
    )

@tool(
    name="check_crawl_job_status",
    description="Check the status of an asynchronous crawl job"
)
async def check_crawl_job_status(job_id: str) -> Dict[str, Any]:
    """
    Check status of a crawl job.
    
    Args:
        job_id: The job ID returned from async crawl
        
    Returns:
        Job status and results if completed
    """
    return await get_job_status_direct(job_id)

@tool(
    name="search_previous_crawl_results",
    description="Search through previously crawled pages by content or URL"
)
async def search_previous_crawl_results(
    query: str,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Search stored crawl results.
    
    Args:
        query: Search query (searches content and URLs)
        limit: Maximum results to return
        
    Returns:
        Matching crawl results
    """
    return await search_crawls_direct(
        query=query,
        limit=limit
    )

@tool(
    name="estimate_crawl_complexity",
    description="Estimate how long a crawl will take based on options"
)
async def estimate_crawl_complexity(
    url: str,
    javascript: bool = False,
    screenshot: bool = False,
    depth: int = 0
) -> Dict[str, Any]:
    """
    Estimate crawl time to help decide sync vs async.
    
    Args:
        url: URL to analyze
        javascript: If JavaScript rendering is needed
        screenshot: If screenshot capture is needed
        depth: Crawl depth for multi-page crawls
        
    Returns:
        Time estimate and execution recommendation
    """
    options = {
        'javascript': javascript,
        'screenshot': screenshot,
        'depth': depth
    }
    
    estimated_time = await estimate_crawl_time(url, options)
    
    return {
        "success": True,
        "url": url,
        "estimated_seconds": estimated_time,
        "recommended_mode": "sync" if estimated_time < 3.0 else "async",
        "complexity": "simple" if estimated_time < 2 else "moderate" if estimated_time < 5 else "complex"
    }
```

### File: `ai/tools/content_processing.py` (NEW)

Content processing tools:

```python
"""
Content processing MCP tools.
"""

from typing import Dict, Any, Optional, List
from ai.tools.decorators import tool
import logging

logger = logging.getLogger("gnosis_wraith")

@tool(
    name="extract_structured_data_with_schema",
    description="Extract structured data from crawled content using a schema"
)
async def extract_structured_data_with_schema(
    content: str,
    schema: Dict[str, str],
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract structured data based on schema.
    
    Args:
        content: The content to process
        schema: Dictionary defining fields to extract
        session_id: Optional session for context
        
    Returns:
        Extracted structured data
    """
    # This would integrate with AI extraction
    from ai.anthropic import process_with_anthropic
    import os
    
    prompt = f"Extract the following fields from this content:\n{schema}\n\nContent:\n{content}"
    
    try:
        # Use AI to extract
        result = await process_with_anthropic(
            prompt,
            os.environ.get('ANTHROPIC_API_KEY')
        )
        
        return {
            "success": True,
            "extracted_data": result,
            "schema_used": schema
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@tool(
    name="convert_html_to_clean_markdown",
    description="Convert HTML content to clean, readable Markdown"
)
async def convert_html_to_clean_markdown(
    html: str,
    preserve_links: bool = True,
    preserve_images: bool = True
) -> Dict[str, Any]:
    """
    Convert HTML to Markdown.
    
    Args:
        html: HTML content to convert
        preserve_links: Keep hyperlinks in output
        preserve_images: Keep image references
        
    Returns:
        Clean Markdown content
    """
    from core.markdown_generation import MarkdownGenerator
    
    generator = MarkdownGenerator()
    markdown = await generator.convert(
        html,
        options={
            'preserve_links': preserve_links,
            'preserve_images': preserve_images
        }
    )
    
    return {
        "success": True,
        "markdown": markdown,
        "length": len(markdown)
    }

@tool(
    name="analyze_content_sentiment_and_entities",
    description="Analyze content for sentiment, entities, and key topics"
)
async def analyze_content_sentiment_and_entities(
    content: str,
    analyze_sentiment: bool = True,
    extract_entities: bool = True,
    identify_topics: bool = True
) -> Dict[str, Any]:
    """
    Perform content analysis.
    
    Args:
        content: Text content to analyze
        analyze_sentiment: Perform sentiment analysis
        extract_entities: Extract named entities
        identify_topics: Identify main topics
        
    Returns:
        Analysis results
    """
    # This would integrate with AI analysis
    results = {
        "success": True,
        "content_length": len(content)
    }
    
    if analyze_sentiment:
        # Placeholder for sentiment analysis
        results["sentiment"] = {
            "score": 0.7,
            "label": "positive"
        }
    
    if extract_entities:
        # Placeholder for entity extraction
        results["entities"] = [
            {"text": "Example Corp", "type": "ORG"},
            {"text": "John Doe", "type": "PERSON"}
        ]
    
    if identify_topics:
        # Placeholder for topic identification
        results["topics"] = ["technology", "business"]
    
    return results

@tool(
    name="summarize_long_text_intelligently",
    description="Create concise summaries of long text content"
)
async def summarize_long_text_intelligently(
    text: str,
    max_length: int = 500,
    style: str = "bullet_points"
) -> Dict[str, Any]:
    """
    Summarize long text content.
    
    Args:
        text: Text to summarize
        max_length: Maximum summary length
        style: Summary style (bullet_points, paragraph, key_points)
        
    Returns:
        Summary content
    """
    from ai.anthropic import process_with_anthropic
    import os
    
    style_prompts = {
        "bullet_points": "Summarize in bullet points:",
        "paragraph": "Summarize in a concise paragraph:",
        "key_points": "Extract the key points:"
    }
    
    prompt = f"{style_prompts.get(style, style_prompts['bullet_points'])}\n\n{text[:3000]}"
    
    try:
        summary = await process_with_anthropic(
            prompt,
            os.environ.get('ANTHROPIC_API_KEY')
        )
        
        return {
            "success": True,
            "summary": summary,
            "original_length": len(text),
            "summary_length": len(summary),
            "compression_ratio": len(summary) / len(text)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

## 2.3 V2 API Endpoints

### File: `web/routes/api_v2.py` (UPDATE)

Update existing V2 endpoints to use the new functions:

```python
"""
V2 API endpoints that wrap the core functions.
These are for HTTP API access, while tools call functions directly.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from pydantic import BaseModel, HttpUrl
from core.crawl_functions import (
    crawl_url_direct,
    get_job_status_direct,
    search_crawls_direct
)

router = APIRouter(prefix="/v2", tags=["v2"])

class CrawlRequest(BaseModel):
    url: HttpUrl
    javascript: bool = False
    screenshot: bool = False
    full_content: bool = False
    depth: int = 0
    max_pages: int = 10
    session_id: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    limit: int = 10

@router.post("/crawl")
async def crawl_endpoint(request: CrawlRequest) -> Dict[str, Any]:
    """
    V2 crawl endpoint with smart sync/async execution.
    
    Automatically chooses between:
    - Synchronous: Returns results immediately for simple crawls
    - Asynchronous: Returns job ID for complex crawls
    """
    options = {
        "javascript": request.javascript,
        "screenshot": request.screenshot,
        "full_content": request.full_content
    }
    
    if request.depth > 0:
        options["depth"] = request.depth
        options["max_pages"] = request.max_pages
    
    # Call the core function
    result = await crawl_url_direct(
        url=str(request.url),
        options=options,
        session_id=request.session_id
    )
    
    return result

@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str) -> Dict[str, Any]:
    """Get status of an async crawl job."""
    return await get_job_status_direct(job_id)

@router.post("/search")
async def search_crawls(request: SearchRequest) -> Dict[str, Any]:
    """Search through stored crawl results."""
    return await search_crawls_direct(
        query=request.query,
        limit=request.limit
    )

@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0",
        "features": [
            "smart-sync-async",
            "session-persistence",
            "job-management",
            "content-processing"
        ]
    }
```

## 2.4 Migration Strategy

### Steps to migrate existing code:

1. **Update app.py** to include v2 router:
```python
# In app.py
from web.routes import api_v2

# Add v2 router
app.include_router(api_v2.router)
```

2. **Update existing endpoints** to detect v2 features:
```python
# In existing endpoints
if request.headers.get("X-API-Version") == "2":
    # Redirect to v2 logic
    return await crawl_url_direct(...)
```

3. **Add backwards compatibility** layer:
```python
# Keep old endpoints working
@router.post("/crawl")
async def legacy_crawl(request):
    # Convert to v2 format
    return await crawl_endpoint(request)
```

## 2.5 Testing the Migration

### File: `tests/test_v2_migration.py`

```python
import pytest
from httpx import AsyncClient
from app import app

@pytest.mark.asyncio
async def test_v2_smart_sync():
    """Test synchronous execution for simple crawls."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/v2/crawl", json={
            "url": "https://example.com",
            "javascript": False
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "async" not in data  # Should be sync

@pytest.mark.asyncio
async def test_v2_smart_async():
    """Test asynchronous execution for complex crawls."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/v2/crawl", json={
            "url": "https://example.com",
            "javascript": True,
            "screenshot": True,
            "depth": 2
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["async"] is True
        assert "job_id" in data

@pytest.mark.asyncio
async def test_v2_job_status():
    """Test job status checking."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create async job
        response = await client.post("/v2/crawl", json={
            "url": "https://example.com",
            "depth": 2
        })
        
        job_id = response.json()["job_id"]
        
        # Check status
        status_response = await client.get(f"/v2/jobs/{job_id}")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert status_data["job_id"] == job_id
        assert status_data["status"] in ["pending", "running", "completed", "failed"]
```

## Deliverables

1. **Core crawl functions** that tools call directly
2. **MCP tool implementations** with descriptive names
3. **Updated V2 endpoints** with smart sync/async
4. **Migration compatibility** for existing code
5. **Test suite** for v2 features

## Success Criteria

- [ ] Tools call functions directly, not endpoints
- [ ] Smart sync/async works based on complexity
- [ ] Session persistence works between calls
- [ ] Job management for async operations
- [ ] All existing endpoints still work
- [ ] V2 endpoints are faster and more efficient

## Next Steps

After Phase 2 completion:
- Phase 3: Integration testing with all components
- Phase 4: UI updates for Claude Desktop
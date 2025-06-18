"""
Core crawling functions for direct tool invocation.
These functions are called by MCP tools, not through HTTP endpoints.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
from core.crawler import crawl_url
from core.browser_session import session_manager
from core.enhanced_storage_service import EnhancedStorageService
from core.job_manager import JobManager


logger = logging.getLogger("gnosis_wraith")

# Smart sync/async threshold (in seconds)
# Increased to allow JavaScript tests to run synchronously
ASYNC_THRESHOLD = 5.0


# Initialize services
storage_service = EnhancedStorageService()
job_manager = JobManager()

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
        # Check if force_sync is requested
        force_sync = options.get('force_sync', False) if options else False
        
        # Estimate crawl time
        estimated_time = await estimate_crawl_time(url, options)
        logger.info(f"Estimated crawl time for {url}: {estimated_time}s")
        
        # Decide sync vs async
        if force_sync or estimated_time < ASYNC_THRESHOLD:
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
    
    # Prepare crawl options
    crawl_options = options or {}
    
    # Execute crawl using the crawl_url function
    raw_result = await crawl_url(
        url=url,
        javascript_enabled=crawl_options.get('javascript', False),
        take_screenshot=crawl_options.get('screenshot', False),
        screenshot_mode=crawl_options.get('screenshot_mode', 'full'),
        ocr_extraction=crawl_options.get('ocr_extraction', True),
        markdown_extraction=crawl_options.get('markdown_extraction', 'enhanced'),
        llm_provider=crawl_options.get('llm_provider'),
        llm_token=crawl_options.get('llm_token'),
        email=user_id
    )
    
    # Transform result to V2 API format
    # Check if crawl_url returned an error
    if 'error' in raw_result:
        return {
            "success": False,
            "error": raw_result.get('error'),
            "message": raw_result.get('title', 'Crawl failed')
        }
    
    # Build successful result in V2 format
    result = {
        "success": True,
        "url": raw_result.get('url', url),
        "title": raw_result.get('title', ''),
        "javascript_enabled": raw_result.get('javascript_enabled', False),
        "content": raw_result.get('filtered_content', ''),
    }
    
    # Add optional fields based on response format
    response_format = crawl_options.get('response_format', 'full')
    
    if response_format == 'full':
        result['html_content'] = raw_result.get('html_content', '')
        result['markdown_content'] = raw_result.get('markdown_content', '')
        result['extracted_text'] = raw_result.get('extracted_text', '')
        
    if response_format == 'minimal':
        # Just content and title
        pass
        
    if response_format == 'llm':
        # For LLM format, use the most concise content
        result['content'] = raw_result.get('fit_markdown_content') or raw_result.get('markdown_content') or raw_result.get('filtered_content', '')
    
    # Add screenshot if present
    if raw_result.get('screenshot'):
        result['screenshot'] = raw_result['screenshot']
    
    # TODO: Store result if user_id provided
    # Storage integration needs to be implemented
    # if user_id and result.get('success'):
    #     storage_result = await storage_service.store_crawl_result(
    #         user_id=user_id,
    #         url=url,
    #         result=result,
    #         metadata={
    #             'sync': True,
    #             'timestamp': datetime.now().isoformat(),
    #             'options': options
    #         }
    #     )
    #     result['storage_id'] = storage_result.get('id')
    
    # Session management handled within crawl_url function
    # Add session info if needed
    if session_id:
        result['session_id'] = session_id
    
    return result

async def _crawl_async(
    url: str,
    options: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create async job and return job info."""
    
    # Create job
    job = await job_manager.create_job(
        job_type='crawl',
        metadata={
            'url': url,
            'options': options or {},
            'session_id': session_id,
            'user_id': user_id
        }
    )

    
    return {
        "success": True,
        "async": True,
        "job_id": job,
        "status": "pending",
        "check_url": f"/v2/jobs/{job}",
        "estimated_time": await estimate_crawl_time(url, options),
        "message": "Crawl job created. Check status with job_id."
    }


async def get_job_status_direct(job_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """Get job status directly."""
    
    job = await job_manager.get_job(job_id)

    if not job:
        return {
            "success": False,
            "error": "Job not found"
        }
    
    response = {
        "success": True,
        "job_id": job_id,
        "status": job['status'],
        "progress": job.get('progress', 0),
        "created_at": job.get('created_at'),
        "updated_at": job.get('updated_at')
    }
    
    # Include result if completed
    if job['status'] == 'completed':
        response['result'] = job.get('result')
    elif job['status'] == 'failed':
        response['error'] = job.get('error')
    
    return response

async def search_crawls_direct(
    query: str,
    user_id: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
) -> Dict[str, Any]:
    """Search stored crawl results."""
    
    results = await storage_service.search_crawls(
        query=query,
        user_id=user_id,
        limit=limit,
        offset=offset
    )
    
    return {
        "success": True,
        "query": query,
        "count": len(results.get('items', [])),
        "total": results.get('total', 0),
        "results": results.get('items', []),
        "limit": limit,
        "offset": offset
    }

async def analyze_website_structure(
    url: str,
    max_depth: int = 2,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze website structure by crawling multiple pages.
    
    Args:
        url: Starting URL
        max_depth: How deep to crawl
        session_id: Optional browser session
        
    Returns:
        Website structure analysis
    """
    try:
        crawler = CrawlerService()
        
        # Reuse session if available
        if session_id:
            browser = await session_manager.get_session(session_id)
            if browser:
                crawler.set_browser(browser)
        
        # Crawl with structure analysis
        structure = await crawler.analyze_structure(url, max_depth)
        
        return {
            "success": True,
            "url": url,
            "structure": structure,
            "pages_analyzed": len(structure.get('pages', [])),
            "depth_reached": structure.get('max_depth_reached', 0)
        }
        
    except Exception as e:
        logger.error(f"Structure analysis error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

async def batch_crawl_urls(
    urls: List[str],
    options: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Crawl multiple URLs in batch.
    Always returns a job since this is complex.
    
    Args:
        urls: List of URLs to crawl
        options: Crawl options for all URLs
        user_id: Optional user ID
        
    Returns:
        Job information
    """
    # Create batch job
    job = await job_manager.create_job(
        job_type='batch_crawl',
        metadata={
            'urls': urls,
            'options': options or {},
            'user_id': user_id,
            'total_urls': len(urls)
        }
    )

    
    # Estimate total time
    total_time = sum([
        await estimate_crawl_time(url, options) 
        for url in urls[:5]  # Sample first 5
    ]) * (len(urls) / min(5, len(urls)))
    
    return {
        "success": True,
        "async": True,
        "job_id": job,
        "status": "pending",
        "check_url": f"/v2/jobs/{job}",
        "estimated_time": total_time,
        "total_urls": len(urls),
        "message": f"Batch crawl job created for {len(urls)} URLs"
    }

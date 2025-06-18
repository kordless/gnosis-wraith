"""
Web crawling MCP tools with descriptive names.
These tools call core functions directly, not HTTP endpoints.
"""

from typing import Dict, Any, Optional, List
from ai.tools.decorators import tool
from core.crawl_functions import (
    crawl_url_direct,
    get_job_status_direct,
    search_crawls_direct,
    estimate_crawl_time,
    analyze_website_structure,
    batch_crawl_urls
)
import logging

logger = logging.getLogger("gnosis_wraith")

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
    
    logger.info(f"Tool crawl_webpage_with_smart_execution called for {url}")
    
    result = await crawl_url_direct(
        url=url,
        options=options,
        session_id=session_id
    )
    
    # Add tool metadata
    result['tool_name'] = 'crawl_webpage_with_smart_execution'
    return result

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
    
    logger.info(f"Tool crawl_website_with_depth_control called for {url} with depth {depth}")
    
    result = await crawl_url_direct(
        url=url,
        options=options,
        session_id=session_id
    )
    
    result['tool_name'] = 'crawl_website_with_depth_control'
    return result

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
    logger.info(f"Tool check_crawl_job_status called for job {job_id}")
    
    result = await get_job_status_direct(job_id)
    result['tool_name'] = 'check_crawl_job_status'
    return result

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
    logger.info(f"Tool search_previous_crawl_results called with query: {query}")
    
    result = await search_crawls_direct(
        query=query,
        limit=limit
    )
    
    result['tool_name'] = 'search_previous_crawl_results'
    return result

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
        "tool_name": "estimate_crawl_complexity",
        "url": url,
        "estimated_seconds": estimated_time,
        "recommended_mode": "sync" if estimated_time < 3.0 else "async",
        "complexity": "simple" if estimated_time < 2 else "moderate" if estimated_time < 5 else "complex"
    }

@tool(
    name="analyze_website_structure",
    description="Analyze the structure and organization of a website"
)
async def analyze_website_structure_tool(
    url: str,
    max_depth: int = 2,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze website structure.
    
    Args:
        url: Starting URL
        max_depth: How deep to analyze (default 2)
        session_id: Reuse browser session
        
    Returns:
        Website structure analysis
    """
    logger.info(f"Tool analyze_website_structure called for {url}")
    
    result = await analyze_website_structure(
        url=url,
        max_depth=max_depth,
        session_id=session_id
    )
    
    result['tool_name'] = 'analyze_website_structure'
    return result

@tool(
    name="batch_crawl_multiple_urls",
    description="Crawl multiple URLs efficiently in a batch job"
)
async def batch_crawl_multiple_urls(
    urls: List[str],
    javascript: bool = False,
    screenshot: bool = False
) -> Dict[str, Any]:
    """
    Batch crawl multiple URLs.
    
    Args:
        urls: List of URLs to crawl
        javascript: Enable JavaScript for all URLs
        screenshot: Capture screenshots for all URLs
        
    Returns:
        Batch job information
    """
    options = {
        'javascript': javascript,
        'screenshot': screenshot
    }
    
    # Remove false options
    options = {k: v for k, v in options.items() if v}
    
    logger.info(f"Tool batch_crawl_multiple_urls called for {len(urls)} URLs")
    
    result = await batch_crawl_urls(
        urls=urls,
        options=options
    )
    
    result['tool_name'] = 'batch_crawl_multiple_urls'
    return result

@tool(
    name="extract_all_links_from_webpage",
    description="Extract all hyperlinks from a webpage"
)
async def extract_all_links_from_webpage(
    url: str,
    internal_only: bool = False,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract all links from a webpage.
    
    Args:
        url: URL to extract links from
        internal_only: Only return links from the same domain
        session_id: Reuse browser session
        
    Returns:
        List of extracted links
    """
    options = {
        'extract_links': True,
        'javascript': True,  # Many sites need JS to show all links
        'full_content': False
    }
    
    result = await crawl_url_direct(
        url=url,
        options=options,
        session_id=session_id
    )
    
    if result.get('success') and not result.get('async'):
        # Process links if sync result
        links = result.get('links', [])
        
        if internal_only and links:
            from urllib.parse import urlparse
            base_domain = urlparse(url).netloc
            links = [link for link in links if urlparse(link).netloc == base_domain]
        
        return {
            "success": True,
            "tool_name": "extract_all_links_from_webpage",
            "url": url,
            "total_links": len(links),
            "links": links,
            "internal_only": internal_only
        }
    
    # Return async job info or error
    result['tool_name'] = 'extract_all_links_from_webpage'
    return result

def get_web_crawling_tools():
    """Get all web crawling tools for registration."""
    return [
        crawl_webpage_with_smart_execution,
        crawl_website_with_depth_control,
        check_crawl_job_status,
        search_previous_crawl_results,
        estimate_crawl_complexity,
        analyze_website_structure_tool,
        batch_crawl_multiple_urls,
        extract_all_links_from_webpage
    ]
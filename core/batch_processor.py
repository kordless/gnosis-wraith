"""
Batch Processor for Parallel URL Crawling

Handles parallel processing of multiple URLs with progress tracking,
error handling, and result collation.
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
import aiohttp
import traceback

from core.crawler import crawl_url
from core.markdown_generation import (
    DefaultMarkdownGenerator,
    PruningContentFilter,
    SimpleBM25ContentFilter
)
from core.storage_service import get_storage_service
from core.url_predictor import URLPredictor

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Processes multiple URLs in parallel with configurable concurrency."""
    
    def __init__(self, 
                 user_email: str,
                 max_concurrent: int = 5,
                 timeout_per_url: int = 30):
        """
        Initialize the batch processor.
        
        Args:
            user_email: User's email for storage partitioning
            max_concurrent: Maximum number of concurrent crawls
            timeout_per_url: Timeout in seconds for each URL crawl
        """
        self.user_email = user_email
        self.max_concurrent = max_concurrent
        self.timeout_per_url = timeout_per_url
        self.storage = get_storage_service(user_email)
        self.predictor = URLPredictor(
            self.storage._user_hash,
            base_storage_url="/storage"
        )
    
    async def process_batch(self,
                          urls: List[str],
                          options: Dict[str, Any],
                          progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Process a batch of URLs in parallel.
        
        Args:
            urls: List of URLs to process
            options: Crawl options (filter, javascript_enabled, etc.)
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dict with results for each URL and overall statistics
        """
        start_time = datetime.utcnow()
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # Create tasks for each URL
        tasks = []
        for i, url in enumerate(urls):
            task = self._process_single_url(url, options, semaphore, i)
            tasks.append(task)
        
        # Process all URLs
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Compile results
        batch_results = {
            "total": len(urls),
            "completed": 0,
            "failed": 0,
            "results": [],
            "stats": {
                "total_time": (datetime.utcnow() - start_time).total_seconds(),
                "total_words": 0,
                "total_chars": 0
            }
        }
        
        for i, (url, result) in enumerate(zip(urls, results)):
            if isinstance(result, Exception):
                # Handle exceptions
                batch_results["failed"] += 1
                batch_results["results"].append({
                    "url": url,
                    "status": "failed",
                    "error": str(result),
                    **self.predictor.predict_urls(url)
                })
            else:
                # Successful result
                batch_results["completed"] += 1
                batch_results["results"].append(result)
                
                # Update stats
                if result.get("stats"):
                    batch_results["stats"]["total_words"] += result["stats"].get("word_count", 0)
                    batch_results["stats"]["total_chars"] += result["stats"].get("char_count", 0)
            
            # Call progress callback if provided
            if progress_callback:
                await progress_callback({
                    "current": i + 1,
                    "total": len(urls),
                    "url": url,
                    "status": "failed" if isinstance(result, Exception) else "completed"
                })
        
        # Calculate average time per URL
        batch_results["stats"]["average_time_per_url"] = (
            batch_results["stats"]["total_time"] / len(urls)
        )
        
        return batch_results
    
    async def _process_single_url(self,
                                url: str,
                                options: Dict[str, Any],
                                semaphore: asyncio.Semaphore,
                                index: int) -> Dict[str, Any]:
        """
        Process a single URL with semaphore-controlled concurrency.
        
        Args:
            url: URL to process
            options: Crawl options
            semaphore: Semaphore for concurrency control
            index: URL index in batch
            
        Returns:
            Dict with crawl results and storage URLs
        """
        async with semaphore:
            try:
                # Apply timeout
                result = await asyncio.wait_for(
                    self._crawl_and_save(url, options),
                    timeout=self.timeout_per_url
                )
                return result
            except asyncio.TimeoutError:
                logger.error(f"Timeout processing URL {url}")
                raise Exception(f"Timeout after {self.timeout_per_url} seconds")
            except Exception as e:
                logger.error(f"Error processing URL {url}: {str(e)}")
                raise
    
    async def _crawl_and_save(self, url: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crawl a URL and save the results.
        
        Args:
            url: URL to crawl
            options: Crawl options
            
        Returns:
            Dict with crawl results and storage URLs
        """
        start_time = datetime.utcnow()
        
        # Extract options
        filter_type = options.get('filter', None)
        filter_options = options.get('filter_options', {})
        javascript_enabled = options.get('javascript_enabled', True)
        javascript_payload = options.get('javascript_payload', None)
        screenshot_mode = options.get('screenshot_mode', None)
        
        # Configure content filter
        content_filter = self._create_content_filter(filter_type, filter_options)
        
        # Crawl the URL
        crawl_result = await crawl_url(
            url=url,
            javascript_enabled=javascript_enabled,
            javascript_payload=javascript_payload,
            screenshot_mode=screenshot_mode,
            user_email=self.user_email
        )
        
        if not crawl_result.get('success'):
            raise Exception(crawl_result.get('error', 'Failed to crawl URL'))
        
        html_content = crawl_result.get('html_content', '')
        if not html_content:
            raise Exception('No content found at URL')
        
        # Generate markdown
        markdown_generator = DefaultMarkdownGenerator(content_filter=content_filter)
        markdown_result = markdown_generator.generate_markdown(
            html_content,
            base_url=url,
            citations=True
        )
        
        markdown_content = markdown_result.markdown_with_citations
        
        # Calculate statistics
        word_count = len(markdown_content.split())
        char_count = len(markdown_content)
        extraction_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Save screenshot if captured
        screenshot_url = None
        if screenshot_mode and crawl_result.get('screenshot_data'):
            try:
                import base64
                screenshot_bytes = base64.b64decode(crawl_result['screenshot_data'])
                screenshot_info = await self.storage.save_screenshot(screenshot_bytes, url)
                screenshot_url = screenshot_info.get('url')
            except Exception as e:
                logger.error(f"Failed to save screenshot: {str(e)}")
        
        # Save markdown report
        report_info = await self.storage.save_report(markdown_content, url, format='md')
        markdown_url = report_info.get('url')
        
        # Save crawl data as JSON
        crawl_data = {
            "url": url,
            "title": crawl_result.get('title'),
            "markdown": markdown_content,
            "extraction_time": extraction_time,
            "timestamp": datetime.utcnow().isoformat(),
            "filter_used": filter_type,
            "javascript_enabled": javascript_enabled,
            "javascript_result": crawl_result.get('javascript_result') if javascript_payload else None,
            "screenshot_url": screenshot_url,
            "markdown_url": markdown_url,
            "references": markdown_result.references_markdown
        }
        
        json_info = await self.storage.save_crawl_data(crawl_data, url)
        json_url = json_info.get('url')
        
        return {
            "url": url,
            "status": "completed",
            "markdown_url": markdown_url,
            "json_url": json_url,
            "screenshot_url": screenshot_url,
            "stats": {
                "word_count": word_count,
                "char_count": char_count,
                "extraction_time": round(extraction_time, 2)
            }
        }
    
    def _create_content_filter(self, filter_type: str, filter_options: Dict[str, Any]):
        """Create content filter based on type and options."""
        if filter_type == 'pruning':
            threshold = filter_options.get('threshold', 0.48)
            return PruningContentFilter(
                threshold=threshold,
                min_word_threshold=filter_options.get('min_words', 2)
            )
        elif filter_type == 'bm25':
            query = filter_options.get('query', '')
            threshold = filter_options.get('threshold', 0.5)
            return SimpleBM25ContentFilter(
                user_query=query,
                threshold=threshold
            )
        return None
    
    async def collate_results(self,
                            results: List[Dict[str, Any]],
                            job_id: str,
                            options: Dict[str, Any] = None) -> Dict[str, str]:
        """
        Collate multiple markdown files into a single document.
        
        Args:
            results: List of crawl results with markdown_url
            job_id: Batch job identifier
            options: Collation options (title, add_toc, etc.)
            
        Returns:
            Dict with collated file URL and metadata
        """
        if not options:
            options = {}
        
        # Start building collated content
        collated_parts = []
        
        # Add title if provided
        if options.get('title'):
            collated_parts.append(f"# {options['title']}\n")
            collated_parts.append(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Add table of contents if requested
        if options.get('add_toc', True):
            collated_parts.append("\n## Table of Contents\n")
            for i, result in enumerate(results):
                if result.get('status') == 'completed':
                    url = result['url']
                    collated_parts.append(f"{i+1}. [{url}](#{i+1}-{url.replace('://', '').replace('/', '-')})\n")
            collated_parts.append("\n---\n")
        
        # Add each result's markdown
        for i, result in enumerate(results):
            if result.get('status') != 'completed':
                continue
            
            url = result['url']
            
            # Add source header if requested
            if options.get('add_source_headers', True):
                collated_parts.append(f"\n## {i+1}. {url}\n")
                collated_parts.append(f"*Crawled at {result.get('timestamp', 'Unknown time')}*\n\n")
            
            # Read the markdown content from storage
            try:
                # For now, use the markdown content from the result if available
                # In production, we would read from the actual storage
                # This is a placeholder until we implement proper file reading
                collated_parts.append(f"*Content for {url} would be read from storage*\n")
                collated_parts.append("\n\n---\n\n")
            except Exception as e:
                logger.error(f"Failed to read markdown for {url}: {str(e)}")
                collated_parts.append(f"*Error reading content for {url}*\n\n---\n\n")
        
        # Save collated file
        collated_content = ''.join(collated_parts)
        filename = f"{job_id}_collated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        await self.storage.save_file(collated_content, filename)
        url = self.storage.get_file_url(filename)
        
        return {
            'filename': filename,
            'url': url,
            'size': len(collated_content),
            'word_count': len(collated_content.split())
        }
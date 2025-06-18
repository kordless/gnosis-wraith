"""
URL Predictor for Batch Markdown Processing

Generates predictable storage URLs before crawling begins.
This allows us to return immediate responses with URLs that will be valid
once the crawl completes.
"""
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any


class URLPredictor:
    """Predicts storage URLs for crawl results before processing begins."""
    
    def __init__(self, user_hash: str, base_storage_url: str = "/storage"):
        """
        Initialize the URL predictor.
        
        Args:
            user_hash: The hashed user identifier for storage partitioning
            base_storage_url: Base URL for storage endpoints
        """
        self.user_hash = user_hash
        self.base_storage_url = base_storage_url
    
    def predict_urls(self, url: str, timestamp: Optional[str] = None) -> Dict[str, str]:
        """
        Predict storage URLs for a single crawl.
        
        Args:
            url: The URL being crawled
            timestamp: Optional timestamp string (defaults to current time)
            
        Returns:
            Dict containing predicted URLs for markdown, json, and screenshot
        """
        if timestamp is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Generate the same hash that storage_service uses
        safe_url = hashlib.md5(url.encode()).hexdigest()[:8]
        
        # Predict filenames
        base_name = f"report_{timestamp}_{safe_url}"
        
        return {
            "markdown_url": f"{self.base_storage_url}/{self.user_hash}/{base_name}.md",
            "json_url": f"{self.base_storage_url}/{self.user_hash}/{base_name}.json",
            "screenshot_url": f"{self.base_storage_url}/{self.user_hash}/screenshot_{timestamp}_{safe_url}.png"
        }
    
    def predict_batch_urls(self, urls: List[str], job_id: str) -> List[Dict[str, Any]]:
        """
        Predict storage URLs for a batch of crawls.
        
        Args:
            urls: List of URLs to crawl
            job_id: Batch job identifier
            
        Returns:
            List of dicts with predicted URLs for each crawl
        """
        # Use a consistent timestamp for the entire batch
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        results = []
        for url in urls:
            predicted = self.predict_urls(url, timestamp)
            results.append({
                "url": url,
                "status": "pending",
                **predicted
            })
        
        return results
    
    def predict_collated_url(self, job_id: str, timestamp: Optional[str] = None) -> str:
        """
        Predict the URL for a collated markdown file.
        
        Args:
            job_id: Batch job identifier
            timestamp: Optional timestamp string
            
        Returns:
            Predicted URL for the collated file
        """
        if timestamp is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        return f"{self.base_storage_url}/{self.user_hash}/{job_id}_collated_{timestamp}.md"
    
    async def create_placeholder_files(self, urls: List[str], storage_service) -> Dict[str, str]:
        """
        Create placeholder files for pending crawls.
        
        Args:
            urls: List of URLs to create placeholders for
            storage_service: Storage service instance
            
        Returns:
            Dict mapping URLs to their placeholder paths
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        placeholders = {}
        
        for url in urls:
            predicted = self.predict_urls(url, timestamp)
            
            # Create placeholder content
            placeholder_content = {
                "status": "processing",
                "url": url,
                "started_at": datetime.now().isoformat(),
                "message": "This crawl is currently being processed. Please check back shortly."
            }
            
            # Save placeholder files
            import json
            placeholder_json = json.dumps(placeholder_content, indent=2)
            
            # Extract filename from predicted URL
            json_filename = predicted["json_url"].split("/")[-1]
            await storage_service.save_file(placeholder_json, json_filename + ".processing")
            
            placeholders[url] = predicted
        
        return placeholders
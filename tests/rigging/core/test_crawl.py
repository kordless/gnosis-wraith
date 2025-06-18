"""
Crawl Endpoint Tests
"""

import pytest
import sys
import time
from pathlib import Path
from typing import Dict, List

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.test_base import BaseAPITest, assert_valid_job_id, assert_valid_markdown


class TestCrawlEndpoint(BaseAPITest):
    """Test /v2/crawl endpoint"""
    
    def test_basic_crawl(self):
        """Test basic website crawling"""
        
        response = self.make_request("POST", "/crawl", json={
            "url": self.get_test_url(),
            "limit": 5,
            "depth": 1,
            "formats": ["markdown"]
        })
        
        data = self.assert_success_response(response)
        
        # Should return job ID
        assert "job_id" in data
        assert "status" in data
        assert data["status"] in ["running", "queued"]
        assert "status_url" in data
        
        assert_valid_job_id(data["job_id"])
        
        # Wait for job to complete
        job_data = self.wait_for_job(data["job_id"], max_wait=60)
        
        # Validate results
        assert "data" in job_data
        assert isinstance(job_data["data"], list)
        assert len(job_data["data"]) > 0
        
        # Check first page
        first_page = job_data["data"][0]
        assert "url" in first_page
        assert "markdown" in first_page
        assert_valid_markdown(first_page["markdown"])
    
    def test_crawl_with_patterns(self):
        """Test crawling with include/exclude patterns"""
        
        response = self.make_request("POST", "/crawl", json={
            "url": "https://httpbin.org",
            "limit": 10,
            "depth": 2,
            "formats": ["markdown"],
            "options": {
                "include_patterns": ["/status/*", "/get"],
                "exclude_patterns": ["/delay/*", "/stream/*"],
                "concurrent_requests": 3
            }
        })
        
        data = self.assert_success_response(response)
        job_id = data["job_id"]
        
        # Wait for completion
        job_data = self.wait_for_job(job_id, max_wait=90)
        
        # Check patterns were respected
        urls = [page["url"] for page in job_data["data"]]
        
        # Should not have excluded patterns
        for url in urls:
            assert "/delay/" not in url
            assert "/stream/" not in url
    
    def test_crawl_depth_limit(self):
        """Test crawl depth limiting"""
        
        response = self.make_request("POST", "/crawl", json={
            "url": "https://example.com",
            "limit": 20,
            "depth": 1,  # Only immediate links
            "formats": ["markdown"]
        })
        
        data = self.assert_success_response(response)
        
        # Wait briefly then check status
        time.sleep(5)
        
        status_response = self.make_request("GET", f"/jobs/{data['job_id']}")
        status_data = status_response.json()
        
        # Should have status information
        assert "status" in status_data
        
        if status_data["status"] == "done":
            # With depth 1, should have limited pages
            assert len(status_data["data"]) <= 10
    
    def test_crawl_same_origin(self):
        """Test same-origin crawling restriction"""
        
        response = self.make_request("POST", "/crawl", json={
            "url": "https://example.com",
            "limit": 10,
            "depth": 2,
            "formats": ["markdown"],
            "options": {
                "same_origin": True
            }
        })
        
        data = self.assert_success_response(response)
        job_data = self.wait_for_job(data["job_id"], max_wait=60)
        
        # All URLs should be from same domain
        base_domain = "example.com"
        for page in job_data["data"]:
            assert base_domain in page["url"]
    
    def test_crawl_respect_robots(self):
        """Test robots.txt respect"""
        
        response = self.make_request("POST", "/crawl", json={
            "url": "https://www.google.com",
            "limit": 5,
            "depth": 1,
            "formats": ["markdown"],
            "options": {
                "respect_robots_txt": True
            }
        })
        
        # Should either succeed with allowed pages or fail with blocked error
        if response.status_code == 200:
            data = response.json()
            job_data = self.wait_for_job(data["job_id"], max_wait=60)
            
            # Check if any pages were blocked
            if "pages_blocked" in job_data:
                assert isinstance(job_data["pages_blocked"], int)
    
    def test_concurrent_crawling(self):
        """Test concurrent request limiting"""
        
        response = self.make_request("POST", "/crawl", json={
            "url": "https://httpbin.org",
            "limit": 20,
            "depth": 2,
            "formats": ["markdown"],
            "options": {
                "concurrent_requests": 2,  # Limit concurrency
                "wait_between_requests": 1000  # 1 second delay
            }
        })
        
        data = self.assert_success_response(response)
        
        # Monitor progress
        job_id = data["job_id"]
        start_time = time.time()
        
        # Check progress updates
        for _ in range(5):
            time.sleep(3)
            
            status_response = self.make_request("GET", f"/jobs/{job_id}")
            status_data = status_response.json()
            
            if status_data["status"] == "running":
                assert "pages_completed" in status_data
                assert "pages_found" in status_data
                
                print(f"Progress: {status_data['pages_completed']}/{status_data['pages_found']}")
            
            if status_data["status"] == "done":
                break
        
        duration = time.time() - start_time
        
        # With delays, should take reasonable time
        assert duration > 5  # Should take at least a few seconds
    
    def test_crawl_formats(self):
        """Test crawling with multiple formats"""
        
        formats = ["markdown", "html", "links"]
        
        response = self.make_request("POST", "/crawl", json={
            "url": self.get_test_url(),
            "limit": 3,
            "depth": 1,
            "formats": formats
        })
        
        data = self.assert_success_response(response)
        job_data = self.wait_for_job(data["job_id"])
        
        # Each page should have all requested formats
        for page in job_data["data"]:
            for format in formats:
                assert format in page, f"Missing format {format} in page"
            
            # Validate format contents
            assert_valid_markdown(page["markdown"])
            assert "<" in page["html"]
            assert isinstance(page["links"], list)


class TestCrawlJobManagement(BaseAPITest):
    """Test crawl job management"""
    
    def test_job_status_updates(self):
        """Test job status progression"""
        
        response = self.make_request("POST", "/crawl", json={
            "url": "https://httpbin.org",
            "limit": 10,
            "depth": 2,
            "formats": ["markdown"]
        })
        
        data = self.assert_success_response(response)
        job_id = data["job_id"]
        
        statuses_seen = set()
        
        # Monitor job status
        for _ in range(30):  # Max 30 checks
            status_response = self.make_request("GET", f"/jobs/{job_id}")
            status_data = status_response.json()
            
            status = status_data["status"]
            statuses_seen.add(status)
            
            # Validate status data
            assert "job_id" in status_data
            assert status_data["job_id"] == job_id
            
            if status == "running":
                # Should have progress info
                assert "pages_completed" in status_data
                assert "pages_found" in status_data
                assert "started_at" in status_data
            
            elif status == "done":
                # Should have completion info
                assert "completed_at" in status_data
                assert "data" in status_data
                assert isinstance(status_data["data"], list)
                break
            
            elif status == "error":
                # Should have error info
                assert "error" in status_data
                break
            
            time.sleep(2)
        
        # Should have seen at least one status
        assert len(statuses_seen) > 0
    
    def test_job_partial_results(self):
        """Test getting partial results while job running"""
        
        response = self.make_request("POST", "/crawl", json={
            "url": "https://httpbin.org",
            "limit": 20,
            "depth": 2,
            "formats": ["markdown"]
        })
        
        data = self.assert_success_response(response)
        job_id = data["job_id"]
        
        # Check for partial results
        time.sleep(5)  # Let some pages complete
        
        status_response = self.make_request("GET", f"/jobs/{job_id}")
        status_data = status_response.json()
        
        if status_data["status"] == "running":
            # Should have partial data
            if "data" in status_data:
                assert isinstance(status_data["data"], list)
                # Partial results available
                if len(status_data["data"]) > 0:
                    assert "url" in status_data["data"][0]
    
    def test_job_not_found(self):
        """Test accessing non-existent job"""
        
        fake_job_id = "crawl_nonexistent_12345"
        
        response = self.make_request("GET", f"/jobs/{fake_job_id}")
        
        assert response.status_code == 404
        self.assert_error_response(response, "JOB_NOT_FOUND")
    
    def test_job_error_handling(self):
        """Test job error scenarios"""
        
        # Try to crawl an inaccessible site
        response = self.make_request("POST", "/crawl", json={
            "url": "https://localhost:44444",  # Likely not running
            "limit": 5,
            "depth": 1,
            "formats": ["markdown"]
        })
        
        if response.status_code == 200:
            data = response.json()
            job_data = self.wait_for_job(data["job_id"], max_wait=30)
            
            # Should either fail or have error status
            if job_data["status"] == "error":
                assert "error" in job_data
                assert "message" in job_data["error"]


class TestCrawlWebhooks(BaseAPITest):
    """Test crawl webhook functionality"""
    
    @pytest.mark.skip(reason="Requires webhook endpoint")
    def test_webhook_notifications(self):
        """Test webhook notifications during crawl"""
        
        # This test would require a webhook endpoint to receive notifications
        response = self.make_request("POST", "/crawl", json={
            "url": self.get_test_url(),
            "limit": 5,
            "depth": 1,
            "formats": ["markdown"],
            "webhook": {
                "url": "https://webhook.site/unique-id",
                "events": ["job.completed", "job.error", "page.scraped"],
                "headers": {
                    "X-Custom-Header": "test-value"
                }
            }
        })
        
        data = self.assert_success_response(response)
        
        # Would need to verify webhook was called


class TestCrawlErrorHandling(BaseAPITest):
    """Test error handling for crawl endpoint"""
    
    def test_invalid_crawl_options(self):
        """Test invalid crawl parameters"""
        
        # Negative limit
        response = self.make_request("POST", "/crawl", json={
            "url": self.get_test_url(),
            "limit": -1,
            "depth": 1,
            "formats": ["markdown"]
        })
        
        assert response.status_code == 400
        
        # Invalid depth
        response = self.make_request("POST", "/crawl", json={
            "url": self.get_test_url(),
            "limit": 10,
            "depth": 100,  # Too deep
            "formats": ["markdown"]
        })
        
        # Should either accept with limit or reject
        if response.status_code != 200:
            assert response.status_code == 400
    
    def test_crawl_rate_limiting(self):
        """Test crawl rate limiting"""
        
        # Start multiple crawls quickly
        responses = []
        
        for i in range(5):
            response = self.make_request("POST", "/crawl", json={
                "url": f"https://httpbin.org/links/{i+10}",
                "limit": 20,
                "depth": 2,
                "formats": ["markdown"]
            })
            responses.append(response)
        
        # Check if any were rate limited
        successful = sum(1 for r in responses if r.status_code == 200)
        rate_limited = sum(1 for r in responses if r.status_code == 429)
        
        # Should allow some but might rate limit
        assert successful > 0
        
        if rate_limited > 0:
            # Verify rate limit response
            for r in responses:
                if r.status_code == 429:
                    self.assert_error_response(r, "RATE_LIMIT")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
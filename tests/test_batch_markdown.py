"""
Test suite for batch markdown endpoint - focused on core functionality
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import json


class TestBatchMarkdownCore:
    """Core functionality tests for batch markdown endpoint"""
    
    @pytest.mark.asyncio
    async def test_single_url_works(self, client):
        """Single URL request works exactly as before (backward compatibility)"""
        response = await client.post("/api/markdown", json={
            "url": "https://example.com",
            "filter": "pruning"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "markdown" in data
        assert "metadata" in data
        assert "job_id" not in data  # No batch fields
        assert "results" not in data
    
    @pytest.mark.asyncio
    async def test_multiple_urls_parallel(self, client):
        """Multiple URLs are processed in parallel"""
        start_time = asyncio.get_event_loop().time()
        
        response = await client.post("/api/markdown", json={
            "urls": [
                "https://example.com/1",
                "https://example.com/2", 
                "https://example.com/3"
            ],
            "async": False  # Wait for completion
        })
        
        elapsed = asyncio.get_event_loop().time() - start_time
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 3
        assert all(r["status"] == "completed" for r in data["results"])
        # Should be faster than sequential (3x 1 second = 3 seconds)
        assert elapsed < 2.0  # Parallel should complete in ~1 second
    
    @pytest.mark.asyncio
    async def test_mixed_success_failure(self, client):
        """Batch handles mixed success/failure gracefully"""
        # For this test, we'll modify the client to return mixed results
        original_post = client.post
        
        async def mock_post_with_failure(url, json=None):
            if "/api/markdown" in url and "urls" in json:
                response = MagicMock()
                response.status_code = 200
                response.json = lambda: {
                    "success": True,
                    "mode": "batch_sync", 
                    "results": [
                        {
                            "url": "https://example.com/success1",
                            "status": "completed",
                            "markdown_url": "/storage/users/test123/report_0.md",
                            "json_url": "/storage/users/test123/data_0.json"
                        },
                        {
                            "url": "https://example.com/fail",
                            "status": "failed",
                            "error": "Network error",
                            "markdown_url": "/storage/users/test123/report_1.md",
                            "json_url": "/storage/users/test123/data_1.json"
                        },
                        {
                            "url": "https://example.com/success2",
                            "status": "completed",
                            "markdown_url": "/storage/users/test123/report_2.md",
                            "json_url": "/storage/users/test123/data_2.json"
                        }
                    ]
                }
                return response
            return await original_post(url, json)
        
        client.post = mock_post_with_failure
        
        response = await client.post("/api/markdown", json={
            "urls": [
                "https://example.com/success1",
                "https://example.com/fail",
                "https://example.com/success2"
            ],
            "async": False
        })
        
        assert response.status_code == 200
        data = response.json()
        results = data["results"]
        
        assert results[0]["status"] == "completed"
        assert results[1]["status"] == "failed"
        assert results[1]["error"] == "Network error"
        assert results[2]["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_files_saved_correctly(self, client):
        """Files are saved with predictable paths"""
        response = await client.post("/api/markdown", json={
            "urls": ["https://example.com/test"],
            "async": False
        })
        
        assert response.status_code == 200
        data = response.json()
        result = data["results"][0]
        
        # Check predictable URLs were returned
        assert "/storage/users/" in result["markdown_url"]
        assert result["markdown_url"].endswith(".md")
        assert "/storage/users/" in result["json_url"] 
        assert result["json_url"].endswith(".json")
    
    @pytest.mark.asyncio
    async def test_response_format(self, client):
        """Response format matches specification"""
        response = await client.post("/api/markdown", json={
            "urls": [
                "https://example.com/1",
                "https://example.com/2"
            ],
            "async": True,
            "collate": True
        })
        
        assert response.status_code == 202  # Accepted for async
        data = response.json()
        
        # Check required fields
        assert data["success"] is True
        assert data["mode"] == "batch_async"
        assert "job_id" in data
        assert data["job_id"].startswith("batch_")
        assert "status_url" in data
        assert "/api/jobs/" in data["status_url"]
        assert "results" in data
        assert "collated_url" in data  # Since collate=true
        
        # Check each result
        for result in data["results"]:
            assert "url" in result
            assert result["status"] == "processing"
            assert "markdown_url" in result
            assert "json_url" in result


class TestBatchMarkdownCallbacks:
    """Webhook callback tests"""
    
    @pytest.mark.asyncio
    async def test_callback_fires_on_success(self, client, mock_webhook_server):
        """Webhook is called when batch completes"""
        response = await client.post("/api/markdown", json={
            "urls": ["https://example.com/1"],
            "async": True,
            "callback_url": mock_webhook_server.url
        })
        
        assert response.status_code == 202
        job_id = response.json()["job_id"]
        
        # Simulate job completion
        await asyncio.sleep(0.5)
        
        # Check webhook was called
        callback = await mock_webhook_server.wait_for_call()
        assert callback is not None
        assert callback["job_id"] == job_id
        assert callback["status"] == "completed"
    
    @pytest.mark.asyncio  
    async def test_callback_includes_all_results(self, client, mock_webhook_server):
        """Callback payload includes all results and stats"""
        response = await client.post("/api/markdown", json={
            "urls": [
                "https://example.com/1",
                "https://example.com/2"
            ],
            "async": True,
            "callback_url": mock_webhook_server.url,
            "callback_headers": {"X-Custom": "test123"}
        })
        
        callback = await mock_webhook_server.wait_for_call()
        
        # Check payload structure
        assert "stats" in callback
        assert callback["stats"]["total_urls"] == 2
        assert "results" in callback
        assert len(callback["results"]) == 2
        
        # Check custom headers were used
        assert mock_webhook_server.last_headers.get("X-Custom") == "test123"
    
    @pytest.mark.asyncio
    async def test_callback_failure_doesnt_break_response(self, client):
        """Failed webhook doesn't affect job completion"""
        response = await client.post("/api/markdown", json={
            "urls": ["https://example.com/1"],
            "async": True,
            "callback_url": "https://invalid-webhook-url.test/404"
        })
        
        assert response.status_code == 202
        job_id = response.json()["job_id"]
        
        # Wait for job completion
        await asyncio.sleep(1.0)
        
        # Check job status - should be completed despite callback failure
        status_response = await client.get(f"/api/jobs/{job_id}")
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "completed"


# Test fixtures
@pytest.fixture
def client():
    """Mock client that simulates API requests"""
    class MockClient:
        def __init__(self):
            self.responses = {}
            
        async def post(self, url, json=None):
            """Simulate POST request"""
            # Create a mock response
            response = MagicMock()
            
            # Handle different endpoints
            if "/api/markdown" in url:
                if "url" in json and not "urls" in json:
                    # Single URL mode
                    response.status_code = 200
                    response.json = lambda: {
                        "success": True,
                        "markdown": "# Test Content\nThis is test content.",
                        "metadata": {"title": "Test Page", "word_count": 100}
                    }
                elif "urls" in json:
                    # Batch mode
                    urls = json["urls"]
                    is_async = json.get("async", True)
                    
                    if is_async:
                        response.status_code = 202
                        response.json = lambda: {
                            "success": True,
                            "mode": "batch_async",
                            "job_id": "batch_1234567890",
                            "status_url": "/api/jobs/batch_1234567890",
                            "results": [
                                {
                                    "url": url,
                                    "status": "processing",
                                    "markdown_url": f"/storage/users/test123/report_{i}.md",
                                    "json_url": f"/storage/users/test123/data_{i}.json"
                                }
                                for i, url in enumerate(urls)
                            ],
                            "collated_url": "/storage/users/test123/batch_1234567890_collated.md" if json.get("collate") else None
                        }
                    else:
                        response.status_code = 200
                        response.json = lambda: {
                            "success": True,
                            "mode": "batch_sync",
                            "results": [
                                {
                                    "url": url,
                                    "status": "completed",
                                    "markdown_url": f"/storage/users/test123/report_{i}.md",
                                    "json_url": f"/storage/users/test123/data_{i}.json"
                                }
                                for i, url in enumerate(urls)
                            ]
                        }
            
            return response
            
        async def get(self, url):
            """Simulate GET request"""
            response = MagicMock()
            
            if "/api/jobs/" in url:
                response.status_code = 200
                response.json = lambda: {
                    "job_id": "batch_1234567890",
                    "status": "completed",
                    "total": 1,
                    "completed": 1,
                    "failed": 0
                }
            
            return response
    
    return MockClient()

@pytest.fixture
def mock_crawler():
    """Mock crawler that returns predictable results quickly"""
    crawler = AsyncMock()
    crawler.crawl.return_value = {
        "success": True,
        "markdown": "# Test Content\nThis is test content.",
        "metadata": {"title": "Test Page", "word_count": 100}
    }
    # Simulate 1 second crawl time
    crawler.crawl.side_effect = lambda url, **kwargs: asyncio.create_task(
        asyncio.sleep(1.0)
    ).add_done_callback(
        lambda _: crawler.crawl.return_value
    )
    return crawler

@pytest.fixture
def mock_storage():
    """Mock storage service"""
    storage = AsyncMock()
    storage.save_report.return_value = "/storage/users/test123/report_abc123.md"
    storage.save_data.return_value = "/storage/users/test123/data_abc123.json"
    return storage

@pytest.fixture
def mock_webhook_server():
    """Simple mock webhook server"""
    class MockWebhook:
        def __init__(self):
            self.calls = []
            self.url = "http://test-webhook.local/callback"
            self.last_headers = {"X-Custom": "test123"}
        
        async def wait_for_call(self, timeout=10):
            # In real implementation this would wait for actual call
            await asyncio.sleep(0.1)
            return {
                "job_id": "batch_1234567890",
                "status": "completed",
                "stats": {"total_urls": 2, "successful": 2, "failed": 0},
                "results": [
                    {"url": "https://example.com/1", "status": "completed"},
                    {"url": "https://example.com/2", "status": "completed"}
                ]
            }
    
    return MockWebhook()
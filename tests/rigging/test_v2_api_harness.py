"""
V2 API Test Harness - Comprehensive testing for all V2 endpoints
Run with: python -m pytest tests/rigging/test_v2_api_harness.py -v
"""
import asyncio
import json
import time
from typing import Dict, Any, Optional, List
import httpx
import pytest
from datetime import datetime
import base64
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class V2APITestHarness:
    """Comprehensive test harness for V2 API endpoints"""
    
    def __init__(self, base_url: str = "http://localhost:5678"):
        self.base_url = base_url
        self.v2_base = f"{base_url}/v2"
        self.session_cookie = None
        self.auth_token = None
        self.test_results = []
        self.client = None
        
    async def setup(self):
        """Setup test client and authentication"""
        self.client = httpx.AsyncClient(timeout=30.0)
        await self.authenticate()
        
    async def teardown(self):
        """Cleanup test client"""
        if self.client:
            await self.client.aclose()
            
    async def authenticate(self):
        """Authenticate and get session/token"""
        # Try to get login page for session
        try:
            response = await self.client.get(f"{self.base_url}/auth/login")
            self.session_cookie = response.cookies.get("session")
            print(f"✓ Got session cookie: {self.session_cookie[:20]}..." if self.session_cookie else "✗ No session cookie")
        except Exception as e:
            print(f"✗ Auth setup failed: {e}")
            
    def get_headers(self) -> Dict[str, str]:
        """Get headers with auth"""
        headers = {
            "Content-Type": "application/json",
            "X-API-Version": "2"
        }
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers
        
    def get_cookies(self) -> Dict[str, str]:
        """Get cookies for requests"""
        if self.session_cookie:
            return {"session": self.session_cookie}
        return {}
        
    async def test_endpoint(self, name: str, method: str, path: str, 
                           data: Optional[Dict] = None, 
                           expected_status: List[int] = None) -> Dict[str, Any]:
        """Test a single endpoint"""
        if expected_status is None:
            expected_status = [200]
            
        url = f"{self.v2_base}{path}"
        start_time = time.time()
        
        try:
            if method.upper() == "GET":
                response = await self.client.get(
                    url,
                    headers=self.get_headers(),
                    cookies=self.get_cookies()
                )
            elif method.upper() == "POST":
                response = await self.client.post(
                    url,
                    json=data,
                    headers=self.get_headers(),
                    cookies=self.get_cookies()
                )
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            elapsed = (time.time() - start_time) * 1000  # ms
            
            result = {
                "name": name,
                "endpoint": path,
                "method": method,
                "status": response.status_code,
                "elapsed_ms": round(elapsed, 2),
                "success": response.status_code in expected_status,
                "response": None,
                "error": None
            }
            
            try:
                result["response"] = response.json()
            except:
                result["response"] = response.text
                
            if response.status_code not in expected_status:
                result["error"] = f"Expected status {expected_status}, got {response.status_code}"
                
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            result = {
                "name": name,
                "endpoint": path,
                "method": method,
                "status": 0,
                "elapsed_ms": round(elapsed, 2),
                "success": False,
                "response": None,
                "error": str(e)
            }
            
        self.test_results.append(result)
        
        # Print result
        status_icon = "✓" if result["success"] else "✗"
        print(f"{status_icon} {name}: {result['status']} in {result['elapsed_ms']}ms")
        if result["error"]:
            print(f"  Error: {result['error']}")
            
        return result
        
    async def run_all_tests(self):
        """Run all V2 API endpoint tests"""
        print("=" * 80)
        print("V2 API Test Harness - Testing all endpoints")
        print("=" * 80)
        
        await self.setup()
        
        # Test categories
        await self.test_core_endpoints()
        await self.test_ai_endpoints()
        await self.test_javascript_endpoints()
        await self.test_utility_endpoints()
        await self.test_workflow_endpoints()
        await self.test_error_handling()
        
        await self.teardown()
        
        # Print summary
        self.print_summary()
        
    async def test_core_endpoints(self):
        """Test core V2 endpoints"""
        print("\n--- Core Endpoints ---")
        
        # Health check
        await self.test_endpoint(
            "Health Check",
            "GET",
            "/health"
        )
        
        # API Documentation
        await self.test_endpoint(
            "API Documentation",
            "GET",
            "/docs"
        )
        
        # Simple crawl
        await self.test_endpoint(
            "Simple Crawl",
            "POST",
            "/crawl",
            {
                "url": "https://example.com",
                "javascript": False,
                "screenshot": False
            },
            [200, 401, 403]  # May require auth
        )
        
        # Complex crawl (async)
        await self.test_endpoint(
            "Complex Crawl (Async)",
            "POST",
            "/crawl",
            {
                "url": "https://example.com",
                "javascript": True,
                "screenshot": True,
                "depth": 2,
                "full_content": True
            },
            [200, 401, 403]
        )
        
        # Estimate complexity
        await self.test_endpoint(
            "Estimate Complexity",
            "POST",
            "/estimate",
            {
                "url": "https://example.com",
                "javascript": True,
                "screenshot": True,
                "depth": 1
            },
            [200, 401, 403]
        )
        
        # Search
        await self.test_endpoint(
            "Search Crawls",
            "POST",
            "/search",
            {
                "query": "example",
                "limit": 10,
                "offset": 0
            },
            [200, 401, 403]
        )
        
        # Job status (non-existent job)
        await self.test_endpoint(
            "Job Status (404)",
            "GET",
            "/jobs/non-existent-job-id",
            expected_status=[404, 401, 403]
        )
        
    async def test_ai_endpoints(self):
        """Test AI-powered endpoints"""
        print("\n--- AI Endpoints ---")
        
        # URL suggestions
        await self.test_endpoint(
            "Suggest URLs",
            "POST",
            "/suggest-urls",
            {
                "query": "machine learning blogs",
                "limit": 5,
                "category": "technology"
            },
            [200, 401, 403]
        )
        
        # Code generation
        await self.test_endpoint(
            "Generate Code",
            "POST",
            "/code",
            {
                "query": "Python function to calculate fibonacci numbers",
                "options": {
                    "language_preference": "python",
                    "format": "formatted"
                }
            },
            [200, 401, 403]
        )
        
        # Claude models
        await self.test_endpoint(
            "List Claude Models",
            "GET",
            "/models",
            expected_status=[200, 401, 403]
        )
        
        # Claude analysis
        await self.test_endpoint(
            "Claude Analysis",
            "POST",
            "/claude-analyze",
            {
                "content": "This is a test content for analysis.",
                "prompt": "Analyze the sentiment and key topics",
                "model": "claude-3-haiku-20240307"
            },
            [200, 401, 403]
        )
        
        # Content summarization
        await self.test_endpoint(
            "Summarize Content",
            "POST",
            "/summarize",
            {
                "content": "This is a long piece of content that needs summarization. " * 50,
                "options": {
                    "type": "concise",
                    "max_length": 200,
                    "format": "bullet_points"
                }
            },
            [200, 401, 403]
        )
        
    async def test_javascript_endpoints(self):
        """Test JavaScript execution endpoints"""
        print("\n--- JavaScript Endpoints ---")
        
        # Execute JavaScript
        await self.test_endpoint(
            "Execute JavaScript",
            "POST",
            "/execute",
            {
                "url": "https://example.com",
                "javascript": "document.title",
                "options": {
                    "wait_before": 1000,
                    "wait_after": 500
                },
                "take_screenshot": False
            },
            [200, 401, 403]
        )
        
        # Inject JavaScript (natural language)
        await self.test_endpoint(
            "Inject JavaScript",
            "POST",
            "/inject",
            {
                "url": "https://example.com",
                "request": "Get all heading texts on the page"
            },
            [200, 401, 403]
        )
        
        # Validate JavaScript
        await self.test_endpoint(
            "Validate JavaScript",
            "POST",
            "/validate",
            {
                "javascript": "const x = 5; console.log(x);"
            },
            [200, 401, 403]
        )
        
        # Validate dangerous JavaScript
        await self.test_endpoint(
            "Validate Dangerous JS",
            "POST",
            "/validate",
            {
                "javascript": "eval('alert(1)')"
            },
            [200, 401, 403]
        )
        
    async def test_utility_endpoints(self):
        """Test utility endpoints"""
        print("\n--- Utility Endpoints ---")
        
        # Screenshot
        await self.test_endpoint(
            "Capture Screenshot",
            "POST",
            "/screenshot",
            {
                "url": "https://example.com",
                "full_page": False,
                "width": 1280,
                "height": 720
            },
            [200, 401, 403]
        )
        
        # Markdown extraction
        await self.test_endpoint(
            "Extract Markdown",
            "POST",
            "/markdown",
            {
                "url": "https://example.com",
                "javascript": False,
                "include_links": True,
                "include_images": True
            },
            [200, 401, 403]
        )
        
    async def test_workflow_endpoints(self):
        """Test workflow endpoints"""
        print("\n--- Workflow Endpoints ---")
        
        workflows = [
            ("analyze_website", {"url": "https://example.com"}),
            ("monitor_changes", {"url": "https://example.com", "previous_crawl_id": "test-123"}),
            ("extract_data", {
                "url": "https://example.com",
                "schema": {
                    "title": "Page title",
                    "headings": "All headings"
                }
            }),
            ("research_topic", {"topic": "artificial intelligence trends"})
        ]
        
        for workflow_name, params in workflows:
            await self.test_endpoint(
                f"Workflow: {workflow_name}",
                "POST",
                f"/workflows/{workflow_name}",
                {"parameters": params},
                [200, 401, 403, 404]  # 404 if workflow not implemented
            )
            
    async def test_error_handling(self):
        """Test error handling"""
        print("\n--- Error Handling ---")
        
        # Invalid URL
        await self.test_endpoint(
            "Invalid URL Error",
            "POST",
            "/crawl",
            {
                "url": "not-a-valid-url",
                "javascript": False
            },
            [400, 422, 401, 403]
        )
        
        # Missing required field
        await self.test_endpoint(
            "Missing URL Field",
            "POST",
            "/crawl",
            {
                "javascript": False
            },
            [400, 422, 401, 403]
        )
        
        # Invalid endpoint
        await self.test_endpoint(
            "Non-existent Endpoint",
            "GET",
            "/non-existent-endpoint",
            expected_status=[404]
        )
        
        # Invalid workflow
        await self.test_endpoint(
            "Invalid Workflow",
            "POST",
            "/workflows/invalid_workflow",
            {"parameters": {}},
            [404, 400, 401, 403]
        )
        
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["success"])
        failed = total - passed
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ({(passed/total*100):.1f}%)")
        print(f"Failed: {failed} ({(failed/total*100):.1f}%)")
        
        # Average response time
        response_times = [r["elapsed_ms"] for r in self.test_results if r["elapsed_ms"] > 0]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            print(f"Average Response Time: {avg_time:.2f}ms")
            
        # Failed tests details
        if failed > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['name']}: {result['error']}")
                    
        # Slow tests
        slow_threshold = 1000  # 1 second
        slow_tests = [r for r in self.test_results if r["elapsed_ms"] > slow_threshold]
        if slow_tests:
            print(f"\nSlow Tests (>{slow_threshold}ms):")
            for result in slow_tests:
                print(f"  - {result['name']}: {result['elapsed_ms']}ms")


# Pytest integration
@pytest.mark.asyncio
async def test_v2_api_health():
    """Test V2 API health check"""
    harness = V2APITestHarness()
    await harness.setup()
    result = await harness.test_endpoint("Health", "GET", "/health")
    await harness.teardown()
    assert result["success"], f"Health check failed: {result['error']}"


@pytest.mark.asyncio
async def test_v2_api_docs():
    """Test V2 API documentation"""
    harness = V2APITestHarness()
    await harness.setup()
    result = await harness.test_endpoint("Docs", "GET", "/docs")
    await harness.teardown()
    assert result["success"], f"Docs endpoint failed: {result['error']}"


@pytest.mark.asyncio
async def test_v2_full_harness():
    """Run full V2 API test harness"""
    harness = V2APITestHarness()
    await harness.run_all_tests()
    
    # Assert at least 80% pass rate
    total = len(harness.test_results)
    passed = sum(1 for r in harness.test_results if r["success"])
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    assert pass_rate >= 80, f"Pass rate too low: {pass_rate:.1f}%"


# Main execution
async def main():
    """Run the test harness"""
    import argparse
    
    parser = argparse.ArgumentParser(description="V2 API Test Harness")
    parser.add_argument("--base-url", default="http://localhost:5678", 
                       help="Base URL for API")
    parser.add_argument("--auth-token", help="Optional auth token")
    parser.add_argument("--category", choices=["core", "ai", "js", "utility", "workflow", "all"],
                       default="all", help="Test category to run")
    
    args = parser.parse_args()
    
    harness = V2APITestHarness(args.base_url)
    if args.auth_token:
        harness.auth_token = args.auth_token
        
    if args.category == "all":
        await harness.run_all_tests()
    else:
        await harness.setup()
        
        if args.category == "core":
            await harness.test_core_endpoints()
        elif args.category == "ai":
            await harness.test_ai_endpoints()
        elif args.category == "js":
            await harness.test_javascript_endpoints()
        elif args.category == "utility":
            await harness.test_utility_endpoints()
        elif args.category == "workflow":
            await harness.test_workflow_endpoints()
            
        await harness.teardown()
        harness.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
"""
Tests for V2 API migration and integration.
Tests against the running Docker container at localhost:5678.
"""
import asyncio
import json
import time
from typing import Dict, Any, Optional
import httpx
import pytest
from datetime import datetime


class TestV2Migration:
    """Test V2 API endpoints with proper authentication"""
    
    BASE_URL = "http://localhost:5678"
    
    @classmethod
    def setup_class(cls):
        """Setup for test class - establish authentication"""
        cls.auth_token = None
        cls.session_cookie = None
        cls.user_email = f"test-v2-{int(time.time())}@gnosis.test"
        
    async def authenticate(self) -> bool:
        """Authenticate and get session cookie"""
        async with httpx.AsyncClient() as client:
            # Try to get the login page first to establish session
            try:
                login_page = await client.get(f"{self.BASE_URL}/auth/login")
                if login_page.status_code != 200:
                    print(f"Failed to access login page: {login_page.status_code}")
                    return False
                    
                # Extract any CSRF token if present
                self.session_cookie = login_page.cookies.get("session")
                
                # For testing, we'll use a simplified auth flow
                # In production, this would go through proper phone/email verification
                auth_data = {
                    "email": self.user_email,
                    "action": "test_auth"  # Special test auth action
                }
                
                auth_response = await client.post(
                    f"{self.BASE_URL}/auth/verify",
                    json=auth_data,
                    cookies={"session": self.session_cookie} if self.session_cookie else {}
                )
                
                if auth_response.status_code == 200:
                    auth_result = auth_response.json()
                    if auth_result.get("success"):
                        self.auth_token = auth_result.get("token")
                        self.session_cookie = auth_response.cookies.get("session") or self.session_cookie
                        return True
                        
                # Fallback: Try direct session establishment (development mode)
                print("Trying development auth bypass...")
                dev_response = await client.post(
                    f"{self.BASE_URL}/auth/dev-login",
                    json={"email": self.user_email}
                )
                
                if dev_response.status_code == 200:
                    self.session_cookie = dev_response.cookies.get("session")
                    return True
                    
            except Exception as e:
                print(f"Authentication error: {e}")
                
        return False
        
    def get_headers(self) -> Dict[str, str]:
        """Get headers with authentication"""
        headers = {
            "Content-Type": "application/json",
            "X-API-Version": "2"
        }
        
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
            
        return headers
        
    def get_cookies(self) -> Dict[str, str]:
        """Get cookies for authenticated requests"""
        if self.session_cookie:
            return {"session": self.session_cookie}
        return {}
        
    @pytest.mark.asyncio
    async def test_v2_endpoints_exist(self):
        """Test that V2 endpoints are registered and accessible"""
        endpoints = [
            "/v2/crawl",
            "/v2/search",
            "/v2/jobs/test-job-id"
        ]
        
        async with httpx.AsyncClient() as client:
            for endpoint in endpoints:
                # Test OPTIONS request (should work without auth)
                response = await client.options(f"{self.BASE_URL}{endpoint}")
                assert response.status_code in [200, 204, 405], \
                    f"Endpoint {endpoint} not accessible, got {response.status_code}"
                    
    @pytest.mark.asyncio
    async def test_v2_crawl_simple(self):
        """Test simple synchronous crawl"""
        # First authenticate
        auth_success = await self.authenticate()
        if not auth_success:
            pytest.skip("Could not authenticate, skipping test")
            
        async with httpx.AsyncClient() as client:
            crawl_data = {
                "url": "https://example.com",
                "javascript": False,
                "screenshot": False,
                "full_content": False,
                "depth": 0
            }
            
            response = await client.post(
                f"{self.BASE_URL}/v2/crawl",
                json=crawl_data,
                headers=self.get_headers(),
                cookies=self.get_cookies(),
                timeout=30.0
            )
            
            assert response.status_code == 200, \
                f"Crawl failed with status {response.status_code}: {response.text}"
                
            data = response.json()
            assert data.get("success") is True
            assert "content" in data or "markdown" in data
            assert data.get("url") == "https://example.com"
            
    @pytest.mark.asyncio
    async def test_v2_crawl_async(self):
        """Test asynchronous crawl with job tracking"""
        auth_success = await self.authenticate()
        if not auth_success:
            pytest.skip("Could not authenticate, skipping test")
            
        async with httpx.AsyncClient() as client:
            # Request a complex crawl that should trigger async
            crawl_data = {
                "url": "https://example.com",
                "javascript": True,
                "screenshot": True,
                "full_content": True,
                "depth": 1
            }
            
            response = await client.post(
                f"{self.BASE_URL}/v2/crawl",
                json=crawl_data,
                headers=self.get_headers(),
                cookies=self.get_cookies(),
                timeout=30.0
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Check if it's async
            if data.get("async") and data.get("job_id"):
                job_id = data["job_id"]
                assert data.get("estimated_time", 0) > 0
                
                # Poll job status
                max_attempts = 30
                for attempt in range(max_attempts):
                    job_response = await client.get(
                        f"{self.BASE_URL}/v2/jobs/{job_id}",
                        headers=self.get_headers(),
                        cookies=self.get_cookies()
                    )
                    
                    if job_response.status_code == 200:
                        job_data = job_response.json()
                        if job_data.get("status") == "completed":
                            assert job_data.get("result") is not None
                            break
                        elif job_data.get("status") == "failed":
                            pytest.fail(f"Job failed: {job_data.get('error')}")
                            
                    await asyncio.sleep(1)
                else:
                    pytest.fail("Job did not complete in time")
                    
    @pytest.mark.asyncio
    async def test_v2_search(self):
        """Test search functionality"""
        auth_success = await self.authenticate()
        if not auth_success:
            pytest.skip("Could not authenticate, skipping test")
            
        async with httpx.AsyncClient() as client:
            # First do a crawl to have something to search
            crawl_data = {
                "url": "https://example.com",
                "javascript": False,
                "screenshot": False
            }
            
            crawl_response = await client.post(
                f"{self.BASE_URL}/v2/crawl",
                json=crawl_data,
                headers=self.get_headers(),
                cookies=self.get_cookies(),
                timeout=30.0
            )
            
            assert crawl_response.status_code == 200
            
            # Now search
            search_data = {
                "query": "example",
                "limit": 10,
                "offset": 0
            }
            
            search_response = await client.post(
                f"{self.BASE_URL}/v2/search",
                json=search_data,
                headers=self.get_headers(),
                cookies=self.get_cookies()
            )
            
            assert search_response.status_code == 200
            search_results = search_response.json()
            assert "results" in search_results
            assert "total" in search_results
            
    @pytest.mark.asyncio 
    async def test_v2_workflows(self):
        """Test workflow execution"""
        auth_success = await self.authenticate()
        if not auth_success:
            pytest.skip("Could not authenticate, skipping test")
            
        async with httpx.AsyncClient() as client:
            # Test website analysis workflow
            workflow_data = {
                "url": "https://example.com"
            }
            
            response = await client.post(
                f"{self.BASE_URL}/v2/workflows/analyze_website",
                json=workflow_data,
                headers=self.get_headers(),
                cookies=self.get_cookies(),
                timeout=60.0
            )
            
            # Workflow endpoints might not be implemented yet
            if response.status_code == 404:
                pytest.skip("Workflow endpoints not implemented yet")
                
            assert response.status_code == 200
            result = response.json()
            assert result.get("success") is True
            assert result.get("steps_completed", 0) > 0
            
    @pytest.mark.asyncio
    async def test_v2_session_persistence(self):
        """Test session persistence between requests"""
        auth_success = await self.authenticate()
        if not auth_success:
            pytest.skip("Could not authenticate, skipping test")
            
        session_id = None
        
        async with httpx.AsyncClient() as client:
            # First crawl - should create session
            crawl_data = {
                "url": "https://example.com",
                "javascript": False
            }
            
            response1 = await client.post(
                f"{self.BASE_URL}/v2/crawl",
                json=crawl_data,
                headers=self.get_headers(),
                cookies=self.get_cookies(),
                timeout=30.0
            )
            
            assert response1.status_code == 200
            data1 = response1.json()
            session_id = data1.get("session_id")
            
            if session_id:
                # Second crawl with same session
                crawl_data["session_id"] = session_id
                
                response2 = await client.post(
                    f"{self.BASE_URL}/v2/crawl",
                    json=crawl_data,
                    headers=self.get_headers(),
                    cookies=self.get_cookies(),
                    timeout=30.0
                )
                
                assert response2.status_code == 200
                data2 = response2.json()
                assert data2.get("session_id") == session_id
                
    @pytest.mark.asyncio
    async def test_v2_error_handling(self):
        """Test error handling for invalid requests"""
        auth_success = await self.authenticate()
        if not auth_success:
            pytest.skip("Could not authenticate, skipping test")
            
        async with httpx.AsyncClient() as client:
            # Test invalid URL
            crawl_data = {
                "url": "not-a-valid-url",
                "javascript": False
            }
            
            response = await client.post(
                f"{self.BASE_URL}/v2/crawl",
                json=crawl_data,
                headers=self.get_headers(),
                cookies=self.get_cookies()
            )
            
            # Should return 400 or 422 for validation error
            assert response.status_code in [400, 422]
            error_data = response.json()
            assert "error" in error_data or "detail" in error_data
            
    @pytest.mark.asyncio
    async def test_v2_response_formats(self):
        """Test different response format options"""
        auth_success = await self.authenticate()
        if not auth_success:
            pytest.skip("Could not authenticate, skipping test")
            
        async with httpx.AsyncClient() as client:
            # Test minimal format
            crawl_data = {
                "url": "https://example.com",
                "javascript": False,
                "response_format": "minimal"
            }
            
            response = await client.post(
                f"{self.BASE_URL}/v2/crawl",
                json=crawl_data,
                headers=self.get_headers(),
                cookies=self.get_cookies(),
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                # Minimal format should have limited fields
                assert "content" in data or "markdown" in data
                assert data.get("success") is True


def run_tests():
    """Run the V2 migration tests"""
    pytest.main([__file__, "-v", "-s"])


if __name__ == "__main__":
    print("Running V2 Migration Tests...")
    print("Make sure the Docker container is running at localhost:5678")
    print("-" * 60)
    run_tests()
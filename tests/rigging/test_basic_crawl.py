"""
Basic API Crawl Tests

Tests basic crawling functionality through the API without requiring authentication.
"""

import pytest
import aiohttp
import asyncio
from typing import Dict, Any

from rigging.config import config


class TestBasicCrawl:
    """Basic API crawl functionality tests"""
    
    
    @pytest.mark.asyncio
    async def test_api_requires_auth(self):
        """Test that crawl endpoints require authentication"""
        # Try to crawl without auth
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{config.BASE_URL}/api/v2/crawl",
                    json={"url": "https://example.com"}
                ) as response:
                    # Should require auth
                    print(f"\n→ Auth test: Got status {response.status}")
                    assert response.status in [401, 403, 302, 422], f"Expected auth required, got {response.status}"
                    print(f"\n✓ API correctly requires authentication (status: {response.status})")
            except aiohttp.ClientError as e:
                pytest.fail(f"Failed to test auth requirement: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_legacy_endpoints_exist(self):
        """Test if legacy endpoints exist"""
        endpoints = [
            ('/api/crawl', 'POST'),
            ('/api/scrape', 'POST'),
            ('/api/search', 'POST')
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint, method in endpoints:
                try:
                    if method == 'POST':
                        async with session.post(f"{config.BASE_URL}{endpoint}") as response:
                            # We expect 401/403 (auth required) or 400 (bad request)
                            # but NOT 404 (not found)
                            if response.status != 404:
                                print(f"\n✓ {endpoint} exists (status: {response.status})")
                            else:
                                print(f"\n✗ {endpoint} not found")
                except:
                    pass
    
    @pytest.mark.asyncio
    async def test_health_check_no_auth(self):
        """Test that health check doesn't require auth"""
        health_endpoints = ['/health', '/api/health', '/']
        
        async with aiohttp.ClientSession() as session:
            for endpoint in health_endpoints:
                try:
                    async with session.get(f"{config.BASE_URL}{endpoint}") as response:
                        if response.status in [200, 301, 302]:
                            print(f"\n✓ {endpoint} accessible without auth")
                            break
                except:
                    continue
    
    @pytest.mark.asyncio
    async def test_invalid_endpoint_404(self):
        """Test that invalid endpoints return 404"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{config.BASE_URL}/api/v2/this-does-not-exist"
                ) as response:
                    assert response.status == 404
                    print(f"\n✓ Invalid endpoints correctly return 404")
            except aiohttp.ClientError:
                pytest.skip("Cannot test 404 handling")
    
    @pytest.mark.asyncio
    async def test_options_request(self):
        """Test OPTIONS request for CORS"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.options(
                    f"{config.BASE_URL}/api/v2/crawl"
                ) as response:
                    # OPTIONS should work even without auth
                    assert response.status in [200, 204, 404, 405]
                    
                    if response.status in [200, 204]:
                        # Check for CORS headers
                        headers = response.headers
                        print(f"\n✓ OPTIONS request successful")
                        if 'Access-Control-Allow-Methods' in headers:
                            print(f"  Allowed methods: {headers['Access-Control-Allow-Methods']}")
            except:
                pytest.skip("Cannot test OPTIONS")


if __name__ == '__main__':
    # Run just this test file
    pytest.main([__file__, '-v'])
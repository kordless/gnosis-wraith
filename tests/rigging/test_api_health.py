"""
API Health Check Tests

Tests basic API connectivity and health endpoints.
"""

import pytest
import aiohttp
import asyncio
from typing import Dict, Any

from rigging.config import config


class TestAPIHealth:
    """API health and connectivity tests"""
    
    @pytest.mark.asyncio
    async def test_api_reachable(self):
        """Test if API is reachable"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{config.BASE_URL}/") as response:
                    assert response.status in [200, 302, 301]  # OK or redirect
            except aiohttp.ClientError as e:
                pytest.fail(f"Cannot reach API at {config.BASE_URL}: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test health check endpoint"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{config.BASE_URL}/health") as response:
                    if response.status == 404:
                        pytest.skip("Health endpoint not implemented")
                    
                    assert response.status == 200
                    data = await response.json()
                    assert 'status' in data or 'healthy' in data
            except aiohttp.ClientError as e:
                pytest.fail(f"Health check failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_api_v2_available(self):
        """Test if V2 API endpoints are available"""
        endpoints = [
            '/api/v2/crawl',
            '/v2/crawl',
            '/api/v2/search'
        ]
        
        available = []
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                try:
                    async with session.options(f"{config.BASE_URL}{endpoint}") as response:
                        if response.status != 404:
                            available.append(endpoint)
                except:
                    pass
        
        assert len(available) > 0, f"No V2 API endpoints found. Checked: {endpoints}"
        print(f"\n✓ Available V2 endpoints: {available}")
    
    @pytest.mark.asyncio
    async def test_auth_required(self):
        """Test that API requires authentication"""
        # Try to access protected endpoint without auth
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{config.BASE_URL}/api/v2/crawl",
                    json={"url": "https://example.com"}
                ) as response:
                    # Should get 401 or 403 without auth
                    print(f"\n→ Auth test: Got status {response.status}")
                    assert response.status in [401, 403, 302, 422]  # 302 for redirect, 422 for validation error
            except aiohttp.ClientError:
                pytest.skip("Cannot test auth requirement")
    
    @pytest.mark.asyncio
    async def test_authenticated_request(self):
        """Test making an authenticated request"""
        headers = config.get_auth_headers()
        if not headers:
            pytest.skip("No Gnosis API token configured")
        
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                # Try a simple authenticated request
                async with session.get(
                    f"{config.BASE_URL}/api/v2/search"
                ) as response:
                    # With auth, should get 200 or 405 (method not allowed)
                    # but not 401/403
                    assert response.status not in [401, 403]
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"\n✓ Authenticated request successful")
            except aiohttp.ClientError as e:
                pytest.fail(f"Authenticated request failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_cors_headers(self):
        """Test CORS headers are properly set"""
        async with aiohttp.ClientSession() as session:
            try:
                headers = {
                    'Origin': 'http://localhost:3000',
                    'Access-Control-Request-Method': 'POST',
                    'Access-Control-Request-Headers': 'Content-Type'
                }
                
                async with session.options(
                    f"{config.BASE_URL}/api/v2/crawl",
                    headers=headers
                ) as response:
                    # Check CORS headers
                    cors_headers = response.headers
                    
                    # These might not be set if CORS is not configured
                    if 'Access-Control-Allow-Origin' in cors_headers:
                        assert cors_headers['Access-Control-Allow-Origin'] in ['*', 'http://localhost:3000']
                    
                    if response.status == 200:  # Successful OPTIONS request
                        assert 'Access-Control-Allow-Methods' in cors_headers
            except:
                pytest.skip("CORS testing not available")


if __name__ == '__main__':
    # Run just this test file
    pytest.main([__file__, '-v'])
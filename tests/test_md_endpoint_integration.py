"""
Integration test for existing /md endpoint
Tests the real API to ensure it works before adding batch functionality
"""
import pytest
import aiohttp
import asyncio
import json
import os

# API configuration
API_KEY = "uiBv8UPjRORy5XLL5mCMwekdxmuseFJ1wcfTuWDHftwXyfzsFrhfxg"
BASE_URL = "http://localhost:5678"  # As per CLAUDE.local.md


class TestMarkdownEndpointIntegration:
    """Integration tests for the /md endpoint"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_existing_md_endpoint_works(self):
        """Test that the current /md endpoint works with a single URL"""
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }
            
            # Test with a simple, fast-loading page
            data = {
                "url": "https://example.com",
                "filter": "none"  # Start with no filtering
            }
            
            async with session.post(
                f"{BASE_URL}/api/markdown",
                json=data,
                headers=headers
            ) as response:
                # Check status
                assert response.status == 200, f"Expected 200, got {response.status}: {await response.text()}"
                
                # Parse response
                result = await response.json()
                
                # Verify response structure based on actual API
                assert "success" in result
                assert result["success"] == True
                assert "markdown" in result
                assert "markdown_url" in result
                assert "json_url" in result
                assert "url" in result
                assert result["url"] == "https://example.com"
                assert "stats" in result
                assert "references" in result
                
                # Verify markdown content exists
                assert len(result["markdown"]) > 0
                assert "Example Domain" in result["markdown"]  # example.com always has this
                
                print(f"\n✓ Single URL request successful")
                print(f"  - Markdown length: {len(result['markdown'])} chars")
                print(f"  - Response fields: {list(result.keys())}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_md_endpoint_with_filter(self):
        """Test /md endpoint with pruning filter"""
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }
            
            data = {
                "url": "https://example.com",
                "filter": "pruning",
                "filter_options": {
                    "threshold": 0.5
                }
            }
            
            async with session.post(
                f"{BASE_URL}/api/markdown",
                json=data,
                headers=headers
            ) as response:
                assert response.status == 200
                result = await response.json()
                
                assert result["success"] == True
                assert "markdown" in result
                assert "filter_applied" in result
                assert result["filter_applied"] == "pruning"
                
                print(f"\n✓ Filtered request successful")
                print(f"  - Filter: {result['filter_applied']}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_md_endpoint_with_javascript(self):
        """Test /md endpoint with JavaScript enabled"""
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }
            
            data = {
                "url": "https://example.com",
                "javascript_enabled": True
            }
            
            async with session.post(
                f"{BASE_URL}/api/markdown",
                json=data,
                headers=headers
            ) as response:
                assert response.status == 200
                result = await response.json()
                
                assert result["success"] == True
                assert "javascript_enabled" in result
                assert result["javascript_enabled"] == True
                
                print(f"\n✓ JavaScript-enabled request successful")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_md_endpoint_error_handling(self):
        """Test /md endpoint error handling with invalid URL"""
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }
            
            data = {
                "url": "not-a-valid-url"
            }
            
            async with session.post(
                f"{BASE_URL}/api/markdown",
                json=data,
                headers=headers
            ) as response:
                # Should still return 200 but with success=false
                result = await response.json()
                
                if response.status == 200:
                    assert result["success"] == False
                    assert "error" in result
                else:
                    # Or might return 400
                    assert response.status == 400
                
                print(f"\n✓ Error handling works correctly")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_md_endpoint_auth_required(self):
        """Test that /md endpoint requires authentication"""
        async with aiohttp.ClientSession() as session:
            data = {
                "url": "https://example.com"
            }
            
            # No auth header
            async with session.post(
                f"{BASE_URL}/api/markdown",
                json=data
            ) as response:
                assert response.status in [401, 403], f"Expected 401/403, got {response.status}"
                
                print(f"\n✓ Authentication is properly enforced")


# Helper to run a specific test
async def run_single_test():
    """Run just the basic test to verify setup"""
    test = TestMarkdownEndpointIntegration()
    await test.test_existing_md_endpoint_works()


if __name__ == "__main__":
    # Run just the basic test
    print("Testing existing /md endpoint...")
    asyncio.run(run_single_test())
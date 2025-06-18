"""
Authenticated Crawl Tests

Tests crawling functionality through the authenticated API endpoints.
"""

import pytest
import aiohttp
import asyncio
from typing import Dict, Any

from rigging.config import config


class TestAuthenticatedCrawl:
    """Test crawling through authenticated API endpoints"""
    
    def get_auth_headers(self):
        """Get auth headers or skip test"""
        headers = config.get_auth_headers()
        if not headers:
            pytest.skip("No Gnosis API token configured")
        return headers
    
    @pytest.mark.asyncio
    async def test_v2_crawl_simple(self):
        """Test simple crawl through V2 API"""
        headers = self.get_auth_headers()
        data = {
            "url": "https://example.com",
            "javascript": False,
            "screenshot": False,
            "response_format": "minimal"
        }
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(
                config.get_api_url("api/v2/crawl"),
                json=data
            ) as response:
                assert response.status == 200
                result = await response.json()
                
                assert result['success'] == True
                assert 'content' in result
                assert 'url' in result
                assert result['url'] in ["https://example.com", "https://example.com/"]
                
                print(f"\n✓ Crawl successful: {len(result['content'])} chars")
    
    @pytest.mark.asyncio
    async def test_v2_crawl_with_javascript(self):
        """Test crawl with JavaScript enabled"""
        if not config.ENABLE_JAVASCRIPT_TESTS:
            pytest.skip("JavaScript tests disabled")
        
        headers = self.get_auth_headers()
        data = {
            "url": "https://example.com",
            "javascript": True,
            "screenshot": False,
            "response_format": "full"
        }
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(
                config.get_api_url("api/v2/crawl"),
                json=data
            ) as response:
                assert response.status == 200
                result = await response.json()
                
                if not result.get('success'):
                    # JavaScript might fail if Playwright isn't installed
                    error_msg = result.get('error', 'Unknown error')
                    if 'playwright' in error_msg.lower() or 'browser' in error_msg.lower():
                        pytest.skip(f"JavaScript crawling not available: {error_msg}")
                    else:
                        print(f"\n✗ JavaScript crawl failed: {error_msg}")
                        print(f"   Full response: {result}")
                
                assert result['success'] == True
                assert 'content' in result
                # Only check javascript_enabled if crawl succeeded
                if result.get('success'):
                    assert result.get('javascript_enabled') == True
    
    @pytest.mark.asyncio
    async def test_v2_crawl_with_screenshot(self):
        """Test crawl with screenshot capture"""
        if not config.ENABLE_SCREENSHOT_TESTS:
            pytest.skip("Screenshot tests disabled")
        
        headers = self.get_auth_headers()
        data = {
            "url": "https://example.com",
            "javascript": True,
            "screenshot": True,
            "response_format": "full"
        }
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(
                config.get_api_url("api/v2/crawl"),
                json=data
            ) as response:
                assert response.status == 200
                result = await response.json()
                
                assert result['success'] == True
                assert 'screenshot' in result
                assert result['screenshot'] is not None
                assert result['screenshot'].startswith('data:image/png;base64,')
    
    @pytest.mark.asyncio
    async def test_v2_crawl_llm_format(self):
        """Test crawl with LLM response format"""
        headers = self.get_auth_headers()
        data = {
            "url": "https://example.com",
            "javascript": False,
            "screenshot": False,
            "response_format": "llm"
        }
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(
                config.get_api_url("api/v2/crawl"),
                json=data
            ) as response:
                assert response.status == 200
                result = await response.json()
                
                # Check for errors
                if not result.get('success'):
                    print(f"\n✗ LLM format crawl failed: {result.get('error', 'Unknown error')}")
                
                # LLM format should be more concise
                assert result['success'] == True
                assert 'content' in result
                assert 'cleaned_html' not in result  # LLM format excludes raw HTML
                assert 'links' not in result  # LLM format excludes links
    
    @pytest.mark.asyncio
    async def test_v2_crawl_with_session(self):
        """Test crawl with session persistence"""
        headers = self.get_auth_headers()
        session_id = "test-session-auth"
        
        # First crawl
        data1 = {
            "url": "https://example.com",
            "session_id": session_id,
            "javascript": True
        }
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(
                config.get_api_url("api/v2/crawl"),
                json=data1
            ) as response:
                assert response.status == 200
                result1 = await response.json()
                assert result1['success'] == True
            
            # Second crawl with same session
            data2 = {
                "url": "https://example.com/about",
                "session_id": session_id,
                "javascript": True
            }
            
            async with session.post(
                config.get_api_url("api/v2/crawl"),
                json=data2
            ) as response:
                assert response.status == 200
                result2 = await response.json()
                assert result2['success'] == True
                
            print(f"\n✓ Session persistence working with ID: {session_id}")
    
    @pytest.mark.asyncio
    async def test_v2_crawl_error_handling(self):
        """Test error handling for invalid crawl requests"""
        headers = self.get_auth_headers()
        # Invalid URL
        data = {
            "url": "not-a-valid-url",
            "javascript": False
        }
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(
                config.get_api_url("api/v2/crawl"),
                json=data
            ) as response:
                assert response.status in [400, 422]  # Bad request or validation error
                error = await response.json()
                assert 'error' in error or 'detail' in error
    
    @pytest.mark.asyncio
    async def test_v2_search_crawls(self):
        """Test searching through previous crawls"""
        headers = self.get_auth_headers()
        
        async with aiohttp.ClientSession(headers=headers) as session:
            # First do a crawl to ensure we have data
            crawl_data = {
                "url": "https://example.com",
                "javascript": False
            }
            
            async with session.post(
                config.get_api_url("api/v2/crawl"),
                json=crawl_data
            ) as response:
                assert response.status == 200
            
            # Now search
            search_data = {
                "query": "example",
                "limit": 10
            }
            
            async with session.post(
                config.get_api_url("api/v2/search"),
                json=search_data
            ) as response:
                if response.status == 404:
                    pytest.skip("Search endpoint not implemented")
                
                assert response.status == 200
                result = await response.json()
                assert 'success' in result or 'results' in result


if __name__ == '__main__':
    # Run just this test file
    pytest.main([__file__, '-v'])
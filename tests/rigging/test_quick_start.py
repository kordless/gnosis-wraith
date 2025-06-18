"""
Quick Start Test

Simple example showing how to write authenticated tests.
"""

import pytest
from rigging.config import config
from rigging.utils.auth_helper import (
    AuthenticatedClient, 
    authenticated_crawl,
    require_auth
)


class TestQuickStart:
    """Quick start examples for writing tests"""
    
    @pytest.mark.asyncio
    @require_auth
    async def test_simple_crawl_example(self):
        """Example: Simple authenticated crawl"""
        # Using the helper function
        result = await authenticated_crawl("https://example.com")
        
        assert result['success'] == True
        assert 'content' in result
        print(f"\n✓ Crawled {result['url']}")
    
    @pytest.mark.asyncio
    @require_auth
    async def test_crawl_with_options_example(self):
        """Example: Crawl with options"""
        result = await authenticated_crawl(
            "https://example.com",
            javascript=True,
            screenshot=config.ENABLE_SCREENSHOT_TESTS,
            response_format="minimal"
        )
        
        assert result['success'] == True
        print(f"\n✓ Crawled with options: JS={result.get('javascript_enabled')}")
    
    @pytest.mark.asyncio
    async def test_using_client_class(self):
        """Example: Using the AuthenticatedClient class"""
        # This gives more control
        client = AuthenticatedClient()
        
        # Check if we have auth
        if not client.token:
            pytest.skip("No auth token")
        
        # Multiple requests with same client
        result1 = await client.crawl("https://example.com")
        result2 = await client.search("example")
        
        assert result1['success'] == True
        print(f"\n✓ Made multiple authenticated requests")
    
    @pytest.mark.asyncio
    async def test_handling_errors(self):
        """Example: Proper error handling"""
        client = AuthenticatedClient()
        
        if not client.token:
            pytest.skip("No auth token")
        
        # Test with invalid URL
        result = await client.crawl("not-a-valid-url")
        
        # The helper adds _status_code to results
        assert result['_status_code'] in [400, 422]
        assert result['success'] == False
        assert 'error' in result
        
        print(f"\n✓ Error handled properly: {result['error']}")
    
    @pytest.mark.asyncio
    async def test_without_auth(self):
        """Example: Testing without authentication"""
        # This test doesn't use @require_auth decorator
        # so it will run even without token
        
        # You can check for auth and handle it
        if config.check_gnosis_auth():
            result = await authenticated_crawl("https://example.com")
            assert result['success'] == True
        else:
            print("\n⚠️  Skipping authenticated test - no token")
            # Do alternative testing or skip
            assert True  # Pass the test


# Quick test runner for this file
if __name__ == '__main__':
    print("\n🚀 Quick Start Test Examples\n")
    print("Make sure you have:")
    print("1. Gnosis Wraith running (docker-compose up)")
    print("2. Your API token in tests/.env")
    print("\nRunning tests...\n")
    
    pytest.main([__file__, '-v'])
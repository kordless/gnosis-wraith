"""
Simple AI Integration Tests

Basic tests for AI functionality through the API with any configured AI provider.
"""

import pytest
import asyncio
from typing import Dict, Any

from rigging.config import config, TestConfig
from rigging.utils.auth_helper import AuthenticatedClient


class TestAISimple:
    """Simple AI integration tests through API"""
    
    @pytest.fixture
    def client(self):
        """Create authenticated API client"""
        if not config.check_gnosis_auth():
            pytest.skip("No Gnosis API token configured")
        return AuthenticatedClient()
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not config.ENABLE_AI_TESTS, reason="AI tests disabled")
    async def test_ai_crawl_with_extraction(self, client):
        """Test crawling with AI content extraction"""
        # Check if we have at least one AI provider
        providers = ['openai', 'anthropic', 'google']
        available = [p for p in providers if config.has_api_key(p)]
        
        if not available:
            pytest.skip("No AI API keys configured")
        
        # Try to crawl with AI extraction
        result = await client.crawl(
            "https://example.com",
            response_format="llm"  # This should trigger AI processing
        )
        
        if result['_status_code'] != 200:
            pytest.skip(f"API returned {result['_status_code']}: {result.get('error', 'Unknown error')}")
        
        assert result['success'] == True
        assert 'content' in result
        print(f"\n✓ AI-enhanced crawl completed successfully")
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not config.ENABLE_AI_TESTS, reason="AI tests disabled")
    async def test_crawl_with_javascript_and_ai(self, client):
        """Test crawling with JavaScript and AI processing"""
        if not config.ENABLE_JAVASCRIPT_TESTS:
            pytest.skip("JavaScript tests disabled")
        
        # Check for AI providers
        if not any(config.has_api_key(p) for p in ['openai', 'anthropic', 'google']):
            pytest.skip("No AI API keys configured")
        
        result = await client.crawl(
            "https://example.com",
            javascript=True,
            response_format="llm"
        )
        
        if result['_status_code'] != 200:
            pytest.skip(f"API returned {result['_status_code']}")
        
        assert result['success'] == True
        assert result.get('javascript_enabled') == True
        print(f"\n✓ JavaScript + AI crawl completed")
    
    @pytest.mark.asyncio
    async def test_ai_provider_configuration(self):
        """Test AI provider configuration check"""
        providers = {
            'openai': config.has_api_key('openai'),
            'anthropic': config.has_api_key('anthropic'),
            'google': config.has_api_key('google')
        }
        
        configured = [k for k, v in providers.items() if v]
        
        print(f"\n📋 AI Provider Status:")
        for provider, has_key in providers.items():
            status = "✓ Configured" if has_key else "✗ Not configured"
            print(f"   {provider.capitalize()}: {status}")
        
        if configured:
            print(f"\n✓ {len(configured)} AI provider(s) available: {', '.join(configured)}")
        else:
            print(f"\n⚠️  No AI providers configured - AI tests will be skipped")


if __name__ == '__main__':
    # Run just this test file
    pytest.main([__file__, '-v'])
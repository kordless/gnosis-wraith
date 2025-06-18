"""
V2 Integration Tests - Direct function testing
Tests the V2 functionality directly without HTTP layer
"""
import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.crawl_functions import crawl_url_direct, estimate_crawl_time
from core.integration import WraithIntegration
from ai.tools.web_crawling import (
    crawl_webpage_with_smart_execution,
    crawl_website_with_depth_control,
    capture_screenshot_of_webpage
)
from ai.tools.content_processing import (
    extract_structured_data_with_schema,
    convert_html_to_clean_markdown
)


class TestCrawlFunctions:
    """Test core crawl functions"""
    
    @pytest.mark.asyncio
    async def test_estimate_crawl_time(self):
        """Test crawl time estimation"""
        # Simple crawl
        simple_time = estimate_crawl_time(
            "https://example.com",
            {"javascript": False, "screenshot": False, "depth": 0}
        )
        assert simple_time < 3.0
        
        # Complex crawl
        complex_time = estimate_crawl_time(
            "https://example.com",
            {"javascript": True, "screenshot": True, "depth": 2}
        )
        assert complex_time > 3.0
        
    @pytest.mark.asyncio
    async def test_crawl_url_direct_sync(self):
        """Test synchronous crawl execution"""
        with patch('core.crawl_functions._crawl_sync') as mock_sync:
            mock_sync.return_value = {
                "success": True,
                "url": "https://example.com",
                "content": "Test content",
                "markdown": "# Test content"
            }
            
            result = await crawl_url_direct(
                "https://example.com",
                {"javascript": False, "screenshot": False}
            )
            
            assert result["success"] is True
            assert result["url"] == "https://example.com"
            assert "content" in result
            mock_sync.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_crawl_url_direct_async(self):
        """Test asynchronous crawl execution"""
        with patch('core.crawl_functions._crawl_async') as mock_async:
            mock_async.return_value = {
                "job_id": "test-job-123",
                "estimated_time": 10
            }
            
            result = await crawl_url_direct(
                "https://example.com",
                {"javascript": True, "screenshot": True, "depth": 2}
            )
            
            assert result["async"] is True
            assert result["job_id"] == "test-job-123"
            assert result["estimated_time"] == 10
            mock_async.assert_called_once()


class TestMCPTools:
    """Test MCP tool functions"""
    
    @pytest.mark.asyncio
    async def test_crawl_webpage_tool(self):
        """Test webpage crawling tool"""
        with patch('core.crawl_functions.crawl_url_direct') as mock_crawl:
            mock_crawl.return_value = {
                "success": True,
                "content": "Test content",
                "url": "https://example.com"
            }
            
            result = await crawl_webpage_with_smart_execution(
                url="https://example.com",
                enable_javascript=False,
                capture_screenshot=False
            )
            
            assert result["success"] is True
            assert "content" in result
            
    @pytest.mark.asyncio
    async def test_extract_structured_data_tool(self):
        """Test structured data extraction"""
        test_content = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Main Title</h1>
                <p>Some content here</p>
            </body>
        </html>
        """
        
        schema = {
            "title": "Page title",
            "heading": "Main heading"
        }
        
        result = await extract_structured_data_with_schema(
            content=test_content,
            schema=schema
        )
        
        assert "structured_data" in result
        assert result["success"] is True
        
    @pytest.mark.asyncio
    async def test_convert_html_to_markdown(self):
        """Test HTML to markdown conversion"""
        html_content = """
        <html>
            <body>
                <h1>Title</h1>
                <p>Paragraph with <strong>bold</strong> text</p>
                <ul>
                    <li>Item 1</li>
                    <li>Item 2</li>
                </ul>
            </body>
        </html>
        """
        
        result = await convert_html_to_clean_markdown(
            html_content=html_content,
            include_links=True,
            include_images=True
        )
        
        assert "markdown" in result
        assert "# Title" in result["markdown"]
        assert "**bold**" in result["markdown"]
        assert result["success"] is True


class TestWorkflows:
    """Test workflow integration"""
    
    @pytest.mark.asyncio
    async def test_analyze_website_workflow(self):
        """Test website analysis workflow"""
        integration = WraithIntegration()
        
        with patch('core.crawl_functions.crawl_url_direct') as mock_crawl:
            mock_crawl.return_value = {
                "success": True,
                "content": "<h1>Test Site</h1><p>Content</p>",
                "markdown": "# Test Site\n\nContent",
                "links": ["https://example.com/page1", "https://example.com/page2"]
            }
            
            result = await integration.execute_workflow(
                "analyze_website",
                {"url": "https://example.com"}
            )
            
            assert result["success"] is True
            assert result["steps_completed"] > 0
            assert "analysis" in result
            
    @pytest.mark.asyncio
    async def test_extract_data_workflow(self):
        """Test data extraction workflow"""
        integration = WraithIntegration()
        
        with patch('core.crawl_functions.crawl_url_direct') as mock_crawl:
            mock_crawl.return_value = {
                "success": True,
                "content": "<h1>Product Page</h1><p>Price: $99.99</p>",
                "url": "https://example.com/product"
            }
            
            schema = {
                "product_name": "Product name",
                "price": "Product price"
            }
            
            result = await integration.execute_workflow(
                "extract_data",
                {"url": "https://example.com/product", "schema": schema}
            )
            
            assert result["success"] is True
            assert "extracted_data" in result
            
    @pytest.mark.asyncio
    async def test_monitor_changes_workflow(self):
        """Test change monitoring workflow"""
        integration = WraithIntegration()
        
        with patch('core.crawl_functions.crawl_url_direct') as mock_crawl:
            # First crawl
            mock_crawl.return_value = {
                "success": True,
                "content": "Original content",
                "crawl_id": "crawl-1"
            }
            
            result = await integration.execute_workflow(
                "monitor_changes",
                {"url": "https://example.com", "previous_crawl_id": "crawl-0"}
            )
            
            assert result["success"] is True
            assert "current_crawl_id" in result
            assert "changes_detected" in result


class TestSessionManagement:
    """Test browser session management"""
    
    @pytest.mark.asyncio
    async def test_session_persistence(self):
        """Test that sessions persist between crawls"""
        with patch('core.crawl_functions.BrowserSessionManager') as MockSessionManager:
            mock_manager = Mock()
            mock_session = Mock()
            mock_session.id = "test-session-123"
            
            MockSessionManager.return_value = mock_manager
            mock_manager.get_or_create_session.return_value = mock_session
            
            # First crawl
            result1 = await crawl_url_direct(
                "https://example.com",
                {"javascript": False},
                session_id=None
            )
            
            # Second crawl with session
            result2 = await crawl_url_direct(
                "https://example.com",
                {"javascript": False},
                session_id="test-session-123"
            )
            
            # Session should be reused
            assert mock_manager.get_or_create_session.call_count >= 1


class TestErrorHandling:
    """Test error handling in V2 components"""
    
    @pytest.mark.asyncio
    async def test_invalid_url_handling(self):
        """Test handling of invalid URLs"""
        result = await crawl_url_direct(
            "not-a-valid-url",
            {"javascript": False}
        )
        
        assert result["success"] is False
        assert "error" in result
        
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self):
        """Test workflow error handling"""
        integration = WraithIntegration()
        
        with patch('core.crawl_functions.crawl_url_direct') as mock_crawl:
            mock_crawl.side_effect = Exception("Network error")
            
            result = await integration.execute_workflow(
                "analyze_website",
                {"url": "https://example.com"}
            )
            
            assert result["success"] is False
            assert "error" in result
            assert "Network error" in result["error"]


def run_tests():
    """Run the integration tests"""
    pytest.main([__file__, "-v", "-s"])


if __name__ == "__main__":
    print("Running V2 Integration Tests...")
    print("-" * 60)
    run_tests()
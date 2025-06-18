"""
Core Scraping Endpoint Tests
"""

import pytest
import sys
from pathlib import Path
from typing import Dict

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.test_base import BaseAPITest, assert_valid_url, assert_valid_markdown, assert_valid_screenshot


class TestScrapeEndpoint(BaseAPITest):
    """Test /v2/scrape endpoint"""
    
    def test_basic_scrape(self):
        """Test basic webpage scraping"""
        
        response = self.make_request("POST", "/scrape", json={
            "url": self.get_test_url(),
            "formats": ["markdown"]
        })
        
        data = self.assert_success_response(response)
        
        # Validate response structure
        assert "data" in data
        assert "markdown" in data["data"]
        assert "url" in data["data"]
        assert "metadata" in data["data"]
        
        # Validate content
        assert_valid_markdown(data["data"]["markdown"])
        assert data["data"]["url"] == self.get_test_url()
        
        # Validate metadata
        metadata = data["data"]["metadata"]
        assert "title" in metadata
        assert "statusCode" in metadata
        assert metadata["statusCode"] == 200
    
    def test_multiple_formats(self):
        """Test scraping with multiple output formats"""
        
        formats = ["markdown", "html", "screenshot", "links", "text"]
        
        response = self.make_request("POST", "/scrape", json={
            "url": self.get_test_url(),
            "formats": formats
        })
        
        data = self.assert_success_response(response)
        
        # Check all requested formats are present
        for format in formats:
            assert format in data["data"], f"Missing format: {format}"
        
        # Validate format contents
        assert_valid_markdown(data["data"]["markdown"])
        assert "<html" in data["data"]["html"].lower()
        assert_valid_screenshot(data["data"]["screenshot"])
        assert isinstance(data["data"]["links"], list)
        assert isinstance(data["data"]["text"], str)
        
        # Validate links structure
        if data["data"]["links"]:
            link = data["data"]["links"][0]
            assert "href" in link
            assert "text" in link
    
    def test_scrape_options(self):
        """Test scraping with various options"""
        
        response = self.make_request("POST", "/scrape", json={
            "url": self.get_test_url(),
            "formats": ["markdown"],
            "options": {
                "wait_for": 3000,
                "timeout": 20000,
                "headers": {
                    "User-Agent": "TestBot/1.0",
                    "Accept-Language": "en-US"
                },
                "viewport": {
                    "width": 1920,
                    "height": 1080
                }
            }
        })
        
        data = self.assert_success_response(response)
        assert "markdown" in data["data"]
    
    def test_javascript_disabled(self):
        """Test scraping with JavaScript disabled"""
        
        response = self.make_request("POST", "/scrape", json={
            "url": self.get_test_url(),
            "formats": ["markdown"],
            "options": {
                "javascript": False
            }
        })
        
        data = self.assert_success_response(response)
        assert "markdown" in data["data"]
    
    def test_custom_viewport(self):
        """Test different viewport sizes"""
        
        viewports = [
            {"width": 375, "height": 667},   # Mobile
            {"width": 768, "height": 1024},  # Tablet  
            {"width": 1920, "height": 1080}  # Desktop
        ]
        
        for viewport in viewports:
            response = self.make_request("POST", "/scrape", json={
                "url": self.get_test_url(),
                "formats": ["screenshot"],
                "options": {
                    "viewport": viewport
                }
            })
            
            data = self.assert_success_response(response)
            assert "screenshot" in data["data"]
    
    def test_authentication_options(self):
        """Test basic auth and cookies"""
        
        # Test with basic auth
        response = self.make_request("POST", "/scrape", json={
            "url": "https://httpbin.org/basic-auth/user/pass",
            "formats": ["markdown"],
            "options": {
                "auth": {
                    "username": "user",
                    "password": "pass"
                }
            }
        })
        
        # Should succeed with correct auth
        data = self.assert_success_response(response)
        
        # Test with cookies
        response = self.make_request("POST", "/scrape", json={
            "url": "https://httpbin.org/cookies",
            "formats": ["markdown"],
            "options": {
                "cookies": [
                    {
                        "name": "test_cookie",
                        "value": "test_value",
                        "domain": ".httpbin.org"
                    }
                ]
            }
        })
        
        data = self.assert_success_response(response)
        # Should see the cookie in the response
        assert "test_cookie" in data["data"]["markdown"]
    
    def test_wait_strategies(self):
        """Test different wait strategies"""
        
        strategies = [
            {"wait_until": "load"},
            {"wait_until": "domcontentloaded"},
            {"wait_until": "networkidle"},
            {"wait_for_selector": "body"},
            {"wait_for": 2000}
        ]
        
        for strategy in strategies:
            response = self.make_request("POST", "/scrape", json={
                "url": self.get_test_url(),
                "formats": ["markdown"],
                "options": strategy
            })
            
            data = self.assert_success_response(response)
            assert "markdown" in data["data"]
    
    def test_resource_blocking(self):
        """Test blocking specific resources"""
        
        response = self.make_request("POST", "/scrape", json={
            "url": self.get_test_url(),
            "formats": ["markdown", "screenshot"],
            "options": {
                "block_resources": ["image", "font", "stylesheet"]
            }
        })
        
        data = self.assert_success_response(response)
        assert "markdown" in data["data"]
        assert "screenshot" in data["data"]
    
    def test_full_page_screenshot(self):
        """Test full page screenshot option"""
        
        response = self.make_request("POST", "/scrape", json={
            "url": self.get_test_url(),
            "formats": ["screenshot"],
            "options": {
                "full_page": True
            }
        })
        
        data = self.assert_success_response(response)
        assert_valid_screenshot(data["data"]["screenshot"])
    
    def test_metadata_extraction(self):
        """Test metadata extraction"""
        
        response = self.make_request("POST", "/scrape", json={
            "url": "https://www.example.com",
            "formats": ["markdown"]
        })
        
        data = self.assert_success_response(response)
        metadata = data["data"]["metadata"]
        
        # Check expected metadata fields
        expected_fields = ["title", "statusCode", "contentType"]
        for field in expected_fields:
            assert field in metadata, f"Missing metadata field: {field}"
        
        # Validate metadata values
        assert isinstance(metadata["statusCode"], int)
        assert metadata["statusCode"] == 200
        assert "text/html" in metadata["contentType"]
    
    def test_processing_time(self):
        """Test that processing time is reported"""
        
        response = self.make_request("POST", "/scrape", json={
            "url": self.get_test_url(),
            "formats": ["markdown"]
        })
        
        data = self.assert_success_response(response)
        
        # Check for timing information
        if "processing_time_ms" in data:
            assert isinstance(data["processing_time_ms"], (int, float))
            assert data["processing_time_ms"] > 0
    
    def test_scrape_id(self):
        """Test that scrape ID is returned"""
        
        response = self.make_request("POST", "/scrape", json={
            "url": self.get_test_url(),
            "formats": ["markdown"]
        })
        
        data = self.assert_success_response(response)
        
        if "scrape_id" in data:
            assert isinstance(data["scrape_id"], str)
            assert len(data["scrape_id"]) > 5


class TestScrapeErrorHandling(BaseAPITest):
    """Test error handling for scrape endpoint"""
    
    def test_invalid_url(self):
        """Test scraping with invalid URL"""
        
        invalid_urls = [
            "not-a-url",
            "http://",
            "ftp://example.com",
            "",
            "javascript:alert(1)"
        ]
        
        for url in invalid_urls:
            response = self.make_request("POST", "/scrape", json={
                "url": url,
                "formats": ["markdown"]
            })
            
            assert response.status_code == 400
            self.assert_error_response(response, "INVALID_URL")
    
    def test_missing_url(self):
        """Test request without URL"""
        
        response = self.make_request("POST", "/scrape", json={
            "formats": ["markdown"]
        })
        
        assert response.status_code == 400
    
    def test_invalid_formats(self):
        """Test with invalid format types"""
        
        response = self.make_request("POST", "/scrape", json={
            "url": self.get_test_url(),
            "formats": ["invalid_format", "another_bad_one"]
        })
        
        # Should either ignore invalid formats or return error
        if response.status_code == 200:
            data = response.json()
            # Check that invalid formats are not in response
            assert "invalid_format" not in data.get("data", {})
        else:
            assert response.status_code == 400
    
    def test_timeout_handling(self):
        """Test timeout behavior"""
        
        response = self.make_request("POST", "/scrape", json={
            "url": "https://httpbin.org/delay/10",
            "formats": ["markdown"],
            "options": {
                "timeout": 2000  # 2 second timeout
            }
        })
        
        # Should timeout
        if response.status_code != 200:
            self.assert_error_response(response, "TIMEOUT_ERROR")
    
    def test_network_error_handling(self):
        """Test handling of network errors"""
        
        response = self.make_request("POST", "/scrape", json={
            "url": "https://this-domain-does-not-exist-12345.com",
            "formats": ["markdown"]
        })
        
        assert response.status_code in [400, 502]
        
        if response.status_code == 502:
            self.assert_error_response(response, "NETWORK_ERROR")
        else:
            self.assert_error_response(response, "INVALID_URL")
    
    def test_blocked_resource(self):
        """Test handling of blocked resources"""
        
        # This might be blocked by robots.txt
        response = self.make_request("POST", "/scrape", json={
            "url": "https://www.facebook.com/robots.txt",
            "formats": ["markdown"]
        })
        
        # Should either succeed or return blocked error
        if response.status_code != 200:
            data = response.json()
            assert data["error"]["code"] in ["BLOCKED_RESOURCE", "NETWORK_ERROR"]


class TestScrapeEdgeCases(BaseAPITest):
    """Test edge cases for scrape endpoint"""
    
    def test_empty_page(self):
        """Test scraping empty page"""
        
        response = self.make_request("POST", "/scrape", json={
            "url": "https://httpbin.org/status/204",  # No content
            "formats": ["markdown", "html"]
        })
        
        # Should handle gracefully
        if response.status_code == 200:
            data = response.json()
            # Content might be empty or minimal
            assert "data" in data
    
    def test_large_page(self):
        """Test scraping large page"""
        
        response = self.make_request("POST", "/scrape", json={
            "url": "https://httpbin.org/bytes/1000000",  # 1MB of data
            "formats": ["text"],
            "options": {
                "timeout": 30000
            }
        })
        
        # Should handle large content
        if response.status_code == 200:
            data = response.json()
            assert "text" in data["data"]
    
    def test_redirect_handling(self):
        """Test handling of redirects"""
        
        response = self.make_request("POST", "/scrape", json={
            "url": "https://httpbin.org/redirect/3",  # 3 redirects
            "formats": ["markdown"],
            "options": {
                "follow_redirects": True
            }
        })
        
        data = self.assert_success_response(response)
        
        # Should follow redirects and scrape final page
        assert "markdown" in data["data"]
        
        # Final URL might be different
        if "url" in data["data"]:
            assert "get" in data["data"]["url"]  # httpbin redirects to /get
    
    def test_special_characters_in_content(self):
        """Test handling of special characters"""
        
        response = self.make_request("POST", "/scrape", json={
            "url": "https://httpbin.org/encoding/utf8",
            "formats": ["markdown", "text"]
        })
        
        data = self.assert_success_response(response)
        
        # Should handle UTF-8 properly
        content = data["data"]["text"]
        assert "∮" in content or "∫" in content  # Math symbols
        assert "Σ" in content  # Greek letters


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
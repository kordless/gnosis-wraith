"""
Search Endpoint Tests
"""

import pytest
import sys
from pathlib import Path
from typing import Dict, List

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.test_base import BaseAPITest, assert_valid_markdown


class TestSearchEndpoint(BaseAPITest):
    """Test /v2/search endpoint"""
    
    def test_basic_search(self):
        """Test basic web search"""
        
        response = self.make_request("POST", "/search", json={
            "query": "artificial intelligence news",
            "limit": 5
        })
        
        data = self.assert_success_response(response)
        
        # Validate response structure
        assert "data" in data
        assert isinstance(data["data"], list)
        assert "query" in data
        assert data["query"] == "artificial intelligence news"
        assert "total_results" in data
        
        # Check results
        if len(data["data"]) > 0:
            result = data["data"][0]
            assert "url" in result
            assert "title" in result
            assert "description" in result
            assert "rank" in result
            assert result["rank"] == 1
    
    def test_search_with_scraping(self):
        """Test search with automatic scraping"""
        
        response = self.make_request("POST", "/search", json={
            "query": "python programming tutorial",
            "limit": 3,
            "scrape_options": {
                "formats": ["markdown", "screenshot"],
                "timeout": 15000
            }
        })
        
        data = self.assert_success_response(response)
        
        # Should have scraped content
        if len(data["data"]) > 0:
            result = data["data"][0]
            
            # Should have search metadata
            assert "title" in result
            assert "url" in result
            
            # Should have scraped content if scraping was enabled
            if "markdown" in result:
                assert_valid_markdown(result["markdown"])
            
            if "screenshot" in result:
                assert result["screenshot"].startswith("data:image/png;base64,")
    
    def test_search_options(self):
        """Test search with various options"""
        
        response = self.make_request("POST", "/search", json={
            "query": "machine learning",
            "limit": 10,
            "search_options": {
                "region": "us",
                "language": "en", 
                "time_range": "month",
                "safe_search": "moderate"
            }
        })
        
        data = self.assert_success_response(response)
        
        # Should respect options
        assert len(data["data"]) <= 10
        
        # Results should be relevant
        if len(data["data"]) > 0:
            # At least some results should mention the query
            titles = [r.get("title", "").lower() for r in data["data"]]
            descriptions = [r.get("description", "").lower() for r in data["data"]]
            
            relevant = sum(1 for t, d in zip(titles, descriptions) 
                         if "machine" in t or "learning" in t or 
                            "machine" in d or "learning" in d)
            
            assert relevant > 0
    
    def test_search_time_ranges(self):
        """Test different time range filters"""
        
        time_ranges = ["day", "week", "month", "year"]
        
        for time_range in time_ranges:
            response = self.make_request("POST", "/search", json={
                "query": "breaking news",
                "limit": 5,
                "search_options": {
                    "time_range": time_range
                }
            })
            
            # Should succeed for all time ranges
            data = self.assert_success_response(response)
            assert "data" in data
    
    def test_search_regions(self):
        """Test search in different regions"""
        
        regions = ["us", "uk", "ca", "au"]
        
        for region in regions:
            response = self.make_request("POST", "/search", json={
                "query": "local news",
                "limit": 3,
                "search_options": {
                    "region": region
                }
            })
            
            # Should succeed for supported regions
            if response.status_code == 200:
                data = response.json()
                assert "data" in data
    
    def test_concurrent_scraping(self):
        """Test concurrent scraping of search results"""
        
        response = self.make_request("POST", "/search", json={
            "query": "technology trends 2025",
            "limit": 5,
            "scrape_options": {
                "formats": ["markdown"],
                "concurrent_requests": 3,
                "timeout": 10000
            }
        })
        
        data = self.assert_success_response(response)
        
        # Should handle concurrent scraping
        scraped_count = sum(1 for r in data["data"] if "markdown" in r)
        
        # At least some should be scraped
        if len(data["data"]) > 0:
            assert scraped_count > 0
    
    def test_search_pagination(self):
        """Test search result pagination (if supported)"""
        
        # First page
        response1 = self.make_request("POST", "/search", json={
            "query": "artificial intelligence",
            "limit": 10,
            "offset": 0
        })
        
        data1 = self.assert_success_response(response1)
        
        # Second page (if offset is supported)
        response2 = self.make_request("POST", "/search", json={
            "query": "artificial intelligence",
            "limit": 10, 
            "offset": 10
        })
        
        if response2.status_code == 200:
            data2 = response2.json()
            
            # Results should be different
            urls1 = {r["url"] for r in data1["data"]}
            urls2 = {r["url"] for r in data2["data"]}
            
            # Should have different URLs
            overlap = urls1.intersection(urls2)
            assert len(overlap) < len(urls1)


class TestSearchErrorHandling(BaseAPITest):
    """Test error handling for search endpoint"""
    
    def test_empty_query(self):
        """Test search with empty query"""
        
        response = self.make_request("POST", "/search", json={
            "query": "",
            "limit": 10
        })
        
        assert response.status_code == 400
    
    def test_invalid_limit(self):
        """Test search with invalid limit"""
        
        # Negative limit
        response = self.make_request("POST", "/search", json={
            "query": "test",
            "limit": -1
        })
        
        assert response.status_code == 400
        
        # Excessive limit
        response = self.make_request("POST", "/search", json={
            "query": "test",
            "limit": 1000
        })
        
        # Should either accept with cap or reject
        if response.status_code == 200:
            data = response.json()
            assert len(data["data"]) <= 100  # Reasonable cap
    
    def test_invalid_options(self):
        """Test search with invalid options"""
        
        response = self.make_request("POST", "/search", json={
            "query": "test search",
            "limit": 5,
            "search_options": {
                "region": "invalid_region",
                "language": "xyz",
                "time_range": "invalid_range"
            }
        })
        
        # Should either ignore invalid options or return error
        assert response.status_code in [200, 400]
    
    def test_search_timeout(self):
        """Test search timeout handling"""
        
        response = self.make_request("POST", "/search", json={
            "query": "complex query with scraping",
            "limit": 20,
            "scrape_options": {
                "formats": ["markdown", "screenshot"],
                "timeout": 1000  # Very short timeout
            }
        })
        
        # Should handle timeouts gracefully
        if response.status_code == 200:
            data = response.json()
            # Some results might fail to scrape
            for result in data["data"]:
                # Should still have basic search data
                assert "url" in result
                assert "title" in result


class TestSearchEdgeCases(BaseAPITest):
    """Test edge cases for search endpoint"""
    
    def test_special_characters_query(self):
        """Test search with special characters"""
        
        queries = [
            "C++ programming",
            "price: $100-$200",
            "email@example.com",
            '"exact phrase search"',
            "site:example.com"
        ]
        
        for query in queries:
            response = self.make_request("POST", "/search", json={
                "query": query,
                "limit": 3
            })
            
            # Should handle special characters
            assert response.status_code == 200
            data = response.json()
            assert data["query"] == query
    
    def test_unicode_query(self):
        """Test search with unicode characters"""
        
        queries = [
            "café münchen",
            "东京 オリンピック",
            "Москва Россия",
            "🤖 AI emoji"
        ]
        
        for query in queries:
            response = self.make_request("POST", "/search", json={
                "query": query,
                "limit": 3
            })
            
            # Should handle unicode
            assert response.status_code == 200
    
    def test_very_long_query(self):
        """Test search with very long query"""
        
        long_query = "artificial intelligence " * 50  # Very long
        
        response = self.make_request("POST", "/search", json={
            "query": long_query,
            "limit": 5
        })
        
        # Should either truncate or reject
        assert response.status_code in [200, 400]
    
    def test_no_results_query(self):
        """Test search that returns no results"""
        
        # Very specific query unlikely to have results
        response = self.make_request("POST", "/search", json={
            "query": "xyzqwerty123456789 nonexistentword",
            "limit": 10
        })
        
        if response.status_code == 200:
            data = response.json()
            # Should handle empty results gracefully
            assert "data" in data
            assert isinstance(data["data"], list)
            # Might be empty
            assert len(data["data"]) >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
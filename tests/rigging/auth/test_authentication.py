"""
Authentication and Authorization Tests
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.test_base import BaseAPITest


class TestAuthentication(BaseAPITest):
    """Test authentication and authorization"""
    
    def test_valid_token(self):
        """Test request with valid token"""
        
        response = self.make_request("POST", "/scrape", json={
            "url": self.get_test_url(),
            "formats": ["markdown"]
        })
        
        data = self.assert_success_response(response)
        assert "data" in data
        assert "markdown" in data["data"]
    
    def test_missing_token(self):
        """Test request without token"""
        
        # Remove auth header
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(
            f"{self.base_url}/scrape",
            headers=headers,
            json={
                "url": self.get_test_url(),
                "formats": ["markdown"]
            }
        )
        
        assert response.status_code == 401
        data = self.assert_error_response(response, "UNAUTHORIZED")
        assert "Authorization" in str(data["error"].get("details", {}))
    
    def test_invalid_token(self):
        """Test request with invalid token"""
        
        headers = {
            "Authorization": "Bearer invalid-token-12345",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{self.base_url}/scrape",
            headers=headers,
            json={
                "url": self.get_test_url(),
                "formats": ["markdown"]
            }
        )
        
        assert response.status_code == 401
        data = self.assert_error_response(response, "UNAUTHORIZED")
    
    def test_malformed_auth_header(self):
        """Test various malformed auth headers"""
        
        malformed_headers = [
            {"Authorization": "invalid-format"},
            {"Authorization": "Basic dGVzdDp0ZXN0"},  # Wrong auth type
            {"Authorization": "Bearer"},  # Missing token
            {"Authorization": " Bearer token"},  # Extra space
            {"Authorization": "bearer token"},  # Wrong case
        ]
        
        for headers in malformed_headers:
            headers["Content-Type"] = "application/json"
            
            response = requests.post(
                f"{self.base_url}/scrape",
                headers=headers,
                json={
                    "url": self.get_test_url(),
                    "formats": ["markdown"]
                }
            )
            
            assert response.status_code == 401, f"Expected 401 for headers: {headers}"
    
    def test_token_in_query_param(self):
        """Test token passed as query parameter (if supported)"""
        
        # Try without header but with query param
        response = requests.post(
            f"{self.base_url}/scrape?token={self.api_token}",
            headers={"Content-Type": "application/json"},
            json={
                "url": self.get_test_url(),
                "formats": ["markdown"]
            }
        )
        
        # This might be supported or not
        if response.status_code == 200:
            self.assert_success_response(response)
        else:
            assert response.status_code == 401
    
    def test_rate_limiting(self):
        """Test rate limiting behavior"""
        
        # Make multiple rapid requests
        responses = []
        
        for i in range(10):
            response = self.make_request("POST", "/scrape", json={
                "url": self.get_test_url(),
                "formats": ["markdown"]
            })
            responses.append(response)
            
            # Check if we hit rate limit
            if response.status_code == 429:
                data = self.assert_error_response(response, "RATE_LIMIT")
                
                # Check rate limit headers
                assert "X-RateLimit-Limit" in response.headers
                assert "X-RateLimit-Remaining" in response.headers
                assert "X-RateLimit-Reset" in response.headers
                
                # Check reset time in response
                assert "reset_in_seconds" in data["error"]["details"]
                assert data["error"]["details"]["reset_in_seconds"] > 0
                
                break
        
        # If we didn't hit rate limit in 10 requests, that's fine too
        if all(r.status_code == 200 for r in responses):
            print("ℹ️  Rate limit not hit in 10 requests")
    
    def test_token_permissions(self):
        """Test token permissions and scopes (if applicable)"""
        
        # This test assumes tokens might have different permissions
        # Skip if not applicable to your implementation
        
        # Test read permission
        response = self.make_request("POST", "/scrape", json={
            "url": self.get_test_url(),
            "formats": ["markdown"]
        })
        
        if response.status_code == 200:
            self.assert_success_response(response)
        else:
            # Might not have permission
            assert response.status_code in [401, 403]
    
    def test_concurrent_auth(self):
        """Test concurrent requests with same token"""
        
        import concurrent.futures
        
        def make_request():
            return self.make_request("POST", "/scrape", json={
                "url": self.get_test_url(),
                "formats": ["markdown"]
            })
        
        # Make 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            responses = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All should succeed or hit rate limit
        for response in responses:
            assert response.status_code in [200, 429]
            
            if response.status_code == 200:
                self.assert_success_response(response)
            else:
                self.assert_error_response(response, "RATE_LIMIT")
    
    def test_auth_header_case_sensitivity(self):
        """Test auth header case sensitivity"""
        
        # Standard format
        response1 = self.make_request("POST", "/scrape", json={
            "url": self.get_test_url(),
            "formats": ["markdown"]
        })
        
        # Different case
        headers = {
            "authorization": f"bearer {self.api_token}",  # lowercase
            "Content-Type": "application/json"
        }
        
        response2 = requests.post(
            f"{self.base_url}/scrape",
            headers=headers,
            json={
                "url": self.get_test_url(),
                "formats": ["markdown"]
            }
        )
        
        # Both should work (HTTP headers are case-insensitive)
        assert response1.status_code == 200
        assert response2.status_code == 200


class TestTokenManagement(BaseAPITest):
    """Test token management endpoints (if available)"""
    
    @pytest.mark.skip(reason="Token management endpoints may not be implemented")
    def test_token_validation(self):
        """Test token validation endpoint"""
        
        response = self.make_request("GET", "/auth/token/validate")
        
        if response.status_code == 200:
            data = self.assert_success_response(response)
            assert "valid" in data
            assert data["valid"] is True
            
            # May include token metadata
            if "token_info" in data:
                info = data["token_info"]
                assert "created_at" in info or "expires_at" in info
    
    @pytest.mark.skip(reason="Token management endpoints may not be implemented")
    def test_token_refresh(self):
        """Test token refresh endpoint"""
        
        response = self.make_request("POST", "/auth/token/refresh")
        
        if response.status_code == 200:
            data = self.assert_success_response(response)
            assert "token" in data
            assert len(data["token"]) > 20
            
            # Test new token works
            headers = {
                "Authorization": f"Bearer {data['token']}",
                "Content-Type": "application/json"
            }
            
            test_response = requests.post(
                f"{self.base_url}/scrape",
                headers=headers,
                json={
                    "url": self.get_test_url(),
                    "formats": ["markdown"]
                }
            )
            
            assert test_response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
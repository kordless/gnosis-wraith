"""
Base test class and utilities for all test suites
"""

import os
import json
import time
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
import pytest
from pathlib import Path


class BaseAPITest:
    """Base class for API tests with common functionality"""
    
    @classmethod
    def setup_class(cls):
        """Setup test class"""
        cls.api_token = os.getenv("GNOSIS_API_TOKEN")
        cls.base_url = os.getenv("GNOSIS_BASE_URL", "http://localhost:5678/api/v2")
        
        if not cls.api_token:
            pytest.skip("GNOSIS_API_TOKEN not set")
        
        cls.headers = {
            "Authorization": f"Bearer {cls.api_token}",
            "Content-Type": "application/json"
        }
        
        # LLM tokens (optional)
        cls.anthropic_token = os.getenv("ANTHROPIC_API_KEY")
        cls.openai_token = os.getenv("OPENAI_API_KEY")
        cls.gemini_token = os.getenv("GEMINI_API_KEY")
        
        # Test configuration
        cls.timeout = int(os.getenv("TEST_TIMEOUT", "30"))
        cls.verbose = os.getenv("TEST_VERBOSE", "true").lower() == "true"
        
        # Results directory
        cls.results_dir = Path(__file__).parent.parent / "results"
        cls.results_dir.mkdir(exist_ok=True)
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make API request with standard headers"""
        
        url = f"{self.base_url}{endpoint}"
        
        # Add headers
        headers = kwargs.pop("headers", {})
        headers.update(self.headers)
        
        # Add timeout
        timeout = kwargs.pop("timeout", self.timeout)
        
        # Log request if verbose
        if self.verbose:
            print(f"\n🔄 {method} {url}")
            if "json" in kwargs:
                print(f"📤 Request: {json.dumps(kwargs['json'], indent=2)}")
        
        # Make request
        start_time = time.time()
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            timeout=timeout,
            **kwargs
        )
        duration = time.time() - start_time
        
        # Log response if verbose
        if self.verbose:
            print(f"⏱️  Duration: {duration:.2f}s")
            print(f"📥 Status: {response.status_code}")
            try:
                print(f"📥 Response: {json.dumps(response.json(), indent=2)}")
            except:
                print(f"📥 Response: {response.text[:200]}...")
        
        return response
    
    def assert_success_response(self, response: requests.Response) -> Dict:
        """Assert response is successful and return data"""
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") is True, f"Expected success=True: {data}"
        
        return data
    
    def assert_error_response(self, response: requests.Response, error_code: str) -> Dict:
        """Assert response is an error with specific code"""
        
        data = response.json()
        assert data.get("success") is False, f"Expected success=False: {data}"
        assert "error" in data, f"Expected error in response: {data}"
        assert data["error"].get("code") == error_code, f"Expected error code {error_code}, got {data['error'].get('code')}"
        
        return data
    
    def wait_for_job(self, job_id: str, max_wait: int = 60) -> Dict:
        """Wait for async job to complete"""
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            response = self.make_request("GET", f"/jobs/{job_id}")
            
            if response.status_code != 200:
                raise Exception(f"Failed to get job status: {response.text}")
            
            data = response.json()
            status = data.get("status")
            
            if status == "done":
                return data
            elif status == "error":
                raise Exception(f"Job failed: {data.get('error')}")
            
            time.sleep(2)
        
        raise TimeoutError(f"Job {job_id} did not complete within {max_wait} seconds")
    
    def save_test_result(self, test_name: str, result: Dict) -> None:
        """Save test result for analysis"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.results_dir / f"{test_name}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                "test": test_name,
                "timestamp": datetime.now().isoformat(),
                "result": result
            }, f, indent=2)
    
    def get_test_url(self, path: str = "") -> str:
        """Get a test URL (example.com is safe for testing)"""
        return f"https://example.com{path}"
    
    def get_llm_config(self, provider: str = "anthropic") -> Dict[str, str]:
        """Get LLM configuration if available"""
        
        configs = {
            "anthropic": {
                "llm_provider": "anthropic",
                "llm_token": self.anthropic_token
            },
            "openai": {
                "llm_provider": "openai",
                "llm_token": self.openai_token
            },
            "gemini": {
                "llm_provider": "gemini",
                "llm_token": self.gemini_token
            }
        }
        
        config = configs.get(provider, {})
        
        # Skip if token not available
        if not config.get("llm_token"):
            pytest.skip(f"{provider} token not configured")
        
        return config


class TestTimer:
    """Context manager for timing test operations"""
    
    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.duration = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration = time.time() - self.start_time
        print(f"⏱️  {self.name} took {self.duration:.2f}s")


def assert_valid_url(url: str) -> None:
    """Assert URL is valid format"""
    assert url.startswith(("http://", "https://")), f"Invalid URL format: {url}"
    assert len(url) > 10, f"URL too short: {url}"


def assert_valid_markdown(content: str) -> None:
    """Assert content is valid markdown"""
    assert isinstance(content, str), "Content must be string"
    assert len(content) > 0, "Content is empty"
    # Basic markdown checks
    assert any(marker in content for marker in ["#", "-", "*", "[", "]"]), "No markdown formatting found"


def assert_valid_screenshot(data: str) -> None:
    """Assert screenshot data is valid base64 PNG"""
    assert isinstance(data, str), "Screenshot must be string"
    assert data.startswith("data:image/png;base64,"), "Invalid screenshot format"
    assert len(data) > 100, "Screenshot data too small"


def assert_valid_job_id(job_id: str) -> None:
    """Assert job ID format is valid"""
    assert isinstance(job_id, str), "Job ID must be string"
    assert len(job_id) > 5, "Job ID too short"
    assert "_" in job_id, "Job ID missing prefix"
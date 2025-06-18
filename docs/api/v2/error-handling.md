# Error Handling Guide

Understanding and handling errors effectively is crucial for building robust applications with the Gnosis Wraith API v2.

## 🚨 Error Response Format

All API errors follow a consistent structure:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error description",
    "details": {
      "field": "Additional context",
      "suggestion": "How to fix the error"
    }
  },
  "request_id": "req_abc123",
  "timestamp": "2025-01-06T10:30:00Z"
}
```

## 📋 Common Error Codes

### Authentication Errors

#### `UNAUTHORIZED` (401)
Missing or invalid API token.

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or missing API token",
    "details": {
      "header": "Authorization",
      "suggestion": "Include 'Authorization: Bearer YOUR_API_TOKEN' header"
    }
  }
}
```

**Fix:**
```python
headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}
```

#### `TOKEN_EXPIRED` (401)
API token has expired.

```json
{
  "error": {
    "code": "TOKEN_EXPIRED",
    "message": "API token has expired",
    "details": {
      "expired_at": "2025-01-05T10:30:00Z",
      "suggestion": "Generate a new token at /auth/token"
    }
  }
}
```

### Validation Errors

#### `INVALID_URL` (400)
Provided URL is malformed or inaccessible.

```json
{
  "error": {
    "code": "INVALID_URL",
    "message": "The provided URL is not valid",
    "details": {
      "url": "not-a-url",
      "reason": "Missing protocol",
      "suggestion": "URL must start with http:// or https://"
    }
  }
}
```

**Common causes:**
- Missing protocol (`example.com` instead of `https://example.com`)
- Invalid characters in URL
- Localhost URLs when not allowed

#### `INVALID_SCHEMA` (400)
Schema validation failed for structured extraction.

```json
{
  "error": {
    "code": "INVALID_SCHEMA",
    "message": "Invalid JSON schema provided",
    "details": {
      "error": "Invalid type 'strong' at properties.title.type",
      "path": "properties.title.type",
      "suggestion": "Use valid JSON Schema types: string, number, boolean, object, array"
    }
  }
}
```

#### `INVALID_JAVASCRIPT` (400)
JavaScript code validation failed.

```json
{
  "error": {
    "code": "INVALID_JAVASCRIPT",
    "message": "JavaScript contains unsafe operations",
    "details": {
      "patterns_found": ["document.cookie", "eval("],
      "line": 5,
      "suggestion": "Remove cookie access and eval statements"
    }
  }
}
```

### Resource Errors

#### `TIMEOUT_ERROR` (408)
Operation exceeded time limit.

```json
{
  "error": {
    "code": "TIMEOUT_ERROR",
    "message": "Page load timeout after 30 seconds",
    "details": {
      "url": "https://slow-site.com",
      "timeout_ms": 30000,
      "elapsed_ms": 30125,
      "suggestion": "Try increasing timeout or check if site is accessible"
    }
  }
}
```

**Fix:**
```python
{
  "options": {
    "timeout": 60000  # Increase to 60 seconds
  }
}
```

#### `NETWORK_ERROR` (502)
Network connection failed.

```json
{
  "error": {
    "code": "NETWORK_ERROR",
    "message": "Failed to connect to target site",
    "details": {
      "url": "https://example.com",
      "reason": "ECONNREFUSED",
      "dns_ok": true,
      "suggestion": "Verify the site is online and accessible"
    }
  }
}
```

#### `BLOCKED_RESOURCE` (403)
Access blocked by target site.

```json
{
  "error": {
    "code": "BLOCKED_RESOURCE",
    "message": "Access denied by target website",
    "details": {
      "url": "https://example.com",
      "reason": "robots.txt disallows crawling",
      "user_agent": "Gnosis-Wraith/2.0",
      "suggestion": "Site blocking automated access"
    }
  }
}
```

### Rate Limiting

#### `RATE_LIMIT` (429)
API rate limit exceeded.

```json
{
  "error": {
    "code": "RATE_LIMIT",
    "message": "Rate limit exceeded",
    "details": {
      "limit": 100,
      "window": "1m",
      "reset_at": "2025-01-06T10:31:00Z",
      "reset_in_seconds": 45
    }
  }
}
```

**Headers included:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1704538260
```

### LLM Provider Errors

#### `LLM_RATE_LIMIT` (429)
LLM provider rate limit hit.

```json
{
  "error": {
    "code": "LLM_RATE_LIMIT",
    "message": "OpenAI rate limit exceeded",
    "details": {
      "provider": "openai",
      "reset_in_seconds": 20,
      "suggestion": "Wait before retrying or use a different provider"
    }
  }
}
```

#### `INVALID_LLM_TOKEN` (401)
LLM authentication failed.

```json
{
  "error": {
    "code": "INVALID_LLM_TOKEN",
    "message": "Invalid Anthropic API key",
    "details": {
      "provider": "anthropic",
      "key_prefix": "sk-ant-",
      "suggestion": "Verify your Anthropic API key is correct"
    }
  }
}
```

#### `LLM_CONTENT_FILTER` (400)
Content blocked by LLM safety filters.

```json
{
  "error": {
    "code": "LLM_CONTENT_FILTER",
    "message": "Content blocked by safety filters",
    "details": {
      "provider": "openai",
      "category": "violence",
      "suggestion": "Modify content to comply with provider policies"
    }
  }
}
```

### Job Errors

#### `JOB_NOT_FOUND` (404)
Job ID doesn't exist.

```json
{
  "error": {
    "code": "JOB_NOT_FOUND",
    "message": "Job not found",
    "details": {
      "job_id": "crawl_xyz789",
      "suggestion": "Check job ID or job may have expired"
    }
  }
}
```

#### `JOB_FAILED` (500)
Background job encountered an error.

```json
{
  "error": {
    "code": "JOB_FAILED",
    "message": "Crawl job failed",
    "details": {
      "job_id": "crawl_abc123",
      "reason": "Maximum retries exceeded",
      "pages_completed": 5,
      "pages_failed": 3,
      "partial_results_available": true
    }
  }
}
```

### Content Errors

#### `CONTENT_TOO_LARGE` (413)
Content exceeds size limits.

```json
{
  "error": {
    "code": "CONTENT_TOO_LARGE",
    "message": "Content exceeds maximum size",
    "details": {
      "size_bytes": 10485760,
      "limit_bytes": 5242880,
      "suggestion": "Content must be under 5MB"
    }
  }
}
```

#### `EXTRACTION_FAILED` (422)
Unable to extract requested data.

```json
{
  "error": {
    "code": "EXTRACTION_FAILED",
    "message": "Failed to extract data with provided schema",
    "details": {
      "reason": "No matching content found",
      "content_type": "PDF",
      "suggestion": "Ensure content contains expected data structure"
    }
  }
}
```

## 🛡️ Error Handling Best Practices

### 1. Implement Retry Logic

```python
import time
import requests
from typing import Optional, Dict

class APIClient:
    def __init__(self, api_token: str, base_url: str):
        self.api_token = api_token
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def _should_retry(self, error_code: str) -> bool:
        """Determine if error is retryable"""
        retryable_codes = [
            "RATE_LIMIT",
            "LLM_RATE_LIMIT", 
            "TIMEOUT_ERROR",
            "NETWORK_ERROR"
        ]
        return error_code in retryable_codes
    
    def _get_retry_delay(self, error: Dict, attempt: int) -> float:
        """Calculate retry delay based on error type"""
        if error.get("code") in ["RATE_LIMIT", "LLM_RATE_LIMIT"]:
            # Use server-provided reset time
            return error.get("details", {}).get("reset_in_seconds", 60)
        else:
            # Exponential backoff for other errors
            return min(2 ** attempt, 60)
    
    def make_request(self, endpoint: str, data: Dict, max_retries: int = 3) -> Dict:
        """Make API request with automatic retry"""
        
        for attempt in range(max_retries + 1):
            try:
                response = requests.post(
                    f"{self.base_url}{endpoint}",
                    headers=self.headers,
                    json=data,
                    timeout=30
                )
                
                result = response.json()
                
                if result.get("success"):
                    return result
                
                error = result.get("error", {})
                
                if self._should_retry(error.get("code")) and attempt < max_retries:
                    delay = self._get_retry_delay(error, attempt)
                    print(f"Retrying in {delay}s: {error.get('message')}")
                    time.sleep(delay)
                    continue
                else:
                    raise APIError(error)
                    
            except requests.exceptions.RequestException as e:
                if attempt < max_retries:
                    delay = 2 ** attempt
                    print(f"Network error, retrying in {delay}s: {str(e)}")
                    time.sleep(delay)
                    continue
                else:
                    raise

class APIError(Exception):
    def __init__(self, error: Dict):
        self.code = error.get("code", "UNKNOWN")
        self.message = error.get("message", "Unknown error")
        self.details = error.get("details", {})
        super().__init__(self.message)
```

### 2. Handle Partial Failures

```python
def crawl_with_partial_results(client: APIClient, url: str, limit: int) -> Dict:
    """Crawl site and handle partial failures gracefully"""
    
    # Start crawl job
    response = client.make_request("/crawl", {
        "url": url,
        "limit": limit,
        "formats": ["markdown"]
    })
    
    job_id = response["job_id"]
    
    # Poll for results
    while True:
        try:
            status = client.make_request(f"/jobs/{job_id}", {})
            
            if status["status"] == "done":
                return {
                    "success": True,
                    "pages": status["data"],
                    "total": len(status["data"])
                }
            elif status["status"] == "error":
                # Return partial results if available
                return {
                    "success": False,
                    "pages": status.get("data", []),
                    "total": len(status.get("data", [])),
                    "error": status["error"]
                }
            
            time.sleep(2)
            
        except APIError as e:
            if e.code == "JOB_NOT_FOUND":
                return {
                    "success": False,
                    "error": "Job expired or not found"
                }
            raise
```

### 3. Fallback Strategies

```python
def extract_with_fallback(client: APIClient, content: str, schema: Dict) -> Optional[Dict]:
    """Try multiple LLM providers with fallback"""
    
    providers = [
        ("anthropic", "your-anthropic-key"),
        ("openai", "your-openai-key"),
        ("gemini", "your-gemini-key")
    ]
    
    errors = []
    
    for provider, token in providers:
        try:
            response = client.make_request("/extract", {
                "content": content,
                "schema": schema,
                "llm_provider": provider,
                "llm_token": token
            })
            
            return response["data"]
            
        except APIError as e:
            errors.append(f"{provider}: {e.message}")
            
            # Don't retry if it's a content/schema issue
            if e.code in ["INVALID_SCHEMA", "CONTENT_TOO_LARGE"]:
                raise
            
            continue
    
    # All providers failed
    raise Exception(f"All providers failed: {'; '.join(errors)}")
```

### 4. Graceful Degradation

```python
def scrape_with_degradation(client: APIClient, url: str) -> Dict:
    """Progressively simplify request on failure"""
    
    strategies = [
        # Try full features first
        {
            "formats": ["markdown", "screenshot", "links"],
            "options": {"javascript": True, "wait_for": 3000}
        },
        # Fallback: No screenshot
        {
            "formats": ["markdown", "links"],
            "options": {"javascript": True, "wait_for": 2000}
        },
        # Fallback: No JavaScript
        {
            "formats": ["markdown"],
            "options": {"javascript": False}
        },
        # Last resort: HTML only
        {
            "formats": ["html"],
            "options": {"javascript": False, "timeout": 10000}
        }
    ]
    
    errors = []
    
    for strategy in strategies:
        try:
            response = client.make_request("/scrape", {
                "url": url,
                **strategy
            })
            
            if not response.get("data", {}).get("markdown") and len(strategies) > 1:
                # No content extracted, try simpler approach
                continue
                
            return response
            
        except APIError as e:
            errors.append(e.code)
            
            # These errors won't be fixed by degradation
            if e.code in ["INVALID_URL", "UNAUTHORIZED", "BLOCKED_RESOURCE"]:
                raise
            
            continue
    
    raise APIError({
        "code": "SCRAPE_FAILED",
        "message": f"All strategies failed: {errors}"
    })
```

## 📊 Error Monitoring

### Log Errors for Analysis

```python
import logging
from datetime import datetime

class ErrorLogger:
    def __init__(self, log_file: str = "api_errors.log"):
        self.logger = logging.getLogger("gnosis_api")
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.ERROR)
    
    def log_error(self, endpoint: str, error: Dict, context: Dict = None):
        """Log API errors with context"""
        
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
            "error_code": error.get("code"),
            "error_message": error.get("message"),
            "details": error.get("details"),
            "context": context or {}
        }
        
        self.logger.error(json.dumps(error_data))
        
        # Track error patterns
        self._track_error_pattern(error.get("code"))
    
    def _track_error_pattern(self, error_code: str):
        """Track error frequency for alerting"""
        # Implementation depends on your monitoring system
        pass

# Usage
error_logger = ErrorLogger()

try:
    response = client.make_request("/scrape", data)
except APIError as e:
    error_logger.log_error("/scrape", {
        "code": e.code,
        "message": e.message,
        "details": e.details
    }, context={
        "url": data.get("url"),
        "formats": data.get("formats")
    })
    raise
```

## 🔍 Debugging Tips

### 1. Enable Debug Mode

```python
# Include debug flag in requests
response = requests.post(
    f"{base_url}/scrape",
    headers=headers,
    json={
        "url": "https://example.com",
        "formats": ["markdown"],
        "debug": True  # Returns additional debugging info
    }
)
```

### 2. Check Request ID

Every response includes a `request_id` for support:

```python
if not response["success"]:
    print(f"Error occurred. Request ID: {response.get('request_id')}")
    print(f"Error details: {response['error']}")
```

### 3. Validate Before Sending

```python
def validate_request(endpoint: str, data: Dict) -> List[str]:
    """Pre-validate request to catch errors early"""
    
    errors = []
    
    if endpoint in ["/scrape", "/crawl", "/screenshot"]:
        if not data.get("url"):
            errors.append("URL is required")
        elif not data["url"].startswith(("http://", "https://")):
            errors.append("URL must start with http:// or https://")
    
    if endpoint in ["/analyze", "/clean", "/summarize"]:
        if not data.get("content"):
            errors.append("Content is required")
        elif len(data["content"]) > 5 * 1024 * 1024:  # 5MB
            errors.append("Content exceeds 5MB limit")
    
    if "llm_provider" in data:
        valid_providers = ["anthropic", "openai", "gemini", "ollama"]
        if data["llm_provider"] not in valid_providers:
            errors.append(f"Invalid LLM provider. Must be one of: {valid_providers}")
    
    return errors

# Use before making request
errors = validate_request("/scrape", request_data)
if errors:
    print(f"Validation errors: {errors}")
else:
    response = client.make_request("/scrape", request_data)
```

## 📚 Error Code Reference

| Code | HTTP Status | Description | Retry |
|------|-------------|-------------|-------|
| `UNAUTHORIZED` | 401 | Invalid/missing API token | No |
| `TOKEN_EXPIRED` | 401 | API token expired | No |
| `INVALID_URL` | 400 | Malformed URL | No |
| `INVALID_SCHEMA` | 400 | Invalid JSON schema | No |
| `INVALID_JAVASCRIPT` | 400 | Unsafe JavaScript code | No |
| `TIMEOUT_ERROR` | 408 | Operation timeout | Yes |
| `NETWORK_ERROR` | 502 | Connection failed | Yes |
| `BLOCKED_RESOURCE` | 403 | Access denied | No |
| `RATE_LIMIT` | 429 | API rate limit | Yes |
| `LLM_RATE_LIMIT` | 429 | LLM provider limit | Yes |
| `INVALID_LLM_TOKEN` | 401 | Invalid LLM key | No |
| `CONTENT_TOO_LARGE` | 413 | Content size limit | No |
| `JOB_NOT_FOUND` | 404 | Job doesn't exist | No |
| `EXTRACTION_FAILED` | 422 | Extraction failed | Maybe |
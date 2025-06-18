# Getting Started with Gnosis Wraith API v2

## 🔐 Authentication

### Obtaining an API Token

1. **Via Web Interface**:
   - Navigate to `https://your-instance.com/auth/token`
   - Log in with your credentials
   - Generate a new API token
   - Copy and store securely

2. **Via API** (if you have credentials):
   ```bash
   curl -X POST https://your-instance.com/auth/api/token \
     -H "Content-Type: application/json" \
     -d '{
       "email": "your-email@example.com",
       "password": "your-password"
     }'
   ```

### Using Your Token

Include the token in the `Authorization` header of every request:

```
Authorization: Bearer YOUR_API_TOKEN
```

## 🌐 Base Configuration

### Base URLs

- **Production**: `https://wraith.nuts.services/api/v2`
- **Self-Hosted**: `https://your-instance.com/api/v2`
- **Local Development**: `http://localhost:5678/api/v2`

### Headers

All requests should include:

```http
Authorization: Bearer YOUR_API_TOKEN
Content-Type: application/json
Accept: application/json
```

## 🚀 Quick Start Examples

### 1. Simple Web Scraping

```python
import requests

# Configure
BASE_URL = "http://localhost:5678/api/v2"
TOKEN = "YOUR_API_TOKEN"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Scrape a webpage
response = requests.post(
    f"{BASE_URL}/scrape",
    headers=headers,
    json={
        "url": "https://example.com",
        "formats": ["markdown", "screenshot"]
    }
)

data = response.json()
print(data["data"]["markdown"])
```

### 2. Execute JavaScript

```python
# Execute JavaScript on a page
response = requests.post(
    f"{BASE_URL}/execute",
    headers=headers,
    json={
        "url": "https://example.com",
        "javascript": "document.querySelectorAll('h1')[0].textContent",
        "take_screenshot": True
    }
)

result = response.json()
print(f"H1 Text: {result['result']}")
```

### 3. AI-Powered Content Analysis

```python
# Analyze content with AI
response = requests.post(
    f"{BASE_URL}/analyze",
    headers=headers,
    json={
        "content": "Apple Inc. announced record profits...",
        "analysis_type": "entities",
        "llm_provider": "anthropic",
        "llm_token": "YOUR_ANTHROPIC_KEY"
    }
)

entities = response.json()["analysis"]["entities"]
print(f"Found {len(entities)} entities")
```

## 📦 Response Format

All API responses follow a consistent format:

### Success Response

```json
{
  "success": true,
  "data": {
    // Response data specific to endpoint
  },
  "metadata": {
    "timestamp": "2025-01-06T10:30:00Z",
    "processing_time_ms": 1234
  }
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "message": "Invalid URL provided",
    "code": "INVALID_URL",
    "details": {
      // Additional error context
    }
  }
}
```

## 🔧 Common Parameters

### Timeout Options

Most endpoints accept timeout parameters:

```json
{
  "options": {
    "timeout": 30000,      // Maximum time in ms
    "wait_before": 2000,   // Wait before action
    "wait_after": 1000     // Wait after action
  }
}
```

### Format Options

Available content formats:

- `markdown` - Cleaned markdown content
- `html` - Raw HTML
- `screenshot` - Base64 encoded PNG
- `links` - Extracted links
- `text` - Plain text

## 🏃 Next Steps

1. **Explore Core Endpoints**: Learn about [web scraping and crawling](./core-endpoints.md)
2. **Try JavaScript Execution**: See [dynamic page manipulation](./javascript-execution.md)
3. **Use AI Features**: Check out [content processing](./content-processing.md)
4. **View Examples**: Browse [real-world examples](./examples.md)

## 💡 Tips

- **Use appropriate timeouts**: Increase timeouts for JavaScript-heavy sites
- **Choose formats wisely**: Only request formats you need to save bandwidth
- **Batch when possible**: Use crawl endpoints for multiple pages
- **Cache tokens**: LLM tokens can be reused across requests
- **Handle errors gracefully**: Implement retry logic for transient failures
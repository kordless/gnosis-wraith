# Wraith API v2 Endpoint Specifications

## Base Configuration
- **Base URL**: `https://your-instance.com/api/v2`
- **Authentication**: `Authorization: Bearer YOUR_API_TOKEN`
- **Content-Type**: `application/json`

## Endpoints

### 1. `/v2/scrape` - Single Page Scraping (Synchronous)

**Method**: `POST`

**Headers**:
```
Authorization: Bearer YOUR_API_TOKEN
Content-Type: application/json
```

**Request Body**:
```json
{
  "url": "https://example.com",
  "formats": ["markdown", "html", "screenshot", "links"],
  "options": {
    "wait_for": 2000,
    "timeout": 30000,
    "headers": {
      "User-Agent": "custom-agent"
    },
    "viewport": {
      "width": 1920,
      "height": 1080
    }
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "url": "https://example.com",
    "markdown": "# Example Domain\n\nThis domain is for use...",
    "html": "<html>...</html>",
    "screenshot": "data:image/png;base64,...",
    "links": [
      {
        "href": "https://www.iana.org/domains/example",
        "text": "More information..."
      }
    ],
    "metadata": {
      "title": "Example Domain",
      "description": "This domain is for use in illustrative examples",
      "statusCode": 200,
      "contentType": "text/html",
      "timestamp": "2025-06-11T09:30:00Z"
    }
  },
  "scrape_id": "scrape_abc123"
}
```

### 2. `/v2/crawl` - Multi-Page Crawling (Asynchronous)

**Method**: `POST`

**Headers**:
```
Authorization: Bearer YOUR_API_TOKEN
Content-Type: application/json
```

**Request Body**:
```json
{
  "url": "https://example.com",
  "limit": 50,
  "depth": 3,
  "formats": ["markdown", "html"],
  "options": {
    "include_patterns": ["/blog/*", "/docs/*"],
    "exclude_patterns": ["/admin/*"],
    "wait_for": 2000,
    "concurrent_requests": 5
  }
}
```

**Response** (Job Created):
```json
{
  "success": true,
  "job_id": "crawl_xyz789",
  "status": "running",
  "status_url": "/v2/jobs/crawl_xyz789"
}
```

### 3. `/v2/jobs/{job_id}` - Check Job Status

**Method**: `GET`

**Headers**:
```
Authorization: Bearer YOUR_API_TOKEN
```

**Response** (Running):
```json
{
  "job_id": "crawl_xyz789",
  "status": "running",
  "data": [
    {
      "url": "https://example.com",
      "markdown": "# Example Domain...",
      "html": "<html>...</html>",
      "timestamp": "2025-06-11T09:30:00Z"
    },
    {
      "url": "https://example.com/page2",
      "markdown": "# Page 2...",
      "html": "<html>...</html>",
      "timestamp": "2025-06-11T09:30:05Z"
    }
  ],
  "pages_completed": 2,
  "pages_found": 15,
  "started_at": "2025-06-11T09:30:00Z"
}
```

**Response** (Done):
```json
{
  "job_id": "crawl_xyz789",
  "status": "done",
  "data": [...], // All pages
  "pages_completed": 15,
  "pages_found": 15,
  "started_at": "2025-06-11T09:30:00Z",
  "completed_at": "2025-06-11T09:31:30Z"
}
```

**Response** (Error):
```json
{
  "job_id": "crawl_xyz789",
  "status": "error",
  "error": {
    "message": "Connection timeout after 30 seconds",
    "code": "TIMEOUT_ERROR",
    "occurred_at": "2025-06-11T09:30:45Z"
  },
  "data": [...], // Any successfully scraped pages
  "pages_completed": 5,
  "pages_found": 15
}
```

### 4. `/v2/extract` (alias: `/v2/llm`) - AI Extraction

**Method**: `POST`

**Headers**:
```
Authorization: Bearer YOUR_API_TOKEN
Content-Type: application/json
```

**Request Body** (With Schema):
```json
{
  "urls": ["https://example.com", "https://example.com/about"],
  "prompt": "Extract company information",
  "schema": {
    "type": "object",
    "properties": {
      "company_name": {"type": "string"},
      "founded_year": {"type": "number"},
      "mission": {"type": "string"},
      "team_size": {"type": "number"}
    }
  }
}
```

**Request Body** (Without Schema):
```json
{
  "urls": ["https://example.com/*"],
  "prompt": "Extract all product names and prices from this e-commerce site"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "company_name": "Example Corp",
    "founded_year": 2010,
    "mission": "To provide examples for documentation",
    "team_size": 50
  },
  "sources": [
    {"url": "https://example.com", "used": true},
    {"url": "https://example.com/about", "used": true}
  ],
  "extract_id": "extract_def456"
}
```

### 5. `/v2/search` - Web Search

**Method**: `POST`

**Headers**:
```
Authorization: Bearer YOUR_API_TOKEN
Content-Type: application/json
```

**Request Body**:
```json
{
  "query": "latest AI news",
  "limit": 10,
  "scrape_options": {
    "formats": ["markdown"],
    "timeout": 10000
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "url": "https://technews.com/ai-breakthrough",
      "title": "Major AI Breakthrough Announced",
      "description": "Researchers announce new model...",
      "markdown": "# Major AI Breakthrough\n\nResearchers today announced...",
      "rank": 1
    }
  ],
  "query": "latest AI news",
  "total_results": 10,
  "search_id": "search_ghi789"
}
```

### 6. `/v2/screenshot` - Screenshot Only

**Method**: `POST`

**Headers**:
```
Authorization: Bearer YOUR_API_TOKEN
Content-Type: application/json
```

**Request Body**:
```json
{
  "url": "https://example.com",
  "format": "base64", // or "url" for file storage
  "options": {
    "full_page": true,
    "viewport": {
      "width": 1920,
      "height": 1080
    }
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "screenshot": "data:image/png;base64,...", // or URL
    "url": "https://example.com",
    "dimensions": {
      "width": 1920,
      "height": 3500
    }
  }
}
```

### 7. `/v2/md` - Markdown Only

**Method**: `POST`

**Headers**:
```
Authorization: Bearer YOUR_API_TOKEN
Content-Type: application/json
```

**Request Body**:
```json
{
  "url": "https://example.com",
  "options": {
    "include_links": true,
    "include_images": false
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "markdown": "# Example Domain\n\nThis domain is for use...",
    "url": "https://example.com",
    "word_count": 150,
    "reading_time": "1 min"
  }
}
```

## Error Responses

All endpoints use consistent error format:

```json
{
  "success": false,
  "error": {
    "code": "INVALID_URL",
    "message": "The provided URL is not valid",
    "details": {
      "url": "not-a-url",
      "suggestion": "Please provide a valid URL starting with http:// or https://"
    }
  }
}
```

## Common Error Codes
- `INVALID_URL` - URL format is invalid
- `UNAUTHORIZED` - Invalid or missing API token
- `RATE_LIMIT` - Rate limit exceeded
- `TIMEOUT_ERROR` - Request timed out
- `NETWORK_ERROR` - Network connection failed
- `EXTRACTION_ERROR` - LLM extraction failed
- `QUOTA_EXCEEDED` - Account quota exceeded

## Rate Limits
- **Default**: 100 requests per minute
- **Crawl**: 10 concurrent crawl jobs
- **Extract**: 50 requests per minute

## Webhooks

Configure webhooks in request:

```json
{
  "url": "https://example.com",
  "webhook": {
    "url": "https://your-server.com/webhook",
    "events": ["job.completed", "job.error", "page.scraped"],
    "headers": {
      "X-Custom-Header": "value"
    }
  }
}
```

Webhook payload:
```json
{
  "event": "job.completed",
  "job_id": "crawl_xyz789",
  "timestamp": "2025-06-11T09:31:30Z",
  "data": {
    "pages_completed": 15,
    "duration_seconds": 90
  }
}
```
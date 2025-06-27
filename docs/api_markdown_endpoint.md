# Gnosis Wraith /api/markdown Endpoint Documentation

## Overview

The `/api/markdown` endpoint extracts clean markdown content from web pages with support for JavaScript rendering, content filtering, screenshots, and batch processing.

## Endpoint

```
POST /api/markdown
```

## Authentication

Requires one of the following authentication methods:
- Session cookie (web login)
- Bearer token: `Authorization: Bearer YOUR_API_TOKEN`
- X-API-Token header: `X-API-Token: YOUR_API_TOKEN`
- JSON body: `{"api_token": "YOUR_API_TOKEN", ...other parameters...}`

## Single URL Request

### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | string | Yes | - | The URL to extract markdown from |
| `javascript_enabled` | boolean | No | `true` | Enable JavaScript rendering for dynamic content |
| `javascript_payload` | string | No | `null` | JavaScript code to inject and execute on the page |
| `screenshot_mode` | string | No | `null` | Screenshot capture mode: `"top"`, `"full"`, or `null` |
| `filter` | string | No | `null` | Content filter type: `"pruning"`, `"bm25"`, or `null` |
| `filter_options` | object | No | `{}` | Filter-specific configuration options |

### Filter Options

#### Pruning Filter
Reduces duplicate and redundant content using a scoring algorithm.

```json
{
  "filter": "pruning",
  "filter_options": {
    "threshold": 0.48,    // Score threshold (0.0-1.0), default: 0.48
    "min_words": 2        // Minimum words to keep a block, default: 2
  }
}
```

#### BM25 Filter
Filters content based on relevance to a search query.

```json
{
  "filter": "bm25",
  "filter_options": {
    "query": "product feedback automation",  // Required: search terms
    "threshold": 0.5                        // Relevance threshold (0.0-1.0), default: 0.5
  }
}
```

### JavaScript Injection

Execute custom JavaScript before content extraction:

```json
{
  "javascript_payload": "document.querySelector('.cookie-banner').remove(); return {custom: 'data'};"
}
```

The JavaScript can:
- Modify the DOM (remove popups, expand content, etc.)
- Return data that will be included in the response
- Interact with the page before markdown extraction

### Response Format

```json
{
  "success": true,
  "url": "https://example.com",
  
  // Primary markdown output (use this)
  "markdown": "# Page Title\n\n[Home](https://example.com/)\n\nContent with proper inline links...",
  
  // Alternative markdown formats
  "markdown_references": "[Home][1]\n\n[1]: https://example.com/",
  "markdown_plain": "Page Title\n\nHome\n\nContent without any links...",
  
  // Backwards compatibility (deprecated)
  "markdown_with_citations": "Home⟨1⟩\n\nContent...",
  "references": "## References\n\n⟨1⟩ https://example.com/",
  
  // Structured data
  "links": [
    {
      "text": "Home",
      "url": "https://example.com/",
      "type": "navigation"
    }
  ],
  "images": [
    {
      "alt": "Logo",
      "src": "https://example.com/logo.png",
      "title": null
    }
  ],
  "urls": ["https://example.com/", "https://example.com/about"],
  
  // Storage URLs
  "markdown_url": "https://wraith.nuts.services/storage/user123/report_20250627_123456.md",
  "json_url": "https://wraith.nuts.services/storage/user123/report_20250627_123456.json",
  "screenshot_url": "https://wraith.nuts.services/storage/user123/screenshot_20250627_123456.png",
  
  // Statistics
  "stats": {
    "word_count": 1234,
    "char_count": 5678,
    "link_count": 42,
    "image_count": 8,
    "extraction_time": 2.5,
    "filter_used": "pruning",
    "javascript_enabled": true,
    "javascript_injected": true
  },
  
  // JavaScript execution result (if payload provided)
  "javascript_result": {
    "custom": "data"
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether the request succeeded |
| `url` | string | The URL that was processed |
| `markdown` | string | **Primary output** - Standard markdown with inline links |
| `markdown_references` | string | Markdown with reference-style links `[text][1]` |
| `markdown_plain` | string | Plain text without any links or images |
| `markdown_with_citations` | string | Legacy format with `⟨1⟩` citations (deprecated) |
| `references` | string | Legacy citation references (deprecated) |
| `links` | array | All extracted links with text, URL, and type |
| `images` | array | All extracted images with alt text and src |
| `urls` | array | Simple list of all unique URLs found |
| `markdown_url` | string | URL where markdown file is saved |
| `json_url` | string | URL where JSON data is saved |
| `screenshot_url` | string | URL of screenshot (if requested) |
| `stats` | object | Extraction statistics and metadata |
| `javascript_result` | any | Result from JavaScript execution (if payload provided) |

## Batch URL Request

Process multiple URLs in a single request (maximum 50 URLs).

### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `urls` | array | Yes | - | Array of URLs to process (max 50) |
| `async` | boolean | No | `true` | Process asynchronously or wait for completion |
| `collate` | boolean | No | `false` | Merge all results into a single document |
| `javascript_enabled` | boolean | No | `true` | Enable JavaScript for all URLs |
| `screenshot_mode` | string | No | `null` | Screenshot mode for all URLs |
| `callback_url` | string | No | `null` | Webhook URL for completion notification |
| `callback_headers` | object | No | `{}` | Additional headers for webhook request |

### Batch Request Example

```json
{
  "urls": [
    "https://example.com/page1",
    "https://example.com/page2",
    "https://example.com/page3"
  ],
  "async": true,
  "collate": true,
  "javascript_enabled": true,
  "callback_url": "https://myapp.com/webhook",
  "callback_headers": {
    "X-Custom-Header": "value"
  }
}
```

### Batch Response (Async)

```json
{
  "success": true,
  "mode": "batch_async",
  "job_id": "batch_1735327123456",
  "status_url": "/api/jobs/batch_1735327123456",
  "results": [
    {
      "url": "https://example.com/page1",
      "status": "pending",
      "markdown_url": "https://wraith.nuts.services/storage/predicted_url1",
      "json_url": "https://wraith.nuts.services/storage/predicted_url2"
    }
  ],
  "collated_url": "https://wraith.nuts.services/storage/collated_document.md"
}
```

## Error Responses

### 400 Bad Request
```json
{
  "success": false,
  "error": "Either 'url' or 'urls' is required"
}
```

### 404 Not Found
```json
{
  "success": false,
  "error": "No content found at URL"
}
```

### 422 Validation Error
```json
{
  "success": false,
  "error": "Validation error",
  "details": [
    {
      "loc": ["filter_options", "query"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "success": false,
  "error": "Internal server error",
  "message": "Error details..."
}
```

### 502 Bad Gateway
DNS resolution failures or unreachable URLs.

### 503 Service Unavailable
Connection refused errors.

### 504 Gateway Timeout
Connection timeout errors.

## Example Requests

### Basic Markdown Extraction
```bash
curl -X POST https://wraith.nuts.services/api/markdown \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com"
  }'
```

### With Pruning Filter
```bash
curl -X POST https://wraith.nuts.services/api/markdown \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "filter": "pruning",
    "filter_options": {
      "threshold": 0.6
    }
  }'
```

### With JavaScript Injection and Screenshot
```bash
curl -X POST https://wraith.nuts.services/api/markdown \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "javascript_payload": "document.querySelector('.modal').style.display='none';",
    "screenshot_mode": "full"
  }'
```

### With BM25 Content Filtering
```bash
curl -X POST https://wraith.nuts.services/api/markdown \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "filter": "bm25",
    "filter_options": {
      "query": "artificial intelligence machine learning",
      "threshold": 0.7
    }
  }'
```

### Batch Processing
```bash
curl -X POST https://wraith.nuts.services/api/markdown \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://example.com/blog/post1",
      "https://example.com/blog/post2"
    ],
    "async": true,
    "collate": true
  }'
```

## Best Practices

1. **Use the Primary `markdown` Field**: This contains standard markdown with proper inline links that works in any markdown parser.

2. **Choose the Right Filter**:
   - No filter: Get all content
   - Pruning: Remove duplicate/redundant content
   - BM25: Extract only content relevant to your query

3. **Handle Errors Gracefully**: Check the `success` field and handle different HTTP status codes appropriately.

4. **Batch Wisely**: Use batch processing for multiple URLs but keep under 50 URLs per request.

5. **JavaScript Injection**: Use sparingly and ensure your JavaScript doesn't break the page structure.

## Changelog

- **v2.1.0** (Current): Added clean markdown formats, structured data extraction, improved URL resolution
- **v2.0.0**: Initial release with citation-based markdown (now deprecated)

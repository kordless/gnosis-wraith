# Batch Markdown API Documentation

The `/api/markdown` endpoint now supports batch processing, allowing you to crawl and convert multiple URLs to markdown in parallel. This guide covers the new batch functionality while maintaining backward compatibility with single URL requests.

## Table of Contents
- [Single URL Mode (Backward Compatible)](#single-url-mode-backward-compatible)
- [Batch URL Mode](#batch-url-mode)
- [Async vs Sync Processing](#async-vs-sync-processing)
- [Webhook Callbacks](#webhook-callbacks)
- [Result Collation](#result-collation)
- [Examples](#examples)
- [Error Handling](#error-handling)
- [Performance Tips](#performance-tips)

## Single URL Mode (Backward Compatible)

The existing single URL functionality remains unchanged:

```bash
curl -X POST http://localhost:5678/api/markdown \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com"
  }'
```

**Response:**
```json
{
  "success": true,
  "url": "https://example.com",
  "markdown": "# Example Domain\n\nThis domain is for use...",
  "markdown_url": "/storage/USER_HASH/report_20250618_120000_abc123.md",
  "json_url": "/storage/USER_HASH/report_20250618_120000_abc123.json",
  "stats": {
    "word_count": 150,
    "char_count": 890,
    "extraction_time": 1.23
  }
}
```

## Batch URL Mode

Process multiple URLs in a single request:

```bash
curl -X POST http://localhost:5678/api/markdown \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://example.com",
      "https://www.python.org",
      "https://docs.python.org/3/"
    ],
    "async": false
  }'
```

### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `urls` | array | Yes* | - | List of URLs to process (max 50) |
| `url` | string | Yes* | - | Single URL (used if `urls` not provided) |
| `async` | boolean | No | true | Process asynchronously (return immediately) |
| `collate` | boolean | No | false | Merge all results into single file |
| `callback_url` | string | No | - | Webhook URL for completion notification |
| `callback_headers` | object | No | {} | Custom headers for webhook request |
| `filter` | string | No | null | Content filter: "pruning" or "bm25" |
| `filter_options` | object | No | {} | Options for the selected filter |
| `javascript_enabled` | boolean | No | true | Enable JavaScript rendering |
| `screenshot_mode` | string | No | null | Screenshot mode: "full", "top", or null |

*Either `url` or `urls` is required

## Async vs Sync Processing

### Synchronous Mode (`async: false`)

Waits for all URLs to be processed before returning:

```json
{
  "success": true,
  "mode": "batch_sync",
  "job_id": "batch_1750220600627",
  "results": [
    {
      "url": "https://example.com",
      "status": "completed",
      "markdown_url": "/storage/USER_HASH/report_20250618_120000_abc123.md",
      "json_url": "/storage/USER_HASH/report_20250618_120000_abc123.json",
      "stats": {
        "word_count": 150,
        "char_count": 890,
        "extraction_time": 1.23
      }
    },
    {
      "url": "https://invalid-url.com",
      "status": "failed",
      "error": "Failed to crawl URL",
      "markdown_url": "/storage/USER_HASH/report_20250618_120000_def456.md",
      "json_url": "/storage/USER_HASH/report_20250618_120000_def456.json"
    }
  ]
}
```

### Asynchronous Mode (`async: true`)

Returns immediately with predicted URLs (HTTP 202 Accepted):

```json
{
  "success": true,
  "mode": "batch_async",
  "job_id": "batch_1750220600503",
  "status_url": "/api/jobs/batch_1750220600503",
  "results": [
    {
      "url": "https://example.com",
      "status": "processing",
      "markdown_url": "/storage/USER_HASH/report_20250618_120000_abc123.md",
      "json_url": "/storage/USER_HASH/report_20250618_120000_abc123.json"
    }
  ]
}
```

## Webhook Callbacks

Get notified when async batch processing completes:

```json
{
  "urls": ["https://example.com", "https://python.org"],
  "async": true,
  "callback_url": "https://your-app.com/webhook/batch-complete",
  "callback_headers": {
    "Authorization": "Bearer YOUR_WEBHOOK_SECRET",
    "X-Custom-Header": "value"
  }
}
```

### Webhook Payload

Your callback URL will receive:

```json
{
  "job_id": "batch_1750220600503",
  "status": "completed",
  "stats": {
    "total_urls": 2,
    "successful": 2,
    "failed": 0,
    "total_time": 4.5,
    "average_time_per_url": 2.25,
    "total_words": 5234,
    "total_characters": 28456
  },
  "results": [
    {
      "url": "https://example.com",
      "status": "completed",
      "markdown_url": "/storage/USER_HASH/report_20250618_120000_abc123.md",
      "word_count": 2156
    }
  ],
  "collated_url": null
}
```

## Result Collation

Merge multiple results into a single markdown file:

```json
{
  "urls": [
    "https://docs.python.org/3/tutorial/index.html",
    "https://docs.python.org/3/tutorial/introduction.html",
    "https://docs.python.org/3/tutorial/controlflow.html"
  ],
  "collate": true,
  "collate_options": {
    "title": "Python Tutorial Collection",
    "add_toc": true,
    "add_source_headers": true
  }
}
```

The collated file includes:
- Custom title
- Table of contents with links
- Source headers for each URL
- All markdown content merged with separators

## Examples

### Example 1: Simple Batch Request

```python
import requests

response = requests.post(
    "http://localhost:5678/api/markdown",
    headers={
        "Authorization": "Bearer YOUR_API_KEY",
        "Content-Type": "application/json"
    },
    json={
        "urls": [
            "https://example.com",
            "https://www.iana.org/domains/example"
        ],
        "async": False  # Wait for completion
    }
)

result = response.json()
for item in result["results"]:
    print(f"{item['url']}: {item['status']}")
```

### Example 2: Async with Webhook

```python
import requests

# Start batch processing
response = requests.post(
    "http://localhost:5678/api/markdown",
    headers={
        "Authorization": "Bearer YOUR_API_KEY",
        "Content-Type": "application/json"
    },
    json={
        "urls": [
            "https://en.wikipedia.org/wiki/Python_(programming_language)",
            "https://en.wikipedia.org/wiki/JavaScript",
            "https://en.wikipedia.org/wiki/Go_(programming_language)"
        ],
        "async": True,
        "collate": True,
        "collate_options": {
            "title": "Programming Languages Overview"
        },
        "callback_url": "https://webhook.site/your-unique-url"
    }
)

print(f"Job ID: {response.json()['job_id']}")
print(f"Status URL: {response.json()['status_url']}")
```

### Example 3: Using Content Filters

```python
import requests

response = requests.post(
    "http://localhost:5678/api/markdown",
    headers={
        "Authorization": "Bearer YOUR_API_KEY",
        "Content-Type": "application/json"
    },
    json={
        "urls": [
            "https://en.wikipedia.org/wiki/Machine_learning",
            "https://en.wikipedia.org/wiki/Deep_learning"
        ],
        "filter": "bm25",
        "filter_options": {
            "query": "neural networks training",
            "threshold": 0.5
        },
        "async": False
    }
)
```

## Error Handling

### Common Errors

1. **Too Many URLs**
```json
{
  "success": false,
  "error": "Maximum 50 URLs allowed per batch"
}
```

2. **Missing Required Fields**
```json
{
  "success": false,
  "error": "Either 'url' or 'urls' is required"
}
```

3. **Individual URL Failures**
In batch mode, individual URL failures don't fail the entire batch:
```json
{
  "url": "https://invalid-domain-xyz.com",
  "status": "failed",
  "error": "Failed to crawl URL: net::ERR_NAME_NOT_RESOLVED"
}
```

## Performance Tips

1. **Optimal Batch Size**: 5-10 URLs per batch for best performance
2. **Concurrency**: The system processes up to 5 URLs concurrently per batch
3. **Timeouts**: Each URL has a 30-second timeout by default
4. **Rate Limiting**: Respect rate limits to avoid throttling

### Performance Comparison

| Mode | URLs | Time | Notes |
|------|------|------|-------|
| Sequential | 10 | ~30s | One at a time |
| Batch Sync | 10 | ~8s | 5 concurrent |
| Batch Async | 10 | ~0.1s | Returns immediately |

## Best Practices

1. **Use Async Mode** for large batches or when you don't need immediate results
2. **Implement Webhook Handlers** to process results as they complete
3. **Handle Partial Failures** - some URLs may fail while others succeed
4. **Monitor Job Status** using the status_url for async requests
5. **Respect Limits** - max 50 URLs per batch, be mindful of rate limits

## Migration Guide

If you're currently making multiple single-URL requests:

**Before:**
```python
urls = ["url1", "url2", "url3"]
results = []
for url in urls:
    response = requests.post("/api/markdown", json={"url": url})
    results.append(response.json())
```

**After:**
```python
response = requests.post("/api/markdown", json={
    "urls": ["url1", "url2", "url3"],
    "async": False
})
results = response.json()["results"]
```

This reduces API calls and improves performance significantly!
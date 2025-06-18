# Core Web Intelligence Endpoints

The core endpoints provide fundamental web scraping and crawling capabilities with advanced options for customization.

## 🌐 Single Page Scraping

### POST `/api/v2/scrape`

Extract content from a single webpage with multiple format options.

#### Request

```json
{
  "url": "https://example.com",
  "formats": ["markdown", "html", "screenshot", "links", "text"],
  "options": {
    "wait_for": 2000,              // Wait time before capture (ms)
    "timeout": 30000,              // Maximum execution time (ms)
    "headers": {
      "User-Agent": "custom-agent",
      "Accept-Language": "en-US"
    },
    "viewport": {
      "width": 1920,
      "height": 1080
    },
    "block_resources": ["image", "font"],  // Optional resource blocking
    "javascript": true             // Enable/disable JavaScript
  }
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "url": "https://example.com",
    "markdown": "# Example Domain\n\nThis domain is for use...",
    "html": "<!DOCTYPE html>...",
    "screenshot": "data:image/png;base64,...",
    "text": "Example Domain This domain is for use...",
    "links": [
      {
        "href": "https://www.iana.org/domains/example",
        "text": "More information...",
        "title": "IANA Example Domains"
      }
    ],
    "metadata": {
      "title": "Example Domain",
      "description": "This domain is for use in illustrative examples",
      "keywords": ["example", "domain"],
      "author": "IANA",
      "statusCode": 200,
      "contentType": "text/html; charset=UTF-8",
      "contentLength": 1256,
      "language": "en",
      "timestamp": "2025-01-06T10:30:00Z"
    }
  },
  "scrape_id": "scrape_abc123",
  "processing_time_ms": 2345
}
```

### Format Options Explained

- **`markdown`** - Clean, readable text with structure preserved
- **`html`** - Raw HTML content of the page
- **`screenshot`** - Base64-encoded PNG image
- **`links`** - All hyperlinks with context
- **`text`** - Plain text without formatting

### Advanced Options

```json
{
  "options": {
    // Timing
    "wait_for": 5000,              // Wait for dynamic content
    "wait_until": "networkidle",   // Options: load, domcontentloaded, networkidle
    
    // Authentication
    "auth": {
      "username": "user",
      "password": "pass"
    },
    
    // Cookies
    "cookies": [
      {
        "name": "session",
        "value": "abc123",
        "domain": ".example.com"
      }
    ],
    
    // Proxy
    "proxy": {
      "server": "http://proxy.example.com:8080",
      "username": "proxyuser",
      "password": "proxypass"
    }
  }
}
```

## 🔄 Multi-Page Crawling

### POST `/api/v2/crawl`

Crawl multiple pages from a website with depth control and pattern matching.

#### Request

```json
{
  "url": "https://example.com",
  "limit": 50,                     // Maximum pages to crawl
  "depth": 3,                      // Maximum depth from start URL
  "formats": ["markdown", "html"],
  "options": {
    "include_patterns": [
      "/blog/*",
      "/docs/*",
      "*/tutorial/*"
    ],
    "exclude_patterns": [
      "/admin/*",
      "*.pdf",
      "/api/*"
    ],
    "wait_for": 2000,
    "concurrent_requests": 5,      // Parallel crawling
    "respect_robots_txt": true,
    "follow_redirects": true,
    "same_origin": true            // Stay on same domain
  }
}
```

#### Response (Job Created)

```json
{
  "success": true,
  "job_id": "crawl_xyz789",
  "status": "running",
  "status_url": "/api/v2/jobs/crawl_xyz789",
  "webhook_url": null
}
```

### Pattern Matching

Patterns support wildcards and regular expressions:

- `*` - Match any characters
- `?` - Match single character
- `[abc]` - Match character set
- `{blog,news}` - Match alternatives

Examples:
- `/blog/*` - All blog posts
- `*/page-[0-9]+` - Paginated content
- `/{en,es,fr}/*` - Multiple languages

## 📊 Job Management

### GET `/api/v2/jobs/{job_id}`

Check the status of asynchronous operations.

#### Response States

**Running:**
```json
{
  "job_id": "crawl_xyz789",
  "status": "running",
  "progress": {
    "pages_completed": 15,
    "pages_found": 45,
    "pages_queued": 30,
    "depth_current": 2,
    "elapsed_seconds": 45
  },
  "data": [...],  // Completed pages so far
  "started_at": "2025-01-06T10:30:00Z"
}
```

**Completed:**
```json
{
  "job_id": "crawl_xyz789",
  "status": "done",
  "data": [...],  // All crawled pages
  "summary": {
    "total_pages": 45,
    "successful": 43,
    "failed": 2,
    "duration_seconds": 120,
    "average_page_time_ms": 2667
  },
  "started_at": "2025-01-06T10:30:00Z",
  "completed_at": "2025-01-06T10:32:00Z"
}
```

**Error:**
```json
{
  "job_id": "crawl_xyz789",
  "status": "error",
  "error": {
    "message": "Rate limit exceeded on target site",
    "code": "RATE_LIMIT_EXTERNAL",
    "details": {
      "pages_before_error": 25,
      "error_url": "https://example.com/page26"
    }
  },
  "data": [...],  // Successfully crawled pages
  "partial_success": true
}
```

## 🔍 Web Search

### POST `/api/v2/search`

Search the web and automatically scrape results.

#### Request

```json
{
  "query": "artificial intelligence news 2025",
  "limit": 20,
  "search_options": {
    "region": "us",               // Country code
    "language": "en",             // Language code
    "time_range": "month",        // Options: day, week, month, year
    "safe_search": "moderate"     // Options: off, moderate, strict
  },
  "scrape_options": {
    "formats": ["markdown", "screenshot"],
    "timeout": 10000,
    "concurrent_requests": 3
  }
}
```

#### Response

```json
{
  "success": true,
  "data": [
    {
      "rank": 1,
      "url": "https://technews.com/ai-breakthrough-2025",
      "title": "Major AI Breakthrough in Natural Language",
      "description": "Researchers announce a new model that...",
      "markdown": "# Major AI Breakthrough in Natural Language\n\n...",
      "screenshot": "data:image/png;base64,...",
      "domain": "technews.com",
      "published_date": "2025-01-05"
    }
  ],
  "query": "artificial intelligence news 2025",
  "total_results": 20,
  "search_engine": "google",
  "search_id": "search_ghi789"
}
```

## 📸 Screenshot Capture

### POST `/api/v2/screenshot`

Capture high-quality screenshots with advanced options.

#### Request

```json
{
  "url": "https://example.com",
  "format": "base64",              // Options: base64, url
  "options": {
    "full_page": true,             // Capture entire page
    "quality": 90,                 // JPEG quality (1-100)
    "type": "png",                 // Options: png, jpeg, webp
    "viewport": {
      "width": 1920,
      "height": 1080,
      "device_scale_factor": 2     // Retina display
    },
    "clip": {                      // Specific area
      "x": 0,
      "y": 0,
      "width": 800,
      "height": 600
    },
    "wait_for": 3000,
    "hide_selectors": [            // Hide elements
      ".cookie-banner",
      "#popup"
    ]
  }
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "screenshot": "data:image/png;base64,...",
    "url": "https://example.com",
    "format": "png",
    "dimensions": {
      "width": 1920,
      "height": 3500
    },
    "file_size_bytes": 456789,
    "capture_time_ms": 2345
  }
}
```

## 📝 Markdown Extraction

### POST `/api/v2/md`

Extract clean, readable markdown from any webpage.

#### Request

```json
{
  "url": "https://example.com/article",
  "options": {
    "include_links": true,         // Preserve hyperlinks
    "include_images": true,        // Include image references
    "simplify_tables": false,      // Convert complex tables
    "remove_scripts": true,        // Remove script content
    "extract_metadata": true,      // Include meta information
    "line_length": 80,            // Wrap lines at length
    "heading_style": "atx"        // Options: atx (#), setext
  }
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "markdown": "# Article Title\n\nBy John Doe | January 6, 2025\n\n...",
    "url": "https://example.com/article",
    "metadata": {
      "title": "Article Title",
      "author": "John Doe",
      "published": "2025-01-06",
      "reading_time": "5 min",
      "word_count": 1234
    },
    "table_of_contents": [
      {"level": 1, "text": "Article Title", "id": "article-title"},
      {"level": 2, "text": "Introduction", "id": "introduction"},
      {"level": 2, "text": "Main Points", "id": "main-points"}
    ]
  }
}
```

## 🔧 Common Options

### Viewport Presets

```json
{
  "options": {
    "viewport": "desktop"  // Presets: mobile, tablet, desktop
  }
}
```

Preset values:
- `mobile`: 375x667 (iPhone SE)
- `tablet`: 768x1024 (iPad)
- `desktop`: 1920x1080 (Full HD)

### Wait Strategies

```json
{
  "options": {
    "wait_until": "networkidle",
    "wait_for_selector": ".content-loaded",
    "wait_for_function": "() => document.querySelectorAll('.item').length > 10"
  }
}
```

### Resource Optimization

```json
{
  "options": {
    "block_resources": ["image", "stylesheet", "font", "media"],
    "cache": true,
    "cache_ttl": 3600  // Cache for 1 hour
  }
}
```

## 📈 Performance Tips

1. **Use specific formats** - Only request formats you need
2. **Enable caching** - Reduce redundant requests
3. **Block unnecessary resources** - Faster page loads
4. **Use appropriate timeouts** - Balance speed and reliability
5. **Batch similar requests** - Use crawl for multiple pages

## 🚨 Error Handling

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": {
    "code": "TIMEOUT_ERROR",
    "message": "Page load timeout after 30 seconds",
    "details": {
      "url": "https://slow-site.com",
      "timeout_ms": 30000,
      "suggestion": "Try increasing the timeout or check if the site is accessible"
    }
  }
}
```

Common error codes:
- `INVALID_URL` - Malformed or inaccessible URL
- `TIMEOUT_ERROR` - Operation exceeded time limit
- `NETWORK_ERROR` - Connection failed
- `BLOCKED_RESOURCE` - robots.txt or security block
- `QUOTA_EXCEEDED` - Account limit reached
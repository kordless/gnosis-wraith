# Gnosis Wraith API Documentation

## API Version 2 (Recommended)

The v2 API provides focused, single-purpose endpoints following industry best practices and crawl4ai patterns. These endpoints offer better performance, cleaner responses, and more predictable behavior.

### Base URL
- Development: `http://localhost:5678/api/v2`
- Production: `https://your-domain.com/api/v2`

### Authentication

All v2 endpoints require authentication using one of the following methods:

#### 1. Session Authentication (Web Interface)
- Automatically handled when logged in via web interface
- Uses secure session cookies
- Best for browser-based access

#### 2. API Token Authentication (Programmatic Access)
- Generate token via web interface or API
- Use in one of three ways:

**Authorization Header (Recommended):**
```bash
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
     -X POST https://your-domain.com/api/v2/md \
     -d '{"url": "https://example.com"}'
```

**X-API-Token Header:**
```bash
curl -H "X-API-Token: YOUR_API_TOKEN" \
     -X POST https://your-domain.com/api/v2/md \
     -d '{"url": "https://example.com"}'
```

**JSON Body (POST only):**
```json
{
  "url": "https://example.com",
  "api_token": "YOUR_API_TOKEN"
}
```

#### Managing API Tokens

**Get Token Info:**
```bash
GET /auth/api/token/info
Authorization: Bearer YOUR_API_TOKEN
```

**Generate New Token (Session Auth Only):**
```bash
POST /auth/api/token/generate
```

**Reset Token:**
```bash
POST /auth/token_reset
```


### Available Endpoints

#### `/api/v2/md` - Markdown Extraction

Optimized endpoint for extracting clean markdown content without overhead.

**Method:** `POST`

**Request:**
```json
{
  "url": "https://example.com",
  "filter": "pruning",              // Optional: null, "pruning", "bm25"
  "filter_options": {               // Optional: filter-specific options
    "threshold": 0.48,
    "query": "specific topic"       // For BM25 filter
  },
  "format": "clean",                // Optional: "raw", "clean", "fit"
  "javascript": true                // Optional: enable JS rendering
}
```

**Response:**
```json
{
  "success": true,
  "url": "https://example.com",
  "markdown": "# Page Title\n\nContent here...",
  "stats": {
    "word_count": 1234,
    "char_count": 5678,
    "extraction_time": 2.34
  }
}
```

#### `/api/v2/screenshot` - Screenshot Capture

Dedicated endpoint for capturing webpage screenshots.

**Method:** `POST`

**Request:**
```json
{
  "url": "https://example.com",
  "mode": "viewport",               // "viewport" or "full"
  "format": "base64",               // "base64", "url", or "file"
  "wait_for": 2000,                 // Optional: wait time in ms
  "options": {
    "quality": 90,                  // Optional: JPEG quality
    "clip": {                       // Optional: capture specific area
      "x": 0,
      "y": 0,
      "width": 800,
      "height": 600
    }
  }
}
```

**Response (base64 format):**
```json
{
  "success": true,
  "url": "https://example.com",
  "screenshot": {
    "data": "data:image/png;base64,iVBORw0KGgoAAAANS...",
    "format": "png",
    "width": 1920,
    "height": 1080,
    "file_size": 245632
  },
  "capture_time": 2.34
}
```

**Response (file format):**
Returns binary image data with appropriate headers.

#### `/api/v2/pdf` - PDF Generation

Generate PDF documents from web pages.

**Method:** `POST`

**Request:**
```json
{
  "url": "https://example.com",
  "options": {
    "format": "A4",                 // "A4", "Letter", "Legal"
    "landscape": false,
    "print_background": true,
    "margin": {
      "top": "1in",
      "bottom": "1in",
      "left": "1in",
      "right": "1in"
    },
    "wait_for": 2000
  }
}
```

**Response:**
Returns binary PDF data with appropriate headers:
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="example_com_2025_01_10.pdf"
Content-Length: 524288
```

#### `/api/v2/html` - HTML Extraction

Extract cleaned or raw HTML content.

**Method:** `POST`

**Request:**
```json
{
  "url": "https://example.com",
  "clean": true,                    // Apply HTML cleaning
  "javascript": true,               // Enable JS rendering
  "wait_for": "div.content"         // Optional: wait for selector
}
```

**Response:**
```json
{
  "success": true,
  "url": "https://example.com",
  "html": "<html>...</html>",
  "title": "Page Title",
  "metadata": {
    "extracted_at": "2025-01-10T12:34:56Z",
    "javascript_used": true
  }
}
```

#### `/api/v2/batch` - Batch Processing

Process multiple URLs with concurrency control.

**Method:** `POST`

**Request:**
```json
{
  "urls": [
    "https://example1.com",
    "https://example2.com",
    "https://example3.com"
  ],
  "options": {
    // Same options as single endpoints
  },
  "batch": {
    "concurrent": 3,                // Max concurrent requests
    "delay": 1000,                  // Delay between requests (ms)
    "continue_on_error": true       // Continue if some URLs fail
  }
}
```

**Response:**
```json
{
  "success": true,
  "total": 3,
  "processed": 3,
  "errors": 0,
  "results": [
    {
      "url": "https://example1.com",
      "success": true,
      "data": { /* Result data */ }
    },
    // ... more results
  ]
}
```

### Error Responses

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "Error message describing the issue"
}
```

HTTP status codes:
- `400` - Bad Request (missing or invalid parameters)
- `401` - Unauthorized (authentication required)
- `404` - Not Found
- `500` - Internal Server Error

### Migration from v1

Key differences from v1 `/api/crawl`:
1. **Focused endpoints** - Each endpoint does one thing well
2. **No HTML by default** - Reduces response sizes dramatically
3. **Cleaner responses** - Only relevant data returned
4. **Better performance** - Optimized for specific use cases
5. **Predictable behavior** - Consistent parameter naming

Example migration:

**v1 (old):**
```bash
curl -X POST /api/crawl \
  -d '{"url": "https://example.com", "response_format": "minimal"}'
```

**v2 (new):**
```bash
curl -X POST /api/v2/md \
  -d '{"url": "https://example.com"}'
```

---

## API Version 1 (Legacy)

### `/api/crawl` Endpoint


The `/api/crawl` endpoint is the primary API for crawling web pages and extracting content. It supports various extraction methods, AI processing, and flexible response formats.

### Endpoint Details

- **URL**: `/api/crawl`
- **Method**: `POST`
- **Authentication**: Required (session or API token)
- **Content-Type**: `application/json`

### Authentication

The v1 API supports the same authentication methods as v2:

1. **Session authentication** (automatic when logged in via web)
2. **API token** via:
   - `Authorization: Bearer YOUR_API_TOKEN` header
   - `X-API-Token: YOUR_API_TOKEN` header
   - `"api_token": "YOUR_API_TOKEN"` in request body

See the [Authentication Guide](AUTH_GUIDE.md) for details.


### Request Structure

```json
{
  "urls": ["https://example.com"],        // Array of URLs to crawl (optional if "url" is provided)
  "url": "https://example.com",           // Single URL (optional if "urls" is provided)
  "title": "Custom Report Title",         // Optional custom title for the report
  "output_format": "markdown",            // Output format: "markdown", "html", "json", "all"
  "response_format": "minimal",           // Response format: "full", "content_only", "minimal"
  "javascript_enabled": false,            // Enable JavaScript rendering
  "take_screenshot": true,                // Capture screenshots
  "screenshot_mode": "full",              // Screenshot mode: "full", "top", "off"
  "ocr_extraction": true,                 // Extract text from screenshots using OCR
  "markdown_extraction": "enhanced",      // Markdown extraction: "enhanced", "basic", "none"
  "llm_provider": "anthropic",            // LLM provider: "anthropic", "openai", "local", or empty
  "llm_token": "your-api-token",          // API token for the LLM provider
  "use_lightning": false,                 // Enable Lightning Network payments
  "lightning_budget": 1000                // Lightning budget in satoshis
}
```

### Request Parameters

#### URLs Configuration
- **`urls`** (array of strings): List of URLs to crawl. Can process multiple URLs in a single request.
- **`url`** (string): Alternative to `urls` for single URL requests. If both are provided, `url` is added to the `urls` array.

#### Report Configuration
- **`title`** (string): Custom title for the generated report. Defaults to "Web Crawl Report - {timestamp}"
- **`output_format`** (string): Controls file generation:
  - `"markdown"`: Generate only Markdown report
  - `"html"`: Generate only HTML report
  - `"json"`: Generate only JSON report
  - `"all"` or `"both"`: Generate all formats

#### Response Format Options
- **`response_format`** (string): Controls the API response structure:
  - `"full"`: Complete response with all metadata and truncated content
  - `"content_only"`: Returns just the markdown content and basic info
  - `"minimal"`: Essential data without truncation or file paths

#### Crawling Configuration
- **`javascript_enabled`** (boolean): Enable JavaScript execution during crawling. Default: `false`
- **`take_screenshot`** (boolean): Capture screenshots of pages. Default: `true`
- **`screenshot_mode`** (string): Screenshot capture mode:
  - `"full"`: Capture entire page
  - `"top"`: Capture only the visible viewport
  - `"off"`: Disable screenshots (same as `take_screenshot: false`)
- **`ocr_extraction`** (boolean): Extract text from screenshots using OCR. Default: `true`
  - Note: Automatically disabled if `take_screenshot` is `false`
- **`markdown_extraction`** (string): Content extraction method:
  - `"enhanced"`: Apply content filtering and pruning (threshold: 0.48)
  - `"basic"`: Convert HTML to Markdown without filtering
  - `"none"`: Skip Markdown generation

#### AI Processing Configuration
- **`llm_provider`** (string): AI provider for content analysis:
  - `"anthropic"`: Use Claude API
  - `"openai"`: Use OpenAI API
  - `"local"`: Use local model
  - Empty/null: Skip AI processing
- **`llm_token`** (string): API authentication token for the specified provider

#### Lightning Network Configuration
- **`use_lightning`** (boolean): Enable Lightning Network micropayments. Default: `false`
- **`lightning_budget`** (number): Maximum satoshis to spend. Default: `0`
  - Individual page analysis: 100 sats
  - Overall summary (multiple URLs): 200 sats

### Response Formats

#### Minimal Format (Default)
```json
{
  "success": true,
  "urls_processed": ["https://example.com"],
  "results": [
    {
      "url": "https://example.com",
      "title": "Example Domain",
      "success": true,
      "markdown_content": "Full extracted content without truncation..."
    }
  ]
}
```

#### Content Only Format
```json
{
  "success": true,
  "url": "https://example.com",
  "markdown_content": "# Example Domain\n\nThis is the extracted content...",
  "title": "Example Domain",
  "report_path": "report_20250108_123456.md",
  "html_path": "report_20250108_123456.html",
  "json_path": "report_20250108_123456.json"
}
```

#### Full Format
```json
{
  "success": true,
  "urls_processed": ["https://example.com"],
  "results": [
    {
      "url": "https://example.com",
      "title": "Example Domain",
      "javascript_enabled": false,
      "take_screenshot": true,
      "ocr_extraction": true,
      "markdown_extraction": "enhanced",
      "screenshot": "screenshot_abc123.png",
      "extracted_text": "Text extracted via OCR (truncated to 1000 chars)...",
      "llm_summary": "AI-generated summary of the content",
      "overall_summary": "Executive summary across all pages (if multiple URLs)"
    }
  ],
  "report_path": "report_20250108_123456.md",
  "html_path": "report_20250108_123456.html",
  "json_path": "report_20250108_123456.json",
  "raw_crawl_data": [/* Full unprocessed crawl results */]
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error message describing what went wrong"
}
```

### Processing Pipeline

1. **URL Validation**: Ensures valid URL(s) are provided
2. **Browser Initialization**: Starts Playwright browser with specified settings
3. **Page Navigation**: Navigates to each URL with error handling
4. **Content Extraction**:
   - HTML content retrieval
   - Screenshot capture (if enabled)
   - OCR text extraction (if enabled)
   - Markdown generation (if enabled)
5. **AI Processing** (if configured):
   - Individual page analysis
   - Overall summary for multiple URLs
6. **Report Generation**: Creates files in requested formats
7. **Response Formatting**: Returns data in specified format

### Content Priority

The system tries multiple content sources in order of preference:
1. `markdown_content` - Generated Markdown from HTML
2. `filtered_content` - Processed/filtered content
3. `fit_markdown_content` - Enhanced filtered Markdown
4. `extracted_text` - OCR-extracted text
5. `html_content` - Raw HTML as fallback

### Usage Examples

#### Basic Single URL Crawl
```bash
curl -X POST http://localhost:5678/api/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "response_format": "minimal"
  }'
```

#### Multiple URLs with AI Processing
```bash
curl -X POST http://localhost:5678/api/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com", "https://example.org"],
    "llm_provider": "anthropic",
    "llm_token": "sk-ant-...",
    "javascript_enabled": true,
    "markdown_extraction": "enhanced"
  }'
```

#### Screenshot-Only Request
```bash
curl -X POST http://localhost:5678/api/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "take_screenshot": true,
    "ocr_extraction": false,
    "markdown_extraction": "none",
    "response_format": "content_only"
  }'
```

### Implementation Notes

1. **Authentication**: The endpoint requires user authentication via session
2. **User Isolation**: Screenshots and reports are stored in user-specific directories based on email hash
3. **Error Handling**: Continues processing even if individual URLs fail
4. **Resource Management**: Browser is always closed after processing completes
5. **Type Safety**: Handles various input types with explicit conversions
6. **Logging**: Comprehensive logging throughout the pipeline for debugging

### Performance Considerations

- JavaScript rendering increases processing time significantly
- OCR extraction is CPU/GPU intensive
- Enhanced markdown filtering adds processing overhead
- Multiple URLs are processed sequentially, not in parallel
- AI processing adds network latency and potential rate limiting

### Storage Paths

- Screenshots: `{STORAGE_PATH}/users/{user_hash}/screenshots/`
- Reports: `{STORAGE_PATH}/users/{user_hash}/reports/`
- JSON data: `{STORAGE_PATH}/users/{user_hash}/reports/`

Where `user_hash` is a SHA-256 hash of the user's email address.

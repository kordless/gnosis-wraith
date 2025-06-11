# Gnosis Wraith API v2 Documentation for MCP Tool Development

## Overview

Gnosis Wraith v2 provides focused REST endpoints for web crawling, content extraction, and document generation. This documentation is designed for AI agents building MCP (Model Context Protocol) tools.

## Base Configuration

```javascript
const WRAITH_CONFIG = {
  baseUrl: 'https://your-wraith-instance.com/api/v2',
  headers: {
    'Authorization': 'Bearer YOUR_API_TOKEN',
    'Content-Type': 'application/json'
  }
};
```

## Authentication

All endpoints require API token authentication via:
- **Header**: `Authorization: Bearer YOUR_API_TOKEN`

## Endpoints

### 1. Markdown Extraction

Extract clean markdown content from any webpage.

**Endpoint**: `POST /md`

**Request**:
```json
{
  "url": "https://example.com",
  "filter": "pruning",              // Optional: null | "pruning" | "bm25"
  "filter_options": {               // Optional
    "threshold": 0.48,              // For pruning filter
    "query": "specific topic"       // For BM25 filter
  },
  "format": "clean",                // Optional: "raw" | "clean" | "fit"
  "javascript": true                // Optional: enable JS rendering
}
```

**Response**:
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

**MCP Tool Example**:
```javascript
async function extractMarkdown(url, options = {}) {
  const response = await fetch(`${WRAITH_CONFIG.baseUrl}/md`, {
    method: 'POST',
    headers: WRAITH_CONFIG.headers,
    body: JSON.stringify({
      url,
      filter: options.filter || null,
      javascript: options.javascript !== false
    })
  });
  
  if (!response.ok) {
    throw new Error(`Failed to extract markdown: ${response.statusText}`);
  }
  
  return await response.json();
}
```

### 2. Screenshot Capture

Capture webpage screenshots in various formats.

**Endpoint**: `POST /screenshot`

**Request**:
```json
{
  "url": "https://example.com",
  "mode": "viewport",               // "viewport" | "full"
  "format": "base64",               // "base64" | "url" | "file"
  "wait_for": 2000,                 // Optional: milliseconds
  "options": {
    "quality": 90,                  // Optional: JPEG quality
    "clip": {                       // Optional: specific area
      "x": 0,
      "y": 0,
      "width": 800,
      "height": 600
    }
  }
}
```

**Response (base64)**:
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

### 3. PDF Generation

Generate PDF documents from webpages.

**Endpoint**: `POST /pdf`

**Request**:
```json
{
  "url": "https://example.com",
  "options": {
    "format": "A4",                 // "A4" | "Letter" | "Legal"
    "landscape": false,
    "print_background": true,
    "margin": {
      "top": "1in",
      "bottom": "1in"
    },
    "wait_for": 2000
  }
}
```

**Response**: Binary PDF data with headers:
- `Content-Type: application/pdf`
- `Content-Disposition: attachment; filename="domain_2025_01_10.pdf"`

### 4. HTML Extraction

Extract cleaned or raw HTML content.

**Endpoint**: `POST /html`

**Request**:
```json
{
  "url": "https://example.com",
  "clean": true,                    // Apply cleaning
  "javascript": true,               // Enable JS
  "wait_for": "div.content"         // Optional: CSS selector
}
```

**Response**:
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

### 5. Batch Processing

Process multiple URLs concurrently.

**Endpoint**: `POST /batch`

**Request**:
```json
{
  "urls": ["https://example1.com", "https://example2.com"],
  "options": {
    "filter": "pruning",
    "javascript": true
  },
  "batch": {
    "concurrent": 3,                // Max concurrent
    "delay": 1000,                  // ms between requests
    "continue_on_error": true
  }
}
```

**Response**:
```json
{
  "success": true,
  "total": 2,
  "processed": 2,
  "errors": 0,
  "results": [
    {
      "url": "https://example1.com",
      "success": true,
      "data": { /* Result data */ }
    }
  ]
}
```

## MCP Tool Implementation Guide

### Basic MCP Tool Structure

```javascript
// wraith_mcp_tool.js
class WraithMCP {
  constructor(apiToken, baseUrl = 'https://wraith.example.com/api/v2') {
    this.apiToken = apiToken;
    this.baseUrl = baseUrl;
    this.headers = {
      'Authorization': `Bearer ${apiToken}`,
      'Content-Type': 'application/json'
    };
  }

  async extractContent(url, options = {}) {
    const endpoint = options.format === 'html' ? '/html' : '/md';
    
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({
        url,
        ...options
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Extraction failed');
    }

    return await response.json();
  }

  async captureScreenshot(url, options = {}) {
    const response = await fetch(`${this.baseUrl}/screenshot`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({
        url,
        mode: options.fullPage ? 'full' : 'viewport',
        format: 'base64',
        ...options
      })
    });

    if (!response.ok) {
      throw new Error('Screenshot capture failed');
    }

    const data = await response.json();
    return data.screenshot.data;
  }

  async generatePDF(url, options = {}) {
    const response = await fetch(`${this.baseUrl}/pdf`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiToken}`
      },
      body: JSON.stringify({
        url,
        options
      })
    });

    if (!response.ok) {
      throw new Error('PDF generation failed');
    }

    return await response.blob();
  }

  async batchExtract(urls, options = {}) {
    const response = await fetch(`${this.baseUrl}/batch`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({
        urls,
        options,
        batch: {
          concurrent: 3,
          delay: 1000,
          continue_on_error: true
        }
      })
    });

    if (!response.ok) {
      throw new Error('Batch processing failed');
    }

    return await response.json();
  }
}
```

### MCP Tool Registration

```javascript
// Register as MCP tool
const wraith = new WraithMCP(process.env.WRAITH_API_TOKEN);

mcp.registerTool({
  name: 'extract_webpage_content',
  description: 'Extract clean markdown content from any webpage',
  parameters: {
    url: { type: 'string', required: true },
    filter: { type: 'string', enum: ['pruning', 'bm25'] },
    query: { type: 'string' }
  },
  handler: async ({ url, filter, query }) => {
    const options = { filter };
    if (filter === 'bm25' && query) {
      options.filter_options = { query };
    }
    
    const result = await wraith.extractContent(url, options);
    return {
      content: result.markdown,
      wordCount: result.stats.word_count
    };
  }
});
```

## Common Use Cases

### 1. Research Assistant

```javascript
async function researchTopic(topic, urls) {
  const wraith = new WraithMCP(API_TOKEN);
  
  // Extract content from multiple sources
  const results = await wraith.batchExtract(urls, {
    filter: 'bm25',
    filter_options: { query: topic }
  });
  
  // Process results
  const relevantContent = results.results
    .filter(r => r.success)
    .map(r => r.data.markdown)
    .join('\n\n---\n\n');
  
  return relevantContent;
}
```

### 2. Documentation Generator

```javascript
async function generateDocumentation(url) {
  const wraith = new WraithMCP(API_TOKEN);
  
  // Extract markdown
  const content = await wraith.extractContent(url, {
    filter: 'pruning',
    javascript: true
  });
  
  // Generate PDF
  const pdfBlob = await wraith.generatePDF(url, {
    format: 'A4',
    print_background: true
  });
  
  return {
    markdown: content.markdown,
    pdf: pdfBlob
  };
}
```

### 3. Visual Content Analyzer

```javascript
async function analyzeVisualContent(url) {
  const wraith = new WraithMCP(API_TOKEN);
  
  // Capture full page screenshot
  const screenshot = await wraith.captureScreenshot(url, {
    fullPage: true,
    wait_for: 3000
  });
  
  // Extract text content
  const content = await wraith.extractContent(url);
  
  return {
    screenshot,
    text: content.markdown,
    stats: content.stats
  };
}
```

## Error Handling

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "Descriptive error message"
}
```

Common HTTP status codes:
- `200` - Success
- `400` - Bad request (invalid parameters)
- `401` - Unauthorized (invalid/missing token)
- `429` - Rate limit exceeded
- `500` - Server error

### Error Handling Example

```javascript
try {
  const result = await wraith.extractContent(url);
  return result;
} catch (error) {
  if (error.message.includes('401')) {
    console.error('Invalid API token');
  } else if (error.message.includes('429')) {
    console.error('Rate limit exceeded, retry later');
  } else {
    console.error('Extraction failed:', error.message);
  }
  throw error;
}
```

## Rate Limits

- Default: 1000 requests/hour per token
- Batch requests count as multiple requests
- Use delays between requests to avoid limits

## Best Practices

1. **Cache Results**: Store extracted content to avoid repeated calls
2. **Use Batch API**: Process multiple URLs efficiently
3. **Handle Timeouts**: Set appropriate timeouts for long-running requests
4. **Error Recovery**: Implement retry logic with exponential backoff
5. **Resource Cleanup**: Close connections properly

## Quick Start Example

```javascript
// Complete example for MCP tool
async function main() {
  const wraith = new WraithMCP(process.env.WRAITH_API_TOKEN);
  
  try {
    // Extract content
    const content = await wraith.extractContent('https://example.com', {
      filter: 'pruning',
      javascript: true
    });
    
    console.log(`Extracted ${content.stats.word_count} words`);
    console.log(content.markdown);
    
  } catch (error) {
    console.error('Failed:', error.message);
  }
}

main();
```

## Environment Variables

```bash
WRAITH_API_TOKEN=your_token_here
WRAITH_BASE_URL=https://your-instance.com/api/v2
```

## Support

For issues or questions about the API, check the response headers for request IDs and include them in bug reports.

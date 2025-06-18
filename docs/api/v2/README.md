# Gnosis Wraith API v2 Documentation

Welcome to the comprehensive guide for Gnosis Wraith API v2. This documentation covers all endpoints, features, and capabilities of the modern API.

## 📚 Documentation Structure

1. **[Getting Started](./getting-started.md)** - Authentication, base URLs, and quick start
2. **[Core Endpoints](./core-endpoints.md)** - Web scraping and crawling endpoints
3. **[JavaScript Execution](./javascript-execution.md)** - Dynamic page manipulation
4. **[Content Processing](./content-processing.md)** - AI-powered content analysis
5. **[Examples](./examples.md)** - Real-world usage examples
6. **[Error Handling](./error-handling.md)** - Common errors and solutions

## 🚀 Quick Start

```bash
# Get your API token from the web interface
curl -X POST https://your-instance.com/api/v2/scrape \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "formats": ["markdown", "screenshot"]
  }'
```

## 🔑 Key Features

### Core Web Intelligence
- **Single Page Scraping** - Extract content from any webpage
- **Multi-Page Crawling** - Crawl entire websites with depth control
- **Screenshot Capture** - Visual representation of pages
- **Search Integration** - Web search with automatic scraping

### AI-Powered Capabilities
- **JavaScript Execution** - Modify pages dynamically
- **Natural Language to Code** - Generate JavaScript from descriptions
- **Content Analysis** - Extract entities, sentiment, and insights
- **Smart Summarization** - Create intelligent summaries
- **Markdown Optimization** - Clean and enhance content

### Developer-Friendly
- **RESTful API** - Standard HTTP methods and responses
- **Multiple SDKs** - Python, JavaScript, and more
- **Comprehensive Examples** - Real-world use cases
- **Detailed Error Messages** - Easy debugging

## 📊 API Overview

| Category | Endpoints | Description |
|----------|-----------|-------------|
| **Core** | `/v2/scrape`, `/v2/crawl`, `/v2/search` | Basic web intelligence |
| **Media** | `/v2/screenshot`, `/v2/md` | Specific format extraction |
| **JavaScript** | `/v2/execute`, `/v2/inject`, `/v2/validate` | Dynamic page manipulation |
| **AI Processing** | `/v2/analyze`, `/v2/clean`, `/v2/summarize` | Content intelligence |
| **Jobs** | `/v2/jobs/{job_id}` | Async operation management |

## 🔒 Authentication

All API requests require authentication using a Bearer token:

```
Authorization: Bearer YOUR_API_TOKEN
```

Get your API token from the web interface at `/auth/token`.

## 📈 Rate Limits

- **Default**: 100 requests per minute
- **Crawling**: 10 concurrent crawls
- **JavaScript**: 50 executions per minute

## 🆕 What's New in v2

1. **LLM Integration** - Direct integration with Anthropic, OpenAI, and Gemini
2. **JavaScript Execution** - Safe, sandboxed JavaScript execution
3. **Enhanced Security** - Pattern-based code validation
4. **Structured Extraction** - Schema-based data extraction
5. **Batch Operations** - Process multiple URLs efficiently

## 📝 Version

Current API Version: **2.0.0**  
Last Updated: **January 2025**

---

For detailed information on each endpoint, please refer to the specific documentation sections.
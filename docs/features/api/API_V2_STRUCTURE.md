# Gnosis Wraith API v2 Complete Structure

## API Design Philosophy
- Single-purpose endpoints for clarity and performance
- Consistent response formats
- LLM-powered agentic capabilities
- Tool chaining and workflow automation

## Base Configuration
- Base URL: `https://your-instance.com/api/v2`
- Authentication: `Authorization: Bearer YOUR_API_TOKEN`
- Content-Type: `application/json`

## Endpoint Categories

### 1. Content Extraction Endpoints

#### `/api/v2/md` - Markdown Extraction ✅
Extract clean markdown from any webpage.

#### `/api/v2/html` - HTML Extraction ✅
Extract raw or cleaned HTML content.

#### `/api/v2/text` - Plain Text Extraction 🔲
Extract plain text without formatting.

#### `/api/v2/structured` - Structured Data Extraction 🔲
Extract structured data (JSON-LD, microdata, etc).

### 2. Visual Capture Endpoints

#### `/api/v2/screenshot` - Screenshot Capture ✅
Capture webpage screenshots (viewport/full).

#### `/api/v2/pdf` - PDF Generation ✅
Generate PDF documents from webpages.

#### `/api/v2/video` - Video Recording 🔲
Record webpage interactions and animations.

### 3. JavaScript Execution Endpoints

#### `/api/v2/execute` - Execute JavaScript 🔲
Execute custom JavaScript on target page.

#### `/api/v2/inject` - LLM-Generated JavaScript Injection 🔲
Generate and execute JavaScript based on natural language request.

#### `/api/v2/interact` - Page Interaction 🔲
Perform clicks, scrolls, form fills via JavaScript.

### 4. LLM-Powered Analysis Endpoints

#### `/api/v2/analyze` - Content Analysis 🔲
Analyze page content with LLM and return insights.

#### `/api/v2/suggest` - Code/Action Suggestions 🔲
Get LLM suggestions for processing extracted content.

#### `/api/v2/clean` - Content Cleanup 🔲
Use LLM to clean and optimize markdown/text.

#### `/api/v2/summarize` - Content Summarization 🔲
Generate summaries of extracted content.

### 5. OCR and Vision Endpoints

#### `/api/v2/ocr` - OCR Extraction 🔲
Extract text from images on page.

#### `/api/v2/vision` - Vision Analysis 🔲
Send images to vision-capable LLMs for analysis.

#### `/api/v2/describe` - Image Description 🔲
Generate descriptions of images found on page.

### 6. Workflow and Automation Endpoints

#### `/api/v2/workflow` - Execute Workflow 🔲
Run multi-step agentic workflows.

#### `/api/v2/chain` - Tool Chaining 🔲
Chain multiple operations in sequence.

#### `/api/v2/pipeline` - Data Pipeline 🔲
Create data transformation pipelines.

### 7. Batch and Parallel Processing

#### `/api/v2/batch` - Batch Processing ✅
Process multiple URLs with same operation.

#### `/api/v2/parallel` - Parallel Execution 🔲
Execute multiple different operations on same URL.

### 8. Search and Discovery

#### `/api/v2/search` - Search Within Content 🔲
Search extracted content using various methods.

#### `/api/v2/discover` - Link Discovery 🔲
Discover and analyze links on page.

#### `/api/v2/sitemap` - Sitemap Generation 🔲
Generate sitemap from crawled pages.

### 9. Monitoring and Status

#### `/api/v2/status` - Job Status 🔲
Check status of long-running operations.

#### `/api/v2/health` - Health Check ✅
API health and availability check.

#### `/api/v2/metrics` - Usage Metrics 🔲
Get usage statistics and metrics.

### 10. Export and Integration

#### `/api/v2/export` - Export in Multiple Formats 🔲
Export results in various formats (CSV, JSON, XML).

#### `/api/v2/webhook` - Webhook Integration 🔲
Send results to webhook endpoints.

#### `/api/v2/stream` - Streaming Results 🔲
Stream results as they're processed.

## Legend
- ✅ Already implemented
- 🔲 To be implemented

## Priority Implementation Order
1. JavaScript execution endpoints (execute, inject)
2. LLM analysis endpoints (analyze, suggest, clean)
3. OCR/Vision endpoints
4. Workflow automation
5. Advanced features (streaming, webhooks)

## Response Format Standards

### Success Response
```json
{
  "success": true,
  "data": {
    // Endpoint-specific data
  },
  "metadata": {
    "timestamp": "2025-01-10T12:34:56Z",
    "processing_time_ms": 1234,
    "tokens_used": 567
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "INVALID_URL",
    "message": "The provided URL is not valid",
    "details": {}
  }
}
```

### Async Operation Response
```json
{
  "success": true,
  "job_id": "job_abc123",
  "status": "processing",
  "status_url": "/api/v2/status/job_abc123"
}
```

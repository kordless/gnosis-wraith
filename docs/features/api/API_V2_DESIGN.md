# Gnosis Wraith API v2 Design Summary

## Overview

The new v2 API endpoints follow crawl4ai's design philosophy while addressing Wraith's specific issues identified in the project notes:

1. **Response size optimization** - HTML content excluded by default
2. **Focused endpoints** - Each endpoint does one thing well
3. **Clean API design** - Predictable parameters and responses
4. **Performance** - Optimized for specific use cases

## Key Design Decisions

### 1. Default Response Optimization

From your notes (#68-72), the main issue was massive response sizes due to HTML inclusion. The v2 API addresses this:

- **No HTML by default** in any endpoint
- **Explicit `/html` endpoint** when HTML is actually needed
- **Minimal response formats** optimized for each use case

### 2. Endpoint Separation

Instead of one monolithic `/api/crawl` endpoint, we have:

- `/api/v2/md` - Just markdown extraction
- `/api/v2/screenshot` - Just screenshots
- `/api/v2/pdf` - Just PDF generation
- `/api/v2/html` - Just HTML (when needed)
- `/api/v2/batch` - Batch processing

### 3. Markdown-First Approach

The `/md` endpoint is optimized for the most common use case:

```json
POST /api/v2/md
{
  "url": "https://example.com"
}

Response:
{
  "success": true,
  "url": "https://example.com",
  "markdown": "# Content here...",
  "stats": { "word_count": 1234 }
}
```

### 4. Flexible Output Formats

Each endpoint supports multiple output formats:

**Screenshot endpoint:**
- `format: "base64"` - For API integration
- `format: "url"` - Returns saved file URL
- `format: "file"` - Direct file download

**PDF endpoint:**
- Always returns actual PDF file
- Proper Content-Type and Content-Disposition headers

### 5. Consistent Error Handling

All endpoints return:
```json
{
  "success": false,
  "error": "Clear error message"
}
```

## Implementation Strategy

### Phase 1: Add New Endpoints (Current)
- Created `/web/routes/api_v2.py` with new endpoints
- Updated documentation
- Backward compatible - old API still works

### Phase 2: Update UI Components
- Update browser extension to use `/api/v2/screenshot`
- Update main UI to use `/api/v2/md` for content
- Add endpoint selection in settings

### Phase 3: Migrate and Optimize
- Update crawl_url() to support lightweight operations
- Implement proper concurrency for batch endpoint
- Add caching layer for repeated requests

### Phase 4: Deprecate v1
- Mark v1 as deprecated in docs
- Add deprecation warnings
- Remove after transition period

## Comparison with crawl4ai

### What We Adopted:
- Focused endpoints (`/md`, `/screenshot`, `/pdf`)
- Minimal response formats
- Batch processing support
- Clean parameter structure

### What We Improved:
- No HTML by default (crawl4ai includes it)
- Flexible output formats per endpoint
- Better error messages
- Simpler authentication (session-based)

### What We Didn't Include:
- Streaming endpoints (can add later if needed)
- JavaScript execution endpoint (security concerns)
- MCP integration (different architecture)

## Benefits

1. **Performance**: Responses are 90%+ smaller without HTML
2. **Clarity**: Each endpoint has clear purpose
3. **Flexibility**: Multiple output formats per endpoint
4. **Compatibility**: Works alongside existing API
5. **Evolution**: Easy to add new endpoints

## Next Steps

1. Implement the core modules:
   - `core/markdown_extractor.py`
   - `core/screenshot_capture.py`
   - `core/pdf_generator.py`
   - `core/html_cleaner.py`

2. Update browser extension to use new endpoints

3. Add endpoint selection to UI settings

4. Monitor usage and optimize based on patterns

5. Consider adding:
   - `/api/v2/extract` - For structured data extraction
   - `/api/v2/analyze` - For AI-powered analysis
   - `/api/v2/stream` - For real-time processing

This design provides a clean upgrade path while maintaining backward compatibility and addressing the core issues identified in your project notes.

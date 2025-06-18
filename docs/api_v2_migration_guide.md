# API V2 Consolidation - Migration Guide

## What Changed

### Before:
- **3 files**: `api.py`, `api_v2.py`, `api_v2_llm.py`
- **3 URL prefixes**: `/api/*`, `/api/v2/*`, `/v2/*`
- **Duplicate endpoints** in multiple files
- **Confusing** "legacy" endpoints on `/v2`

### After:
- **1 consolidated file**: `api_v2_consolidated.py`
- **1 URL prefix**: `/api/v2/*`
- **No duplicates**, each endpoint implemented once
- **Clear organization** by functionality

## URL Changes

All V2 endpoints now use consistent `/api/v2/*` prefix:

| Old URL | New URL |
|---------|---------|
| `/v2/crawl` | `/api/v2/crawl` |
| `/v2/jobs/{id}` | `/api/v2/jobs/{id}` |
| `/v2/search` | `/api/v2/search` |
| `/v2/estimate` | `/api/v2/estimate` |
| `/v2/execute` | `/api/v2/execute` |
| `/v2/inject` | `/api/v2/inject` |
| `/v2/validate` | `/api/v2/validate` |
| `/v2/suggest-urls` | `/api/v2/suggest-urls` |
| `/v2/code` | `/api/v2/code` |
| `/v2/models` | `/api/v2/models` |
| `/v2/claude-analyze` | `/api/v2/claude-analyze` |
| `/v2/summarize` | `/api/v2/summarize` |
| `/v2/screenshot` | `/api/v2/screenshot` |
| `/v2/markdown` | `/api/v2/markdown` |
| `/v2/workflows/{name}` | `/api/v2/workflows/{name}` |
| `/v2/health` | `/api/v2/health` |
| `/v2/docs` | `/api/v2/docs` |

## New/Renamed Endpoints

- `/api/v2/suggest` → `/api/v2/suggest-code` (to differentiate from suggest-urls)
- `/api/v2/interact` - New endpoint for page element interactions
- `/api/v2/analyze` - Advanced content analysis (different from claude-analyze)
- `/api/v2/clean` - Clean markdown content
- `/api/v2/extract` - Extract structured data

## Client Code Updates

Update any code using the old `/v2/*` endpoints:

```python
# Old
response = requests.post("http://localhost:5678/v2/execute", ...)

# New  
response = requests.post("http://localhost:5678/api/v2/execute", ...)
```

```javascript
// Old
fetch('/v2/crawl', {...})

// New
fetch('/api/v2/crawl', {...})
```

## Features Added

1. **Consistent error handling** across all endpoints
2. **Pydantic validation** for request bodies
3. **Better organization** - endpoints grouped by functionality
4. **Improved documentation** at `/api/v2/docs`
5. **Health check** includes feature availability

## Archived Files

The following files are no longer used but kept for reference:
- `web/routes/api_v2.py` - Original V2 API implementation
- `web/routes/api_v2_llm.py` - LLM-specific endpoints

## Testing

Test all endpoints after migration:

```bash
# Health check
curl http://localhost:5678/api/v2/health

# Get API docs
curl http://localhost:5678/api/v2/docs

# Test crawl
curl -X POST http://localhost:5678/api/v2/crawl \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Test execute
curl -X POST http://localhost:5678/api/v2/execute \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "javascript": "document.title"
  }'
```

## Benefits

1. **Single source of truth** - All V2 endpoints in one file
2. **Easier maintenance** - No more hunting across files
3. **Consistent URLs** - Everything under `/api/v2`
4. **Better testing** - Clear endpoint locations
5. **Reduced confusion** - No more "legacy" endpoints on new paths

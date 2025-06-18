# Gnosis Wraith API Consolidation Plan

## Current State Analysis

### File Structure:
1. **web/routes/api.py** - Original v1 API
2. **web/routes/api_v2.py** - V2 API with merged LLM endpoints
3. **web/routes/api_v2_llm.py** - Separate LLM endpoints (redundant)

### URL Prefixes:
- `/api/*` - V1 endpoints
- `/api/v2/*` - V2 endpoints (should be primary)
- `/v2/*` - Redundant v2 prefix (should be removed)

## Endpoint Inventory

### Core Crawling Endpoints:
| Endpoint | Current Location | Target Location |
|----------|-----------------|-----------------|
| POST /crawl | api.py (/api/crawl) | Keep in V1 |
| POST /crawl | api_v2.py (/api/v2/crawl, /v2/crawl) | Consolidate to /api/v2/crawl |
| GET /jobs/{id} | api_v2.py (/v2/jobs/{id}) | Move to /api/v2/jobs/{id} |
| POST /search | api_v2.py (/api/v2/search, /v2/search) | Consolidate to /api/v2/search |
| POST /estimate | api_v2.py (/v2/estimate) | Move to /api/v2/estimate |

### JavaScript/Browser Endpoints:
| Endpoint | Current Location | Target Location |
|----------|-----------------|-----------------|
| POST /execute | api_v2.py (/v2/execute) + api_v2_llm.py (/api/v2/execute) | Keep at /api/v2/execute |
| POST /inject | api_v2.py (/v2/inject) + api_v2_llm.py (/api/v2/inject) | Keep at /api/v2/inject |
| POST /validate | api_v2.py (/v2/validate) + api_v2_llm.py (/api/v2/validate) | Keep at /api/v2/validate |
| POST /interact | api_v2_llm.py (/api/v2/interact) | Keep at /api/v2/interact |

### AI/LLM Endpoints:
| Endpoint | Current Location | Target Location |
|----------|-----------------|-----------------|
| POST /suggest-urls | api_v2.py (/v2/suggest-urls) | Move to /api/v2/suggest-urls |
| POST /suggest | api_v2_llm.py (/api/v2/suggest) | Rename to /api/v2/suggest-code |
| POST /code | api_v2.py (/v2/code) | Move to /api/v2/code |
| GET /models | api_v2.py (/v2/models) | Move to /api/v2/models |
| POST /claude-analyze | api_v2.py (/v2/claude-analyze) | Move to /api/v2/claude-analyze |
| POST /analyze | api_v2_llm.py (/api/v2/analyze) | Keep at /api/v2/analyze |
| POST /summarize | Both files (duplicate!) | Consolidate to /api/v2/summarize |

### Content Processing Endpoints:
| Endpoint | Current Location | Target Location |
|----------|-----------------|-----------------|
| POST /clean | api_v2_llm.py (/api/v2/clean) | Keep at /api/v2/clean |
| POST /extract | api_v2_llm.py (/api/v2/extract) | Keep at /api/v2/extract |
| POST /markdown | api_v2.py (/v2/markdown) | Move to /api/v2/markdown |
| POST /screenshot | api_v2.py (/v2/screenshot) | Move to /api/v2/screenshot |

### Workflow Endpoints:
| Endpoint | Current Location | Target Location |
|----------|-----------------|-----------------|
| POST /workflows/{name} | api_v2.py (/v2/workflows/{name}) | Move to /api/v2/workflows/{name} |

### Utility Endpoints:
| Endpoint | Current Location | Target Location |
|----------|-----------------|-----------------|
| GET /health | api_v2.py (/v2/health) | Move to /api/v2/health |
| GET /docs | api_v2.py (/v2/docs) | Move to /api/v2/docs |

## Implementation Plan

### Phase 1: Create New Consolidated File
1. Create `web/routes/api_v2_consolidated.py`
2. Single blueprint: `api_v2` with prefix `/api/v2`
3. Import all necessary dependencies
4. Organize endpoints by category

### Phase 2: Migrate Endpoints
1. Copy unique endpoints from `api_v2_llm.py`
2. Merge duplicate endpoints (choose best implementation)
3. Fix all endpoint routes to use `/api/v2/*` prefix
4. Remove redundant code

### Phase 3: Update Registration
1. Update `web/routes/__init__.py` to only import consolidated file
2. Remove imports for old v2 files
3. Test all endpoints

### Phase 4: Cleanup
1. Archive old files (don't delete immediately)
2. Update documentation
3. Update tests

### Phase 5: Client Updates
1. Update any frontend code using `/v2/*` endpoints
2. Update API documentation
3. Add deprecation notices if needed

## Endpoint Organization Structure

```python
# web/routes/api_v2_consolidated.py

# Core Crawling
- /api/v2/crawl
- /api/v2/jobs/{job_id}
- /api/v2/search
- /api/v2/estimate

# JavaScript Execution
- /api/v2/execute
- /api/v2/inject
- /api/v2/validate
- /api/v2/interact

# AI/LLM Features
- /api/v2/claude-analyze
- /api/v2/analyze
- /api/v2/summarize
- /api/v2/suggest-urls
- /api/v2/suggest-code
- /api/v2/code
- /api/v2/models

# Content Processing
- /api/v2/clean
- /api/v2/extract
- /api/v2/markdown
- /api/v2/screenshot

# Workflows
- /api/v2/workflows/{workflow_name}

# Utility
- /api/v2/health
- /api/v2/docs
```

## Benefits
1. **Single source of truth** - All V2 endpoints in one file
2. **Consistent URL structure** - Everything under `/api/v2`
3. **No duplication** - Each endpoint implemented once
4. **Clear organization** - Grouped by functionality
5. **Easier maintenance** - One file to update
6. **Better testing** - Clear endpoint locations

## Migration Checklist
- [ ] Create consolidated file
- [ ] Migrate core endpoints
- [ ] Migrate JavaScript endpoints
- [ ] Migrate AI/LLM endpoints
- [ ] Migrate content endpoints
- [ ] Migrate workflow endpoints
- [ ] Migrate utility endpoints
- [ ] Update __init__.py
- [ ] Test all endpoints
- [ ] Update documentation
- [ ] Archive old files
- [ ] Update client code

# V2 API Test Harness

Comprehensive test suite for Gnosis Wraith V2 API endpoints.

## Overview

This test harness provides:
- **API Testing**: Complete endpoint coverage with auth handling
- **Performance Testing**: Load, concurrency, and stress testing  
- **Integration Testing**: End-to-end workflow validation

## Prerequisites

1. Ensure Docker container is running:
```bash
./scripts/dev/restart-dev.ps1
```

2. Install test dependencies:
```bash
pip install httpx pytest pytest-asyncio
```

## Test Suites

### 1. API Harness (`test_v2_api_harness.py`)

Tests all V2 endpoints for functionality and error handling.

**Run all tests:**
```bash
python tests/rigging/test_v2_api_harness.py
```

**Run specific category:**
```bash
python tests/rigging/test_v2_api_harness.py --category core
# Options: core, ai, js, utility, workflow, all
```

**Test Categories:**
- **Core**: crawl, search, jobs, estimate, health, docs
- **AI**: suggest-urls, code generation, Claude analysis, summarization
- **JavaScript**: execute, inject, validate
- **Utility**: screenshot, markdown extraction
- **Workflows**: pre-built workflow execution

### 2. Performance Tests (`test_v2_performance.py`)

Measures API performance under various load conditions.

**Run all performance tests:**
```bash
python tests/rigging/test_v2_performance.py
```

**Run specific test:**
```bash
python tests/rigging/test_v2_performance.py --test concurrent
# Options: concurrent, sustained, ramp, burst, session, all
```

**Test Types:**
- **Concurrent**: Parallel request handling (10, 25, 50 requests)
- **Sustained**: Constant load over time (e.g., 5 req/s for 30s)
- **Ramp**: Gradually increasing load to find breaking point
- **Burst**: Sudden traffic spikes
- **Session**: Session persistence under load

### 3. Integration Tests (`test_v2_integration.py`)

Tests complete user workflows and feature integration.

**Run all workflows:**
```bash
python tests/rigging/test_v2_integration.py
```

**Run specific workflow:**
```bash
python tests/rigging/test_v2_integration.py --workflow ai
# Options: crawl, async, session, ai, js, extract, monitor, search
```

**Workflows:**
- **Crawl & Analyze**: Crawl → AI analysis → Code generation
- **Async Jobs**: Complex crawl with job monitoring
- **Session**: Session creation and reuse
- **AI Pipeline**: URL suggestion → Content extraction → Summarization
- **JavaScript**: Natural language → JS generation → Validation → Execution
- **Data Extraction**: Schema-based structured data extraction
- **Monitoring**: Change detection between crawls
- **Search**: Multi-page crawl and search

## Using with pytest

Run all tests with pytest:
```bash
pytest tests/rigging/ -v
```

Run specific test file:
```bash
pytest tests/rigging/test_v2_api_harness.py -v
```

Run with coverage:
```bash
pytest tests/rigging/ --cov=web.routes.api_v2 --cov-report=html
```

## Output Files

Tests generate the following files:
- `test_results.json` - Summary of all test results
- `performance_results.json` - Detailed performance metrics
- `integration_results.json` - Workflow execution details

## Custom Base URL

To test against a different server:
```bash
python tests/rigging/test_v2_api_harness.py --base-url http://staging.example.com:5678
```

## Authentication

Tests handle authentication automatically. If you need to use a specific auth token:
```bash
python tests/rigging/test_v2_api_harness.py --auth-token YOUR_TOKEN
```

## Interpreting Results

### API Tests
- ✓ = Endpoint returned expected status code
- ✗ = Unexpected status or error
- Response times should be <1000ms for simple operations

### Performance Tests
- Success rate should be >95% under normal load
- P95 response time should be <2000ms
- Breaking point indicates maximum sustainable load

### Integration Tests  
- Each workflow has multiple steps
- Failure shows which step failed
- Data flows between steps using context variables

## Troubleshooting

**Server not reachable:**
- Ensure Docker container is running
- Check port 5678 is accessible
- Verify no firewall blocking

**Authentication failures:**
- Tests expect development auth mode
- Check auth endpoints are working
- Session cookies may expire

**Slow tests:**
- Performance tests intentionally generate load
- Integration tests may wait for async operations
- Use --quick flag for faster subset

## Adding New Tests

1. Add endpoint to appropriate category in `test_v2_api_harness.py`
2. Create workflow in `test_v2_integration.py` 
3. Add load scenario in `test_v2_performance.py`

Example:
```python
await self.test_endpoint(
    "New Feature",
    "POST", 
    "/new-endpoint",
    {"param": "value"},
    [200, 201]  # Expected status codes
)
```
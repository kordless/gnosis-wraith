# Gnosis Wraith Test Suite

A comprehensive test suite for Gnosis Wraith with support for API key management, environment configuration, and multiple test categories.

## Quick Start

1. **Set up your environment:**
   ```bash
   cd tests
   cp .env.example .env
   # Edit .env and add your API keys
   ```

2. **Install test dependencies:**
   ```bash
   pip install -r rigging/requirements.txt
   ```

3. **Run basic tests (no API keys required):**
   ```bash
   python run_tests.py basic
   ```

## Test Runner Commands

```bash
# Run basic tests (API health, basic crawl)
python run_tests.py basic

# Run AI-powered tests (requires API keys)
python run_tests.py ai

# Run all tests
python run_tests.py all

# List available test categories
python run_tests.py list

# Run specific category
python run_tests.py -c auth
python run_tests.py -c content

# Run specific test file
python run_tests.py -t test_api_health.py

# Run tests by keyword
python run_tests.py -k "test_simple_crawl"

# Run tests with specific markers
python run_tests.py -m "not slow"
```

## Environment Configuration

The test suite uses `.env` for configuration. Copy `.env.example` to `.env` and configure:

### Authentication (Required)
- `GNOSIS_API_TOKEN` - Your Gnosis Wraith API token
  - Get this from the web UI:
    1. Start Gnosis Wraith: `docker-compose up` or `python app.py`
    2. Go to http://localhost:5000
    3. Log in with your phone number
    4. Click the API Token button in the UI
    5. Copy the token to your `.env` file

### AI Provider Keys (Optional)
- `OPENAI_API_KEY` - For GPT models
- `ANTHROPIC_API_KEY` - For Claude models  
- `GOOGLE_API_KEY` - For Gemini models
- `OLLAMA_BASE_URL` - For local Ollama models

### Test Settings
- `TEST_BASE_URL` - API base URL (default: http://localhost:5000)
- `TEST_TIMEOUT` - Default timeout in seconds
- `TEST_USER_EMAIL` - Test user email
- `TEST_USER_PHONE` - Test user phone

### Feature Flags
- `ENABLE_SCREENSHOT_TESTS` - Enable screenshot tests
- `ENABLE_JAVASCRIPT_TESTS` - Enable JavaScript tests
- `ENABLE_AI_TESTS` - Enable AI-powered tests

## Test Categories

### `/rigging/` - Main test suite
- **auth/** - Authentication tests
- **content/** - Content processing tests
- **core/** - Core functionality tests
- **errors/** - Error handling tests
- **javascript/** - JavaScript execution tests
- **performance/** - Performance benchmarks

### Basic Tests (No AI Required)
- `test_api_health.py` - API connectivity and health checks
- `test_basic_crawl.py` - Basic crawling without AI
- `test_ai_simple.py` - Simple AI tests (prompts for keys if needed)

## Running Tests Without API Keys

The test suite can prompt for API keys at runtime:

```bash
# Run tests - will prompt for missing keys
python run_tests.py ai

# The runner will:
# 1. Check .env for keys
# 2. Prompt for missing keys
# 3. Use provided keys for that session only
```

## Writing New Tests

1. **Create test file** in appropriate category:
   ```python
   # tests/rigging/category/test_feature.py
   import pytest
   from tests.rigging.config import config
   
   class TestFeature:
       @pytest.mark.asyncio
       async def test_something(self):
           assert True
   ```

2. **Use configuration:**
   ```python
   from tests.rigging.config import config
   
   # Check if AI is enabled
   if config.ENABLE_AI_TESTS:
       # Run AI tests
   
   # Get API key (prompts if missing)
   key = config.prompt_for_key('openai')
   ```

3. **Skip tests conditionally:**
   ```python
   @pytest.mark.skipif(
       not config.ENABLE_SCREENSHOT_TESTS,
       reason="Screenshot tests disabled"
   )
   async def test_screenshot(self):
       # Test code
   ```

## Advanced Usage

### Running with Coverage
```bash
pytest tests/rigging/ --cov=core --cov=ai --cov-report=html
```

### Parallel Execution
```bash
pytest tests/rigging/ -n auto  # Use all CPU cores
pytest tests/rigging/ -n 4     # Use 4 workers
```

### Generate HTML Report
```bash
pytest tests/rigging/ --html=report.html --self-contained-html
```

### Verbose Output
```bash
python run_tests.py all -v  # Or use pytest directly
pytest tests/rigging/ -vv   # Very verbose
```

## Troubleshooting

### "No module named 'core'" Error
The test runner adds the project root to Python path. Run tests using:
```bash
python tests/run_tests.py
# NOT: python run_tests.py (from tests dir)
```

### API Key Issues
- Keys are loaded from `tests/.env` (not project root .env)
- You can set keys as environment variables
- The runner will prompt for missing keys

### Async Test Issues
Make sure to:
- Use `@pytest.mark.asyncio` decorator
- Use `async def test_...` for async tests
- Install `pytest-asyncio` package

## CI/CD Integration

For CI/CD, set API keys as environment variables:

```yaml
# GitHub Actions example
env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  TEST_BASE_URL: http://localhost:5000

run: |
  pip install -r tests/rigging/requirements.txt
  python tests/run_tests.py all
```
# Wraith Python SDK Specification

## Package Information
- **Name**: `wraith-sdk` (or `gnosis-wraith`)
- **Version**: 2.0.0
- **Python**: >=3.7
- **Dependencies**: 
  - `requests>=2.28.0`
  - `aiohttp>=3.8.0` (for async support)
  - `pydantic>=2.0.0` (for data models)
  - `typing-extensions>=4.0.0`

## Installation

```bash
pip install wraith-sdk
```

## Basic Usage

### Synchronous Client

```python
from wraith import WraithClient

# Initialize client
client = WraithClient(api_key="YOUR_API_KEY")
# Or use environment variable WRAITH_API_KEY

# Scrape a single page
result = client.scrape("https://example.com", formats=["markdown", "html"])
print(result.markdown)
print(result.metadata.title)

# Crawl multiple pages (async job)
crawl_job = client.crawl("https://example.com", limit=50)

# Check job status
status = crawl_job.status()  # "running", "done", or "error"

# Wait for completion
result = crawl_job.wait()  # Blocks until done

# Or check periodically
while crawl_job.status() == "running":
    partial_data = crawl_job.data  # Access partial results
    print(f"Scraped {len(partial_data)} pages so far...")
    time.sleep(5)
```

### Asynchronous Client

```python
import asyncio
from wraith import AsyncWraithClient

async def main():
    async with AsyncWraithClient(api_key="YOUR_API_KEY") as client:
        # Scrape single page
        result = await client.scrape("https://example.com")
        
        # Crawl with streaming updates
        async for page in client.crawl_stream("https://example.com", limit=50):
            print(f"Scraped: {page.url}")
```

## Core Classes

### WraithClient

```python
class WraithClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.wraith.dev",
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize Wraith client.
        
        Args:
            api_key: API key (or set WRAITH_API_KEY env var)
            base_url: API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
    
    def scrape(
        self,
        url: str,
        formats: List[str] = ["markdown"],
        wait_for: Optional[int] = None,
        timeout: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        viewport: Optional[Dict[str, int]] = None
    ) -> ScrapeResult:
        """Scrape a single URL synchronously."""
    
    def crawl(
        self,
        url: str,
        limit: Optional[int] = None,
        depth: Optional[int] = None,
        formats: List[str] = ["markdown"],
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        concurrent_requests: int = 5
    ) -> CrawlJob:
        """Start a crawl job."""
    
    def extract(
        self,
        urls: Union[str, List[str]],
        prompt: str,
        schema: Optional[Dict[str, Any]] = None
    ) -> ExtractResult:
        """Extract structured data using AI."""
    
    def search(
        self,
        query: str,
        limit: int = 10,
        scrape_results: bool = False,
        formats: List[str] = ["markdown"]
    ) -> SearchResult:
        """Search the web and optionally scrape results."""
    
    def screenshot(
        self,
        url: str,
        full_page: bool = True,
        viewport: Optional[Dict[str, int]] = None,
        format: str = "base64"
    ) -> ScreenshotResult:
        """Take a screenshot of a URL."""
    
    def markdown(
        self,
        url: str,
        include_links: bool = True,
        include_images: bool = False
    ) -> MarkdownResult:
        """Get markdown content only."""
```

### Data Models

```python
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class Metadata(BaseModel):
    title: Optional[str]
    description: Optional[str]
    status_code: int
    content_type: str
    timestamp: datetime

class ScrapeResult(BaseModel):
    url: str
    markdown: Optional[str]
    html: Optional[str]
    screenshot: Optional[str]
    links: Optional[List[Dict[str, str]]]
    metadata: Metadata
    scrape_id: str

class CrawlJob(BaseModel):
    job_id: str
    status: str  # "running", "done", "error"
    
    @property
    def data(self) -> List[ScrapeResult]:
        """Get current results (partial if still running)."""
        
    def wait(self, timeout: Optional[int] = None) -> List[ScrapeResult]:
        """Wait for job completion."""
        
    def cancel(self) -> bool:
        """Cancel the running job."""

class ExtractResult(BaseModel):
    data: Dict[str, Any]
    sources: List[Dict[str, Any]]
    extract_id: str

class SearchResult(BaseModel):
    results: List[Dict[str, Any]]
    query: str
    total_results: int
    search_id: str
```

## Advanced Features

### Custom Headers and Authentication

```python
# With custom headers
result = client.scrape(
    "https://api.example.com/data",
    headers={
        "Authorization": "Bearer TOKEN",
        "X-Custom-Header": "value"
    }
)

# With cookies
result = client.scrape(
    "https://example.com",
    headers={
        "Cookie": "session=abc123; user=john"
    }
)
```

### Batch Operations

```python
# Scrape multiple URLs in parallel
urls = ["https://example.com", "https://example.org", "https://example.net"]
results = client.scrape_batch(urls, formats=["markdown"])

# Extract from multiple URLs
extract_result = client.extract(
    urls=["https://example.com/*"],  # Wildcard support
    prompt="Extract all product prices",
    schema={
        "type": "object",
        "properties": {
            "products": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "price": {"type": "number"}
                    }
                }
            }
        }
    }
)
```

### Webhook Support

```python
# Configure webhooks for long-running operations
crawl_job = client.crawl(
    "https://example.com",
    limit=1000,
    webhook={
        "url": "https://your-server.com/webhook",
        "events": ["job.completed", "job.error"],
        "headers": {
            "X-Secret": "your-secret"
        }
    }
)
```

### Error Handling

```python
from wraith.exceptions import (
    WraithError,
    AuthenticationError,
    RateLimitError,
    TimeoutError,
    ExtractionError
)

try:
    result = client.scrape("https://example.com")
except AuthenticationError:
    print("Invalid API key")
except RateLimitError as e:
    print(f"Rate limit exceeded. Retry after {e.retry_after} seconds")
except TimeoutError:
    print("Request timed out")
except WraithError as e:
    print(f"Error: {e.message}")
```

### Context Manager Support

```python
# Automatic cleanup and connection pooling
with WraithClient(api_key="YOUR_API_KEY") as client:
    result = client.scrape("https://example.com")
    # Connections are properly closed on exit
```

### Streaming Results

```python
# Stream crawl results as they complete
for page in client.crawl_stream("https://example.com", limit=100):
    print(f"Scraped: {page.url}")
    process_page(page)
```

### LLM Integration Helpers

```python
# Easy integration with LangChain
from wraith.integrations import LangChainLoader

loader = LangChainLoader(client)
documents = loader.load("https://example.com")

# Easy integration with LlamaIndex
from wraith.integrations import LlamaIndexReader

reader = LlamaIndexReader(client)
documents = reader.load_data(["https://example.com"])
```

## Configuration

### Environment Variables

```bash
WRAITH_API_KEY=your_api_key
WRAITH_BASE_URL=https://custom.wraith.instance
WRAITH_TIMEOUT=60
WRAITH_MAX_RETRIES=5
```

### Configuration File

```python
# wraith_config.py
config = {
    "api_key": "your_api_key",
    "base_url": "https://api.wraith.dev",
    "timeout": 30,
    "max_retries": 3,
    "default_formats": ["markdown"],
    "user_agent": "MyApp/1.0"
}

client = WraithClient(**config)
```

## CLI Usage

```bash
# Install with CLI support
pip install wraith-sdk[cli]

# Scrape a URL
wraith scrape https://example.com --format markdown --output example.md

# Crawl a website
wraith crawl https://example.com --limit 50 --depth 3 --output crawl_results.json

# Extract data
wraith extract https://example.com --prompt "Extract contact information"

# Search
wraith search "latest AI news" --limit 10 --scrape
```

## Testing

```python
# Mock client for testing
from wraith.testing import MockWraithClient

def test_my_scraper():
    client = MockWraithClient()
    client.mock_response("https://example.com", {
        "markdown": "# Test Content",
        "metadata": {"title": "Test"}
    })
    
    result = my_scraper_function(client)
    assert result.title == "Test"
```

## Migration from v1

```python
# Old v1 code
from wraith import Wraith
w = Wraith()
result = w.process("https://example.com", mode="markdown")

# New v2 code
from wraith import WraithClient
client = WraithClient()
result = client.scrape("https://example.com", formats=["markdown"])
```

## Performance Tips

1. **Use connection pooling**: Reuse client instances
2. **Batch operations**: Use `scrape_batch()` for multiple URLs
3. **Async for I/O bound**: Use `AsyncWraithClient` for concurrent operations
4. **Stream large crawls**: Use `crawl_stream()` to process results as they arrive
5. **Set appropriate timeouts**: Adjust based on site complexity

## Complete Example

```python
import asyncio
from wraith import AsyncWraithClient
from wraith.exceptions import WraithError

async def scrape_news_site():
    async with AsyncWraithClient() as client:
        try:
            # Search for news
            search_results = await client.search(
                "AI breakthroughs 2024",
                limit=5,
                scrape_results=True
            )
            
            # Extract structured data from results
            articles = await client.extract(
                urls=[r.url for r in search_results.results],
                prompt="Extract article title, summary, and publication date",
                schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "summary": {"type": "string"},
                        "date": {"type": "string"}
                    }
                }
            )
            
            return articles.data
            
        except WraithError as e:
            print(f"Error: {e}")
            return None

# Run the async function
if __name__ == "__main__":
    results = asyncio.run(scrape_news_site())
    print(results)
```
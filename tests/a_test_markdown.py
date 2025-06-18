"""
Test for the new /api/markdown endpoint

This test verifies the markdown extraction functionality
of the new API structure using apis/api.py
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, Any, Optional


# Configuration
API_TOKEN = "s0qWg6tky2IL6kNeoTh7d3zubp_f0EziQPFoARNizlsJtva0uAfyFg"  # Replace with your actual token
BASE_URL = "http://localhost:5678"
MARKDOWN_ENDPOINT = f"{BASE_URL}/api/markdown"


async def test_markdown_extraction(
    url: str,
    javascript_enabled: bool = True,
    screenshot_mode: Optional[str] = None,
    filter_type: Optional[str] = None,
    filter_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Test the markdown extraction endpoint.
    
    Args:
        url: URL to extract markdown from
        javascript_enabled: Whether to enable JavaScript
        screenshot_mode: 'top', 'full', or None
        filter_type: 'pruning', 'bm25', or None
        filter_options: Options for the selected filter
        
    Returns:
        Response data from the API
    """
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "url": url,
        "javascript_enabled": javascript_enabled
    }
    
    if screenshot_mode:
        payload["screenshot_mode"] = screenshot_mode
    
    if filter_type:
        payload["filter"] = filter_type
        
    if filter_options:
        payload["filter_options"] = filter_options
    
    print(f"\n{'='*60}")
    print(f"Testing markdown extraction for: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"{'='*60}\n")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                MARKDOWN_ENDPOINT,
                headers=headers,
                json=payload
            ) as response:
                data = await response.json()
                
                print(f"Status: {response.status}")
                print(f"Response: {json.dumps(data, indent=2)}")
                
                if response.status == 200 and data.get("success"):
                    print("\n✅ Success!")
                    print(f"Markdown length: {len(data.get('markdown', ''))}")
                    print(f"Word count: {data.get('stats', {}).get('word_count', 0)}")
                    
                    if data.get("markdown_url"):
                        print(f"Markdown saved at: {data['markdown_url']}")
                    if data.get("json_url"):
                        print(f"JSON saved at: {data['json_url']}")
                    if data.get("screenshot_url"):
                        print(f"Screenshot saved at: {data['screenshot_url']}")
                else:
                    print(f"\n❌ Failed: {data.get('error', 'Unknown error')}")
                
                return data
                
        except aiohttp.ClientError as e:
            print(f"\n❌ Request failed: {str(e)}")
            return {"success": False, "error": str(e)}


async def test_health_check():
    """Test the health check endpoint (no auth required)."""
    print(f"\n{'='*60}")
    print("Testing health check endpoint")
    print(f"{'='*60}\n")
    
    endpoints = [
        f"{BASE_URL}/health",
        f"{BASE_URL}/api/health",
        f"{BASE_URL}/api/v2/health"
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints:
            try:
                async with session.get(endpoint) as response:
                    data = await response.json()
                    status_icon = "✅" if response.status == 200 else "❌"
                    print(f"{status_icon} {endpoint}: {response.status} - {data.get('status', 'No status')}")
            except Exception as e:
                print(f"❌ {endpoint}: Failed - {str(e)}")


async def run_all_tests():
    """Run all tests."""
    print(f"Starting Markdown API Tests - {datetime.now()}")
    print(f"Using API Token: {'*' * 20}{API_TOKEN[-4:] if len(API_TOKEN) > 4 else 'NOT SET'}")
    
    # Test health endpoints first (no auth needed)
    await test_health_check()
    
    if API_TOKEN == "YOUR_TOKEN_HERE":
        print("\n⚠️  WARNING: Please set your API token before running markdown tests!")
        return
    
    # Test 1: Basic markdown extraction
    await test_markdown_extraction(
        url="https://example.com",
        javascript_enabled=False
    )
    
    # Test 2: With JavaScript and screenshot
    await test_markdown_extraction(
        url="https://www.python.org",
        javascript_enabled=True,
        screenshot_mode="top"
    )
    
    # Test 3: With pruning filter
    await test_markdown_extraction(
        url="https://en.wikipedia.org/wiki/Web_scraping",
        filter_type="pruning",
        filter_options={
            "threshold": 0.5,
            "min_words": 5
        }
    )
    
    # Test 4: With BM25 filter
    await test_markdown_extraction(
        url="https://docs.python.org/3/",
        filter_type="bm25",
        filter_options={
            "query": "functions classes modules",
            "threshold": 0.3
        }
    )
    
    # Test 5: Full page screenshot
    await test_markdown_extraction(
        url="https://github.com",
        javascript_enabled=True,
        screenshot_mode="full"
    )


async def test_single_url(url: str):
    """Test a single URL - useful for debugging."""
    if API_TOKEN == "YOUR_TOKEN_HERE":
        print("\n⚠️  WARNING: Please set your API token!")
        return
        
    await test_markdown_extraction(
        url=url,
        javascript_enabled=True,
        screenshot_mode="top"
    )


if __name__ == "__main__":
    # Run all tests
    asyncio.run(run_all_tests())
    
    # Or test a single URL:
    # asyncio.run(test_single_url("https://example.com"))

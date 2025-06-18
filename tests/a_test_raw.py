"""
Test for the /api/raw endpoint

This test verifies the raw HTML extraction functionality
without markdown conversion, storage, or screenshots.
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, Any, Optional


# Configuration
API_TOKEN = "P4WAxQIyjSSLr5nmqD6NtQp9BrnSRer_E_zSTknM"  # Replace with your actual token
BASE_URL = "http://localhost:5678"
RAW_ENDPOINT = f"{BASE_URL}/api/raw"


async def test_raw_extraction(
    url: str,
    javascript_enabled: bool = True,
    javascript_payload: Optional[str] = None
) -> Dict[str, Any]:
    """
    Test the raw HTML extraction endpoint.
    
    Args:
        url: URL to extract HTML from
        javascript_enabled: Whether to enable JavaScript
        javascript_payload: Optional JavaScript code to execute
        
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
    
    if javascript_payload:
        payload["javascript_payload"] = javascript_payload
    
    print(f"\n{'='*60}")
    print(f"Testing raw HTML extraction for: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"{'='*60}\n")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                RAW_ENDPOINT,
                headers=headers,
                json=payload
            ) as response:
                data = await response.json()
                
                print(f"Status: {response.status}")
                
                if response.status == 200 and data.get("success"):
                    print("✅ Success!")
                    print(f"Title: {data.get('title', 'No title')}")
                    print(f"HTML length: {len(data.get('html', ''))}")
                    print(f"Content length: {data.get('content_length', 0)}")
                    
                    # Show first 500 chars of HTML
                    html = data.get('html', '')
                    if html:
                        print(f"\nFirst 500 characters of HTML:")
                        print("-" * 50)
                        print(html[:500])
                        print("-" * 50)
                    
                    # Show JavaScript result if any
                    if data.get("javascript_result"):
                        print(f"\nJavaScript Result:")
                        print(json.dumps(data["javascript_result"], indent=2))
                else:
                    print(f"❌ Failed: {data.get('error', 'Unknown error')}")
                    print(f"Full response: {json.dumps(data, indent=2)}")
                
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
        f"{BASE_URL}/api/health"
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
    print(f"Starting Raw API Tests - {datetime.now()}")
    print(f"Using API Token: {'*' * 20}{API_TOKEN[-4:] if len(API_TOKEN) > 4 else 'NOT SET'}")
    
    # Test health endpoints first (no auth needed)
    await test_health_check()
    
    if API_TOKEN == "YOUR_TOKEN_HERE":
        print("\n⚠️  WARNING: Please set your API token before running raw tests!")
        return
    
    # Test 1: Basic raw HTML extraction
    print("\n\n" + "="*60)
    print("TEST 1: Basic HTML extraction (no JavaScript)")
    print("="*60)
    await test_raw_extraction(
        url="https://example.com",
        javascript_enabled=False
    )
    
    '''
    # Test 2: With JavaScript enabled
    print("\n\n" + "="*60)
    print("TEST 2: HTML extraction with JavaScript enabled")
    print("="*60)
    await test_raw_extraction(
        url="https://www.python.org",
        javascript_enabled=True
    )
    
    # Test 3: With JavaScript payload to get page metrics
    print("\n\n" + "="*60)
    print("TEST 3: HTML extraction with JavaScript payload")
    print("="*60)
    await test_raw_extraction(
        url="https://news.ycombinator.com",
        javascript_enabled=True,
        javascript_payload="""
        // Get page metrics
        return {
            title: document.title,
            linkCount: document.querySelectorAll('a').length,
            imageCount: document.querySelectorAll('img').length,
            headingCount: document.querySelectorAll('h1, h2, h3, h4, h5, h6').length,
            wordCount: document.body.innerText.split(/\\s+/).length,
            hasVideo: document.querySelectorAll('video').length > 0,
            hasForms: document.querySelectorAll('form').length > 0,
            viewport: {
                width: window.innerWidth,
                height: window.innerHeight
            }
        };
        """
    )
    
    # Test 4: JavaScript to extract specific data
    print("\n\n" + "="*60)
    print("TEST 4: Extract specific data with JavaScript")
    print("="*60)
    await test_raw_extraction(
        url="https://github.com/trending",
        javascript_enabled=True,
        javascript_payload="""
        // Extract trending repositories
        const repos = [];
        document.querySelectorAll('article.Box-row').forEach((article, index) => {
            if (index < 5) {  // Get first 5
                const link = article.querySelector('h2 a');
                const description = article.querySelector('p');
                const stars = article.querySelector('span.d-inline-block.float-sm-right');
                
                repos.push({
                    name: link ? link.textContent.trim() : '',
                    url: link ? link.href : '',
                    description: description ? description.textContent.trim() : '',
                    stars: stars ? stars.textContent.trim() : ''
                });
            }
        });
        return {
            pageTitle: document.title,
            trendingRepos: repos,
            extractedAt: new Date().toISOString()
        };
        """
    )
    '''

    # Test 5: Error handling - invalid URL
    print("\n\n" + "="*60)
    print("TEST 5: Error handling - invalid URL")
    print("="*60)
    await test_raw_extraction(
        url="not-a-valid-url",
        javascript_enabled=False
    )
    
    # Test 6: Error handling - missing protocol
    print("\n\n" + "="*60)
    print("TEST 6: Error handling - URL without protocol")
    print("="*60)
    await test_raw_extraction(
        url="example.com",
        javascript_enabled=False
    )
    
    # Test 7: Valid URL that might not exist
    print("\n\n" + "="*60)
    print("TEST 7: Valid URL format but non-existent domain")
    print("="*60)
    await test_raw_extraction(
        url="https://this-domain-definitely-does-not-exist-12345.com",
        javascript_enabled=False
    )



async def test_single_url(url: str, js_code: Optional[str] = None):
    """Test a single URL - useful for debugging."""
    if API_TOKEN == "YOUR_TOKEN_HERE":
        print("\n⚠️  WARNING: Please set your API token!")
        return
        
    await test_raw_extraction(
        url=url,
        javascript_enabled=True,
        javascript_payload=js_code
    )


if __name__ == "__main__":
    # Run all tests
    asyncio.run(run_all_tests())
    
    # Or test a single URL:
    # asyncio.run(test_single_url("https://example.com"))
    
    # Or test with custom JavaScript:
    # asyncio.run(test_single_url(
    #     "https://example.com",
    #     "return { customData: document.body.innerHTML.length };"
    # ))

#!/usr/bin/env python3
"""
Test script for Gnosis Wraith /api/markdown endpoint
Tests both single URL and batch URL processing
Based on the actual implementation in web/routes/apis/api.py
"""

import asyncio
import aiohttp
import json
import time
from typing import List, Dict, Any

# Configuration
REMOTE_SERVER = "https://wraith.nuts.services"
API_KEY = "NI1qoVZLEgTVxWFr7lxdx_10ZvqGRgYEEEPa9uS1WHwjkdUkEqh72Q"  # Your API key

# Test URLs
TEST_URLS = [
    "https://example.com",
    "https://www.wikipedia.org",
    "https://news.ycombinator.com",
    "https://www.python.org",
    "https://docs.python.org/3/"
]

async def test_single_url_markdown():
    """Test single URL markdown extraction (backward compatible)"""
    print("\n=== Testing Single URL Markdown ===")
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {
        "url": TEST_URLS[0],
        "javascript_enabled": True,
        "screenshot_mode": None  # No screenshot for speed
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            start_time = time.time()
            async with session.post(f"{REMOTE_SERVER}/api/markdown", json=payload, headers=headers) as response:
                elapsed = time.time() - start_time
                
                print(f"URL: {TEST_URLS[0]}")
                print(f"Status: {response.status}")
                print(f"Time: {elapsed:.2f}s")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Success")
                    print(f"Response keys: {list(data.keys())}")
                    
                    # Check various response fields
                    if 'success' in data:
                        print(f"Success: {data['success']}")
                    if 'url' in data:
                        print(f"URL: {data['url']}")
                    if 'markdown_url' in data:
                        print(f"Markdown URL: {data['markdown_url']}")
                    if 'json_url' in data:
                        print(f"JSON URL: {data['json_url']}")
                    if 'stats' in data:
                        print(f"Stats: {data['stats']}")
                else:
                    error_data = await response.json()
                    print(f"❌ Error: {error_data}")
                    
                return response.status == 200
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return False

async def test_batch_sync():
    """Test synchronous batch processing"""
    print("\n=== Testing Batch Markdown (Sync) ===")
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {
        "urls": TEST_URLS[:3],  # Test with 3 URLs
        "async": False,  # Wait for completion
        "javascript_enabled": True,
        "screenshot_mode": None
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            start_time = time.time()
            async with session.post(f"{REMOTE_SERVER}/api/markdown", json=payload, headers=headers) as response:
                elapsed = time.time() - start_time
                
                print(f"URLs: {len(payload['urls'])} URLs")
                print(f"Status: {response.status}")
                print(f"Time: {elapsed:.2f}s")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Success")
                    print(f"Mode: {data.get('mode', 'N/A')}")
                    print(f"Job ID: {data.get('job_id', 'N/A')}")
                    
                    if 'results' in data:
                        print(f"\nResults: {len(data['results'])} items")
                        for i, result in enumerate(data['results'][:2]):  # Show first 2
                            print(f"\nResult {i+1}:")
                            print(f"  URL: {result.get('url', 'N/A')}")
                            print(f"  Status: {result.get('status', 'N/A')}")
                            print(f"  Markdown URL: {result.get('markdown_url', 'N/A')}")
                            print(f"  JSON URL: {result.get('json_url', 'N/A')}")
                else:
                    error_data = await response.json()
                    print(f"❌ Error: {error_data}")
                    
                return response.status == 200
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return False

async def test_batch_async():
    """Test asynchronous batch processing"""
    print("\n=== Testing Batch Markdown (Async) ===")
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {
        "urls": TEST_URLS[:4],  # Test with 4 URLs
        "async": True,  # Don't wait for completion
        "javascript_enabled": False,  # Faster without JS
        "screenshot_mode": None
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            start_time = time.time()
            async with session.post(f"{REMOTE_SERVER}/api/markdown", json=payload, headers=headers) as response:
                elapsed = time.time() - start_time
                
                print(f"URLs: {len(payload['urls'])} URLs")
                print(f"Status: {response.status}")
                print(f"Time: {elapsed:.2f}s (should be fast for async)")
                
                if response.status in [200, 202]:  # 202 Accepted for async
                    data = await response.json()
                    print(f"✅ Success (Status: {response.status})")
                    print(f"Mode: {data.get('mode', 'N/A')}")
                    print(f"Job ID: {data.get('job_id', 'N/A')}")
                    print(f"Status URL: {data.get('status_url', 'N/A')}")
                    
                    if 'results' in data:
                        print(f"\nPredicted URLs: {len(data['results'])} items")
                        for i, result in enumerate(data['results'][:2]):
                            print(f"  {i+1}. {result.get('url', 'N/A')} - Status: {result.get('status', 'N/A')}")
                else:
                    error_data = await response.json()
                    print(f"❌ Error: {error_data}")
                    
                return response.status in [200, 202]
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return False

async def test_batch_with_collation():
    """Test batch processing with collation"""
    print("\n=== Testing Batch with Collation ===")
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {
        "urls": [
            "https://docs.python.org/3/tutorial/introduction.html",
            "https://docs.python.org/3/tutorial/controlflow.html"
        ],
        "async": False,  # Wait for completion to get collated result
        "collate": True,
        "collate_options": {
            "title": "Python Tutorial Collection",
            "add_toc": True,
            "add_source_headers": True
        },
        "javascript_enabled": False
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            start_time = time.time()
            async with session.post(f"{REMOTE_SERVER}/api/markdown", json=payload, headers=headers) as response:
                elapsed = time.time() - start_time
                
                print(f"URLs: {len(payload['urls'])} URLs")
                print(f"Status: {response.status}")
                print(f"Time: {elapsed:.2f}s")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Success")
                    
                    if 'collated_url' in data:
                        print(f"Collated file URL: {data['collated_url']}")
                    
                    if 'results' in data:
                        print(f"Individual results: {len(data['results'])}")
                else:
                    error_data = await response.json()
                    print(f"❌ Error: {error_data}")
                    
                return response.status == 200
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return False

async def test_with_filters():
    """Test markdown extraction with content filters"""
    print("\n=== Testing with Content Filters ===")
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    # Test with pruning filter
    payload = {
        "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
        "filter": "pruning",
        "filter_options": {
            "threshold": 0.5,
            "min_words": 3
        },
        "javascript_enabled": False
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            print("Testing Pruning Filter...")
            start_time = time.time()
            async with session.post(f"{REMOTE_SERVER}/api/markdown", json=payload, headers=headers) as response:
                elapsed = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    print(f"  ✅ Pruning filter success (Time: {elapsed:.2f}s)")
                    if 'stats' in data:
                        print(f"  Stats: {data['stats']}")
                else:
                    print(f"  ❌ Pruning filter failed: Status {response.status}")
            
            # Test with BM25 filter
            payload["filter"] = "bm25"
            payload["filter_options"] = {
                "query": "python programming syntax",
                "threshold": 0.4
            }
            
            print("\nTesting BM25 Filter...")
            start_time = time.time()
            async with session.post(f"{REMOTE_SERVER}/api/markdown", json=payload, headers=headers) as response:
                elapsed = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    print(f"  ✅ BM25 filter success (Time: {elapsed:.2f}s)")
                    if 'stats' in data:
                        print(f"  Stats: {data['stats']}")
                else:
                    print(f"  ❌ BM25 filter failed: Status {response.status}")
                    
            return True
                    
        except Exception as e:
            print(f"❌ Exception: {e}")
            return False

async def test_error_handling():
    """Test error handling with invalid URLs"""
    print("\n=== Testing Error Handling ===")
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    # Test invalid URL
    payload = {
        "url": "not-a-valid-url"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            print("Testing invalid URL...")
            async with session.post(f"{REMOTE_SERVER}/api/markdown", json=payload, headers=headers) as response:
                data = await response.json()
                print(f"  Status: {response.status}")
                print(f"  Response: {data}")
                
            # Test missing URL
            payload = {}
            print("\nTesting missing URL...")
            async with session.post(f"{REMOTE_SERVER}/api/markdown", json=payload, headers=headers) as response:
                data = await response.json()
                print(f"  Status: {response.status}")
                print(f"  Response: {data}")
                
            # Test too many URLs
            payload = {
                "urls": ["https://example.com"] * 51  # Over 50 limit
            }
            print("\nTesting too many URLs...")
            async with session.post(f"{REMOTE_SERVER}/api/markdown", json=payload, headers=headers) as response:
                data = await response.json()
                print(f"  Status: {response.status}")
                print(f"  Response: {data}")
                
            return True
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return False

async def main():
    """Run all tests"""
    print("=" * 60)
    print("Gnosis Wraith /api/markdown Endpoint Tests")
    print(f"Server: {REMOTE_SERVER}")
    print(f"API Key: {API_KEY[:10]}...")
    print("=" * 60)
    
    # Run tests
    tests = [
        ("Single URL", test_single_url_markdown),
        ("Batch Sync", test_batch_sync),
        ("Batch Async", test_batch_async),
        ("Batch with Collation", test_batch_with_collation),
        ("Content Filters", test_with_filters),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    print("\n📝 Implementation Notes:")
    print("- The /api/markdown endpoint supports both single and batch URLs")
    print("- Batch mode is triggered by providing 'urls' array instead of 'url'")
    print("- Maximum 50 URLs per batch")
    print("- Supports async processing with webhooks")
    print("- Supports content filters (pruning, BM25)")
    print("- Supports collation to merge results")

if __name__ == "__main__":
    asyncio.run(main())

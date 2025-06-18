"""
Live test for the batch markdown endpoint
Tests the actual implementation against a running server
"""
import asyncio
import aiohttp
import json
import time

API_KEY = "uiBv8UPjRORy5XLL5mCMwekdxmuseFJ1wcfTuWDHftwXyfzsFrhfxg"
BASE_URL = "http://localhost:5678"


async def test_single_url_still_works():
    """Test that single URL requests still work (backward compatibility)"""
    print("\n1. Testing backward compatibility with single URL...")
    
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "url": "https://example.com"
        }
        
        async with session.post(
            f"{BASE_URL}/api/markdown",
            json=data,
            headers=headers
        ) as response:
            result = await response.json()
            
            print(f"   Status: {response.status}")
            print(f"   Success: {result.get('success')}")
            print(f"   Has markdown: {'markdown' in result}")
            print(f"   No batch fields: {'job_id' not in result}")
            
            assert response.status == 200
            assert result['success'] == True
            assert 'markdown' in result
            assert 'job_id' not in result


async def test_batch_sync_mode():
    """Test batch processing in synchronous mode"""
    print("\n2. Testing batch mode (sync)...")
    
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "urls": [
                "https://example.com",
                "https://www.iana.org/domains/example"
            ],
            "async": False  # Synchronous mode
        }
        
        start_time = time.time()
        
        async with session.post(
            f"{BASE_URL}/api/markdown",
            json=data,
            headers=headers
        ) as response:
            result = await response.json()
            elapsed = time.time() - start_time
            
            print(f"   Status: {response.status}")
            print(f"   Mode: {result.get('mode')}")
            print(f"   Results: {len(result.get('results', []))}")
            print(f"   Time taken: {elapsed:.2f}s")
            
            if result.get('success'):
                for i, r in enumerate(result['results']):
                    print(f"   URL {i+1}: {r['url']} - {r['status']}")
            else:
                print(f"   Error: {result.get('error')}")
            
            assert response.status == 200
            assert result.get('mode') == 'batch_sync'
            assert len(result.get('results', [])) == 2


async def test_batch_async_mode():
    """Test batch processing in asynchronous mode"""
    print("\n3. Testing batch mode (async)...")
    
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "urls": [
                "https://example.com",
                "https://www.wikipedia.org",
                "https://www.python.org"
            ],
            "async": True  # Asynchronous mode
        }
        
        async with session.post(
            f"{BASE_URL}/api/markdown",
            json=data,
            headers=headers
        ) as response:
            result = await response.json()
            
            print(f"   Status: {response.status}")
            print(f"   Mode: {result.get('mode')}")
            print(f"   Job ID: {result.get('job_id')}")
            print(f"   Status URL: {result.get('status_url')}")
            
            if result.get('success'):
                print(f"   Predicted URLs:")
                for i, r in enumerate(result['results']):
                    print(f"     - {r['markdown_url']}")
            else:
                print(f"   Error: {result.get('error')}")
            
            assert response.status == 202  # Accepted
            assert result.get('mode') == 'batch_async'
            assert 'job_id' in result
            assert 'status_url' in result


async def test_batch_with_collation():
    """Test batch processing with collation"""
    print("\n4. Testing batch with collation...")
    
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "urls": [
                "https://example.com",
                "https://www.iana.org/domains/example"
            ],
            "async": False,
            "collate": True,
            "collate_options": {
                "title": "Example Domains Collection",
                "add_toc": True
            }
        }
        
        async with session.post(
            f"{BASE_URL}/api/markdown",
            json=data,
            headers=headers
        ) as response:
            result = await response.json()
            
            print(f"   Status: {response.status}")
            print(f"   Has collated URL: {'collated_url' in result}")
            
            if 'collated_url' in result:
                print(f"   Collated URL: {result['collated_url']}")
            
            assert response.status == 200
            assert 'collated_url' in result


async def test_batch_error_handling():
    """Test batch with invalid URLs"""
    print("\n5. Testing error handling...")
    
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Test too many URLs
        data = {
            "urls": ["https://example.com"] * 51,  # 51 URLs (over limit)
            "async": False
        }
        
        async with session.post(
            f"{BASE_URL}/api/markdown",
            json=data,
            headers=headers
        ) as response:
            result = await response.json()
            
            print(f"   Too many URLs status: {response.status}")
            print(f"   Error: {result.get('error')}")
            
            assert response.status == 400
            assert "50 URLs" in result.get('error', '')


async def main():
    """Run all tests"""
    print("Testing Batch Markdown Endpoint Implementation")
    print("=" * 50)
    
    try:
        await test_single_url_still_works()
        print("   ✓ Backward compatibility maintained")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
    
    try:
        await test_batch_sync_mode()
        print("   ✓ Synchronous batch mode works")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
    
    try:
        await test_batch_async_mode()
        print("   ✓ Asynchronous batch mode works")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
    
    try:
        await test_batch_with_collation()
        print("   ✓ Collation feature works")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
    
    try:
        await test_batch_error_handling()
        print("   ✓ Error handling works")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
    
    print("\n" + "=" * 50)
    print("Testing complete!")


if __name__ == "__main__":
    asyncio.run(main())
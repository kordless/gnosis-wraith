"""
Test to ensure API works correctly after OCR removal
"""
import asyncio
import aiohttp
import json

API_KEY = "uiBv8UPjRORy5XLL5mCMwekdxmuseFJ1wcfTuWDHftwXyfzsFrhfxg"
BASE_URL = "http://localhost:5678"


async def test_api_still_works():
    """Test that the API endpoints work without OCR"""
    print("Testing API after OCR removal...")
    
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Test 1: Single URL crawl
        print("\n1. Testing single URL crawl...")
        data = {
            "url": "https://example.com",
            "take_screenshot": True,
            "javascript_enabled": False
        }
        
        async with session.post(
            f"{BASE_URL}/api/crawl",
            json=data,
            headers=headers
        ) as response:
            if response.status == 200:
                result = await response.json()
                print(f"   ✓ Single crawl works: {result['results'][0]['title']}")
            else:
                print(f"   ✗ Error: {response.status}")
        
        # Test 2: Markdown extraction
        print("\n2. Testing markdown extraction...")
        data = {
            "url": "https://example.com"
        }
        
        async with session.post(
            f"{BASE_URL}/api/markdown",
            json=data,
            headers=headers
        ) as response:
            if response.status == 200:
                result = await response.json()
                print(f"   ✓ Markdown extraction works")
                print(f"   - Markdown length: {len(result['markdown'])} chars")
            else:
                print(f"   ✗ Error: {response.status}")
        
        # Test 3: Batch markdown (to ensure our new feature still works)
        print("\n3. Testing batch markdown...")
        data = {
            "urls": ["https://example.com", "https://www.iana.org/domains/example"],
            "async": False
        }
        
        async with session.post(
            f"{BASE_URL}/api/markdown",
            json=data,
            headers=headers
        ) as response:
            if response.status == 200:
                result = await response.json()
                print(f"   ✓ Batch markdown works")
                print(f"   - Processed {len(result['results'])} URLs")
            else:
                print(f"   ✗ Error: {response.status}")
        
        # Test 4: Ensure ocr_extraction parameter is ignored gracefully
        print("\n4. Testing backward compatibility (ocr_extraction ignored)...")
        data = {
            "url": "https://example.com",
            "ocr_extraction": True  # This should be ignored
        }
        
        async with session.post(
            f"{BASE_URL}/api/crawl",
            json=data,
            headers=headers
        ) as response:
            if response.status == 200:
                result = await response.json()
                # Check that ocr_extraction is not in the response
                has_ocr = any('ocr_extraction' in r for r in result['results'])
                if not has_ocr:
                    print(f"   ✓ OCR parameter properly ignored")
                else:
                    print(f"   ✗ OCR still in response")
            else:
                print(f"   ✗ Error: {response.status}")


async def main():
    print("=" * 50)
    print("OCR Removal Verification Test")
    print("=" * 50)
    
    try:
        await test_api_still_works()
        print("\n" + "=" * 50)
        print("All tests completed!")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    asyncio.run(main())
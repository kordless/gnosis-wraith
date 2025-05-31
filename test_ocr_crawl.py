#!/usr/bin/env python3
"""
Test OCR Crawl Configuration
Tests the crawl API with different OCR and screenshot settings to verify:
1. OCR doesn't initialize when disabled
2. OCR only initializes when actually enabled and used
3. Screenshots work with and without OCR
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
TEST_URL = "https://example.com"  # Simple test page
CRAWL_ENDPOINT = f"{BASE_URL}/api/crawl"

def make_crawl_request(test_name, config):
    """Make a crawl request with the given configuration"""
    print(f"\n🧪 Test: {test_name}")
    print(f"📋 Config: {json.dumps(config, indent=2)}")
    
    start_time = time.time()
    
    try:
        response = requests.post(CRAWL_ENDPOINT, json=config, timeout=60)
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️  Duration: {duration:.2f}s")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Success: {result.get('message', 'Crawl completed')}")
                if 'results' in result and result['results']:
                    first_result = result['results'][0]
                    print(f"📄 Report: {first_result.get('report_path', 'N/A')}")
                    print(f"📸 Screenshot: {first_result.get('screenshot', 'N/A')}")
                    print(f"🔍 OCR Text: {'Yes' if first_result.get('extracted_text') else 'No'}")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
        else:
            print(f"❌ HTTP Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out")
    except requests.exceptions.ConnectionError:
        print("🔌 Connection error - is the server running?")
    except Exception as e:
        print(f"💥 Error: {str(e)}")
    
    print("-" * 60)

def test_server_health():
    """Check if the server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
            return True
        else:
            print(f"⚠️  Server responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server health check failed: {e}")
        return False

def main():
    print("🕷️  Gnosis Wraith OCR Crawl Test")
    print("=" * 60)
    print(f"🎯 Target URL: {TEST_URL}")
    print(f"🔗 API Endpoint: {CRAWL_ENDPOINT}")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check server health first
    if not test_server_health():
        print("\n❌ Cannot proceed - server is not responding")
        return
    
    # Test configurations
    test_configs = [
        {
            "name": "No Screenshots, No OCR",
            "config": {
                "url": TEST_URL,
                "title": "Test No Screenshots No OCR",
                "take_screenshot": False,
                "screenshot_mode": "off",
                "javascript_enabled": False,
                "ocr_extraction": False,
                "markdown_extraction": "basic"
            }
        },
        {
            "name": "Screenshots Only, No OCR",
            "config": {
                "url": TEST_URL,
                "title": "Test Screenshots Only No OCR",
                "take_screenshot": True,
                "screenshot_mode": "top",
                "javascript_enabled": False,
                "ocr_extraction": False,
                "markdown_extraction": "basic"
            }
        },
        {
            "name": "Screenshots + OCR Enabled",
            "config": {
                "url": TEST_URL,
                "title": "Test Screenshots With OCR",
                "take_screenshot": True,
                "screenshot_mode": "top",
                "javascript_enabled": False,
                "ocr_extraction": True,
                "markdown_extraction": "basic"
            }
        },
        {
            "name": "Full Screenshots + OCR",
            "config": {
                "url": TEST_URL,
                "title": "Test Full Screenshots With OCR",
                "take_screenshot": True,
                "screenshot_mode": "full",
                "javascript_enabled": False,
                "ocr_extraction": True,
                "markdown_extraction": "basic"
            }
        }
    ]
    
    # Run tests
    for test_case in test_configs:
        make_crawl_request(test_case["name"], test_case["config"])
        time.sleep(2)  # Brief pause between tests
    
    print("\n🎉 All tests completed!")
    print("\n📝 What to look for in the server logs:")
    print("✅ No EasyOCR warnings for tests 1-2 (OCR disabled)")
    print("🔄 'Initializing OCR (lazy load)' message only appears for test 3")
    print("⚡ Subsequent OCR tests (test 4) should reuse existing OCR instance")
    print("📊 Response times should be faster for non-OCR tests")

if __name__ == "__main__":
    main()

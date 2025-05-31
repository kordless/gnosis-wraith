#!/usr/bin/env python3
"""
Advanced OCR Test with Multiple URLs
Tests OCR behavior with different types of content
"""

import requests
import json
import time
import argparse
from datetime import datetime

# Test URLs with different characteristics  
TEST_URLS = {
    "simple": "https://example.com",
    "text_heavy": "https://en.wikipedia.org/wiki/Optical_character_recognition", 
    "splunk": "https://www.splunk.com",
    "tableau": "https://www.tableau.com",
    "local_test": "http://httpbin.org/html"
}

def run_comprehensive_test(base_url="http://localhost:5000", target_url=None):
    """Run comprehensive OCR tests"""
    
    url = target_url or TEST_URLS["simple"]
    crawl_endpoint = f"{base_url}/api/crawl"
    
    print(f"🎯 Testing with URL: {url}")
    print(f"🔗 Endpoint: {crawl_endpoint}")
    
    # Test sequence designed to verify OCR lazy loading
    tests = [
        {
            "name": "🚫 Baseline: No OCR, No Screenshots",
            "config": {
                "url": url,
                "title": "Baseline Test",
                "take_screenshot": False,
                "ocr_extraction": False,
                "markdown_extraction": "basic"
            },
            "expect_ocr_init": False
        },
        {
            "name": "📸 Screenshots Only (OCR should NOT initialize)",
            "config": {
                "url": url,
                "title": "Screenshots Only Test", 
                "take_screenshot": True,
                "screenshot_mode": "top",
                "ocr_extraction": False,
                "markdown_extraction": "basic"
            },
            "expect_ocr_init": False
        },
        {
            "name": "🔍 FIRST OCR Test (should trigger lazy init)",
            "config": {
                "url": url,
                "title": "First OCR Test",
                "take_screenshot": True,
                "screenshot_mode": "top", 
                "ocr_extraction": True,
                "markdown_extraction": "basic"
            },
            "expect_ocr_init": True
        },
        {
            "name": "🔄 SECOND OCR Test (should reuse existing OCR)",
            "config": {
                "url": url,
                "title": "Second OCR Test",
                "take_screenshot": True,
                "screenshot_mode": "full",
                "ocr_extraction": True, 
                "markdown_extraction": "basic"
            },
            "expect_ocr_init": False  # Should reuse
        }
    ]
    
    print(f"\n📋 Running {len(tests)} test cases...")
    
    for i, test in enumerate(tests, 1):
        print(f"\n{'='*20} Test {i}/{len(tests)} {'='*20}")
        print(f"🧪 {test['name']}")
        
        if test['expect_ocr_init']:
            print("⚠️  Expected: OCR initialization should occur")
        else:
            print("✅ Expected: No OCR initialization")
            
        print(f"📤 Config: {json.dumps(test['config'], indent=2)}")
        
        start_time = time.time()
        
        try:
            response = requests.post(crawl_endpoint, json=test['config'], timeout=60)
            duration = time.time() - start_time
            
            print(f"⏱️  Duration: {duration:.2f}s")
            print(f"📊 HTTP Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("✅ Crawl Success")
                    if 'results' in result and result['results']:
                        first_result = result['results'][0]
                        has_screenshot = bool(first_result.get('screenshot'))
                        has_ocr_text = bool(first_result.get('extracted_text'))
                        
                        print(f"📸 Screenshot Generated: {'Yes' if has_screenshot else 'No'}")
                        print(f"🔍 OCR Text Extracted: {'Yes' if has_ocr_text else 'No'}")
                        
                        # Validate expectations
                        config = test['config']
                        if config.get('take_screenshot') and not has_screenshot:
                            print("⚠️  WARNING: Expected screenshot but none generated")
                        if config.get('ocr_extraction') and not has_ocr_text:
                            print("⚠️  WARNING: Expected OCR text but none extracted")
                        if not config.get('ocr_extraction') and has_ocr_text:
                            print("⚠️  WARNING: OCR text found but OCR was disabled")
                else:
                    print(f"❌ Crawl Failed: {result.get('error', 'Unknown error')}")
            else:
                print(f"❌ HTTP Error: {response.text}")
                
        except Exception as e:
            print(f"💥 Request Error: {str(e)}")
        
        # Pause between tests
        if i < len(tests):
            print("⏸️  Waiting 3 seconds before next test...")
            time.sleep(3)
    
    print(f"\n🎉 Test sequence completed!")
    print(f"\n📝 Check server logs for:")
    print("   • OCR initialization should only appear during test 3")
    print("   • No EasyOCR warnings during tests 1-2") 
    print("   • Test 4 should be faster (reusing existing OCR)")

def main():
    parser = argparse.ArgumentParser(description='Test OCR crawl functionality')
    parser.add_argument('--url', help='URL to test (default: example.com)')
    parser.add_argument('--server', default='http://localhost:5000', help='Server URL')
    parser.add_argument('--preset', choices=TEST_URLS.keys(), help='Use preset URL')
    parser.add_argument('--category', choices=list(TEST_COMPANY_URLS.keys()), help='Test URLs from specific category')
    parser.add_argument('--quick', choices=['quick_logging_test', 'visual_heavy_test', 'enterprise_dashboard_test'], help='Run quick test configuration')
    parser.add_argument('--limit', type=int, default=4, help='Maximum number of URLs to test')
    parser.add_argument('--list-categories', action='store_true', help='List available categories and exit')
    parser.add_argument('--list-quick', action='store_true', help='List quick test configs and exit')
    
    args = parser.parse_args()
    
    # Handle list commands
    if args.list_categories:
        print_test_categories()
        return
    
    if args.list_quick:
        print_simple_configs()
        return
    
    # Determine target URL
    if args.preset:
        target_url = TEST_URLS[args.preset]
        print(f"🎯 Using preset '{args.preset}': {target_url}")
    else:
        target_url = args.url
    
    print("🕷️  Gnosis Wraith Advanced OCR Test")
    print("=" * 60)
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Health check
    try:
        health_response = requests.get(f"{args.server}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Server health check passed")
        else:
            print(f"⚠️  Server health check returned {health_response.status_code}")
    except Exception as e:
        print(f"❌ Server health check failed: {e}")
        print("Make sure the Gnosis Wraith server is running!")
        return
    
    # Determine test mode
    if args.quick:
        # Quick test configuration
        urls = get_simple_test_config(args.quick)
        print(f"🚀 Running quick test: {args.quick}")
        print(f"📊 Testing {len(urls)} URLs")
        run_multi_url_test(args.server, urls)
    elif args.category:
        # Category-based test
        url_data = get_test_urls(args.category, limit=args.limit)
        urls = [item['url'] for item in url_data]
        print(f"📂 Running category test: {args.category}")
        print(f"📊 Testing {len(urls)} URLs from {args.category}")
        run_multi_url_test(args.server, urls)
    elif target_url:
        # Single URL test
        run_comprehensive_test(args.server, target_url)
    else:
        # Default: quick logging test
        urls = get_simple_test_config('quick_logging_test')
        print("🚀 Running default quick logging test")
        print(f"📊 Testing {len(urls)} URLs")
        run_multi_url_test(args.server, urls)

if __name__ == "__main__":
    main()

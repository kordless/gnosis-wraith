#!/usr/bin/env python3
"""
Test script for the new response_format parameter in Gnosis Wraith API
"""

import requests
import json
import time

def test_response_format(url="https://example.com", wraith_url="http://localhost:5678"):
    """Test all three response formats"""
    
    formats = ['full', 'content_only', 'minimal']
    
    for format_type in formats:
        print(f"\n🧪 Testing response_format='{format_type}'")
        print("-" * 50)
        
        payload = {
            'url': url,
            'response_format': format_type,
            'markdown_extraction': 'enhanced',
            'take_screenshot': False,
            'javascript_enabled': True,
            'timeout': 30
        }
        
        try:
            response = requests.post(
                f'{wraith_url}/api/crawl',
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"✅ Status: {response.status_code}")
                print(f"📊 Response keys: {list(result.keys())}")
                
                # Show response structure based on format
                if format_type == 'content_only':
                    print(f"🔍 Has markdown_content: {'markdown_content' in result}")
                    if 'markdown_content' in result:
                        content_length = len(result['markdown_content'])
                        print(f"📝 Content length: {content_length} characters")
                        print(f"📄 Preview: {result['markdown_content'][:100]}...")
                
                elif format_type == 'minimal':
                    print(f"🔍 Has results array: {'results' in result}")
                    if 'results' in result:
                        results_count = len(result['results'])
                        print(f"📊 Results count: {results_count}")
                        if results_count > 0:
                            first_result = result['results'][0]
                            print(f"🔑 First result keys: {list(first_result.keys())}")
                            if 'markdown_content' in first_result:
                                content_length = len(first_result['markdown_content'])
                                print(f"📝 Content length: {content_length} characters")
                
                elif format_type == 'full':
                    print(f"🔍 Has results array: {'results' in result}")
                    print(f"🔍 Has raw_crawl_data: {'raw_crawl_data' in result}")
                    print(f"🔍 Has report_path: {'report_path' in result}")
                    if 'results' in result:
                        results_count = len(result['results'])
                        print(f"📊 Results count: {results_count}")
                
                # Save response for inspection
                filename = f"test_response_{format_type}.json"
                with open(filename, 'w') as f:
                    json.dump(result, f, indent=2)
                print(f"💾 Saved response to: {filename}")
                
            else:
                print(f"❌ Status: {response.status_code}")
                print(f"❌ Error: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        
        # Rate limiting between tests
        time.sleep(2)

def test_backward_compatibility(url="https://example.com", wraith_url="http://localhost:5678"):
    """Test that old requests without response_format still work"""
    
    print(f"\n🔄 Testing backward compatibility (no response_format parameter)")
    print("-" * 50)
    
    payload = {
        'url': url,
        'markdown_extraction': 'enhanced',
        'take_screenshot': False,
        'javascript_enabled': True,
        'timeout': 30
        # No response_format parameter - should default to 'full'
    }
    
    try:
        response = requests.post(
            f'{wraith_url}/api/crawl',
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"📊 Response keys: {list(result.keys())}")
            print(f"🔍 Has results array: {'results' in result}")
            print(f"🔍 Has raw_crawl_data: {'raw_crawl_data' in result}")
            print("✅ Backward compatibility maintained!")
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

def main():
    print("🚀 Gnosis Wraith Response Format Testing")
    print("=" * 60)
    
    # Check if Wraith is running
    try:
        response = requests.get("http://localhost:5678/health", timeout=5)
        if response.status_code == 200:
            print("✅ Gnosis Wraith API is running")
        else:
            print("⚠️  Gnosis Wraith API responded but might have issues")
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to Gnosis Wraith API at http://localhost:5678")
        print("   Please make sure Gnosis Wraith is running first")
        return
    
    # Test all response formats
    test_response_format()
    
    # Test backward compatibility
    test_backward_compatibility()
    
    print(f"\n🎉 Testing complete!")
    print("Check the generated JSON files to see the different response structures.")

if __name__ == "__main__":
    main()

import requests
import json
import re

def crawl_with_wraith(url, server_url="http://localhost:5678"):
    """
    Simple example of calling the Wraith crawler API
    
    Args:
        url: The URL to crawl
        server_url: Wraith server URL (default: local server)
    
    Returns:
        dict: Crawl results containing markdown content and metadata
    """
    
    # Clean the server URL thoroughly - remove ALL whitespace including \r\n
    server_url = re.sub(r'\s+', '', server_url)
    server_url = server_url.rstrip('/')
    
    # Remove any accidental duplicate /crawl paths
    if server_url.endswith('/crawl'):
        server_url = server_url[:-6]
    
    # Construct clean endpoint
    endpoint = f"{server_url}/crawl"
    
    print(f"🔍 Clean server URL: {repr(server_url)}")
    print(f"🔍 Final endpoint: {repr(endpoint)}")
    print(f"🔍 Endpoint: {endpoint}")
    
    # Basic request payload
    payload = {
        "url": url,
        "take_screenshot": True,
        "javascript_enabled": False,
        "ocr_extraction": False,
        "markdown_extraction": "enhanced",
        "use_cache": True,
        "timeout": 30
    }
    
    try:
        # Make the API request
        response = requests.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"📡 Response status: {response.status_code}")
        
        # Check if request was successful
        response.raise_for_status()
        
        # Parse JSON response
        result = response.json()
        
        # Print JSON structure and keys
        print("\n" + "="*50)
        print("🔍 JSON RESPONSE ANALYSIS")
        print("="*50)
        
        if isinstance(result, dict):
            print(f"📋 Top-level keys: {list(result.keys())}")
            print(f"📊 Total keys: {len(result.keys())}")
            
            # Print each key with its type and preview (suppress verbose content)
            for key, value in result.items():
                value_type = type(value).__name__
                
                if key == "raw_crawl_data":
                    # Show structure but not content for raw_crawl_data
                    if isinstance(value, list) and len(value) > 0:
                        preview = f"({len(value)} items) - [CONTENT SUPPRESSED - see markdown below]"
                    else:
                        preview = f"({len(value)} items)" if hasattr(value, '__len__') else str(value)
                elif isinstance(value, str):
                    preview = f"'{value[:100]}...'" if len(value) > 100 else f"'{value}'"
                elif isinstance(value, (list, dict)):
                    preview = f"({len(value)} items)" if hasattr(value, '__len__') else str(value)
                else:
                    preview = str(value)
                
                print(f"  🔑 {key}: {value_type} = {preview}")
            
            # Print clean JSON (suppress html_content and filtered_content)
            print("\n" + "="*50)
            print("📄 CLEAN JSON RESPONSE (html/raw content suppressed)")
            print("="*50)
            
            # Create a copy of result with only the essential data
            filtered_result = result.copy()
            if "raw_crawl_data" in filtered_result:
                raw_data = filtered_result["raw_crawl_data"]
                if isinstance(raw_data, list) and len(raw_data) > 0:
                    # Keep only essential fields, suppress html_content and filtered_content
                    filtered_result["raw_crawl_data"] = [
                        {
                            "url": item.get("url", "N/A"),
                            "title": item.get("title", "N/A"),
                            "screenshot": item.get("screenshot", "N/A"),
                            "javascript_enabled": item.get("javascript_enabled", False),
                            "markdown_content": item.get("markdown_content", ""),
                            "fit_markdown_content": item.get("fit_markdown_content", ""),
                            "_html_length": len(item.get("html_content", "")),
                            "_filtered_content_length": len(item.get("filtered_content", "")),
                            "_note": "html_content and filtered_content suppressed"
                        }
                        for item in raw_data
                    ]
            
            print(json.dumps(filtered_result, indent=2, ensure_ascii=False))
            
        else:
            print(f"⚠️  Response is not a dict, it's a {type(result).__name__}: {result}")
        
        # Enhanced success checking for Wraith API format
        if result.get("success"):
            print(f"\n✅ Successfully crawled: {url}")
            
            # Extract data from raw_crawl_data (first item)
            raw_data = result.get("raw_crawl_data", [])
            if raw_data and len(raw_data) > 0:
                crawl_data = raw_data[0]
                title = crawl_data.get("title", "N/A")
                markdown = crawl_data.get("markdown_content", "")
                fit_markdown = crawl_data.get("fit_markdown_content", "")
                screenshot = crawl_data.get("screenshot", "")
                
                print(f"📄 Title: {title}")
                print(f"📊 Markdown content length: {len(markdown)} characters")
                print(f"📊 Fit markdown length: {len(fit_markdown)} characters")
                print(f"📸 Screenshot: {screenshot}")
                print(f"📁 JSON file: {result.get('json_path', 'N/A')}")
                print(f"📁 Report file: {result.get('report_path', 'N/A')}")
                print(f"🔗 URLs processed: {result.get('urls_processed', [])}")
                
                # Show enhanced markdown content (prefer fit_markdown_content if available)
                display_markdown = fit_markdown if fit_markdown else markdown
                if display_markdown:
                    print(f"\n📝 Enhanced Markdown Content:")
                    print("=" * 60)
                    print(display_markdown)
                    print("=" * 60)
                
            else:
                print("⚠️  No raw_crawl_data found in response")
                
            return result
        else:
            print(f"\n❌ Crawl failed: {result.get('error', 'Unknown error')}")
            return result  # Return the result anyway so we can see what's in it
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
        print(f"❌ Full URL that failed: {repr(endpoint)}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse response: {e}")
        print(f"❌ Raw response text: {response.text}")
        return None

# Test with different server configurations
if __name__ == "__main__":
    # Test 1: Remote server (skip local since it's returning 405)
    print("=== Testing Remote Wraith Server ===")
    result = crawl_with_wraith("https://example.com", "https://wraith.nuts.services/api")
    
    if result:
        print("\n" + "="*70)
        print("🎯 TESTING WITH A MORE COMPLEX SITE")
        print("="*70)
        # Test with a more complex site
        result2 = crawl_with_wraith("https://httpbin.org/html", "https://wraith.nuts.services/api")

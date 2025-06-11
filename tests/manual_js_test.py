#!/usr/bin/env python3
"""
Manual test script for JavaScript execution - interactive testing
"""

import requests
import json

def test_execute():
    """Manually test the execute endpoint"""
    
    print("\n🧪 Manual JavaScript Execution Test")
    print("=" * 50)
    
    # Test server
    base_url = input("Enter server URL (default: http://localhost:5678): ").strip()
    if not base_url:
        base_url = "http://localhost:5678"
    
    # Test authentication
    api_token = input("Enter API token (or press Enter to skip): ").strip()
    headers = {}
    if api_token:
        headers['Authorization'] = f'Bearer {api_token}'
    
    # Test URL
    test_url = input("Enter URL to test (default: https://example.com): ").strip()
    if not test_url:
        test_url = "https://example.com"
    
    # Example JavaScript snippets
    examples = {
        "1": {
            "name": "Get page title",
            "code": "return document.title;"
        },
        "2": {
            "name": "Count links",
            "code": "return document.querySelectorAll('a').length;"
        },
        "3": {
            "name": "Extract all links",
            "code": """
const links = Array.from(document.querySelectorAll('a'));
return links.map(link => ({
    text: link.textContent.trim(),
    href: link.href
}));"""
        },
        "4": {
            "name": "Get all headings",
            "code": """
const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'));
return headings.map(h => ({
    level: h.tagName,
    text: h.textContent.trim()
}));"""
        },
        "5": {
            "name": "Custom JavaScript",
            "code": None
        }
    }
    
    print("\nSelect JavaScript to execute:")
    for key, example in examples.items():
        print(f"  {key}. {example['name']}")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice not in examples:
        print("Invalid choice!")
        return
    
    if choice == "5":
        print("\nEnter your JavaScript code (press Enter twice to finish):")
        lines = []
        while True:
            line = input()
            if line == "":
                if lines and lines[-1] == "":
                    break
            lines.append(line)
        javascript = "\n".join(lines[:-1])  # Remove last empty line
    else:
        javascript = examples[choice]['code']
    
    print(f"\n📝 Executing JavaScript on {test_url}...")
    print("JavaScript code:")
    print("-" * 40)
    print(javascript)
    print("-" * 40)
    
    # Test validation first
    print("\n🔍 Validating JavaScript...")
    try:
        response = requests.post(
            f"{base_url}/api/v2/validate",
            json={"javascript": javascript},
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('is_safe'):
                print("✅ JavaScript is safe to execute")
            else:
                print("⚠️  JavaScript validation warnings:")
                for violation in result.get('violations', []):
                    print(f"   - {violation}")
                
                proceed = input("\nProceed anyway? (y/N): ").strip().lower()
                if proceed != 'y':
                    return
        else:
            print(f"❌ Validation failed: {response.status_code}")
            print(response.text)
            return
    except Exception as e:
        print(f"❌ Error validating: {str(e)}")
        return
    
    # Execute JavaScript
    print("\n🚀 Executing JavaScript...")
    try:
        response = requests.post(
            f"{base_url}/api/v2/execute",
            json={
                "url": test_url,
                "javascript": javascript,
                "options": {
                    "wait_before": 2000,
                    "wait_after": 1000,
                    "timeout": 30000
                }
            },
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Execution successful!")
                print("\n📊 Result:")
                print(json.dumps(result.get('result'), indent=2))
            else:
                print(f"❌ Execution failed: {result.get('error')}")
        else:
            print(f"❌ HTTP {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error executing: {str(e)}")

def test_inject():
    """Test LLM-powered JavaScript injection"""
    
    print("\n🤖 Testing LLM JavaScript Generation")
    print("=" * 50)
    
    # Check for API key
    import os
    llm_token = os.getenv('ANTHROPIC_API_KEY')
    if not llm_token:
        llm_token = input("Enter Anthropic API key: ").strip()
        if not llm_token:
            print("❌ LLM token required for this test")
            return
    
    base_url = input("Enter server URL (default: http://localhost:5678): ").strip()
    if not base_url:
        base_url = "http://localhost:5678"
    
    api_token = input("Enter API token (or press Enter to skip): ").strip()
    headers = {}
    if api_token:
        headers['Authorization'] = f'Bearer {api_token}'
    
    test_url = input("Enter URL to test (default: https://example.com): ").strip()
    if not test_url:
        test_url = "https://example.com"
    
    print("\nDescribe what you want the JavaScript to do:")
    request_text = input("> ").strip()
    
    if not request_text:
        print("❌ Request description required")
        return
    
    print(f"\n🤖 Generating JavaScript for: {request_text}")
    
    try:
        response = requests.post(
            f"{base_url}/api/v2/inject",
            json={
                "url": test_url,
                "request": request_text,
                "llm_provider": "anthropic",
                "llm_token": llm_token,
                "execute_immediately": True,
                "return_code": True
            },
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Generation successful!")
                
                if result.get('code'):
                    print("\n📝 Generated JavaScript:")
                    print("-" * 40)
                    print(result['code'])
                    print("-" * 40)
                
                if result.get('execution', {}).get('success'):
                    print("\n✅ Execution successful!")
                    print("\n📊 Result:")
                    print(json.dumps(result['execution']['result'], indent=2))
                else:
                    print(f"\n❌ Execution failed: {result.get('execution', {}).get('error')}")
            else:
                print(f"❌ Generation failed: {result.get('error')}")
        else:
            print(f"❌ HTTP {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def main():
    """Main menu"""
    while True:
        print("\n🧪 Gnosis Wraith JavaScript Testing")
        print("=" * 40)
        print("1. Test direct JavaScript execution")
        print("2. Test LLM-powered JavaScript generation")
        print("3. Exit")
        
        choice = input("\nSelect option: ").strip()
        
        if choice == "1":
            test_execute()
        elif choice == "2":
            test_inject()
        elif choice == "3":
            print("👋 Goodbye!")
            break
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    main()
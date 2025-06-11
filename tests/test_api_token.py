#!/usr/bin/env python3
"""
Test script for Gnosis Wraith API token authentication

This script demonstrates how to use API tokens with the Gnosis Wraith API.

Usage:
    python test_api_token.py YOUR_API_TOKEN [base_url]

Example:
    python test_api_token.py abc123def456 http://localhost:5678
"""

import sys
import json
import requests
from typing import Dict, Any


def test_token_info(api_token: str, base_url: str) -> Dict[str, Any]:
    """Test the token info endpoint"""
    print("\n1. Testing Token Info Endpoint...")
    
    response = requests.get(
        f"{base_url}/auth/api/token/info",
        headers={"Authorization": f"Bearer {api_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Token is valid for user: {data['user']['email']}")
        print(f"  Account type: {data['user']['account_type']}")
        print(f"  Auth method: {data['auth_method']}")
        return data
    else:
        print(f"✗ Token validation failed: {response.status_code}")
        print(f"  Response: {response.text}")
        return None


def test_v2_markdown(api_token: str, base_url: str, test_url: str) -> bool:
    """Test the v2 markdown endpoint"""
    print("\n2. Testing v2 Markdown Extraction...")
    
    response = requests.post(
        f"{base_url}/api/v2/md",
        headers={
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        },
        json={"url": test_url}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Successfully extracted markdown from {test_url}")
        print(f"  Word count: {data['stats']['word_count']}")
        print(f"  First 100 chars: {data['markdown'][:100]}...")
        return True
    else:
        print(f"✗ Markdown extraction failed: {response.status_code}")
        print(f"  Response: {response.text}")
        return False


def test_v1_crawl(api_token: str, base_url: str, test_url: str) -> bool:
    """Test the v1 crawl endpoint with token in body"""
    print("\n3. Testing v1 Crawl with Token in Body...")
    
    response = requests.post(
        f"{base_url}/api/crawl",
        headers={"Content-Type": "application/json"},
        json={
            "url": test_url,
            "api_token": api_token,
            "response_format": "minimal",
            "take_screenshot": False,
            "markdown_extraction": "basic"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Successfully crawled {test_url}")
        if data.get('results') and len(data['results']) > 0:
            result = data['results'][0]
            print(f"  Title: {result.get('title', 'N/A')}")
            print(f"  Success: {result.get('success', False)}")
        return True
    else:
        print(f"✗ Crawl failed: {response.status_code}")
        print(f"  Response: {response.text}")
        return False


def test_alternative_headers(api_token: str, base_url: str, test_url: str) -> bool:
    """Test alternative authentication methods"""
    print("\n4. Testing Alternative Auth Methods...")
    
    # Test X-API-Token header
    print("   Testing X-API-Token header...")
    response = requests.post(
        f"{base_url}/api/v2/md",
        headers={
            "X-API-Token": api_token,
            "Content-Type": "application/json"
        },
        json={"url": test_url}
    )
    
    if response.status_code == 200:
        print("   ✓ X-API-Token header works")
    else:
        print(f"   ✗ X-API-Token header failed: {response.status_code}")
    
    return response.status_code == 200


def main():
    """Main test function"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    api_token = sys.argv[1]
    base_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:5678"
    test_url = "https://example.com"
    
    print(f"Testing Gnosis Wraith API Token Authentication")
    print(f"Base URL: {base_url}")
    print(f"Test URL: {test_url}")
    print(f"Token: {api_token[:8]}..." if len(api_token) > 8 else "Token: [SHORT]")
    
    # Run tests
    token_info = test_token_info(api_token, base_url)
    if not token_info:
        print("\n❌ Token validation failed. Please check your token.")
        sys.exit(1)
    
    v2_success = test_v2_markdown(api_token, base_url, test_url)
    v1_success = test_v1_crawl(api_token, base_url, test_url)
    alt_success = test_alternative_headers(api_token, base_url, test_url)
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    print(f"Token Info:    {'✓ PASS' if token_info else '✗ FAIL'}")
    print(f"v2 Markdown:   {'✓ PASS' if v2_success else '✗ FAIL'}")
    print(f"v1 Crawl:      {'✓ PASS' if v1_success else '✗ FAIL'}")
    print(f"Alt Headers:   {'✓ PASS' if alt_success else '✗ FAIL'}")
    
    if all([token_info, v2_success, v1_success, alt_success]):
        print("\n✅ All tests passed! API token authentication is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()

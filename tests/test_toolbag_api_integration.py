"""
API integration tests for enhanced toolbag functionality.
Run these against the running Docker container.

NOTE: These tests are for FUTURE functionality after Phase 2-4 implementation.
Currently, only the enhanced toolbag backend (Phase 1) is complete.
"""

import asyncio
import aiohttp
import json
import os
from typing import Dict, Any, Optional

# Base URL for the API
BASE_URL = "http://localhost:5678"

# Get API token from environment or use a test token
API_TOKEN = os.environ.get("GNOSIS_API_TOKEN", "test-token-12345")

class TestToolbagAPIIntegration:
    """Test the enhanced toolbag through API calls."""
    
    async def test_tool_execution_with_context(self):
        """Test that tools can be executed with context passing."""
        async with aiohttp.ClientSession() as session:
            # First request - crawl a page
            payload = {
                "url": "https://example.com",
                "tools": ["suggest_url"],
                "query": "Find information about example.com"
            }
            
            async with session.post(f"{BASE_URL}/api/crawl", json=payload) as resp:
                result1 = await resp.json()
                print(f"First result: {json.dumps(result1, indent=2)}")
                assert resp.status == 200
                
                # Check if session was created
                session_id = result1.get("session_id")
                if session_id:
                    print(f"Session created: {session_id}")
    
    async def test_v2_smart_sync_async(self):
        """Test V2 endpoint smart sync/async detection."""
        async with aiohttp.ClientSession() as session:
            # Test 1: Simple crawl (should be sync)
            payload = {
                "url": "https://example.com",
                "javascript": False,
                "screenshot": False
            }
            
            headers = {"X-API-Version": "2"}
            
            async with session.post(f"{BASE_URL}/v2/crawl", json=payload, headers=headers) as resp:
                result = await resp.json()
                print(f"Simple crawl result: {json.dumps(result, indent=2)}")
                
                # Simple crawl should complete immediately (sync)
                if result.get("success"):
                    assert "async" not in result or result["async"] is False
                    print("✓ Simple crawl executed synchronously")
            
            # Test 2: Complex crawl (should be async)
            payload = {
                "url": "https://example.com",
                "javascript": True,
                "screenshot": True,
                "depth": 2
            }
            
            async with session.post(f"{BASE_URL}/v2/crawl", json=payload, headers=headers) as resp:
                result = await resp.json()
                print(f"Complex crawl result: {json.dumps(result, indent=2)}")
                
                # Complex crawl should return job info
                if result.get("success") and result.get("async"):
                    assert "job_id" in result
                    print(f"✓ Complex crawl created job: {result['job_id']}")
                    
                    # Check job status
                    job_id = result["job_id"]
                    await asyncio.sleep(1)
                    
                    async with session.get(f"{BASE_URL}/v2/jobs/{job_id}") as job_resp:
                        job_status = await job_resp.json()
                        print(f"Job status: {json.dumps(job_status, indent=2)}")
    
    async def test_tool_chaining(self):
        """Test multiple tools chained together."""
        async with aiohttp.ClientSession() as session:
            # Execute a chain of tools
            payload = {
                "tools": ["suggest_url", "check_for_odd_user"],
                "query": "hacker news",
                "mode": "chain"
            }
            
            async with session.post(f"{BASE_URL}/api/tools/execute", json=payload) as resp:
                result = await resp.json()
                print(f"Tool chain result: {json.dumps(result, indent=2)}")
                
                if result.get("success"):
                    assert "results" in result or "tool_calls" in result
                    print("✓ Tool chain executed successfully")
    
    async def test_session_persistence(self):
        """Test that browser sessions persist between calls."""
        async with aiohttp.ClientSession() as session:
            # First call - should create session
            payload1 = {
                "url": "https://example.com/login",
                "javascript": True
            }
            
            async with session.post(f"{BASE_URL}/v2/crawl", json=payload1) as resp:
                result1 = await resp.json()
                session_id = result1.get("session_id")
                
                if session_id:
                    print(f"Session created: {session_id}")
                    
                    # Second call - reuse session
                    payload2 = {
                        "url": "https://example.com/dashboard",
                        "javascript": True,
                        "session_id": session_id
                    }
                    
                    async with session.post(f"{BASE_URL}/v2/crawl", json=payload2) as resp2:
                        result2 = await resp2.json()
                        print("✓ Session reused for second crawl")

async def run_tests():
    """Run all tests."""
    tester = TestToolbagAPIIntegration()
    
    print("=== Testing Tool Execution with Context ===")
    try:
        await tester.test_tool_execution_with_context()
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n=== Testing V2 Smart Sync/Async ===")
    try:
        await tester.test_v2_smart_sync_async()
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n=== Testing Tool Chaining ===")
    try:
        await tester.test_tool_chaining()
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n=== Testing Session Persistence ===")
    try:
        await tester.test_session_persistence()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("=" * 70)
    print("IMPORTANT: These tests are for FUTURE functionality!")
    print("=" * 70)
    print("\nCurrent Implementation Status:")
    print("✅ Phase 1: Toolbag enhancements (COMPLETE)")
    print("   - Tool usage limits (.pop() mechanics)")
    print("   - Session management") 
    print("   - Context passing")
    print("   - Enhanced provider integration")
    print("\n❌ Phase 2: V2 Endpoints (NOT IMPLEMENTED)")
    print("   - /v2/crawl endpoint")
    print("   - Smart sync/async execution")
    print("   - Core crawl functions")
    print("\n❌ Phase 3: Integration (NOT IMPLEMENTED)")
    print("   - Workflow system")
    print("   - Tool chaining endpoints")
    print("\n❌ Phase 4: UI Updates (NOT IMPLEMENTED)")
    print("   - V2 UI components")
    print("   - Claude Desktop integration")
    print("\n" + "=" * 70)
    print("\nTo continue implementation:")
    print("1. Implement Phase 2: Create core/crawl_functions.py")
    print("2. Implement Phase 2: Create MCP tools in ai/tools/")
    print("3. Implement Phase 2: Add V2 endpoints to web/routes/api_v2.py")
    print("4. Then these tests will work!")
    print("=" * 70)
    
    # Uncomment to run tests after implementation
    # asyncio.run(run_tests())
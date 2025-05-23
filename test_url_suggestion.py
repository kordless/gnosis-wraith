#!/usr/bin/env python3
"""
Test script to verify the URL suggestion toolbag integration works correctly.
"""

import asyncio
import os
import sys
import json
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_toolbag_integration():
    """Test the toolbag integration with URL suggestion tools."""
    try:
        # Import the toolbag
        from ai.toolbag import toolbag
        
        print("=== Testing URL Suggestion Toolbag Integration ===\n")
        
        # Test 1: Simple query
        print("Test 1: Simple URL suggestion")
        result1 = await toolbag.execute(
            tools=['suggest_url'],
            query='I want to learn about Python programming',
            provider='anthropic'
        )
        print(f"Result 1: {json.dumps(result1, indent=2)}")
        print()
        
        # Test 2: Direct URL
        print("Test 2: Direct URL validation")
        result2 = await toolbag.execute(
            tools=['suggest_url'],
            query='https://docs.python.org',
            provider='anthropic'
        )
        print(f"Result 2: {json.dumps(result2, indent=2)}")
        print()
        
        # Test 3: Check decorator registration
        print("Test 3: Check tool registration")
        from ai.tools.decorators import get_all_tools
        tools = get_all_tools()
        print(f"Registered tools: {list(tools.keys())}")
        
        if 'suggest_url' in tools:
            print("✓ suggest_url tool is registered")
        else:
            print("✗ suggest_url tool is NOT registered")
        
        print()
        
        # Test 4: Direct tool execution
        print("Test 4: Direct tool execution")
        from ai.tools.decorators import execute_tool
        result4 = await execute_tool('suggest_url', query='machine learning news')
        print(f"Direct execution result: {json.dumps(result4, indent=2)}")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Set a dummy API key for testing (the direct tool execution won't need it)
    if not os.environ.get('ANTHROPIC_API_KEY'):
        os.environ['ANTHROPIC_API_KEY'] = 'test-key-for-direct-execution'
    
    asyncio.run(test_toolbag_integration())

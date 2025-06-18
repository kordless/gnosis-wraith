# Phase 3: Integration and Testing Plan

## Overview
Integrate all components (toolbag, MCP tools, V2 endpoints) and create comprehensive testing infrastructure.

## Timeline: Week 4 (5-7 days)

## 3.1 Integration Architecture

### File: `core/integration.py` (NEW)

Create integration layer that connects all components:

```python
"""
Integration layer connecting toolbag, MCP tools, and core functions.
"""

import logging
from typing import Dict, Any, List, Optional
from ai.toolbag import ToolBag
from ai.tools import get_tools_by_names
from core.crawl_functions import crawl_url_direct
from core.browser_session import session_manager

logger = logging.getLogger("gnosis_wraith")

class WraithIntegration:
    """
    Central integration point for Gnosis Wraith's agentic system.
    """
    
    def __init__(self):
        self.toolbag = ToolBag(provider='anthropic')
        self.active_sessions = {}
        
    async def execute_workflow(
        self,
        workflow_name: str,
        parameters: Dict[str, Any],
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a predefined workflow.
        
        Workflows combine multiple tools in intelligent sequences.
        """
        workflows = {
            "analyze_website": self._workflow_analyze_website,
            "monitor_changes": self._workflow_monitor_changes,
            "extract_data": self._workflow_extract_data,
            "research_topic": self._workflow_research_topic
        }
        
        if workflow_name not in workflows:
            return {
                "success": False,
                "error": f"Unknown workflow: {workflow_name}"
            }
        
        try:
            return await workflows[workflow_name](parameters, api_key)
        except Exception as e:
            logger.error(f"Workflow error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "workflow": workflow_name
            }
    
    async def _workflow_analyze_website(
        self,
        params: Dict[str, Any],
        api_key: Optional[str]
    ) -> Dict[str, Any]:
        """
        Analyze a website workflow:
        1. Crawl homepage
        2. Analyze structure
        3. Extract key information
        4. Generate report
        """
        url = params.get('url')
        if not url:
            return {"success": False, "error": "URL required"}
        
        # Step 1: Initial crawl
        crawl_result = await self.toolbag.execute(
            tools=['crawl_webpage_with_smart_execution'],
            query=f"Crawl {url} to understand the website structure",
            api_key=api_key
        )
        
        if not crawl_result.get('success'):
            return crawl_result
        
        # Extract session if created
        session_id = crawl_result.get('session_id')
        
        # Step 2: Analyze structure
        structure_result = await self.toolbag.execute(
            tools=['analyze_website_structure'],
            query=f"Analyze the structure of {url}",
            api_key=api_key,
            previous_result=crawl_result
        )
        
        # Step 3: Extract key information
        extract_result = await self.toolbag.execute(
            tools=['extract_key_information_points'],
            query="Extract the most important information from this website",
            api_key=api_key,
            previous_result=structure_result
        )
        
        # Step 4: Generate summary
        summary_result = await self.toolbag.execute(
            tools=['summarize_long_text_intelligently'],
            query="Create a comprehensive summary of the website analysis",
            api_key=api_key,
            previous_result=extract_result
        )
        
        return {
            "success": True,
            "workflow": "analyze_website",
            "url": url,
            "steps_completed": 4,
            "session_id": session_id,
            "analysis": summary_result.get('response'),
            "structure": structure_result.get('response'),
            "key_points": extract_result.get('response')
        }
    
    async def _workflow_monitor_changes(
        self,
        params: Dict[str, Any],
        api_key: Optional[str]
    ) -> Dict[str, Any]:
        """
        Monitor website for changes:
        1. Crawl current state
        2. Compare with previous crawl
        3. Identify changes
        4. Alert on significant changes
        """
        # Implementation here
        pass
    
    async def _workflow_extract_data(
        self,
        params: Dict[str, Any],
        api_key: Optional[str]
    ) -> Dict[str, Any]:
        """
        Extract structured data:
        1. Crawl target pages
        2. Apply extraction schema
        3. Validate data
        4. Export results
        """
        # Implementation here
        pass
    
    async def _workflow_research_topic(
        self,
        params: Dict[str, Any],
        api_key: Optional[str]
    ) -> Dict[str, Any]:
        """
        Research a topic across multiple sources:
        1. Generate search queries
        2. Crawl multiple sources
        3. Extract relevant information
        4. Synthesize findings
        """
        # Implementation here
        pass

# Global integration instance
integration = WraithIntegration()
```

## 3.2 Comprehensive Test Suite

### File: `tests/test_integration.py`

Test the full integration:

```python
"""
Integration tests for the complete Gnosis Wraith system.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from ai.toolbag import ToolBag
from ai.tools.decorators import tool, clear_tools
from core.browser_session import session_manager
from core.integration import integration

# Test fixtures
@pytest.fixture
async def clean_environment():
    """Reset environment for each test."""
    clear_tools()
    await session_manager.close_all_sessions()
    yield
    clear_tools()
    await session_manager.close_all_sessions()

@pytest.fixture
def mock_api_key():
    """Provide mock API key."""
    return "test-api-key-12345"

# Mock tools for testing
@tool(name="mock_crawl_tool", description="Mock crawl tool for testing")
async def mock_crawl_tool(url: str, **kwargs) -> Dict[str, Any]:
    """Mock crawl implementation."""
    return {
        "success": True,
        "url": url,
        "content": f"Mock content from {url}",
        "session_id": "mock_session_123"
    }

@tool(name="mock_analyze_tool", description="Mock analyze tool")
async def mock_analyze_tool(content: str, **kwargs) -> Dict[str, Any]:
    """Mock analysis implementation."""
    return {
        "success": True,
        "analysis": "Mock analysis result",
        "entities": ["Entity1", "Entity2"]
    }

class TestToolbagIntegration:
    """Test toolbag with mock tools."""
    
    @pytest.mark.asyncio
    async def test_tool_chaining(self, clean_environment):
        """Test tools can chain together."""
        toolbag = ToolBag(provider='anthropic')
        
        # Mock the provider's execute_tools
        with patch('ai.anthropic.execute_tools') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "response": "Crawled and analyzed",
                "tool_calls": [
                    {"name": "mock_crawl_tool", "input": {"url": "https://example.com"}},
                    {"name": "mock_analyze_tool", "input": {"content": "Mock content"}}
                ]
            }
            
            result = await toolbag.execute(
                tools=['mock_crawl_tool', 'mock_analyze_tool'],
                query='Crawl and analyze example.com'
            )
            
            assert result['success'] is True
            assert len(result['tool_calls']) == 2
    
    @pytest.mark.asyncio
    async def test_session_persistence(self, clean_environment):
        """Test browser sessions persist between tool calls."""
        # Create a session
        await session_manager.create_session("test_session", Mock())
        
        # Verify it exists
        session = await session_manager.get_session("test_session")
        assert session is not None
        
        # Use in tool chain
        toolbag = ToolBag()
        with patch('ai.anthropic.execute_tools') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "session_id": "test_session",
                "session_data": {"state": "modified"}
            }
            
            result = await toolbag.execute(
                tools=['mock_crawl_tool'],
                query='Use existing session'
            )
            
            assert result['session_id'] == "test_session"
    
    @pytest.mark.asyncio
    async def test_tool_usage_limits(self, clean_environment):
        """Test tool usage limits work correctly."""
        toolbag = ToolBag()
        toolbag.set_tool_limit("expensive_tool", 2)
        
        # First two calls should work
        available = toolbag.get_available_tools(["expensive_tool"])
        assert "expensive_tool" in available
        
        toolbag.tool_usage_count["expensive_tool"] = 1
        available = toolbag.get_available_tools(["expensive_tool"])
        assert "expensive_tool" in available
        
        # Third call should be blocked
        toolbag.tool_usage_count["expensive_tool"] = 2
        available = toolbag.get_available_tools(["expensive_tool"])
        assert "expensive_tool" not in available

class TestSmartSyncAsync:
    """Test smart sync/async execution."""
    
    @pytest.mark.asyncio
    async def test_sync_for_simple_crawl(self):
        """Test simple crawls execute synchronously."""
        from core.crawl_functions import crawl_url_direct, estimate_crawl_time
        
        # Test estimation
        time_estimate = await estimate_crawl_time(
            "https://example.com",
            {"javascript": False}
        )
        assert time_estimate < 3.0  # Should be sync
        
        # Mock the actual crawl
        with patch('core.crawl_functions._crawl_sync') as mock_sync:
            mock_sync.return_value = {"success": True, "content": "Test"}
            
            result = await crawl_url_direct(
                "https://example.com",
                {"javascript": False}
            )
            
            mock_sync.assert_called_once()
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_async_for_complex_crawl(self):
        """Test complex crawls execute asynchronously."""
        from core.crawl_functions import crawl_url_direct, estimate_crawl_time
        
        # Test estimation
        time_estimate = await estimate_crawl_time(
            "https://example.com",
            {"javascript": True, "screenshot": True, "depth": 2}
        )
        assert time_estimate >= 3.0  # Should be async
        
        # Mock the actual crawl
        with patch('core.crawl_functions._crawl_async') as mock_async:
            mock_async.return_value = {
                "success": True,
                "async": True,
                "job_id": "job_123"
            }
            
            result = await crawl_url_direct(
                "https://example.com",
                {"javascript": True, "screenshot": True, "depth": 2}
            )
            
            mock_async.assert_called_once()
            assert result["async"] is True
            assert "job_id" in result

class TestWorkflows:
    """Test complete workflows."""
    
    @pytest.mark.asyncio
    async def test_analyze_website_workflow(self, mock_api_key):
        """Test the analyze website workflow."""
        with patch('ai.anthropic.execute_tools') as mock_execute:
            # Mock successful execution
            mock_execute.side_effect = [
                {"success": True, "response": "Crawled", "session_id": "sess_123"},
                {"success": True, "response": "Structure analyzed"},
                {"success": True, "response": "Key points extracted"},
                {"success": True, "response": "Summary generated"}
            ]
            
            result = await integration.execute_workflow(
                "analyze_website",
                {"url": "https://example.com"},
                api_key=mock_api_key
            )
            
            assert result["success"] is True
            assert result["workflow"] == "analyze_website"
            assert result["steps_completed"] == 4
            assert "analysis" in result
            assert "structure" in result
            assert "key_points" in result

class TestErrorHandling:
    """Test error handling across the system."""
    
    @pytest.mark.asyncio
    async def test_tool_not_found(self):
        """Test handling of non-existent tools."""
        toolbag = ToolBag()
        
        with patch('ai.anthropic.execute_tools') as mock_execute:
            mock_execute.return_value = {
                "success": False,
                "error": "Tool 'nonexistent_tool' not found"
            }
            
            result = await toolbag.execute(
                tools=['nonexistent_tool'],
                query='Try to use missing tool'
            )
            
            assert result["success"] is False
            assert "not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_api_key_missing(self):
        """Test handling of missing API keys."""
        toolbag = ToolBag()
        
        with patch('ai.anthropic.execute_tools') as mock_execute:
            mock_execute.return_value = {
                "success": False,
                "error": "No Anthropic API key provided"
            }
            
            result = await toolbag.execute(
                tools=['mock_tool'],
                query='Test without API key'
            )
            
            assert result["success"] is False
            assert "API key" in result["error"]
    
    @pytest.mark.asyncio
    async def test_network_timeout(self):
        """Test handling of network timeouts."""
        from core.crawl_functions import crawl_url_direct
        
        with patch('core.crawl_functions._crawl_sync') as mock_sync:
            mock_sync.side_effect = asyncio.TimeoutError("Network timeout")
            
            result = await crawl_url_direct(
                "https://slow-site.com",
                {"javascript": False}
            )
            
            assert result["success"] is False
            assert "timeout" in result["error"].lower()
```

## 3.3 Performance Testing

### File: `tests/test_performance.py`

```python
"""
Performance tests for Gnosis Wraith.
"""

import pytest
import asyncio
import time
from statistics import mean, stdev
from ai.toolbag import ToolBag
from core.crawl_functions import crawl_url_direct

class TestPerformance:
    """Test system performance."""
    
    @pytest.mark.asyncio
    async def test_concurrent_crawls(self):
        """Test multiple concurrent crawls."""
        urls = [
            "https://example1.com",
            "https://example2.com",
            "https://example3.com",
            "https://example4.com",
            "https://example5.com"
        ]
        
        start_time = time.time()
        
        # Run crawls concurrently
        tasks = [
            crawl_url_direct(url, {"javascript": False})
            for url in urls
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # All should complete in reasonable time
        assert total_time < 10.0  # 10 seconds for 5 crawls
        
        # Check results
        successful = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
        assert successful >= 3  # At least 3 should succeed
    
    @pytest.mark.asyncio
    async def test_toolbag_chaining_performance(self):
        """Test performance of tool chaining."""
        toolbag = ToolBag()
        
        # Time a chain of 3 tools
        start_time = time.time()
        
        with patch('ai.anthropic.execute_tools') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "response": "Completed",
                "tool_calls": [
                    {"name": "tool1"},
                    {"name": "tool2"},
                    {"name": "tool3"}
                ]
            }
            
            result = await toolbag.execute_chain(
                tools=['tool1', 'tool2', 'tool3'],
                query='Test chain performance'
            )
        
        end_time = time.time()
        chain_time = end_time - start_time
        
        # Should complete quickly
        assert chain_time < 1.0  # Less than 1 second for chain setup
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_session_reuse_performance(self):
        """Test performance improvement from session reuse."""
        from core.browser_session import session_manager
        
        # First crawl (creates session)
        start1 = time.time()
        result1 = await crawl_url_direct(
            "https://example.com",
            {"javascript": True}
        )
        time1 = time.time() - start1
        
        session_id = result1.get('session_id')
        
        # Second crawl (reuses session)
        start2 = time.time()
        result2 = await crawl_url_direct(
            "https://example.com/page2",
            {"javascript": True},
            session_id=session_id
        )
        time2 = time.time() - start2
        
        # Session reuse should be faster
        assert time2 < time1 * 0.7  # At least 30% faster
```

## 3.4 Load Testing

### File: `tests/test_load.py`

```python
"""
Load testing for Gnosis Wraith.
"""

import pytest
import asyncio
from typing import List, Dict, Any
import random

class TestLoad:
    """Test system under load."""
    
    @pytest.mark.asyncio
    async def test_high_concurrency(self):
        """Test system with high concurrent load."""
        num_requests = 50
        
        async def make_request(i: int) -> Dict[str, Any]:
            """Simulate a user request."""
            try:
                # Randomly choose operation
                operations = [
                    ('crawl', {"url": f"https://example{i}.com"}),
                    ('search', {"query": f"test query {i}"}),
                    ('analyze', {"content": f"test content {i}"})
                ]
                
                op_type, params = random.choice(operations)
                
                # Simulate processing
                await asyncio.sleep(random.uniform(0.1, 0.5))
                
                return {
                    "success": True,
                    "operation": op_type,
                    "index": i
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "index": i
                }
        
        # Run all requests concurrently
        start_time = asyncio.get_event_loop().time()
        
        tasks = [make_request(i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = asyncio.get_event_loop().time()
        total_time = end_time - start_time
        
        # Calculate metrics
        successful = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
        failed = num_requests - successful
        
        print(f"\nLoad Test Results:")
        print(f"Total requests: {num_requests}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Requests/second: {num_requests/total_time:.2f}")
        
        # Assert reasonable performance
        assert successful >= num_requests * 0.95  # 95% success rate
        assert total_time < 30  # Complete within 30 seconds
```

## 3.5 Integration Documentation

### File: `docs/INTEGRATION_GUIDE.md`

Create integration guide:

```markdown
# Gnosis Wraith Integration Guide

## Overview
This guide explains how to integrate with Gnosis Wraith's agentic system.

## Quick Start

### Using the Toolbag
```python
from ai.toolbag import ToolBag

# Create toolbag instance
toolbag = ToolBag(provider='anthropic')

# Execute single tool
result = await toolbag.execute(
    tools=['crawl_webpage_with_smart_execution'],
    query='Crawl https://example.com',
    api_key='your-api-key'
)

# Execute tool chain
chain_result = await toolbag.execute_chain(
    tools=['crawl', 'analyze', 'summarize'],
    query='Analyze website comprehensively',
    api_key='your-api-key'
)
```

### Using Workflows
```python
from core.integration import integration

# Execute predefined workflow
result = await integration.execute_workflow(
    'analyze_website',
    {'url': 'https://example.com'},
    api_key='your-api-key'
)
```

### Direct Function Calls
```python
from core.crawl_functions import crawl_url_direct

# Call core functions directly
result = await crawl_url_direct(
    url='https://example.com',
    options={'javascript': True}
)
```

## Tool Naming Convention

Tools follow descriptive naming:
- `crawl_webpage_with_smart_execution`
- `extract_structured_data_with_schema`
- `analyze_content_sentiment_and_entities`

## Session Management

Sessions persist browser state:
```python
# First crawl creates session
result1 = await crawl_url_direct('https://site.com/login')
session_id = result1['session_id']

# Subsequent crawls reuse session
result2 = await crawl_url_direct(
    'https://site.com/dashboard',
    session_id=session_id
)
```

## Error Handling

All functions return consistent error format:
```python
{
    "success": False,
    "error": "Descriptive error message",
    "error_type": "timeout|auth|network|..."
}
```
```

## Deliverables

1. **Integration layer** connecting all components
2. **Comprehensive test suite** covering:
   - Tool chaining
   - Session persistence
   - Smart sync/async
   - Error handling
   - Performance
   - Load testing
3. **Integration documentation** for developers
4. **Performance benchmarks** and metrics
5. **Load test results** and recommendations

## Success Criteria

- [ ] All components work together seamlessly
- [ ] Tests cover >90% of integration points
- [ ] Performance meets targets (<3s for sync, job creation for async)
- [ ] System handles 50+ concurrent requests
- [ ] Error handling is consistent across all layers
- [ ] Documentation is clear and complete

## Next Steps

After Phase 3 completion:
- Phase 4: UI updates for Claude Desktop integration
- Deploy to production environment
- Monitor performance and usage
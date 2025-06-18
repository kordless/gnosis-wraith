"""
Tests for enhanced toolbag functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from ai.toolbag import ToolBag
from ai.tools import TOOL_LIMITS
from core.browser_session import BrowserSessionManager

@pytest.fixture
async def toolbag():
    """Create a test toolbag instance."""
    tb = ToolBag(provider='anthropic')
    yield tb
    # Cleanup
    tb.reset_usage()

@pytest.fixture
async def session_manager():
    """Create a test session manager."""
    sm = BrowserSessionManager()
    yield sm
    # Cleanup
    await sm.close_all_sessions()

class TestToolUsageLimits:
    """Test tool usage limits and .pop() mechanics."""
    
    @pytest.mark.asyncio
    async def test_set_tool_limit(self, toolbag):
        """Test setting tool usage limits."""
        toolbag.set_tool_limit("expensive_tool", 2)
        assert toolbag.tool_limits["expensive_tool"] == 2
    
    @pytest.mark.asyncio
    async def test_get_available_tools_with_limits(self, toolbag):
        """Test that tools become unavailable after limit is reached."""
        # Set limit of 2 uses
        toolbag.set_tool_limit("limited_tool", 2)
        
        # First use - should be available
        available = toolbag.get_available_tools(["limited_tool", "unlimited_tool"])
        assert "limited_tool" in available
        assert "unlimited_tool" in available
        
        # Use the tool once
        toolbag.tool_usage_count["limited_tool"] = 1
        available = toolbag.get_available_tools(["limited_tool"])
        assert "limited_tool" in available
        
        # Use the tool twice - at limit
        toolbag.tool_usage_count["limited_tool"] = 2
        available = toolbag.get_available_tools(["limited_tool"])
        assert "limited_tool" not in available  # Should be exhausted
    
    @pytest.mark.asyncio
    async def test_unlimited_tools(self, toolbag):
        """Test that tools without limits can be used many times."""
        # Don't set a limit for this tool
        toolbag.tool_usage_count["unlimited_tool"] = 100
        
        available = toolbag.get_available_tools(["unlimited_tool"])
        assert "unlimited_tool" in available
    
    @pytest.mark.asyncio
    async def test_reset_usage(self, toolbag):
        """Test that reset_usage clears counts and context."""
        toolbag.tool_usage_count = {"tool1": 5, "tool2": 3}
        toolbag.execution_context = {"data": "test"}
        
        toolbag.reset_usage()
        
        assert toolbag.tool_usage_count == {}
        assert toolbag.execution_context == {}

class TestSessionManagement:
    """Test browser session persistence."""
    
    @pytest.mark.asyncio
    async def test_create_session(self, session_manager):
        """Test creating a browser session."""
        mock_browser = Mock()
        session_id = await session_manager.create_session("test_session", mock_browser)
        
        assert session_id == "test_session"
        assert "test_session" in session_manager.sessions
        assert session_manager.sessions["test_session"]["browser"] == mock_browser
    
    @pytest.mark.asyncio
    async def test_get_session(self, session_manager):
        """Test retrieving a browser session."""
        mock_browser = Mock()
        await session_manager.create_session("test_session", mock_browser)
        
        retrieved = await session_manager.get_session("test_session")
        assert retrieved == mock_browser
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, session_manager):
        """Test retrieving a non-existent session returns None."""
        retrieved = await session_manager.get_session("nonexistent")
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_session_metadata(self, session_manager):
        """Test updating session metadata."""
        mock_browser = Mock()
        await session_manager.create_session("test_session", mock_browser)
        
        # Update metadata
        await session_manager.update_session_metadata(
            "test_session",
            {"current_url": "https://example.com", "logged_in": True}
        )
        
        # Check metadata was stored
        session = session_manager.sessions["test_session"]
        assert session["metadata"]["current_url"] == "https://example.com"
        assert session["metadata"]["logged_in"] is True
    
    @pytest.mark.asyncio
    async def test_close_session(self, session_manager):
        """Test manually closing a session."""
        mock_browser = AsyncMock()
        await session_manager.create_session("test_session", mock_browser)
        
        await session_manager.close_session("test_session")
        
        assert "test_session" not in session_manager.sessions
        mock_browser.close.assert_called_once()

class TestToolChaining:
    """Test tool chaining with context passing."""
    
    @pytest.mark.asyncio
    async def test_execute_chain_basic(self, toolbag):
        """Test basic tool chain execution."""
        # Mock the execute method
        async def mock_execute(*args, **kwargs):
            tool = kwargs.get('tools', ['unknown'])[0]
            return {
                "success": True,
                "tool_name": tool,
                "response": f"Result from {tool}"
            }
        
        toolbag.execute = mock_execute
        
        result = await toolbag.execute_chain(
            tools=["tool1", "tool2", "tool3"],
            query="Test query"
        )
        
        assert result["success"] is True
        assert result["tools_executed"] == 3
        assert len(result["results"]) == 3
    
    @pytest.mark.asyncio
    async def test_execute_chain_with_limits(self, toolbag):
        """Test chain execution respects tool limits."""
        toolbag.set_tool_limit("limited_tool", 1)
        
        # Mock execute
        async def mock_execute(*args, **kwargs):
            return {"success": True}
        
        toolbag.execute = mock_execute
        
        # Try to use limited_tool twice
        result = await toolbag.execute_chain(
            tools=["limited_tool", "limited_tool", "unlimited_tool"],
            query="Test"
        )
        
        # Should only execute limited_tool once
        assert result["tools_executed"] == 2  # limited_tool once + unlimited_tool
    
    @pytest.mark.asyncio
    async def test_execute_chain_session_persistence(self, toolbag):
        """Test that sessions persist between tool calls."""
        # Mock execute to return session info
        call_count = 0
        
        async def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                # First tool creates session
                return {
                    "success": True,
                    "session_id": "browser_session_123",
                    "session_data": {"page": "loaded"}
                }
            else:
                # Later tools should receive session
                return {"success": True}
        
        toolbag.execute = mock_execute
        
        result = await toolbag.execute_chain(
            tools=["crawl_tool", "analyze_tool"],
            query="Test"
        )
        
        # Check session was stored
        assert "browser_session_123" in result["session_store"]
        assert result["session_store"]["browser_session_123"]["page"] == "loaded"

class TestEnhancedContext:
    """Test enhanced context passing in execute_tools."""
    
    @pytest.mark.asyncio
    async def test_execute_tools_enhanced_context(self):
        """Test that execute_tools receives and uses enhanced context."""
        from ai.anthropic import execute_tools
        
        # Create test context
        context = {
            "tools": ["test_tool"],
            "query": "Test query",
            "previous_results": [
                {"tool_name": "tool1", "response": "First result"},
                {"tool_name": "tool2", "response": "Second result"}
            ],
            "execution_context": {"shared": "data"},
            "session_store": {"session1": {"state": "active"}}
        }
        
        # Mock the process_with_anthropic_tools function
        with patch('ai.anthropic.process_with_anthropic_tools') as mock_process:
            mock_process.return_value = {
                "response": "Test response",
                "tool_calls": []
            }
            
            # Mock environment API key
            with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
                result = await execute_tools(context)
        
        # Verify enhanced context was used
        assert result["success"] is True
        assert result["execution_metadata"]["context_used"] is True
        assert result["execution_metadata"]["sessions_active"] == 1
        
        # Verify the call included context in the query
        call_args = mock_process.call_args
        assert "Previous tool results:" in call_args[1]["text"]
        assert "Active sessions: ['session1']" in call_args[1]["text"]

class TestIntegration:
    """Integration tests for the complete enhanced toolbag."""
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test a complete workflow with all enhancements."""
        # Create toolbag
        toolbag = ToolBag(provider='anthropic')
        
        # Set tool limits from registry
        for tool_name, limit in TOOL_LIMITS.items():
            toolbag.set_tool_limit(tool_name, limit)
        
        # Mock provider module
        mock_provider = Mock()
        mock_provider.execute_tools = AsyncMock(return_value={
            "success": True,
            "response": "Tool executed",
            "session_id": "test_session_123"
        })
        
        with patch.object(toolbag, '_load_provider_module', return_value=mock_provider):
            # Execute a tool
            result = await toolbag.execute(
                tools=["suggest_url"],
                query="Find information about Python",
                api_key="test_key"
            )
            
            assert result["success"] is True
            
            # Verify context was passed
            call_args = mock_provider.execute_tools.call_args[0][0]
            assert "execution_context" in call_args
            assert "session_store" in call_args

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
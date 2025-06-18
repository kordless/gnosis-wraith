# Phase 1: Toolbag Enhancement Plan

## Overview
Enhance the existing toolbag system with simple .pop() mechanics, usage limits, and session management for tool chaining.

## Timeline: Week 1 (5-7 days)

## 1.1 Core Toolbag Updates

### File: `ai/toolbag.py`

Add these features to the existing ToolBag class:

```python
class ToolBag:
    def __init__(self, provider=None, model=None):
        # Existing code...
        self.tool_usage_count = {}      # Track usage per execution
        self.tool_limits = {}           # Max uses per tool
        self.session_store = {}         # Browser/state sessions
        self.execution_context = {}     # Shared data between tools
    
    def set_tool_limit(self, tool_name: str, max_uses: int):
        """Set how many times a tool can be used in one execution"""
        self.tool_limits[tool_name] = max_uses
    
    def reset_usage(self):
        """Reset usage counts for new execution"""
        self.tool_usage_count = {}
        self.execution_context = {}
    
    def get_available_tools(self, requested_tools: List[str]) -> List[str]:
        """Filter tools based on usage limits"""
        available = []
        for tool in requested_tools:
            if tool in self.tool_limits:
                current = self.tool_usage_count.get(tool, 0)
                if current < self.tool_limits[tool]:
                    available.append(tool)
                else:
                    logger.info(f"Tool {tool} exhausted ({current}/{self.tool_limits[tool]})")
            else:
                available.append(tool)  # No limit
        return available
    
    async def execute_chain(self, 
                          tools: List[str], 
                          query: str,
                          mode: str = 'auto',
                          **kwargs) -> Dict[str, Any]:
        """Execute tools with chaining and context passing"""
        self.reset_usage()
        results = []
        
        for i, tool in enumerate(tools):
            # Check availability
            available = self.get_available_tools([tool])
            if not available:
                logger.warning(f"Tool {tool} not available")
                continue
            
            # Update usage
            self.tool_usage_count[tool] = self.tool_usage_count.get(tool, 0) + 1
            
            # Execute with context
            context = {
                'query': query,
                'previous_results': results,
                'execution_context': self.execution_context,
                'session_store': self.session_store,
                **kwargs
            }
            
            result = await self.execute(
                tools=[tool],
                **context
            )
            
            results.append(result)
            
            # Update execution context
            if result.get('session_id'):
                self.session_store[result['session_id']] = result.get('session_data')
        
        return {
            'success': True,
            'results': results,
            'tools_executed': len(results),
            'final_context': self.execution_context
        }
```

### File: `ai/tools/__init__.py`

Add tool limits registry:

```python
# Tool usage limits (per execution)
TOOL_LIMITS = {
    # Singleton tools (once only)
    "initialize_browser_session": 1,
    "generate_final_crawl_report": 1,
    "cleanup_browser_sessions": 1,
    
    # Limited use tools
    "perform_expensive_ai_analysis": 3,
    "execute_complex_javascript_injection": 5,
    "capture_full_page_screenshot": 10,
    
    # Unlimited tools (not listed) can be used as many times as needed
}

# Tool categories with descriptive names
TOOL_CATEGORIES = {
    # Web interaction tools
    "web_scraping": [
        "scrape_webpage_with_javascript",
        "extract_webpage_content_as_markdown", 
        "capture_webpage_screenshot_full_page",
        "extract_all_links_from_webpage"
    ],
    
    "web_crawling": [
        "crawl_website_with_depth_control",
        "discover_urls_intelligently",
        "filter_urls_by_relevance",
        "analyze_website_structure"
    ],
    
    # Data processing tools
    "content_extraction": [
        "extract_structured_data_with_schema",
        "convert_html_to_clean_markdown",
        "extract_images_and_media_urls",
        "parse_tables_to_json"
    ],
    
    # AI analysis tools
    "content_analysis": [
        "analyze_content_sentiment_and_entities",
        "summarize_long_text_intelligently",
        "classify_content_by_topic",
        "extract_key_information_points"
    ],
    
    # Job management tools
    "job_control": [
        "create_async_crawl_job",
        "check_job_status_and_progress",
        "retrieve_job_results_when_ready",
        "cancel_running_job"
    ],
    
    # Storage tools
    "data_storage": [
        "save_crawl_results_to_storage",
        "query_stored_crawl_data",
        "generate_pdf_report_from_data",
        "export_data_as_json_or_csv"
    ]
}

def get_tool_with_limit(tool_name: str) -> Tuple[str, int]:
    """Get tool with its usage limit"""
    return tool_name, TOOL_LIMITS.get(tool_name, -1)  # -1 = unlimited
```

## 1.2 Session Management

### File: `core/browser_session.py` (NEW)

Create a simple session manager:

```python
from typing import Dict, Any, Optional
import asyncio
from datetime import datetime, timedelta

class BrowserSessionManager:
    """Manages browser sessions for tool chaining"""
    
    def __init__(self):
        self.sessions: Dict[str, Any] = {}
        self.session_timeout = timedelta(minutes=5)
    
    async def create_session(self, session_id: str, browser_instance: Any) -> str:
        """Store a browser session"""
        self.sessions[session_id] = {
            'browser': browser_instance,
            'created_at': datetime.now(),
            'last_used': datetime.now()
        }
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Any]:
        """Retrieve a browser session"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session['last_used'] = datetime.now()
            return session['browser']
        return None
    
    async def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        now = datetime.now()
        expired = []
        
        for sid, session in self.sessions.items():
            if now - session['last_used'] > self.session_timeout:
                expired.append(sid)
        
        for sid in expired:
            browser = self.sessions[sid]['browser']
            await browser.close()
            del self.sessions[sid]
    
    async def close_all_sessions(self):
        """Close all browser sessions"""
        for session in self.sessions.values():
            await session['browser'].close()
        self.sessions.clear()

# Global session manager
session_manager = BrowserSessionManager()
```

## 1.3 Enhanced Provider Integration

### File: `ai/anthropic.py` (UPDATE)

Update the execute_tools function to support chaining:

```python
async def execute_tools(context: Dict[str, Any]) -> Dict[str, Any]:
    """Execute tools with enhanced context support"""
    try:
        # Extract enhanced context
        previous_results = context.get('previous_results', [])
        execution_context = context.get('execution_context', {})
        session_store = context.get('session_store', {})
        
        # Build enhanced prompt with context
        if previous_results:
            context_info = "\n\nPrevious tool results:"
            for i, result in enumerate(previous_results):
                context_info += f"\n{i+1}. {result.get('tool_name', 'Unknown')}: {result.get('summary', 'No summary')}"
            
            # Add to user prompt
            original_query = context.get('query', '')
            context['query'] = f"{original_query}{context_info}"
        
        # Add session information to tool schemas
        tool_schemas = context.get('tools', [])
        for schema in tool_schemas:
            if 'session_aware' in schema.get('metadata', {}):
                schema['description'] += "\n\nThis tool can use session_id from previous tools."
        
        # Continue with existing execution...
        result = await process_with_anthropic_tools(...)
        
        # Add execution metadata
        result['execution_metadata'] = {
            'tools_available': len(tool_schemas),
            'context_used': bool(previous_results),
            'sessions_active': len(session_store)
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Enhanced tool execution error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
```

## 1.4 Testing Strategy

### Create test file: `tests/test_toolbag_enhancements.py`

```python
import pytest
from ai.toolbag import ToolBag

@pytest.mark.asyncio
async def test_tool_limits():
    """Test tool usage limits"""
    toolbag = ToolBag()
    toolbag.set_tool_limit("expensive_tool", 2)
    
    # First two uses should work
    available = toolbag.get_available_tools(["expensive_tool"])
    assert "expensive_tool" in available
    
    toolbag.tool_usage_count["expensive_tool"] = 1
    available = toolbag.get_available_tools(["expensive_tool"])
    assert "expensive_tool" in available
    
    # Third use should be blocked
    toolbag.tool_usage_count["expensive_tool"] = 2
    available = toolbag.get_available_tools(["expensive_tool"])
    assert "expensive_tool" not in available

@pytest.mark.asyncio
async def test_session_persistence():
    """Test session passing between tools"""
    toolbag = ToolBag()
    
    # Mock execution with session
    result1 = {
        'session_id': 'test_session_123',
        'session_data': {'page': 'modified'}
    }
    
    toolbag.session_store[result1['session_id']] = result1['session_data']
    
    # Verify session is available
    assert 'test_session_123' in toolbag.session_store
    assert toolbag.session_store['test_session_123']['page'] == 'modified'

@pytest.mark.asyncio
async def test_execution_context():
    """Test context passing between tools"""
    toolbag = ToolBag()
    
    # Simulate tool chain execution
    results = await toolbag.execute_chain(
        tools=['mock_tool_1', 'mock_tool_2'],
        query='test query'
    )
    
    # Verify results structure
    assert 'results' in results
    assert 'tools_executed' in results
    assert 'final_context' in results
```

## Deliverables

1. **Enhanced toolbag.py** with:
   - Usage tracking and limits
   - Session management
   - Context passing
   - Chain execution

2. **Updated tool registry** with:
   - Descriptive tool names
   - Usage limits
   - Category organization

3. **Session manager** for browser persistence

4. **Enhanced provider integration** for context awareness

5. **Test suite** for new features

## Success Criteria

- [ ] Tools can be limited to N uses per execution
- [ ] Browser sessions persist between tool calls
- [ ] Context passes correctly between tools
- [ ] LLM understands previous tool results
- [ ] All existing functionality still works
- [ ] Tests pass for new features

## Next Steps

After Phase 1 completion:
- Phase 2: Create MCP tool implementations
- Phase 3: Integrate with v2 endpoints
- Phase 4: UI updates
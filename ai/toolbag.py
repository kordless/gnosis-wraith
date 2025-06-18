"""
Toolbag: A flexible tool execution and chaining system for AI-powered tasks.

Supports multi-provider, multi-tool execution with complex chaining capabilities.
"""

import logging
import importlib
from typing import Dict, Any, List, Optional, Union

# Configure logging
logger = logging.getLogger("gnosis_wraith")

class ToolBag:
    """
    Manages tool execution across different providers and supports tool chaining.
    
    Core design principles:
    1. Provider-agnostic tool execution
    2. Flexible input and output handling
    3. Support for multi-step tool chains
    4. Robust error management
    5. Tool usage limits with .pop() mechanics
    6. Session persistence for browser state
    """
    
    def __init__(self, 
                 provider: Optional[str] = None, 
                 model: Optional[str] = None):
        """
        Initialize a ToolBag with optional default provider and model.
        
        Args:
            provider: Default AI provider (e.g., 'anthropic', 'openai')
            model: Default model to use
        """
        self.provider = provider
        self.model = model
        
        # Mapping of provider modules
        self._provider_modules = {
            'anthropic': 'ai.anthropic',
            'openai': 'ai.openai',
            # Add more providers as needed
        }
        
        # Tool usage tracking
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
    
    def _load_provider_module(self, provider: str):
        """
        Dynamically load the module for a specific provider.
        
        Args:
            provider: Name of the provider
        
        Returns:
            Loaded provider module
        """
        if provider not in self._provider_modules:
            raise ValueError(f"Unsupported provider: {provider}")
        
        try:
            return importlib.import_module(self._provider_modules[provider])
        except ImportError as e:
            logger.error(f"Failed to import provider module for {provider}: {e}")
            raise
    
    async def execute(self, 
                      tools: List[str], 
                      query: Optional[str] = None,
                      prompt: Optional[str] = None,
                      provider: Optional[str] = None,
                      model: Optional[str] = None,
                      api_key: Optional[str] = None,
                      previous_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a chain of tools with the specified configuration.
        
        Args:
            tools: List of tool names to execute
            query: Optional input query
            prompt: Optional system or user prompt
            provider: Specific provider for this execution (overrides default)
            model: Specific model for this execution (overrides default)
            api_key: Optional API key for the provider
            previous_result: Result from a previous tool execution to chain
        
        Returns:
            Dictionary with tool execution results
        """
        # Determine provider and model
        current_provider = provider or self.provider
        current_model = model or self.model
        
        if not current_provider:
            raise ValueError("No AI provider specified")
        
        # Load the provider module
        provider_module = self._load_provider_module(current_provider)
        
        # Prepare execution context with enhanced features
        context = {
            'tools': tools,
            'query': query,
            'prompt': prompt,
            'model': current_model,
            'api_key': api_key,
            'previous_result': previous_result,
            'previous_results': [],  # For compatibility
            'execution_context': self.execution_context,
            'session_store': self.session_store
        }
        
        try:
            # DEBUG: Log the execution context
            logger.info(f"🎯 Toolbag.execute called:")
            logger.info(f"  tools: {tools}")
            logger.info(f"  query: '{query}'")
            logger.info(f"  provider: {current_provider}")
            logger.info(f"  model: {current_model}")
            
            # Call provider-specific tool execution method
            # This assumes each provider module has a consistent interface
            result = await provider_module.execute_tools(context)
            
            return result
        
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'provider': current_provider,
                'model': current_model
            }
    
    async def execute_chain(self, 
                          tools: List[str], 
                          query: str,
                          mode: str = 'auto',
                          provider: Optional[str] = None,
                          model: Optional[str] = None,
                          api_key: Optional[str] = None,
                          **kwargs) -> Dict[str, Any]:
        """
        Execute tools with chaining and context passing.
        
        Args:
            tools: List of tool names to execute in sequence
            query: The user query
            mode: Execution mode ('auto', 'sequential', 'parallel')
            provider: AI provider to use
            model: Model to use
            api_key: API key for authentication
            **kwargs: Additional arguments passed to tools
            
        Returns:
            Dictionary with all results and final context
        """
        self.reset_usage()
        results = []
        
        for i, tool in enumerate(tools):
            # Check availability
            available = self.get_available_tools([tool])
            if not available:
                logger.warning(f"Tool {tool} not available (usage limit reached)")
                continue
            
            # Update usage
            self.tool_usage_count[tool] = self.tool_usage_count.get(tool, 0) + 1
            
            # Execute with context
            result = await self.execute(
                tools=[tool],
                query=query,
                provider=provider,
                model=model,
                api_key=api_key,
                previous_result=results[-1] if results else None,
                **kwargs
            )
            
            results.append(result)
            
            # Update execution context
            if result.get('success'):
                self.execution_context[f'tool_{i}_{tool}'] = result
                
                # Store session if provided
                if result.get('session_id'):
                    self.session_store[result['session_id']] = result.get('session_data', {})
        
        return {
            'success': True,
            'results': results,
            'tools_executed': len(results),
            'final_context': self.execution_context,
            'session_store': self.session_store
        }

# Create a global toolbag instance for convenience
toolbag = ToolBag(provider='anthropic', model='claude-3-5-sonnet-20241022')

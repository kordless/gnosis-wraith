"""
Simple tool decorator system - no external dependencies
"""

import inspect
import re
from typing import Dict, Any, Callable, get_type_hints
from functools import wraps

# Global tool registry
_TOOLS = {}

def tool(name: str = None, description: str = None):
    """
    Simple decorator to register tools without external dependencies.
    
    Args:
        name: Tool name (defaults to function name)
        description: Tool description (defaults to function docstring)
    """
    def decorator(func: Callable):
        tool_name = name or func.__name__
        tool_description = description or (func.__doc__ or "").strip().split('\n')[0]
        
        # Generate schema from function signature
        schema = _generate_schema_from_function(func)
        
        # Store tool info
        _TOOLS[tool_name] = {
            "name": tool_name,
            "description": tool_description,
            "input_schema": schema,
            "function": func
        }
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator

def _generate_schema_from_function(func: Callable) -> Dict[str, Any]:
    """Generate JSON schema from function signature."""
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)
    
    # Extract parameter descriptions from docstring
    param_descriptions = _extract_param_descriptions(func)
    
    properties = {}
    required = []
    
    for param_name, param in sig.parameters.items():
        if param_name in ['self', 'cls']:
            continue
            
        param_type = type_hints.get(param_name, str)
        
        # Convert Python types to JSON schema types
        if param_type == str:
            json_type = "string"
        elif param_type == int:
            json_type = "integer"
        elif param_type == float:
            json_type = "number"
        elif param_type == bool:
            json_type = "boolean"
        else:
            json_type = "string"  # Default fallback
        
        param_info = {
            "type": json_type,
            "description": param_descriptions.get(param_name, f"Parameter {param_name}")
        }
        
        # Add default value if present
        if param.default != inspect.Parameter.empty:
            param_info["default"] = param.default
        else:
            required.append(param_name)
        
        properties[param_name] = param_info
    
    return {
        "type": "object",
        "properties": properties,
        "required": required
    }

def _extract_param_descriptions(func: Callable) -> Dict[str, str]:
    """Extract parameter descriptions from docstring."""
    docstring = func.__doc__
    param_descriptions = {}
    
    if docstring:
        # Support both :param format and Args: format
        lines = docstring.split('\n')
        for line in lines:
            line = line.strip()
            # :param name: description format
            param_match = re.match(r':param\s+(\w+):\s*(.+)', line)
            if param_match:
                param_descriptions[param_match.group(1)] = param_match.group(2)
            # Args: format (look for name: description)
            elif ':' in line and not line.startswith(':'):
                parts = line.split(':', 1)
                if len(parts) == 2:
                    param_name = parts[0].strip()
                    param_desc = parts[1].strip()
                    if param_name.isidentifier():
                        param_descriptions[param_name] = param_desc
    
    return param_descriptions

def get_all_tools() -> Dict[str, Dict[str, Any]]:
    """Get all registered tools."""
    return _TOOLS.copy()

def get_tool_schemas() -> list:
    """Get tool schemas in Claude/OpenAI format."""
    return [
        {
            "name": tool_info["name"],
            "description": tool_info["description"], 
            "input_schema": tool_info["input_schema"]
        }
        for tool_info in _TOOLS.values()
    ]

async def execute_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """Execute a tool by name."""
    if tool_name not in _TOOLS:
        return {"success": False, "error": f"Tool '{tool_name}' not found"}
    
    try:
        tool_func = _TOOLS[tool_name]["function"]
        return await tool_func(**kwargs)
    except Exception as e:
        return {"success": False, "error": str(e)}

def clear_tools():
    """Clear all registered tools (useful for testing)."""
    global _TOOLS
    _TOOLS = {}

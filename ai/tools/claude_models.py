"""
Claude model definitions and configuration for tool integrations.
"""

# Claude model definitions for tool interactions
CLAUDE_MODELS = {
    "claude-3-opus-20240229": {
        "name": "Claude 3 Opus",
        "description": "Most powerful Claude model with highest reasoning capabilities",
        "max_tokens": 4096,
        "cost_per_1k_input": 15.00,
        "cost_per_1k_output": 75.00,
        "tool_support": True
    },
    "claude-3-sonnet-20240229": {
        "name": "Claude 3 Sonnet",
        "description": "Balanced model with strong reasoning and fast responses",
        "max_tokens": 4096,
        "cost_per_1k_input": 3.00,
        "cost_per_1k_output": 15.00,
        "tool_support": True
    },
    "claude-3-haiku-20240307": {
        "name": "Claude 3 Haiku",
        "description": "Fast, compact model for efficient interactions",
        "max_tokens": 4096,
        "cost_per_1k_input": 0.25,
        "cost_per_1k_output": 1.25,
        "tool_support": True
    },
    "claude-3-5-sonnet-20240620": {
        "name": "Claude 3.5 Sonnet",
        "description": "New improved model with enhanced reasoning",
        "max_tokens": 4096,
        "cost_per_1k_input": 3.00,
        "cost_per_1k_output": 15.00,
        "tool_support": True
    }
}

def get_available_models():
    """
    Get a list of available Claude models.
    
    Returns:
        Dictionary of available models with their configurations
    """
    return CLAUDE_MODELS

def get_default_model():
    """
    Get the default Claude model for tool operations.
    
    Returns:
        String with the default model identifier
    """
    return "claude-3-haiku-20240307"  # Most cost-effective for tool operations

def get_model_by_performance(performance_level="balanced"):
    """
    Select a Claude model based on desired performance level.
    
    Args:
        performance_level: One of "high", "balanced", or "efficient"
        
    Returns:
        String with the appropriate model identifier
    """
    if performance_level == "high":
        return "claude-3-opus-20240229"
    elif performance_level == "balanced":
        return "claude-3-sonnet-20240229"
    elif performance_level == "efficient":
        return "claude-3-haiku-20240307"
    elif performance_level == "latest":
        return "claude-3-5-sonnet-20240620"
    else:
        # Default to balanced
        return "claude-3-sonnet-20240229"
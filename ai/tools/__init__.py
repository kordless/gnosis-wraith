"""
AI Tools Manager - Provider-agnostic tool loading and management

This module provides functions to load and manage tools based on query requirements,
supporting multiple AI providers (Anthropic, OpenAI, Ollama, etc.).
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from ai.tools.calculate import get_calculation_tools
from ai.tools.url_suggestion import get_url_suggestion_tools
from ai.tools.cryptocurrency import get_cryptocurrency_tools
from ai.tools.check_for_odd_user import get_check_for_odd_user_tools
from ai.tools.decorators import execute_tool

# Import the tool modules to ensure they're registered
import ai.tools.calculate
import ai.tools.url_suggestion  
import ai.tools.cryptocurrency
import ai.tools.check_for_odd_user

# Import new tool modules
try:
    from ai.tools.web_crawling import get_web_crawling_tools
    import ai.tools.web_crawling
except ImportError:
    get_web_crawling_tools = lambda: []

try:
    from ai.tools.content_processing import get_content_processing_tools
    import ai.tools.content_processing
except ImportError:
    get_content_processing_tools = lambda: []

logger = logging.getLogger("gnosis_wraith")

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

# Tool categories and their corresponding loader functions
TOOL_CATEGORIES = {
    "calculation": get_calculation_tools,
    "math": get_calculation_tools,  # Alias
    "url": get_url_suggestion_tools,
    "web": get_url_suggestion_tools,  # Alias
    "suggestion": get_url_suggestion_tools,  # Alias
    "cryptocurrency": get_cryptocurrency_tools,
    "crypto": get_cryptocurrency_tools,  # Alias
    "bitcoin": get_cryptocurrency_tools,  # Alias
    "finance": get_cryptocurrency_tools,  # Alias
    "check_odd_user": get_check_for_odd_user_tools,
    "odd_user": get_check_for_odd_user_tools,  # Alias
    "user_behavior": get_check_for_odd_user_tools,  # Alias
    "web_crawling": get_web_crawling_tools,
    "crawling": get_web_crawling_tools,  # Alias
    "scraping": get_web_crawling_tools,  # Alias
    "content_processing": get_content_processing_tools,
    "content": get_content_processing_tools,  # Alias
    "processing": get_content_processing_tools  # Alias
}

def get_tools_for_query(query: str, categories: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Get appropriate tools based on query analysis or specified categories.
    
    Args:
        query: The user query to analyze
        categories: Optional list of specific tool categories to load
        
    Returns:
        List of tools in Claude/OpenAI compatible format
    """
    try:
        if categories:
            # Use specified categories
            selected_categories = categories
        else:
            # Analyze query to determine needed tools
            selected_categories = analyze_query_for_tools(query)
        
        logger.info(f"Loading tools for categories: {selected_categories}")
        
        tools = []
        for category in selected_categories:
            if category in TOOL_CATEGORIES:
                category_tools = TOOL_CATEGORIES[category]()  # No longer async
                tools.extend(category_tools)
                logger.info(f"Loaded {len(category_tools)} tools from category: {category}")
            else:
                logger.warning(f"Unknown tool category: {category}")
        
        logger.info(f"Total tools loaded: {len(tools)}")
        return tools
        
    except Exception as e:
        logger.error(f"Error loading tools: {e}")
        return []

def analyze_query_for_tools(query: str) -> List[str]:
    """
    Analyze a query to determine which tool categories are needed.
    
    Args:
        query: The user query to analyze
        
    Returns:
        List of tool category names
    """
    query_lower = query.lower()
    categories = []
    
    # Check for calculation/math keywords
    math_keywords = [
        'calculate', 'compute', 'math', 'arithmetic', 'add', 'subtract', 'multiply', 'divide',
        'percentage', 'percent', 'convert', 'units', 'temperature', 
        'sum', 'total', 'average', 'mean', 'formula', 'equation'
    ]
    
    if any(keyword in query_lower for keyword in math_keywords):
        categories.append("calculation")
    
    # Check for cryptocurrency/finance keywords
    crypto_keywords = [
        'bitcoin', 'btc', 'cryptocurrency', 'crypto', 'price', 'market cap',
        'trading', 'exchange rate', 'currency', 'financial', 'investment'
    ]
    
    if any(keyword in query_lower for keyword in crypto_keywords):
        categories.append("cryptocurrency")
    
    # Check for URL/web keywords
    url_keywords = [
        'url', 'website', 'site', 'web', 'link', 'domain', 'page', 'crawl',
        'visit', 'browse', 'read about', 'find information', 'search for',
        'documentation', 'docs', 'tutorial', 'guide', 'news', 'article'
    ]
    
    if any(keyword in query_lower for keyword in url_keywords):
        categories.append("url")
    
    # Check if query contains URLs
    if 'http' in query_lower or 'www.' in query_lower or '.com' in query_lower:
        categories.append("url")
    
    # If no specific categories detected, default to URL tools for general queries
    if not categories:
        categories.append("url")
    
    # Always include check_for_odd_user when URL tools are included
    # This allows the AI to detect when users are trying to chat instead of providing URLs
    if "url" in categories:
        categories.append("check_odd_user")
    
    return categories

def get_all_available_tools() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all available tools organized by category.
    
    Returns:
        Dictionary mapping category names to their tools
    """
    try:
        all_tools = {}
        
        for category, loader_func in TOOL_CATEGORIES.items():
            tools = loader_func()  # No longer async
            all_tools[category] = tools
            logger.info(f"Loaded {len(tools)} tools for category: {category}")
        
        return all_tools
        
    except Exception as e:
        logger.error(f"Error loading all tools: {e}")
        return {}

def get_tools_by_names(tool_names: List[str]) -> List[Dict[str, Any]]:
    """
    Get specific tools by their names.
    
    Args:
        tool_names: List of tool names to load
        
    Returns:
        List of matching tools
    """
    try:
        all_tools_by_category = get_all_available_tools()  # No longer async
        
        # Flatten all tools into a single list
        all_tools = []
        for category_tools in all_tools_by_category.values():
            all_tools.extend(category_tools)
        
        # Filter by requested names
        selected_tools = []
        for tool in all_tools:
            if tool.get("name") in tool_names:
                selected_tools.append(tool)
        
        logger.info(f"Found {len(selected_tools)} tools matching names: {tool_names}")
        return selected_tools
        
    except Exception as e:
        logger.error(f"Error getting tools by names: {e}")
        return []

def list_available_categories() -> List[str]:
    """
    List all available tool categories.
    
    Returns:
        List of category names
    """
    return list(TOOL_CATEGORIES.keys())

def list_available_tools() -> Dict[str, str]:
    """
    List all available tools with their descriptions (synchronous version).
    
    Returns:
        Dictionary mapping tool names to descriptions
    """
    # Note: This is a simplified version that doesn't actually load the tools
    # For full tool information, use get_all_available_tools()
    return {
        "calculate": "Perform basic arithmetic calculations",
        "percentage_calculator": "Calculate percentages with different operations",
        "unit_converter": "Convert between different units of measurement",
        "suggest_url": "Suggest URLs based on search queries",
        "validate_url": "Validate URLs and check crawlability",
        "analyze_domain": "Analyze domains for crawling characteristics",
        "check_for_odd_user": "Check if user is acting oddly or trying to chat with the crawler"
    }

def get_tool_with_limit(tool_name: str) -> Tuple[str, int]:
    """
    Get tool with its usage limit.
    
    Args:
        tool_name: Name of the tool
        
    Returns:
        Tuple of (tool_name, limit) where limit is -1 for unlimited
    """
    return tool_name, TOOL_LIMITS.get(tool_name, -1)  # -1 = unlimited

# Export main functions
__all__ = [
    "get_tools_for_query",
    "get_all_available_tools", 
    "get_tools_by_names",
    "analyze_query_for_tools",
    "list_available_categories",
    "list_available_tools",
    "get_tool_with_limit",
    "TOOL_LIMITS"
]

"""
Check for Odd User toolbag - Tool for detecting when users are acting oddly or trying to chat with a crawler

This module contains a tool that detects when users are trying to chat with an AI system
rather than providing URLs for crawling, and provides guidance to redirect them appropriately.
"""

from typing import Dict, Any
import logging
from .decorators import tool

logger = logging.getLogger("gnosis_wraith")

@tool(description="CRITICAL: ALWAYS call this FIRST to check if user is chatting instead of requesting URL crawling. Set user_is_acting_odd=True for ANY greeting, question, or conversational message.")
async def check_for_odd_user(
    user_is_acting_odd: bool,
    thinking_notes: str = ""
) -> Dict[str, Any]:
    """
    CRITICAL TOOL: MUST be called FIRST to detect users trying to chat instead of requesting URL crawling.
    
    SET user_is_acting_odd=True for ALL of these cases:
    - ANY greetings: "hello", "hi", "hey", "are you there", "how are you", "what's up"
    - Questions to the AI: "can you help me", "what can you do", "who are you"
    - Conversational messages: "hello bot are you there?", "reply to my inquiry"
    - Chat attempts: Any message that sounds like talking to a person/bot
    - General topics: "python programming", "latest news", "weather" (without "crawl" or URL)
    - Questions about topics: "tell me about X", "what is Y", "how does Z work"
    
    SET user_is_acting_odd=False ONLY for:
    - Actual URLs: "https://example.com", "reddit.com", "news.ycombinator.com"
    - Clear crawl requests: "crawl reddit", "scrape news.ycombinator.com"
    - Website names with crawling intent: "hacker news" (when clearly asking to crawl it)
    
    CRITICAL: "hello bot are you there?" = user_is_acting_odd=True (this is clearly chatting!)
    
    Args:
        user_is_acting_odd: True if user is chatting/asking questions instead of requesting crawling
        thinking_notes: Your reasoning for the decision (for debugging)
    
    Returns:
        Dict with guidance on how to handle the user behavior
    """
    try:
        logger.info(f"🤔 check_for_odd_user called with user_is_acting_odd={user_is_acting_odd}")
        logger.info(f"   thinking_notes: '{thinking_notes}'")
        
        if user_is_acting_odd:
            return {
                "success": True,
                "user_is_acting_odd": True,
                "guidance": "User appears to be trying to chat or ask questions rather than provide URLs for crawling. You MUST call suggest_url with the most relevant URL you can think of based on their input, and use the simple_response_to_users_odd_inquiry parameter to provide a friendly response that addresses their question while explaining this is a web crawler.",
                "must_call_suggest_url": True,
                "suggested_response_approach": "Be friendly and helpful while redirecting them to web crawling. Use suggest_url's simple_response_to_users_odd_inquiry parameter to respond to their question, then suggest a relevant URL to crawl that relates to their topic of interest.",
                "tip": "Call suggest_url immediately with the best URL you can think of that relates to their inquiry, and populate simple_response_to_users_odd_inquiry with a response to their question.",
                "thinking_notes": thinking_notes
            }
        else:
            return {
                "success": True,
                "user_is_acting_odd": False,
                "guidance": "User appears to be using the system normally for web crawling purposes.",
                "must_call_suggest_url": False,
                "suggested_response_approach": "Continue with normal URL processing and crawling workflow.",
                "thinking_notes": thinking_notes
            }
            
    except Exception as e:
        logger.error(f"Error in check_for_odd_user: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "user_is_acting_odd": user_is_acting_odd,
            "thinking_notes": thinking_notes
        }

# Import decorator system to register tools
from .decorators import get_tool_schemas, execute_tool

# Function to get tools for AI providers
def get_check_for_odd_user_tools():
    """Get check for odd user tools in Claude/OpenAI compatible format."""
    return get_tool_schemas()

# Tool execution function
async def execute_check_for_odd_user_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """Execute a check for odd user tool by name."""
    return await execute_tool(tool_name, **kwargs)

# Export functions
__all__ = ["get_check_for_odd_user_tools", "execute_check_for_odd_user_tool", "check_for_odd_user"]

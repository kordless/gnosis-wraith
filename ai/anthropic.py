import logging
import json
from typing import List, Dict, Any, Optional, Union
from anthropic import AsyncAnthropic
from ai.tools import get_tools_for_query

# Get logger from config
logger = logging.getLogger("gnosis_wraith")

async def process_with_anthropic(text: str, token: str) -> str:
    """
    Process text with Anthropic's Claude API using the legacy message-based approach.
    This function is maintained for backward compatibility.
    """
    logger.info("Processing text with Anthropic API (legacy mode)")
    
    client = AsyncAnthropic(api_key=token)
    
    try:
        response = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": f"I've extracted text from a website. Please analyze it and provide a concise summary highlighting key information and main points:\n\n{text}"
                }
            ]
        )
        
        # Extract content from the response
        if hasattr(response, 'content') and len(response.content) > 0:
            for content_block in response.content:
                if hasattr(content_block, 'type') and content_block.type == 'text':
                    return content_block.text
            
            # Fallback to accessing text directly if the above doesn't work
            if hasattr(response.content[0], 'text'):
                return response.content[0].text
            
            return "No text content found in Anthropic API response"
        else:
            return "No content returned from Anthropic API"
            
    except Exception as e:
        logger.error(f"Anthropic API error: {str(e)}")
        raise Exception(f"Anthropic API error: {str(e)}")

async def process_with_anthropic_tools(
    text: str, 
    token: str, 
    tools: Optional[List[Dict[str, Any]]] = None,
    query_context: Optional[str] = None,
    system_prompt: Optional[str] = None,
    model: str = "claude-3-5-sonnet-20241022",
    max_iterations: int = 3
) -> Dict[str, Any]:
    """
    Process text with Anthropic's Claude API using tool calling capabilities.
    
    Args:
        text: The text prompt to send to Claude
        token: Anthropic API token
        tools: Optional list of tool definitions in Claude format (if None, auto-selected)
        query_context: Optional context for automatic tool selection
        system_prompt: Optional system prompt to guide Claude's behavior
        model: Claude model to use
        max_iterations: Maximum number of tool calling iterations
    
    Returns:
        Dictionary with response text and any tool calls made
    """
    logger.info(f"Processing with Anthropic API using tools (model: {model})")
    
    # Auto-select tools if not provided
    if tools is None:
        logger.info("Auto-selecting tools based on query context")
        tools = await get_tools_for_query(query_context or text)
        logger.info(f"Auto-selected {len(tools)} tools")
    
    logger.debug(f"Available tools: {len(tools)}")
    
    # Create Anthropic client with explicit configuration to avoid version conflicts
    try:
        client = AsyncAnthropic(
            api_key=token,
            max_retries=3,
            timeout=60.0
        )
    except Exception as client_error:
        logger.error(f"Error creating Anthropic client: {client_error}")
        # Try with minimal configuration
        client = AsyncAnthropic(api_key=token)
    
    # Initialize conversation
    messages = [
        {
            "role": "user",
            "content": text
        }
    ]
    
    try:
        iteration = 0
        final_response = None
        has_used_tools = False
        tool_calls_made = []
        
        while iteration < max_iterations:
            logger.info(f"Starting iteration {iteration+1}/{max_iterations}")
            
            # Prepare API parameters
            api_params = {
                "model": model,
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0,
            }
            
            # Add system prompt if provided
            if system_prompt:
                api_params["system"] = system_prompt
                
            # Add tools if provided
            if tools and len(tools) > 0:
                api_params["tools"] = tools
                api_params["tool_choice"] = {"type": "auto"}
            
            # Call Claude with tools
            logger.debug(f"Calling Claude with {len(messages)} messages")
            response = await client.messages.create(**api_params)
            
            # Extract the text response
            response_text = ""
            if hasattr(response, 'content') and len(response.content) > 0:
                for content_item in response.content:
                    if hasattr(content_item, 'type') and content_item.type == 'text':
                        response_text += content_item.text
            
            # Check for tool calls in the content
            tool_calls = []
            for idx, content_item in enumerate(response.content):
                if hasattr(content_item, 'type') and content_item.type == 'tool_use':
                    logger.info(f"Found tool_use content: {content_item}")
                    tool_calls.append(content_item)
            
            # If there are no tool calls or we're at max iteration, we're done
            if not tool_calls or iteration == max_iterations - 1:
                logger.info("No tool calls found or max iteration reached, ending conversation")
                final_response = response
                break
            
            # Record tool calls found in this iteration
            for tool_call in tool_calls:
                tool_calls_made.append({
                    "name": tool_call.name,
                    "input": tool_call.input,
                    "id": tool_call.id
                })
                
            has_used_tools = True
            
            # Add the assistant's response with tool calls to the conversation
            assistant_content = []
            for content_item in response.content:
                if hasattr(content_item, 'type') and content_item.type == 'text':
                    assistant_content.append({
                        "type": "text",
                        "text": content_item.text
                    })
                elif hasattr(content_item, 'type') and content_item.type == 'tool_use':
                    assistant_content.append({
                        "type": "tool_use",
                        "id": content_item.id,
                        "name": content_item.name,
                        "input": content_item.input
                    })
            
            assistant_message = {
                "role": "assistant",
                "content": assistant_content
            }
            messages.append(assistant_message)
            
            # Process actual tool calls using the MCP tool system
            tool_result_blocks = []
            for tool_call in tool_calls:
                try:
                    # DEBUG: Log the tool call details
                    logger.info(f"🤖 Claude wants to call tool: {tool_call.name}")
                    logger.info(f"🔧 Tool input from Claude: {tool_call.input}")
                    logger.info(f"🆔 Tool call ID: {tool_call.id}")
                    
                    # Execute the actual tool from our MCP system
                    result_data = await execute_mcp_tool(tool_call.name, tool_call.input)
                    
                    tool_result_blocks.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": json.dumps(result_data)
                    })
                except Exception as e:
                    logger.error(f"Error executing tool {tool_call.name}: {str(e)}")
                    tool_result_blocks.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": json.dumps({
                            "error": f"Error executing tool: {str(e)}",
                            "success": False
                        })
                    })
            
            user_message = {
                "role": "user",
                "content": tool_result_blocks
            }
            messages.append(user_message)
            
            iteration += 1
        
        # Format the final response
        result = {
            "response": response_text,
            "conversation": messages,
            "tool_calls_used": has_used_tools,
            "tool_calls": tool_calls_made,
            "iterations": iteration
        }
        
        logger.info(f"Returning final response after {iteration} iterations")
        return result
        
    except Exception as e:
        logger.error(f"Anthropic API tools error: {str(e)}")
        raise Exception(f"Anthropic API tools error: {str(e)}")

async def execute_mcp_tool(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool by name with given input using the new decorator system.
    
    Args:
        tool_name: Name of the tool to execute
        tool_input: Input parameters for the tool
        
    Returns:
        Dictionary with tool execution result
    """
    try:
        # Import the decorator system
        from ai.tools.decorators import execute_tool
        
        # Execute the tool using the decorator system
        result = await execute_tool(tool_name, **tool_input)
        return result
        
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {str(e)}")
        return {
            "success": False,
            "error": f"Error executing tool: {str(e)}"
        }

async def execute_tools(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute tools via the toolbag system. This is the interface expected by toolbag.py.
    
    Args:
        context: Dictionary containing:
            - tools: List of tool names to execute
            - query: User query
            - prompt: Optional system prompt
            - model: Model to use
            - api_key: Optional API key for authentication
            - previous_result: Previous tool result for chaining
    
    Returns:
        Dictionary with execution results
    """
    try:
        tools = context.get('tools', [])
        query = context.get('query', '')
        prompt = context.get('prompt', '')
        model = context.get('model', 'claude-3-5-sonnet-20241022')
        previous_result = context.get('previous_result')
        
        logger.info(f"Executing tools via Anthropic: {tools}")
        
        # Get API key from context or fall back to environment
        import os
        token = context.get('api_key') or os.environ.get('ANTHROPIC_API_KEY')
        if not token:
            return {
                "success": False,
                "error": "No Anthropic API key provided in request or environment variables"
            }
        
        # Import tool schemas from the tools
        from ai.tools.decorators import get_tool_schemas
        tool_schemas = get_tool_schemas()
        
        # Filter to only the requested tools
        filtered_schemas = [
            schema for schema in tool_schemas 
            if schema['name'] in tools
        ]
        
        if not filtered_schemas:
            return {
                "success": False,
                "error": f"No valid tools found for: {tools}"
            }
        
        # Create system prompt for tool usage with specific URL guidance
        system_prompt = prompt or """You are a web crawler assistant that helps users crawl websites, not a general chatbot.

CRITICAL WORKFLOW:
1. ALWAYS call check_for_odd_user FIRST to determine if the user is trying to chat vs. requesting web crawling
2. If user_is_acting_odd=True: Still call suggest_url with a relevant URL AND provide a friendly response in simple_response_to_users_odd_inquiry explaining this is a web crawler

DETECTING ODD USERS (set user_is_acting_odd=True for):
- ANY greetings: "hello", "hi", "hey", "are you there", "how are you"
- Questions to AI: "can you help me", "what can you do", "who are you"  
- Conversational messages: "hello bot are you there?", "reply to my inquiry"
- General topic questions: "tell me about python", "what's the weather"

EXAMPLES:
- "hello bot are you there?" → user_is_acting_odd=True (this is clearly chatting!)
- "hacker news" → user_is_acting_odd=False (requesting to crawl a site)
- "can you help me?" → user_is_acting_odd=True (asking the AI for help)

URL FORMATTING RULES:
When using suggest_url, you MUST provide complete URLs starting with http:// or https://

CORRECT: "https://news.ycombinator.com/"
INCORRECT: "Hacker News" 

SPECIAL TEST MODE: If query contains "TESTFALLBACK", intentionally return just a site name to test fallback."""
        
        # Build the user query text
        user_text = query
        if previous_result:
            user_text += f"\n\nPrevious result: {json.dumps(previous_result)}"
        
        # Call Anthropic with tools
        result = await process_with_anthropic_tools(
            text=user_text,
            token=token,
            tools=filtered_schemas,
            system_prompt=system_prompt,
            model=model,
            max_iterations=3
        )
        
        return {
            "success": True,
            "provider": "anthropic",
            "model": model,
            "tools_used": tools,
            **result
        }
        
    except Exception as e:
        logger.error(f"Error in execute_tools: {str(e)}")
        
        # Provide more specific error messages for common authentication issues
        error_str = str(e)
        if 'authentication' in error_str.lower() or 'unauthorized' in error_str.lower() or 'invalid api key' in error_str.lower():
            return {
                "success": False,
                "error": "Anthropic API authentication failed - please check your API token is valid and has the necessary permissions",
                "provider": "anthropic"
            }
        elif 'api key' in error_str.lower() and 'not found' in error_str.lower():
            return {
                "success": False,
                "error": "Anthropic API token not found or invalid - please provide a valid API token",
                "provider": "anthropic"
            }
        else:
            return {
                "success": False,
                "error": f"Anthropic API error: {error_str}",
                "provider": "anthropic"
            }

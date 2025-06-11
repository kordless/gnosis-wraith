"""API v2 LLM-powered endpoints for JavaScript execution and content processing."""
import os
import logging
import datetime
from quart import request, jsonify, Response, Blueprint
from core.config import logger
from core.javascript_executor import JavaScriptExecutor
from ai.agents.javascript_agent import JavaScriptAgent
from ai.agents.content_agent import ContentAgent
from ai.validators.javascript_validator import JavaScriptValidator
from web.routes.auth import login_required

# Create v2 LLM API blueprint
api_v2_llm = Blueprint('api_v2_llm', __name__, url_prefix='/api/v2')

# Initialize components
js_executor = JavaScriptExecutor()
js_agent = JavaScriptAgent()
js_validator = JavaScriptValidator()
content_agent = ContentAgent()

@api_v2_llm.route('/execute', methods=['POST'])
@login_required
async def execute_javascript_endpoint():
    """Execute JavaScript code on a webpage.
    
    This endpoint allows direct JavaScript execution with safety validation.
    """
    try:
        data = await request.get_json()
        url = data.get('url')
        javascript = data.get('javascript')
        
        if not url:
            return jsonify({
                "success": False,
                "error": "URL is required"
            }), 400
        
        if not javascript:
            return jsonify({
                "success": False,
                "error": "JavaScript code is required"
            }), 400
        
        # Extract execution options
        options = data.get('options', {})
        wait_before = options.get('wait_before', 2000)
        wait_after = options.get('wait_after', 1000)
        timeout = options.get('timeout', 30000)
        
        # Screenshot options
        take_screenshot = data.get('take_screenshot', False)
        screenshot_options = data.get('screenshot_options', {})
        
        # Markdown extraction options
        extract_markdown = data.get('extract_markdown', False)
        markdown_options = data.get('markdown_options', {})
        
        logger.info(f"JavaScript execution requested for {url} (screenshot: {take_screenshot}, markdown: {extract_markdown})")
        
        # Execute the JavaScript
        result = await js_executor.execute_javascript(
            url=url,
            javascript_code=javascript,
            wait_before=wait_before,
            wait_after=wait_after,
            timeout=timeout,
            take_screenshot=take_screenshot,
            screenshot_options=screenshot_options,
            extract_markdown=extract_markdown,
            markdown_options=markdown_options,
            user_email=request.user_email
        )
        
        # Add metadata to response
        if result['success']:
            result['metadata'] = {
                'timestamp': datetime.datetime.now().isoformat(),
                'processing_time_ms': result.get('execution_time', 0)
            }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"JavaScript execution error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_v2_llm.route('/inject', methods=['POST'])
@login_required
async def inject_javascript_endpoint():
    """Generate and execute JavaScript based on natural language request.
    
    This endpoint uses LLM to generate JavaScript code from a natural language
    description, validates it, and then executes it on the target page.
    """
    try:
        data = await request.get_json()
        url = data.get('url')
        request_text = data.get('request')
        llm_provider = data.get('llm_provider', 'anthropic')
        llm_token = data.get('llm_token')
        llm_model = data.get('llm_model')
        
        if not url:
            return jsonify({
                "success": False,
                "error": "URL is required"
            }), 400
        
        if not request_text:
            return jsonify({
                "success": False,
                "error": "Request description is required"
            }), 400
        
        if not llm_token:
            return jsonify({
                "success": False,
                "error": "LLM token is required"
            }), 400
        
        # Extract options
        execute_immediately = data.get('execute_immediately', True)
        return_code = data.get('return_code', False)
        options = data.get('options', {})
        
        logger.info(f"JavaScript injection requested for {url}: {request_text[:100]}...")
        
        # Generate JavaScript using LLM
        generation_result = await js_agent.generate_javascript(
            request=request_text,
            context={'url': url},
            llm_provider=llm_provider,
            llm_token=llm_token,
            llm_model=llm_model
        )
        
        if not generation_result['success']:
            return jsonify(generation_result), 400
        
        generated_code = generation_result['code']
        safe_code = generation_result['safe_code']
        
        response = {
            "success": True,
            "generated": True,
            "validation": generation_result['validation']
        }
        
        if return_code:
            response['code'] = generated_code
            response['safe_code'] = safe_code
        
        # Execute if requested
        if execute_immediately:
            execution_result = await js_executor.execute_javascript(
                url=url,
                javascript_code=generated_code,
                wait_before=options.get('wait_before', 2000),
                wait_after=options.get('wait_after', 1000),
                timeout=options.get('timeout', 30000),
                user_email=request.user_email
            )
            
            response['execution'] = execution_result
            response['success'] = execution_result['success']
            
            if execution_result['success']:
                response['result'] = execution_result['result']
        
        # Add metadata
        response['metadata'] = {
            'timestamp': datetime.datetime.now().isoformat(),
            'llm_provider': llm_provider,
            'tokens_used': generation_result.get('tokens_used', 0)
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"JavaScript injection error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_v2_llm.route('/validate', methods=['POST'])
@login_required
async def validate_javascript_endpoint():
    """Validate JavaScript code for safety without executing it."""
    try:
        data = await request.get_json()
        javascript = data.get('javascript')
        
        if not javascript:
            return jsonify({
                "success": False,
                "error": "JavaScript code is required"
            }), 400
        
        # Validate the code
        validation_result = js_validator.validate(javascript)
        is_safe, violations = validation_result
        
        response = {
            "success": True,
            "is_safe": is_safe,
            "violations": violations
        }
        
        if is_safe:
            response['safe_code'] = js_validator.sanitize_for_execution(javascript)
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"JavaScript validation error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_v2_llm.route('/suggest', methods=['POST'])
@login_required
async def suggest_code_endpoint():
    """Generate code suggestions for processing extracted content.
    
    This endpoint analyzes extracted content and generates code snippets
    to process it according to the user's goal.
    """
    try:
        data = await request.get_json()
        content = data.get('content')
        goal = data.get('goal')
        output_format = data.get('output_format', 'javascript')
        llm_provider = data.get('llm_provider', 'anthropic')
        llm_token = data.get('llm_token')
        
        if not content:
            return jsonify({
                "success": False,
                "error": "Content is required"
            }), 400
        
        if not goal:
            return jsonify({
                "success": False,
                "error": "Goal description is required"
            }), 400
        
        if not llm_token:
            return jsonify({
                "success": False,
                "error": "LLM token is required"
            }), 400
        
        # Validate output format
        valid_formats = ['javascript', 'python', 'jq']
        if output_format not in valid_formats:
            return jsonify({
                "success": False,
                "error": f"Invalid output format. Must be one of: {valid_formats}"
            }), 400
        
        logger.info(f"Code suggestion requested: {goal[:100]}...")
        
        # TODO: Implement content analysis and code generation
        # This will be implemented with the ContentAgent
        
        return jsonify({
            "success": False,
            "error": "This endpoint is under development"
        }), 501
        
    except Exception as e:
        logger.error(f"Code suggestion error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_v2_llm.route('/interact', methods=['POST'])
@login_required
async def interact_with_page_endpoint():
    """Perform interactive actions on a webpage using JavaScript.
    
    This endpoint allows clicking, scrolling, form filling, and other
    interactions via JavaScript execution.
    """
    try:
        data = await request.get_json()
        url = data.get('url')
        actions = data.get('actions', [])
        
        if not url:
            return jsonify({
                "success": False,
                "error": "URL is required"
            }), 400
        
        if not actions:
            return jsonify({
                "success": False,
                "error": "Actions array is required"
            }), 400
        
        logger.info(f"Page interaction requested for {url}: {len(actions)} actions")
        
        # Build JavaScript for interactions
        js_code = _build_interaction_javascript(actions)
        
        # Validate the generated code
        is_safe, violations = js_validator.validate(js_code)
        if not is_safe:
            return jsonify({
                "success": False,
                "error": "Generated interaction code failed safety validation",
                "violations": violations
            }), 400
        
        # Execute the interactions
        result = await js_executor.execute_javascript(
            url=url,
            javascript_code=js_code,
            wait_before=data.get('wait_before', 2000),
            wait_after=data.get('wait_after', 1000),
            timeout=data.get('timeout', 30000),
            user_email=request.user_email
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Page interaction error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def _build_interaction_javascript(actions: list) -> str:
    """Build JavaScript code for page interactions."""
    js_parts = ["// Page interaction script", "const results = [];"]
    
    for i, action in enumerate(actions):
        action_type = action.get('type')
        selector = action.get('selector')
        
        if action_type == 'click':
            js_parts.append(f"""
// Action {i}: Click element
const element{i} = document.querySelector('{selector}');
if (element{i}) {{
    element{i}.click();
    results.push({{action: {i}, type: 'click', success: true}});
}} else {{
    results.push({{action: {i}, type: 'click', success: false, error: 'Element not found'}});
}}
""")
        elif action_type == 'scroll':
            target = action.get('target', 'bottom')
            if target == 'bottom':
                js_parts.append(f"""
// Action {i}: Scroll to bottom
window.scrollTo(0, document.body.scrollHeight);
results.push({{action: {i}, type: 'scroll', success: true}});
""")
            elif target == 'element':
                js_parts.append(f"""
// Action {i}: Scroll to element
const element{i} = document.querySelector('{selector}');
if (element{i}) {{
    element{i}.scrollIntoView({{behavior: 'smooth'}});
    results.push({{action: {i}, type: 'scroll', success: true}});
}} else {{
    results.push({{action: {i}, type: 'scroll', success: false, error: 'Element not found'}});
}}
""")
        elif action_type == 'fill':
            value = action.get('value', '')
            js_parts.append(f"""
// Action {i}: Fill input
const element{i} = document.querySelector('{selector}');
if (element{i}) {{
    element{i}.value = '{value}';
    element{i}.dispatchEvent(new Event('input', {{bubbles: true}}));
    results.push({{action: {i}, type: 'fill', success: true}});
}} else {{
    results.push({{action: {i}, type: 'fill', success: false, error: 'Element not found'}});
}}
""")
        elif action_type == 'wait':
            duration = action.get('duration', 1000)
            js_parts.append(f"""
// Action {i}: Wait
await new Promise(resolve => setTimeout(resolve, {duration}));
results.push({{action: {i}, type: 'wait', success: true, duration: {duration}}});
""")
    
    js_parts.append("return results;")
    return "\n".join(js_parts)

@api_v2_llm.route('/analyze', methods=['POST'])
@login_required
async def analyze_content_endpoint():
    """Analyze content using LLM for various insights.
    
    This endpoint supports entity extraction, sentiment analysis,
    classification, and custom analysis types.
    """
    try:
        data = await request.get_json()
        content = data.get('content')
        analysis_type = data.get('analysis_type', 'general')
        custom_prompt = data.get('custom_prompt')
        llm_provider = data.get('llm_provider', 'anthropic')
        llm_token = data.get('llm_token')
        llm_model = data.get('llm_model')
        
        if not content:
            return jsonify({
                "success": False,
                "error": "Content is required"
            }), 400
        
        if not llm_token:
            return jsonify({
                "success": False,
                "error": "LLM token is required"
            }), 400
        
        # Validate analysis type
        valid_types = ['entities', 'sentiment', 'classification', 'summary', 
                      'key_facts', 'topics', 'general']
        if analysis_type not in valid_types and not custom_prompt:
            return jsonify({
                "success": False,
                "error": f"Invalid analysis type. Must be one of: {valid_types} or provide custom_prompt"
            }), 400
        
        logger.info(f"Content analysis requested: {analysis_type}")
        
        # Perform analysis
        result = await content_agent.analyze_content(
            content=content,
            analysis_type=analysis_type,
            custom_prompt=custom_prompt,
            llm_provider=llm_provider,
            llm_token=llm_token,
            llm_model=llm_model
        )
        
        # Add metadata
        if result['success']:
            result['metadata'] = {
                'timestamp': datetime.datetime.now().isoformat(),
                'content_length': len(content),
                'analysis_type': analysis_type
            }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Content analysis error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_v2_llm.route('/clean', methods=['POST'])
@login_required
async def clean_markdown_endpoint():
    """Clean and optimize markdown content using LLM.
    
    This endpoint removes unwanted content, fixes formatting,
    and optimizes markdown structure.
    """
    try:
        data = await request.get_json()
        markdown = data.get('markdown')
        goals = data.get('goals', ['remove_ads', 'fix_formatting'])
        preserve = data.get('preserve', ['links', 'images'])
        aggressive = data.get('aggressive', False)
        llm_provider = data.get('llm_provider', 'anthropic')
        llm_token = data.get('llm_token')
        llm_model = data.get('llm_model')
        
        if not markdown:
            return jsonify({
                "success": False,
                "error": "Markdown content is required"
            }), 400
        
        if not llm_token:
            return jsonify({
                "success": False,
                "error": "LLM token is required"
            }), 400
        
        # Validate goals
        valid_goals = ['remove_ads', 'fix_formatting', 'simplify_structure', 
                      'remove_boilerplate', 'fix_links', 'normalize_headers']
        invalid_goals = [g for g in goals if g not in valid_goals]
        if invalid_goals:
            return jsonify({
                "success": False,
                "error": f"Invalid goals: {invalid_goals}. Valid goals: {valid_goals}"
            }), 400
        
        # Validate preserve options
        valid_preserve = ['links', 'images', 'tables', 'code_blocks', 
                         'lists', 'headers', 'emphasis']
        invalid_preserve = [p for p in preserve if p not in valid_preserve]
        if invalid_preserve:
            return jsonify({
                "success": False,
                "error": f"Invalid preserve options: {invalid_preserve}. Valid options: {valid_preserve}"
            }), 400
        
        logger.info(f"Markdown cleanup requested with goals: {goals}")
        
        # Clean the markdown
        result = await content_agent.clean_markdown(
            markdown=markdown,
            goals=goals,
            preserve=preserve,
            llm_provider=llm_provider,
            llm_token=llm_token,
            llm_model=llm_model,
            aggressive=aggressive
        )
        
        # Add metadata
        if result['success']:
            result['metadata'] = {
                'timestamp': datetime.datetime.now().isoformat(),
                'mode': 'aggressive' if aggressive else 'conservative'
            }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Markdown cleanup error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_v2_llm.route('/summarize', methods=['POST'])
@login_required
async def summarize_content_endpoint():
    """Summarize content using LLM.
    
    This endpoint creates various types of summaries from content.
    """
    try:
        data = await request.get_json()
        content = data.get('content')
        summary_type = data.get('summary_type', 'brief')
        max_length = data.get('max_length')
        focus_areas = data.get('focus_areas')
        output_format = data.get('output_format', 'text')
        llm_provider = data.get('llm_provider', 'anthropic')
        llm_token = data.get('llm_token')
        llm_model = data.get('llm_model')
        
        if not content:
            return jsonify({
                "success": False,
                "error": "Content is required"
            }), 400
        
        if not llm_token:
            return jsonify({
                "success": False,
                "error": "LLM token is required"
            }), 400
        
        # Validate summary type
        valid_types = ['brief', 'detailed', 'bullet_points', 'key_facts', 'executive']
        if summary_type not in valid_types:
            return jsonify({
                "success": False,
                "error": f"Invalid summary type. Must be one of: {valid_types}"
            }), 400
        
        # Validate output format
        valid_formats = ['text', 'markdown', 'json']
        if output_format not in valid_formats:
            return jsonify({
                "success": False,
                "error": f"Invalid output format. Must be one of: {valid_formats}"
            }), 400
        
        logger.info(f"Content summarization requested: {summary_type} in {output_format} format")
        
        # Create summary
        result = await content_agent.summarize_content(
            content=content,
            summary_type=summary_type,
            max_length=max_length,
            focus_areas=focus_areas,
            output_format=output_format,
            llm_provider=llm_provider,
            llm_token=llm_token,
            llm_model=llm_model
        )
        
        # Add metadata
        if result['success']:
            result['metadata'] = {
                'timestamp': datetime.datetime.now().isoformat()
            }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Content summarization error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_v2_llm.route('/extract', methods=['POST'])
@login_required
async def extract_structured_data_endpoint():
    """Extract structured data from content using LLM.
    
    This endpoint extracts data according to a provided schema.
    """
    try:
        data = await request.get_json()
        content = data.get('content')
        schema = data.get('schema')
        llm_provider = data.get('llm_provider', 'anthropic')
        llm_token = data.get('llm_token')
        llm_model = data.get('llm_model')
        
        if not content:
            return jsonify({
                "success": False,
                "error": "Content is required"
            }), 400
        
        if not schema:
            return jsonify({
                "success": False,
                "error": "Schema is required"
            }), 400
        
        if not llm_token:
            return jsonify({
                "success": False,
                "error": "LLM token is required"
            }), 400
        
        logger.info(f"Structured data extraction requested")
        
        # Extract data
        result = await content_agent.extract_structured_data(
            content=content,
            schema=schema,
            llm_provider=llm_provider,
            llm_token=llm_token,
            llm_model=llm_model
        )
        
        # Add metadata
        if result['success']:
            result['metadata'] = {
                'timestamp': datetime.datetime.now().isoformat()
            }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Structured data extraction error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
"""Prompts for JavaScript code generation"""
from typing import Dict, Any

def get_javascript_generation_prompt(request: str, context: Dict[str, Any]) -> str:
    """
    Generate a prompt for JavaScript code generation based on the request.
    
    Args:
        request: Natural language description of what the JavaScript should do
        context: Additional context (URL, page info, etc.)
        
    Returns:
        Formatted prompt for LLM
    """
    url = context.get('url', 'the current page')
    
    prompt = f"""You are a JavaScript expert tasked with generating safe, efficient JavaScript code that will be executed in a web browser.

USER REQUEST: {request}

TARGET PAGE: {url}

REQUIREMENTS:
1. Generate JavaScript code that fulfills the user's request
2. The code must be safe and not perform any malicious actions
3. Use only browser-safe JavaScript (no Node.js specific features)
4. Focus on DOM manipulation and data extraction
5. Return results in a structured format when possible
6. Handle errors gracefully
7. Do not make external network requests
8. Do not modify cookies, localStorage, or sessionStorage
9. Do not submit forms or change page location
10. Include helpful comments explaining what the code does

ALLOWED OPERATIONS:
- Select DOM elements (querySelector, querySelectorAll, etc.)
- Read element properties (textContent, href, src, attributes)
- Process and transform data (map, filter, reduce)
- Create structured data objects
- Console logging for debugging
- Basic mathematical operations
- String and array manipulations

OUTPUT FORMAT:
Return only the JavaScript code without any explanation or markdown formatting.
The code should be ready to execute and return a result.

Example structure:
// Description of what this code does
const elements = document.querySelectorAll('selector');
const result = Array.from(elements).map(el => ({
    property: el.textContent
}));
return result;

Now generate JavaScript code for the user's request:"""
    
    return prompt

def get_code_analysis_prompt(code: str, goal: str) -> str:
    """
    Generate a prompt for analyzing and improving existing JavaScript code.
    """
    return f"""Analyze the following JavaScript code and suggest improvements to better achieve the stated goal.

GOAL: {goal}

CODE:
{code}

Please provide:
1. Analysis of what the current code does
2. Potential issues or limitations
3. Improved version of the code
4. Explanation of the improvements

Focus on safety, efficiency, and correctness."""

def get_extraction_prompt(html_sample: str, extraction_goal: str) -> str:
    """
    Generate a prompt for creating JavaScript to extract specific data from HTML.
    """
    return f"""Given the following HTML structure, generate JavaScript code to extract the requested data.

EXTRACTION GOAL: {extraction_goal}

HTML SAMPLE:
{html_sample[:2000]}  # Limit sample size

Generate JavaScript code that:
1. Identifies the correct selectors for the target data
2. Extracts the data in a structured format
3. Handles cases where elements might be missing
4. Returns a clean, organized result

The code should be defensive and handle edge cases gracefully."""
"""
Code generation using multiple LLM providers
"""
import asyncio
import json
from typing import Dict, Any

async def generate_code(query: str, language: str, provider: str, api_key: str, options: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate code using specified LLM provider
    """
    try:
        # Build prompt based on language and options
        prompt = build_code_prompt(query, language, options)
        
        # Route to appropriate provider
        if provider == 'anthropic':
            return await generate_with_anthropic(prompt, api_key, options)
        elif provider == 'openai':
            return await generate_with_openai(prompt, api_key, options)
        elif provider == 'gemini':
            return await generate_with_gemini(prompt, api_key, options)
        else:
            return {
                'success': False,
                'error': f'Unsupported provider: {provider}'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f'Code generation failed: {str(e)}'
        }

def build_code_prompt(query: str, language: str, options: Dict[str, Any]) -> str:
    """Build appropriate prompt for code generation"""
    
    comments_level = options.get('comments_level', 2)
    include_error_handling = options.get('include_error_handling', True)
    
    # Map numeric comments level to text
    comments_map = {
        1: 'minimal',
        2: 'standard',
        3: 'extensive'
    }
    comments_text = comments_map.get(comments_level, 'standard')
    
    prompt = f"""Generate {language} code for the following requirement:

{query}

Requirements:
- Language: {language}
- Comments level: {comments_text} (minimal=few comments, standard=important comments, extensive=detailed comments)
- Error handling: {'Include' if include_error_handling else 'Exclude'} error handling
- Write clean, production-ready code
- Include relevant imports and dependencies

Return only the code without explanations."""

    return prompt

async def generate_with_anthropic(prompt: str, api_key: str, options: Dict[str, Any]) -> Dict[str, Any]:
    """Generate code using Anthropic Claude API"""
    try:
        # Import Anthropic client
        from anthropic import AsyncAnthropic
        
        client = AsyncAnthropic(api_key=api_key)
        
        # Call Claude API
        response = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            temperature=0.7,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract code from response
        if response.content and len(response.content) > 0:
            code = response.content[0].text
            return {
                'success': True,
                'code': code
            }
        else:
            return {
                'success': False,
                'error': 'No code generated'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f'Anthropic generation failed: {str(e)}'
        }

async def generate_with_openai(prompt: str, api_key: str, options: Dict[str, Any]) -> Dict[str, Any]:
    """Generate code using OpenAI GPT API"""
    try:
        # Import OpenAI client
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=api_key)
        
        # Call OpenAI API
        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        
        # Extract code from response
        if response.choices and len(response.choices) > 0:
            code = response.choices[0].message.content
            return {
                'success': True,
                'code': code
            }
        else:
            return {
                'success': False,
                'error': 'No code generated'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f'OpenAI generation failed: {str(e)}'
        }

async def generate_with_gemini(prompt: str, api_key: str, options: Dict[str, Any]) -> Dict[str, Any]:
    """Generate code using Google Gemini API"""
    try:
        # Import Google Generative AI client
        import google.generativeai as genai
        
        # Configure API key
        genai.configure(api_key=api_key)
        
        # Create model
        model = genai.GenerativeModel('gemini-pro')
        
        # Generate content
        response = await model.generate_content_async(prompt)
        
        # Extract code from response
        if response.text:
            return {
                'success': True,
                'code': response.text
            }
        else:
            return {
                'success': False,
                'error': 'No code generated'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f'Gemini generation failed: {str(e)}'
        }
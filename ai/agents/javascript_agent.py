"""JavaScript generation and execution agent"""
import json
import asyncio
from typing import Dict, Any, Optional
from ai.validators.javascript_validator import JavaScriptValidator
from ai.validators.safety_checker import SafetyChecker
from ai.prompts.javascript_injection import get_javascript_generation_prompt

class JavaScriptAgent:
    """Agent for generating and validating JavaScript code"""
    
    def __init__(self):
        self.validator = JavaScriptValidator()
        self.safety_checker = SafetyChecker()
    
    async def generate_javascript(
        self, 
        request: str, 
        context: Dict[str, Any], 
        llm_provider: str,
        llm_token: str,
        llm_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate JavaScript code based on natural language request.
        
        Args:
            request: Natural language description of what the JavaScript should do
            context: Additional context (URL, page info, etc.)
            llm_provider: LLM provider to use (anthropic, openai, gemini)
            llm_token: API token for the LLM provider
            llm_model: Optional specific model to use
            
        Returns:
            Dict with success status, generated code, and validation results
        """
        try:
            # Sanitize the request
            sanitized_request = self.safety_checker.sanitize_llm_input(request)
            
            # Build the prompt
            prompt = get_javascript_generation_prompt(sanitized_request, context)
            
            # Generate code using the appropriate provider
            if llm_provider == 'anthropic':
                code = await self._generate_with_anthropic(prompt, llm_token, llm_model)
            elif llm_provider == 'openai':
                code = await self._generate_with_openai(prompt, llm_token, llm_model)
            elif llm_provider == 'gemini':
                code = await self._generate_with_gemini(prompt, llm_token, llm_model)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported LLM provider: {llm_provider}'
                }
            
            # Validate the generated code
            is_safe, violations = self.validator.validate(code)
            
            if not is_safe:
                return {
                    'success': False,
                    'error': 'Generated code failed safety validation',
                    'violations': violations,
                    'code': code  # Include for debugging
                }
            
            # Wrap code for safe execution
            safe_code = self.validator.sanitize_for_execution(code)
            
            return {
                'success': True,
                'code': code,
                'safe_code': safe_code,
                'validation': {
                    'is_safe': is_safe,
                    'violations': violations
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'JavaScript generation failed: {str(e)}'
            }
    
    async def _generate_with_anthropic(
        self, 
        prompt: str, 
        api_key: str,
        model: Optional[str] = None
    ) -> str:
        """Generate code using Anthropic Claude"""
        from anthropic import AsyncAnthropic
        
        client = AsyncAnthropic(api_key=api_key)
        
        response = await client.messages.create(
            model=model or "claude-3-5-sonnet-20241022",
            max_tokens=4000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Extract code from response
        code = response.content[0].text
        
        # Try to extract code block if present
        if '```javascript' in code:
            code = code.split('```javascript')[1].split('```')[0].strip()
        elif '```js' in code:
            code = code.split('```js')[1].split('```')[0].strip()
        elif '```' in code:
            # Generic code block
            parts = code.split('```')
            if len(parts) >= 3:
                code = parts[1].strip()
        
        return code
    
    async def _generate_with_openai(
        self, 
        prompt: str, 
        api_key: str,
        model: Optional[str] = None
    ) -> str:
        """Generate code using OpenAI GPT"""
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=api_key)
        
        response = await client.chat.completions.create(
            model=model or "gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=4000
        )
        
        code = response.choices[0].message.content
        
        # Extract code block if present
        if '```javascript' in code:
            code = code.split('```javascript')[1].split('```')[0].strip()
        elif '```js' in code:
            code = code.split('```js')[1].split('```')[0].strip()
        elif '```' in code:
            parts = code.split('```')
            if len(parts) >= 3:
                code = parts[1].strip()
        
        return code
    
    async def _generate_with_gemini(
        self, 
        prompt: str, 
        api_key: str,
        model: Optional[str] = None
    ) -> str:
        """Generate code using Google Gemini"""
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model or 'gemini-pro')
        
        response = await model.generate_content_async(prompt)
        code = response.text
        
        # Extract code block if present
        if '```javascript' in code:
            code = code.split('```javascript')[1].split('```')[0].strip()
        elif '```js' in code:
            code = code.split('```js')[1].split('```')[0].strip()
        elif '```' in code:
            parts = code.split('```')
            if len(parts) >= 3:
                code = parts[1].strip()
        
        return code
    
    def validate_code(self, code: str) -> Dict[str, Any]:
        """
        Validate JavaScript code without generating it.
        
        Args:
            code: JavaScript code to validate
            
        Returns:
            Validation results
        """
        is_safe, violations = self.validator.validate(code)
        
        return {
            'is_safe': is_safe,
            'violations': violations,
            'safe_code': self.validator.sanitize_for_execution(code) if is_safe else None
        }
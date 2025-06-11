# Claude Code Task: Phase 3 - Connect Code Generation to LLM APIs

## Previous Phases Completed
✅ **Phase 1**: Custom token management removed from forge.html (was already clean)
✅ **Phase 2**: Unified token management components integrated into Forge
- Added TokenStatusButton with color-coded brain icon
- Added TokenManagerModal for professional token management  
- Added shared state with main crawler interface
- Forge now has same token UI as main crawler

## Current State
The Forge now has proper token management UI, but the code generation functionality is not connected to the actual LLM APIs. The "Generate" button currently doesn't produce real AI-generated code.

## Your Mission: Phase 3 - Connect Code Generation to LLMs

### Target Files
- `gnosis_wraith/server/templates/forge.html` (frontend)
- `gnosis_wraith/server/routes/api.py` (backend endpoint)

### Problem to Solve
Currently the Forge has:
- ✅ Professional token management UI
- ✅ Code generation form (language selection, options)
- ❌ No connection between "Generate" button and actual LLM APIs
- ❌ No backend endpoint for code generation

### Step 1: Update Frontend Code Generation Logic

Find the `handleGenerateCode` function in `forge.html` and replace it with:

```javascript
const handleGenerateCode = async () => {
  if (!inputValue.trim() || authStatus !== 'authorized') return;
  
  setIsGenerating(true);
  setGeneratedCode('// Generating code...');
  
  try {
    // Get current provider and token from unified token system
    const provider = localStorage.getItem('gnosis_wraith_llm_provider') || 'anthropic';
    const cookieName = `gnosis_wraith_llm_token_${provider}`;
    
    // Use the same CookieUtils that other components use
    const apiKey = CookieUtils.getCookie(cookieName);
    
    if (!apiKey) {
      setGeneratedCode('# Error: No API token configured for ' + provider + '\n# Please click the brain icon to configure your API token.');
      setIsTokenModalOpen(true); // Auto-open token modal
      return;
    }
    
    // Make API call to new code generation endpoint
    const response = await fetch('/api/code-generation', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query: inputValue,
        language: selectedLanguage === 'custom' ? customLanguage : selectedLanguage,
        provider: provider,
        api_key: apiKey,
        options: {
          comments_level: commentsLevel,
          include_error_handling: includeErrorHandling,
          custom_parameters: customParameters
        }
      })
    });
    
    if (response.ok) {
      const result = await response.json();
      if (result.success && result.code) {
        setGeneratedCode(result.code);
      } else {
        setGeneratedCode('# Error: ' + (result.error || 'Failed to generate code'));
      }
    } else {
      const errorText = await response.text();
      setGeneratedCode('# Error: HTTP ' + response.status + ' - ' + errorText);
    }
    
  } catch (error) {
    setGeneratedCode('# Error: Request failed - ' + error.message);
  } finally {
    setIsGenerating(false);
    setInputValue('');
  }
};
```

### Step 2: Create Backend Code Generation Endpoint

Add this new endpoint to `gnosis_wraith/server/routes/api.py`:

```python
@api_bp.route('/code-generation', methods=['POST'])
async def code_generation():
    """Generate code using LLM APIs based on user requirements."""
    try:
        data = await request.get_json()
        
        # Extract request parameters
        query = data.get('query', '').strip()
        language = data.get('language', 'python')
        provider = data.get('provider', 'anthropic')
        api_key = data.get('api_key', '')
        options = data.get('options', {})
        
        # Validate inputs
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query is required'
            }), 400
            
        if not api_key:
            return jsonify({
                'success': False,
                'error': f'API key is required for provider: {provider}'
            }), 400
        
        # Import AI helper (reuse existing anthropic.py or create new module)
        from gnosis_wraith.ai.code_generator import generate_code
        
        # Generate code using specified provider
        result = await generate_code(
            query=query,
            language=language,
            provider=provider,
            api_key=api_key,
            options=options
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'code': result['code'],
                'language': language,
                'provider': provider
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        logger.error(f"Code generation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500
```

### Step 3: Create Code Generation Module

Create new file `gnosis_wraith/ai/code_generator.py`:

```python
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
    
    comments_level = options.get('comments_level', 'STD')
    include_error_handling = options.get('include_error_handling', True)
    
    prompt = f"""Generate {language} code for the following requirement:

{query}

Requirements:
- Language: {language}
- Comments level: {comments_level} (MIN=minimal, STD=standard, MAX=extensive)
- Error handling: {'Include' if include_error_handling else 'Exclude'} error handling
- Write clean, production-ready code
- Include relevant imports and dependencies

Return only the code without explanations."""

    return prompt

async def generate_with_anthropic(prompt: str, api_key: str, options: Dict[str, Any]) -> Dict[str, Any]:
    """Generate code using Anthropic Claude API"""
    try:
        # Reuse existing anthropic integration from gnosis_wraith.ai.anthropic
        from gnosis_wraith.ai.anthropic import get_anthropic_response
        
        response = await get_anthropic_response(prompt, api_key)
        
        if response and response.get('success'):
            return {
                'success': True,
                'code': response.get('content', '# No code generated')
            }
        else:
            return {
                'success': False,
                'error': response.get('error', 'Anthropic API error')
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f'Anthropic generation failed: {str(e)}'
        }

async def generate_with_openai(prompt: str, api_key: str, options: Dict[str, Any]) -> Dict[str, Any]:
    """Generate code using OpenAI GPT API"""
    # TODO: Implement OpenAI integration
    return {
        'success': False,
        'error': 'OpenAI integration not yet implemented'
    }

async def generate_with_gemini(prompt: str, api_key: str, options: Dict[str, Any]) -> Dict[str, Any]:
    """Generate code using Google Gemini API"""
    # TODO: Implement Gemini integration  
    return {
        'success': False,
        'error': 'Gemini integration not yet implemented'
    }
```

## Expected Behavior After Implementation

1. **User enters code requirement** in Forge input field
2. **Clicks Generate button** → Shows "Generating code..."
3. **System checks for API token** → Opens modal if missing
4. **Makes API call** to `/api/code-generation` with current provider token
5. **Backend routes to appropriate LLM** (Claude, GPT, or Gemini)
6. **Returns generated code** in syntax-highlighted display
7. **User can copy or download** the generated code

## Success Criteria

1. ✅ Generate button connects to real LLM APIs
2. ✅ Code generation works with Anthropic Claude (primary)
3. ✅ Error handling for missing/invalid tokens
4. ✅ Generated code appears in syntax-highlighted display
5. ✅ Language selection affects code generation prompts
6. ✅ Options (comments level, error handling) influence output
7. ✅ Integration works with unified token management system

## Reference Files to Examine

- `gnosis_wraith/ai/anthropic.py` - Existing Anthropic API integration
- `gnosis_wraith/server/routes/api.py` - API endpoint patterns
- `gnosis_wraith/server/templates/index.html` - How main app uses tokens

This phase transforms the Forge from a UI mockup into a fully functional AI-powered code generation tool.
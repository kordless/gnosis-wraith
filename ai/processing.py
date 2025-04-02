import logging
from typing import Optional

from .anthropic import process_with_anthropic
from .openai import process_with_openai
from .gemini import process_with_gemini
from .ollama import process_with_ollama

# Get logger from config
logger = logging.getLogger("gnosis_wraith")

async def process_with_llm(text: str, provider: str, token: Optional[str] = None):
    """Process text with the specified LLM provider."""
    if provider != 'local' and not token:
        logger.warning(f"No token provided for {provider}")
        return None
    
    # Truncate text if too long (APIs typically have context limits)
    max_length = 8000  # Conservative limit that works for most APIs
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    logger.info(f"Processing text with {provider} LLM")
    
    try:
        if provider == 'anthropic':
            return await process_with_anthropic(text, token)
        elif provider == 'openai':
            return await process_with_openai(text, token)
        elif provider == 'gemini':
            return await process_with_gemini(text, token)
        elif provider == 'local':
            return await process_with_ollama(text)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    except Exception as e:
        logger.error(f"Error in LLM processing with {provider}: {str(e)}")
        raise
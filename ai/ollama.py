import logging
import requests

# Get logger from config
logger = logging.getLogger("gnosis_wraith")

async def process_with_ollama(text, model_name="mistral"):
    """Process text with a local Ollama model."""
    try:
        url = "http://localhost:11434/api/generate"
        
        # CPU-only configuration after GPU removal
        payload = {
            "model": model_name,
            "prompt": f"Analyze and summarize the following web content. Focus on key information and main points:\n\n{text}",
            "stream": False,
            "options": {
                "num_gpu": 0,
                "num_thread": 8  # Use CPU threads
            }
        }
        
        logger.info(f"Processing text with local {model_name} model (CPU mode)")
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            return result.get('response', "No response from local model")
        else:
            return f"Error from Ollama API: {response.status_code}"
    except Exception as e:
        logger.error(f"Error with local Ollama model: {str(e)}")
        raise

def set_ollama_gpu():
    """Configure Ollama to use GPU - DEPRECATED."""
    # GPU support removed along with CUDA/PyTorch dependencies
    logger.info("GPU configuration removed - Ollama will use CPU mode")
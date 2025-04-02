import logging
import requests
import torch

# Get logger from config
logger = logging.getLogger("webwraith")

async def process_with_ollama(text, model_name="mistral"):
    """Process text with a local Ollama model using GPU if available."""
    try:
        # Configure model based on GPU availability
        use_gpu = torch.cuda.is_available()
        
        url = "http://localhost:11434/api/generate"
        
        # Add GPU configuration if available
        payload = {
            "model": model_name,
            "prompt": f"Analyze and summarize the following web content. Focus on key information and main points:\n\n{text}",
            "stream": False,
            "options": {
                "num_gpu": 1 if use_gpu else 0,
                "num_thread": 8 if not use_gpu else 4  # Use more CPU threads if no GPU
            }
        }
        
        logger.info(f"Processing text with local {model_name} model (GPU: {use_gpu})")
        
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
    """Configure Ollama to use GPU if available."""
    try:
        if torch.cuda.is_available():
            import os
            os.environ["OLLAMA_HOST"] = "localhost:11434"
            os.environ["OLLAMA_USE_GPU"] = "1"
            logger.info("Configured Ollama to use GPU")
    except Exception as e:
        logger.error(f"Failed to configure Ollama GPU: {str(e)}")
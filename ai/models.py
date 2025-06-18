import os
import logging

# Get logger from config
logger = logging.getLogger("gnosis_wraith")

class ModelManager:
    """Manages and selects AI models for different tasks."""
    
    def __init__(self):
        """Initialize the model manager."""
        self.local_models = {}
        self.remote_providers = {}
        # OCR functionality has been removed from the project
    
    async def extract_text_from_image(self, image_path):
        """Extract text from an image using OCR - DEPRECATED."""
        logger.warning("OCR functionality has been removed from Gnosis Wraith")
        return "OCR functionality has been removed. Please use a dedicated OCR service."
    
    def set_ollama_gpu(self):
        """Configure Ollama to use GPU if available - DEPRECATED."""
        # GPU support removed along with CUDA/PyTorch dependencies
        logger.info("GPU configuration removed - Ollama will use default settings")
    
    def get_model_for_task(self, task, provider=None):
        """Get the appropriate model for a given task."""
        # This would be extended with actual model selection logic
        pass
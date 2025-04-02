import os
import logging
import torch
from PIL import Image

# Get logger from config
logger = logging.getLogger("webwraith")

class ModelManager:
    """Manages and selects AI models for different tasks."""
    
    def __init__(self):
        """Initialize the model manager."""
        self.local_models = {}
        self.remote_providers = {}
        self.ocr_reader = None
        self._initialize_ocr()
    
    def _initialize_ocr(self):
        """Initialize EasyOCR for text extraction with GPU if available."""
        try:
            # Import these here to handle potential import errors gracefully
            import numpy as np
            import easyocr
            
            # First check if CUDA is available
            use_gpu = torch.cuda.is_available()
            
            if use_gpu:
                try:
                    # Try initializing with GPU first
                    self.ocr_reader = easyocr.Reader(['en'], gpu=True)
                    logger.info("✅ EasyOCR initialized with GPU acceleration")
                except Exception as gpu_error:
                    # If GPU initialization fails, fall back to CPU
                    logger.warning(f"⚠️ GPU initialization failed: {str(gpu_error)}")
                    logger.warning("⚠️ Falling back to CPU mode for EasyOCR")
                    self.ocr_reader = easyocr.Reader(['en'], gpu=False)
                    logger.info("✅ EasyOCR initialized in CPU mode")
            else:
                # CPU mode
                self.ocr_reader = easyocr.Reader(['en'], gpu=False)
                logger.info("⚠️ EasyOCR initialized without GPU acceleration (CPU only)")
                
        except ImportError as e:
            logger.error(f"❌ Failed to initialize EasyOCR: Missing dependency: {str(e)}")
            logger.error("Please ensure numpy and easyocr are properly installed")
            self.ocr_reader = None
        except Exception as e:
            logger.error(f"❌ Failed to initialize EasyOCR: {str(e)}")
            self.ocr_reader = None
    
    async def extract_text_from_image(self, image_path):
        """Extract text from an image using OCR."""
        if not self.ocr_reader:
            self._initialize_ocr()
            if not self.ocr_reader:
                return "Text extraction failed: OCR reader not available. Check dependencies."
                
        try:
            import time
            import numpy as np
            
            # Use a timer to measure OCR performance
            start_time = time.time()
            
            image = Image.open(image_path)
            image_np = np.array(image)
            results = self.ocr_reader.readtext(image_np)
            extracted_text = ' '.join([result[1] for result in results])
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            logger.info(f"Extracted {len(results)} text regions from {image_path} in {processing_time:.2f} seconds")
            
            return extracted_text
        except ImportError as e:
            logger.error(f"Error extracting text - missing dependency: {str(e)}")
            return f"Text extraction failed: Missing dependency: {str(e)}"
        except Exception as e:
            logger.error(f"Error extracting text from image: {str(e)}")
            return f"Text extraction failed: {str(e)}"
    
    def set_ollama_gpu(self):
        """Configure Ollama to use GPU if available."""
        try:
            if torch.cuda.is_available():
                os.environ["OLLAMA_HOST"] = "localhost:11434"
                os.environ["OLLAMA_USE_GPU"] = "1"
                logger.info("Configured Ollama to use GPU")
        except Exception as e:
            logger.error(f"Failed to configure Ollama GPU: {str(e)}")
    
    def get_model_for_task(self, task, provider=None):
        """Get the appropriate model for a given task."""
        # This would be extended with actual model selection logic
        pass
import os
import logging
import sys
from pathlib import Path

# Configuration
STORAGE_PATH = os.environ.get('GNOSIS_WRAITH_STORAGE_PATH', os.path.join(os.path.expanduser("~"), ".gnosis-wraith"))
SCREENSHOTS_DIR = os.path.join(STORAGE_PATH, "screenshots")
REPORTS_DIR = os.path.join(STORAGE_PATH, "reports")
DATA_DIR = os.path.join(STORAGE_PATH, "data")  # Added dedicated data directory
LOG_FILE = os.path.join(STORAGE_PATH, "gnosis-wraith.log")

# Ensure directories exist
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)  # Create data directory
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Update environment variables for access in other modules
os.environ['GNOSIS_WRAITH_SCREENSHOTS_DIR'] = SCREENSHOTS_DIR
os.environ['GNOSIS_WRAITH_REPORTS_DIR'] = REPORTS_DIR
os.environ['GNOSIS_WRAITH_DATA_DIR'] = DATA_DIR  # Add environment variable for data directory

# Setup logging
logger = logging.getLogger("gnosis_wraith")
logger.setLevel(logging.INFO)

c_handler = logging.StreamHandler()
f_handler = logging.FileHandler(LOG_FILE)
c_handler.setLevel(logging.INFO)  # Changed from WARNING to INFO
f_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
c_handler.setFormatter(formatter)
f_handler.setFormatter(formatter)

logger.addHandler(c_handler)
logger.addHandler(f_handler)

# Lightning Network configuration
LIGHTNING_ENABLED = os.environ.get('GNOSIS_WRAITH_LIGHTNING_ENABLED', 'false').lower() == 'true'
LIGHTNING_NODE_URL = os.environ.get('GNOSIS_WRAITH_LIGHTNING_NODE_URL', 'localhost:10009')

# AI configuration
DEFAULT_AI_PROVIDER = os.environ.get('GNOSIS_WRAITH_DEFAULT_AI', 'local')

def check_gpu_availability():
    """Check if GPU is available for acceleration."""
    try:
        import torch
        gpu_available = torch.cuda.is_available()
        if gpu_available:
            device_name = torch.cuda.get_device_name(0)
            logger.info(f"GPU available: {device_name}")
            return True
        else:
            logger.info("No GPU available, using CPU only")
            return False
    except Exception as e:
        logger.warning(f"Error checking GPU availability: {str(e)}")
        return False
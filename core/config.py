import os
import logging
import sys
from pathlib import Path

# Storage configuration now handled by storage_service.py
# Only keep logging configuration here
STORAGE_PATH = os.environ.get('STORAGE_PATH', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'storage'))
LOGS_DIR = os.path.join(STORAGE_PATH, "logs")
LOG_FILE = os.path.join(LOGS_DIR, "gnosis-wraith.log")

# Compatibility shims for old code that expects these paths
# These are deprecated - use storage_service.py instead
SCREENSHOTS_DIR = os.path.join(STORAGE_PATH, "screenshots")
REPORTS_DIR = os.path.join(STORAGE_PATH, "reports")

# Ensure only logs directory exists
os.makedirs(LOGS_DIR, exist_ok=True)



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
    """Check if GPU is available for acceleration - DEPRECATED."""
    # GPU support removed along with CUDA/PyTorch dependencies
    logger.info("GPU support has been removed from Gnosis Wraith")
    return False
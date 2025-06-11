# Routes package initialization
from quart import Blueprint

# Create blueprints for different route groups
api_bp = Blueprint('api', __name__, url_prefix='/api')
pages_bp = Blueprint('pages', __name__)

# Import route modules to register their routes with the blueprints
from . import api
from . import pages
from . import extension

# Import the direct blueprint from api.py
from .api import direct_bp

# Import v2 API blueprint
try:
    from .api_v2 import api_v2
    v2_available = True
except ImportError:
    v2_available = False

# Import v2 LLM API blueprint
try:
    from .api_v2_llm import api_v2_llm
    v2_llm_available = True
except ImportError:
    v2_llm_available = False

# Function to register all blueprints with the app
def register_blueprints(app):
    """Register all blueprints with the given Quart app."""
    app.register_blueprint(api_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(direct_bp)  # Register the direct routes blueprint
    
    # Register v2 API if available
    if v2_available:
        app.register_blueprint(api_v2)
    
    # Register v2 LLM API if available
    if v2_llm_available:
        app.register_blueprint(api_v2_llm)
    
    # Register extension blueprint separately
    extension.register_extension_blueprint(app)
    
    # Log registered blueprints for debugging
    from core.config import logger
    blueprints = "api, pages, direct, and extension"
    if v2_available:
        blueprints += ", api_v2"
    if v2_llm_available:
        blueprints += ", api_v2_llm"
    logger.info(f"Registered blueprints: {blueprints}")
    
    # Log registered routes for debugging
    for rule in app.url_map.iter_rules():
        logger.info(f"Registered route: {rule.endpoint} -> {rule.rule}")

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

# Function to register all blueprints with the app
def register_blueprints(app):
    """Register all blueprints with the given Quart app."""
    app.register_blueprint(api_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(direct_bp)  # Register the direct routes blueprint
    
    # Register extension blueprint separately
    extension.register_extension_blueprint(app)
    
    # Log registered blueprints for debugging
    from server.config import logger
    logger.info(f"Registered blueprints: api, pages, direct, and extension")
    
    # Log registered routes for debugging
    for rule in app.url_map.iter_rules():
        logger.info(f"Registered route: {rule.endpoint} -> {rule.rule}")
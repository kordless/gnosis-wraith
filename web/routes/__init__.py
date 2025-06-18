# Routes package initialization
from quart import Blueprint

# DISABLED OLD API FILES - Now using apis/api.py instead
# The following imports are commented out to disable the old API routes:
# from . import api  # DISABLED - using apis/api.py instead
# from . import api_v2  # DISABLED - functionality moved to apis/api.py
# from . import api_v2_llm  # DISABLED - functionality moved to apis/api.py

# Create the pages blueprint here to avoid circular import
pages_bp = Blueprint('pages', __name__)

# Import the NEW API blueprint from apis subdirectory
from .apis.api import api_bp as new_api_bp

# Import the aliases blueprint
from .apis.aliases import alias_bp

# Import auth blueprint
from .auth import auth

# Import route modules after blueprint creation to register routes
from . import pages  # This will now use the pages_bp created above
from . import extension

# Function to register all blueprints with the app
def register_blueprints(app):
    """Register all blueprints with the given Quart app."""
    # Register the NEW API blueprint from apis/api.py
    app.register_blueprint(new_api_bp)
    
    # Register the aliases for backward compatibility
    app.register_blueprint(alias_bp)
    
    # Register other blueprints we're keeping
    app.register_blueprint(pages_bp)
    # NOTE: auth blueprint is registered directly in app.py, not here

    
    # Register extension blueprint separately
    extension.register_extension_blueprint(app)
    
    # Log registered blueprints for debugging
    from core.config import logger
    logger.info("Registered blueprints: new API (from apis/api.py), aliases, pages, auth, and extension")
    logger.info("DISABLED: old api.py, api_v2.py, and api_v2_llm.py")
    
    # Log registered routes for debugging
    for rule in app.url_map.iter_rules():
        logger.info(f"Registered route: {rule.endpoint} -> {rule.rule}")

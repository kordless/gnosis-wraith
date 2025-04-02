# Routes package initialization
from quart import Blueprint

# Create blueprints for different route groups
api_bp = Blueprint('api', __name__, url_prefix='/api')
pages_bp = Blueprint('pages', __name__)

# Import route modules to register their routes with the blueprints
from . import api
from . import pages

# Function to register all blueprints with the app
def register_blueprints(app):
    """Register all blueprints with the given Quart app."""
    app.register_blueprint(api_bp)
    app.register_blueprint(pages_bp)
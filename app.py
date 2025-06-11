"""
Gnosis Wraith Server Application - Main Entry Point
"""
import os
import sys
from quart import Quart
from quart_cors import cors

# Import configuration and logging
from core.config import logger, STORAGE_PATH

# Import route registration
from web.routes import register_blueprints

# Import auth blueprint and decorator
from web.routes.auth import auth, login_required

# Import initializers
from core.initializers import init_job_system

# Environment detection for dev features
IS_DEVELOPMENT = os.getenv('ENVIRONMENT', 'development') == 'development'
ENABLE_DEV_ENDPOINTS = os.getenv('ENABLE_DEV_ENDPOINTS', 'false').lower() == 'true'

# Create Quart app with correct static and template paths
app = Quart(__name__, 
           static_folder='web/static', 
           template_folder='web/templates')

# Set secret key for sessions
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Configure app
app.config['BRAND'] = os.environ.get('BRAND', 'Gnosis Wraith')
app.config['BRAND_FAVICON'] = os.environ.get('BRAND_FAVICON', '/static/images/favicon.ico')
app.config['BRAND_COLOR'] = os.environ.get('BRAND_COLOR', '#6c63ff')
app.config['BRAND_SERVICE'] = os.environ.get('BRAND_SERVICE', 'Gnosis Wraith')
app.config['BRAND_SERVICE_URL'] = os.environ.get('BRAND_SERVICE_URL', 'https://gnosis-wraith.com')
app.config['BRAND_GITHUB_URL'] = os.environ.get('BRAND_GITHUB_URL', 'https://github.com/gnosis-wraith')
app.config['BRAND_DISCORD_URL'] = os.environ.get('BRAND_DISCORD_URL', '')
app.config['BRAND_YOUTUBE_URL'] = os.environ.get('BRAND_YOUTUBE_URL', '')
app.config['APP_DOMAIN'] = os.environ.get('APP_DOMAIN', 'localhost:5678')

# Enable CORS
app = cors(app, allow_origin="*")

# Register auth blueprint
app.register_blueprint(auth, url_prefix='/auth')

# Register all other blueprints
register_blueprints(app)

# Register dev blueprint only in development
if IS_DEVELOPMENT and ENABLE_DEV_ENDPOINTS:
    from web.routes.dev import dev_bp
    app.register_blueprint(dev_bp)
    logger.info("Development endpoints enabled at /dev/*")

# Initialize job system
init_job_system(app)

# Health check endpoint for Google Cloud Run
@app.route('/health')
async def health_check():
    """Health check endpoint"""
    return {'status': 'healthy', 'service': 'gnosis-wraith'}, 200

# Test protected endpoint
@app.route('/test-auth')
@login_required
async def test_auth():
    """Test endpoint that requires authentication"""
    from quart import session
    return {
        'status': 'authenticated',
        'user': session.get('user_email', 'unknown'),
        'uid': session.get('user_uid', 'unknown')
    }, 200

# Root endpoint
@app.route('/')
async def root():
    """Root endpoint - redirect to main page"""
    from quart import redirect
    return redirect('/wraith')

# Log startup information
logger.info(f"Gnosis Wraith Server starting...")
logger.info(f"Storage path: {STORAGE_PATH}")
logger.info(f"Static folder: {app.static_folder}")
logger.info(f"Template folder: {app.template_folder}")

# This is used when directly running this file
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5678, use_reloader=False)
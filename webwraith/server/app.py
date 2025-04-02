"""
WebWraith Server Application - Main Entry Point
"""
import sys
import os

# Add the project root to sys.path to enable imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the app from the root app.py
try:
    from app import app
except ImportError as e:
    from quart import Quart
    
    app = Quart(__name__)
    
    @app.route('/')
    async def error_page():
        return f"""
        <html>
            <head><title>WebWraith - Import Error</title></head>
            <body>
                <h1>WebWraith - Import Error</h1>
                <p>There was an error importing the application: {str(e)}</p>
                <p>Please check that all dependencies are installed and the application is properly configured.</p>
            </body>
        </html>
        """

# This is used when directly running this file
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5678)
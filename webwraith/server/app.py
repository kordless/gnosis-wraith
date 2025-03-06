
from quart import Quart, request, jsonify, send_file, render_template, send_from_directory
import os
import asyncio
import json
import time
import uuid
import sys
import logging

# Import the main WebWraith functionality
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from webwraith import BrowserControl, Config

app = Quart(__name__, 
           static_folder='static',
           template_folder='templates')

# Main route
@app.route('/')
async def index():
    """Main page of the WebWraith server"""
    return await render_template('index.html')

# API endpoints would go here

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)

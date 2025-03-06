#!/usr/bin/env python3
"""
WebWraith Structure Setup

This script creates the directory structure and stub files for the WebWraith browser integration.
It will set up both the server component and browser extension directories.
"""

import os
import sys
import shutil
from pathlib import Path

def create_directory(path):
    """Create directory if it doesn't exist"""
    os.makedirs(path, exist_ok=True)
    print(f"Created directory: {path}")

def create_file(path, content="# Placeholder content"):
    """Create a file with placeholder content"""
    with open(path, 'w') as f:
        f.write(content)
    print(f"Created file: {path}")

def setup_webwraith_structure(base_dir):
    """
    Set up the WebWraith directory structure.
    
    Structure:
    webwraith/
    ├── server/                # Server component (Quart app)
    │   ├── app.py             # Main server application
    │   ├── templates/         # HTML templates
    │   │   ├── index.html     # Main page
    │   │   └── error.html     # Error page
    │   └── static/            # Static assets
    │       ├── css/
    │       │   ├── styles.css # Main styles
    │       │   └── report.css # Report styles
    │       └── js/
    │           ├── main.js    # Main UI script
    │           └── report.js  # Report script
    ├── extension/             # Browser extension
    │   ├── manifest.json      # Extension manifest
    │   ├── background.js      # Background script
    │   ├── popup.html         # Popup UI
    │   ├── popup.js           # Popup script
    │   ├── content.js         # Content script
    │   └── images/            # Extension icons
    │       ├── icon16.png
    │       ├── icon48.png
    │       └── icon128.png
    └── webwraith.py           # Enhanced WebWraith core functionality
    """
    
    # Create base directory
    create_directory(base_dir)
    
    # Server component
    server_dir = os.path.join(base_dir, "server")
    create_directory(server_dir)
    
    # Server templates
    templates_dir = os.path.join(server_dir, "templates")
    create_directory(templates_dir)
    create_file(os.path.join(templates_dir, "index.html"), "<!-- Main page template -->")
    create_file(os.path.join(templates_dir, "error.html"), "<!-- Error page template -->")
    
    # Server static files
    static_dir = os.path.join(server_dir, "static")
    css_dir = os.path.join(static_dir, "css")
    js_dir = os.path.join(static_dir, "js")
    create_directory(css_dir)
    create_directory(js_dir)
    
    # CSS files
    create_file(os.path.join(css_dir, "styles.css"), "/* Main styles */")
    create_file(os.path.join(css_dir, "report.css"), "/* Report styles */")
    
    # JS files
    create_file(os.path.join(js_dir, "main.js"), "// Main UI script")
    create_file(os.path.join(js_dir, "report.js"), "// Report script")
    
    # Server app
    app_content = """
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
    \"\"\"Main page of the WebWraith server\"\"\"
    return await render_template('index.html')

# API endpoints would go here

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)
"""
    create_file(os.path.join(server_dir, "app.py"), app_content)
    
    # Browser extension
    extension_dir = os.path.join(base_dir, "extension")
    create_directory(extension_dir)
    
    # Extension images
    images_dir = os.path.join(extension_dir, "images")
    create_directory(images_dir)
    
    # Create placeholder icons (1x1 pixel transparent PNG)
    pixel_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n\x94\xd4\x00\x00\x00\x00IEND\xaeB`\x82'
    for size in [16, 48, 128]:
        with open(os.path.join(images_dir, f"icon{size}.png"), 'wb') as f:
            f.write(pixel_png)
        print(f"Created file: {os.path.join(images_dir, f'icon{size}.png')}")
    
    # Extension files
    create_file(os.path.join(extension_dir, "manifest.json"), '{\n  "manifest_version": 3,\n  "name": "WebWraith Analyzer",\n  "version": "1.0.0"\n}')
    create_file(os.path.join(extension_dir, "background.js"), "// Background script")
    create_file(os.path.join(extension_dir, "popup.html"), "<!-- Popup UI -->")
    create_file(os.path.join(extension_dir, "popup.js"), "// Popup script")
    create_file(os.path.join(extension_dir, "content.js"), "// Content script")
    
    # WebWraith core
    webwraith_content = """
import os
import asyncio
import warnings
from typing import Dict, Any, List, Optional
from playwright.async_api import async_playwright

# This silences the ResourceWarning about unclosed transports
warnings.filterwarnings("ignore", message="unclosed transport", category=ResourceWarning)

class Config:
    \"\"\"Configuration class for WebWraith\"\"\"
    def __init__(self):
        self.base_dir = os.path.join(os.path.expanduser("~"), ".webwraith")
        self.screenshots_dir = os.path.join(self.base_dir, "screenshots")
        self.thumbnails_dir = os.path.join(self.base_dir, "thumbnails")
        
        # Ensure directories exist
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.thumbnails_dir, exist_ok=True)
    
    def get_screenshots_dir(self):
        return self.screenshots_dir
    
    def get_thumbnails_dir(self):
        return self.thumbnails_dir

class BrowserControl:
    \"\"\"Browser control class\"\"\"
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
    
    async def start_browser(self):
        \"\"\"Start browser\"\"\"
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
    
    async def navigate(self, url):
        \"\"\"Navigate to URL\"\"\"
        if not self.page:
            await self.start_browser()
        await self.page.goto(url)
    
    async def close(self):
        \"\"\"Close browser\"\"\"
        if self.browser:
            await self.browser.close()
    
    # More methods would be implemented here

# Custom event loop for Windows
def use_custom_event_loop():
    \"\"\"Set up custom event loop for Windows\"\"\"
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Main function for CLI use
async def analyze_url_for_server(url, analysis_id, output_path):
    \"\"\"Analyze URL and generate report\"\"\"
    # This would be implemented
    pass
"""
    create_file(os.path.join(base_dir, "webwraith.py"), webwraith_content)
    
    # Create a README file
    readme_content = """# WebWraith Browser Integration

A comprehensive tool for analyzing web content before visiting.

## Directory Structure

### Server Component
- `server/app.py`: Main server application (Quart)
- `server/templates/`: HTML templates
- `server/static/`: Static assets (CSS, JS)

### Browser Extension
- `extension/`: Browser extension files
- `extension/manifest.json`: Extension configuration
- `extension/background.js`: Background script
- `extension/popup.html`: Popup UI
- `extension/popup.js`: Popup script

### Core Functionality
- `webwraith.py`: Enhanced WebWraith core functionality

## Setup and Usage

1. Install dependencies:
   ```bash
   pip install quart uvicorn playwright newspaper3k readability-lxml beautifulsoup4 nltk pillow
   python -m playwright install chromium
   ```

2. Start the server:
   ```bash
   cd server
   python app.py
   ```

3. Load the extension in Chrome:
   - Open chrome://extensions
   - Enable Developer mode
   - Click "Load unpacked" and select the `extension` folder

## Features
- Full-page screenshots
- Content analysis for promotional elements
- Summary generation
- Browser integration
"""
    create_file(os.path.join(base_dir, "README.md"), readme_content)
    
    print("\nWebWraith structure has been set up successfully!")
    print(f"Root directory: {base_dir}")
    print("\nNext steps:")
    print("1. Copy the actual implementation code into each file")
    print("2. Install dependencies: quart uvicorn playwright newspaper3k readability-lxml beautifulsoup4 nltk pillow")
    print("3. Install Playwright browsers: python -m playwright install chromium")
    print("4. Start the server: python server/app.py")

if __name__ == "__main__":
    # Determine base directory
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    else:
        base_dir = os.path.join(os.getcwd(), "webwraith")
    
    # Confirm with user
    print(f"This will create a WebWraith structure in: {base_dir}")
    response = input("Continue? (y/n): ")
    
    if response.lower() == 'y':
        setup_webwraith_structure(base_dir)
    else:
        print("Setup canceled.")
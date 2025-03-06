# WebWraith Browser Integration

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

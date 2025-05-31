# Gnosis Wraith Project Outline

## File Structure Reference
All paths listed below are relative to the project root directory: `gnosis-wraith/`

## Project Overview
Gnosis Wraith is a web crawling and content extraction system with a browser extension interface. The project combines server-side web processing capabilities with browser integration for seamless content analysis and extraction.

## System Architecture

### Components
1. **Browser Extension**
   - User interface for content capture and interaction
   - Background processing and communication with server
   - Content scripts for DOM manipulation and extraction

2. **Server Application**
   - API endpoints for processing requests
   - Web crawling and content extraction engine
   - Content processing and rendering pipeline
   - Data storage and management

3. **User Interfaces**
   - Extension popup interface
   - Web dashboard
   - Reports and visualization system

## Directory Structure

### Root Level
- **Configuration Files**: Docker, requirements, deployment configs
- **Build Scripts**: For extension, server, and deployment
- **Documentation**: Development notes, plans, and reference materials

### Extension (`gnosis_wraith/extension/`)
- **Background Service** (`gnosis_wraith/extension/background.js`): Handles extension lifecycle and background processes
- **Content Scripts** (`gnosis_wraith/extension/content.js`): Operates within web pages for content extraction
- **Popup Interface** (`gnosis_wraith/extension/popup.html`, `gnosis_wraith/extension/popup.js`): User interaction within the extension
- **Configuration** (`gnosis_wraith/extension/manifest.json`): Extension definition and permissions

### Server (`gnosis_wraith/server/`)
- **Core Application** (`gnosis_wraith/server/app.py`): Main server entry point
- **Route Definitions**:
  - `gnosis_wraith/server/routes/api.py`: API endpoints for extension and clients
  - `gnosis_wraith/server/routes/extension.py`: Extension-specific functionality
  - `gnosis_wraith/server/routes/pages.py`: Web interface route handlers
- **Templates** (`gnosis_wraith/server/templates/`): HTML templates for web interfaces
  - `gnosis_wraith/server/templates/index.html`: Main landing page
  - `gnosis_wraith/server/templates/wraith.html`: Main application interface
  - `gnosis_wraith/server/templates/reports.html`: Reports interface
  - `gnosis_wraith/server/templates/error.html`: Error pages
- **Static Assets** (`gnosis_wraith/server/static/`): 
  - CSS (`gnosis_wraith/server/static/css/`): Stylesheets
  - JavaScript (`gnosis_wraith/server/static/js/`): Client-side scripts
    - `gnosis_wraith/server/static/js/script.js`: Main application script
    - `gnosis_wraith/server/static/js/upload.js`: File upload handling
  - Images (`gnosis_wraith/server/static/images/`): Image resources

## Key Features
1. Web page content extraction
2. Markdown conversion
3. Report generation
4. Content analysis
5. Browser integration
6. Customizable extraction settings

## Dev flow TBD

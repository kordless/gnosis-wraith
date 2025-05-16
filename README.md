# Gnosis Wraith

## Try It Now!
[Gnosis Wraith](https://gnosis-wraith-949870462453.us-central1.run.app)

## Vision: The Adaptive Web Perception Engine

Gnosis Wraith is a powerful web crawling and content analysis system that serves as the perception layer for AI systems. It captures, analyzes, and transforms web content through multiple intelligence layers - from basic crawling and OCR to sophisticated AI analysis and integration.

> *Gnosis is an AI oracle, and Wraith is the eye.*

## Key Features

- 🌐 **Intelligent Web Crawling** - Process any website with or without JavaScript
- 📸 **Screenshot Capture** - High-quality visual representation of web pages
- 👁️ **OCR Processing** - Extract text from images using EasyOCR
- 🧠 **AI Content Analysis** - Process content with OpenAI, Claude, Google Gemini or local models
- 🔄 **DOM Content Extraction** - Direct browser DOM capturing via extension
- 📊 **Smart Content Filtering** - Automated filtering of relevant information
- 📝 **Report Generation** - Beautiful Markdown and HTML reports
- 🧩 **Browser Extension** - Capture and process content directly from your browser
- ⚡ **Lightning Network** - Optional micropayments for AI analysis

## Quick Installation

### Docker (Recommended)

```bash
# Pull the latest image
docker pull kordless/gnosis-wraith:latest

# Run the container
docker run -d -p 5678:5678 --name gnosis-wraith kordless/gnosis-wraith:latest

# Access the web interface at http://localhost:5678
```

### Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: '3'
services:
  gnosis-wraith:
    image: kordless/gnosis-wraith:latest
    ports:
      - "5678:5678"
    volumes:
      - ./data:/data
    restart: unless-stopped
```

Then run:

```bash
docker-compose up -d
```

## Browser Extension

For full functionality, install the browser extension:

1. Access the web interface at `http://localhost:5678`
2. Navigate to the "Browser Extension" tab
3. Download and install the extension following browser-specific instructions
4. Use keyboard shortcuts or context menus to capture and analyze web content

## Usage Guide

### Web Interface

The web interface offers multiple ways to interact with Gnosis Wraith:

- **Single URL Crawl** - Process any website with customizable options
- **Image Upload** - Extract text from images using OCR
- **Browser Extension** - Capture and process web content directly

### API Endpoints

- **`/api/crawl`** - Crawl URLs and generate comprehensive reports
- **`/api/upload`** - Upload and analyze images
- **`/api/jobs`** - Manage background processing jobs
- **`/reports`** - Access generated reports

## Configuration Options

Gnosis Wraith offers flexible configuration:

- **JavaScript Rendering** - Enable/disable JavaScript for web crawling
- **Screenshot Capture** - Take screenshots of web pages
- **OCR Extraction** - Extract text from images using OCR
- **Markdown Extraction** - Control content extraction methods
- **AI Integration** - Connect with various AI providers

## Architecture

Gnosis Wraith is built on a modular architecture with these core components:

1. **Web Server** - Asynchronous Quart application for HTTP interface
2. **Browser Engine** - Playwright-based automation for web interaction
3. **Processing Pipeline** - Multi-stage content extraction and analysis
4. **Job System** - Background processing for long-running tasks
5. **Storage Layer** - Efficient report and image management
6. **Extension Integration** - Browser-based content capture

## Development Setup

For those wanting to contribute or modify:

1. Clone the repository
   ```bash
   git clone https://github.com/kordless/gnosis-wraith.git
   cd gnosis-wraith
   ```

2. Create and activate a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application
   ```bash
   python app.py
   ```

## Future Roadmap

Gnosis Wraith is evolving toward a dynamic module system that will:

- 🔄 **Generate Client Modules** - Create Python code to interact with any API or service on demand
- 🔄 **Interface Mirroring** - Simulate any API it observes for other systems to use
- 🔄 **Data Source Integration** - Connect to databases, queues, and network protocols automatically
- 🔄 **Self-Improvement** - Learn from usage patterns to enhance generated code

This system will enable Gnosis Wraith to act as a universal adapter between diverse web services and data sources, dynamically extending its capabilities without manual coding.

## Technologies

- **Python** - Primary development language
- **Playwright** - Modern browser automation
- **EasyOCR** - Optical character recognition
- **Quart** - Asynchronous web framework
- **AI Integration** - OpenAI, Claude, Gemini, Ollama
- **Docker** - Containerization for deployment

## License

See [LICENSE.md](LICENSE.md) for details.

---

*Seeing is believing. Gnosis Wraith sees it all.*
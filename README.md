# Gnosis Wraith

## Vision: The Adaptive Web Perception Engine

Gnosis Wraith is a powerful web crawling and content analysis system that serves as the perception layer for AI systems. It captures, analyzes, and transforms content through multiple intelligence layers - from basic crawling and OCR to sophisticated AI analysis and integration.

> *Gnosis is an AI oracle, and Wraith is the eye.*

## Try It Now!
[Gnosis Wraith](https://wraith.nuts.services)

## Join the Community
[![Discord](https://img.shields.io/badge/Discord-Join%20Us-7289da?logo=discord&logoColor=white)](https://discord.gg/AQnAn9XgFJ)

## Key Features

- 🌐 **Intelligent Web Crawling** - Process any website with or without JavaScript
- 📸 **Screenshot Capture** - High-quality visual representation of web pages
- 🖼️ **OCR Processing** - Extract text from images using EasyOCR
- 🧠 **AI Content Analysis** - Process content with OpenAI, Claude, Google Gemini or local models
- 🔄 **DOM Content Extraction** - Direct browser DOM capturing via extension
- 📊 **Smart Content Filtering** - Automated filtering of relevant information
- 📝 **Report Generation** - Beautiful Markdown and HTML reports
- 🧩 **Browser Extension** - Capture and process content directly from your browser
- ⚡ **Lightning Network** - Optional micropayments for AI analysis
- 🗂️ **User-Isolated Storage** - Multi-tenant support with hash-based user bucketing
- ☁️ **Cloud-Ready Storage** - Seamless switching between local filesystem and Google Cloud Storage

### 🆕 New in v2 API

- 💻 **JavaScript Execution** - Execute custom JavaScript on any webpage with safety validation
- 🤖 **LLM-Powered JavaScript** - Generate JavaScript from natural language requests
- 📋 **Content Analysis** - Extract entities, sentiment, and structured data using LLMs
- 🧹 **Smart Markdown Cleanup** - AI-powered content cleaning and optimization
- 📄 **Intelligent Summarization** - Create summaries in multiple formats and styles


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

### Cloud Deployment

Gnosis Wraith is deployable to Google Cloud Run out of the box, providing a serverless container execution environment:

```bash
# Deploy to Google Cloud Run
gcloud run deploy gnosis-wraith --image kordless/gnosis-wraith:latest --platform managed
```

### Distributed Setup

For high-volume crawling requirements:
- Deploy multiple instances as on-demand crawlers in a distributed setup
- Scale horizontally to increase performance for large crawling operations
- Task system efficiently handles processing delays, making it suitable for asynchronous operation

### Performance Considerations

- While GPU acceleration is supported for OCR and AI processing tasks, the system's asynchronous task architecture efficiently handles processing delays even on CPU-only deployments
- The job system effectively manages resource-intensive operations by queuing and processing them as resources become available

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

## Storage System

Gnosis Wraith features an advanced storage abstraction layer that supports both local development and cloud deployment:

### Key Features

- **User Isolation**: Each user's reports are stored in separate buckets using SHA-256 hashing
- **Cloud Support**: Automatic switching between local filesystem and Google Cloud Storage (GCS)
- **Multi-Tenancy**: Built-in support for multiple users with complete data isolation
- **Migration Tools**: Scripts to migrate existing reports to the new structure

### Storage Structure

```
users/
├── a1b2c3d4e5f6/     # User hash bucket
│   ├── reports/      # User's reports
│   └── screenshots/  # User's screenshots
└── system/           # System/shared reports
```

For detailed implementation information, see:
- [Storage Implementation Guide](./docs/STORAGE_IMPLEMENTATION_GUIDE.md)
- [Storage Quick Reference](./docs/STORAGE_QUICK_REFERENCE.md)

## Configuration Options

Gnosis Wraith offers flexible configuration:

- **JavaScript Rendering** - Enable/disable JavaScript for web crawling
- **Screenshot Capture** - Take screenshots of web pages
- **OCR Extraction** - Extract text from images using OCR
- **Markdown Extraction** - Control content extraction methods
- **AI Integration** - Connect with various AI providers
- **Storage Backend** - Choose between local filesystem or Google Cloud Storage
- **User Bucketing** - Enable/disable user isolation for multi-tenant deployments


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
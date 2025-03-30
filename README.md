# Gnosis Wraith (WebWraith): The AI Oracle's Eye

A powerful web crawling and content analysis system that serves as the perception layer for the Gnosis ecosystem. Built with Python, Quart, and Playwright, Gnosis Wraith operates both as a standalone tool and as the "eye" for a broader AI oracle system.

## Vision

Gnosis Wraith serves as the perception component of a multi-part AI oracle system:

- **Gnosis Wraith** (this project): The "eye" that crawls, analyzes, and indexes web content
- **Gnosis Wright**: The agent system that consumes and leverages the data gathered by Wraith
- **Gnosis Pipelines** (upcoming): Integration system for data flows and specialized processing

Together, these components form an AI oracle capable of gathering truths from the web and presenting them in a proxied, enhanced manner to users.

## Operational Modes

Gnosis Wraith operates in multiple modes with graceful fallbacks:

1. **Basic Mode**: Web crawling, screenshot capture, and OCR text extraction without AI analysis
2. **Simple AI**: Local lightweight AI models for basic content analysis (using Ollama/local foundation models)
3. **Advanced AI**: Integration with more powerful remote AI services (Anthropic, OpenAI, Gemini)
4. **Hybrid Mode**: Combines local and remote processing based on content complexity

The system automatically selects the appropriate mode based on available resources and configuration.

## Core Features

- **Autonomous Web Crawling**: Extract content from websites with advanced automation
- **Multi-Modal Extraction**: Combine OCR, HTML parsing, and AI to extract comprehensive information
- **Search Indexing**: Index content in Solr and vector stores for semantic retrieval
- **Visual Analysis**: Capture and analyze visual elements of web pages
- **Modular Intelligence**: Process content with various AI models based on task requirements
- **Browser Extension**: Pre-click analysis and enhanced browsing experience
- **Standalone & Integration Modes**: Works independently or as part of the larger Gnosis ecosystem

## Real-World Applications

- **Truth Oracle**: Gather and present factual information from across the web
- **Dynamic Content Integration**: Connect to real-world systems (e.g., NMEA 2000 marine data)
- **Voice-Controlled Interfaces**: Graph and display information on demand via vocal commands
- **Autonomous Research**: Standalone agent that crawls and contributes to knowledge repositories
- **Content Proxying**: Create enhanced web experiences with AI-augmented content

## Directory Structure

```
gnosis-wraith/
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose configuration
├── .dockerignore          # Docker ignore file
├── server/                # Web server assets
│   ├── static/            # Static files (CSS, JS)
│   │   ├── css/           # CSS styles
│   │   │   └── styles.css # Main stylesheet
│   │   └── js/            # JavaScript files
│   │       └── script.js  # Main script file
│   └── templates/         # HTML templates
│       ├── index.html     # Homepage template
│       └── reports.html   # Reports page template
├── ai/                    # AI integration modules
│   ├── models.py          # Model management and selection
│   ├── anthropic.py       # Anthropic Claude integration
│   ├── openai.py          # OpenAI integration
│   ├── gemini.py          # Google Gemini integration
│   └── ollama.py          # Local Ollama model integration
├── search/                # Search indexing components
│   ├── solr.py            # Solr indexing and search
│   └── vector.py          # Vector store operations
└── extension/             # Browser extension
    ├── manifest.json      # Extension manifest
    ├── popup.html         # Extension popup
    ├── background.js      # Extension background script
    └── content.js         # Extension content script
```

## Prerequisites

- Docker and Docker Compose (for containerized deployment)
- Python 3.10 or higher (for local development)
- Chrome/Chromium browser (for Playwright)
- Ollama (optional, for local AI models)
- Solr (optional, for search indexing)

## System Components

### 1. Perception Engine

The core crawling and extraction system:

- **Browser Automation**: Uses Playwright for high-fidelity web navigation
- **Multi-Method Extraction**: Combines HTML parsing, OCR, and AI extraction
- **Content Classification**: Categorizes and labels extracted content
- **Visual Processing**: Analyzes layout, images, and visual elements

### 2. AI Processing Layer

Flexible intelligence that adapts to available resources:

- **Model Management**: Automatically selects optimal models based on tasks
- **Local Processing**: Uses lightweight models via Ollama for privacy and speed
- **Remote Integration**: Connects to cloud AI services for advanced analysis
- **Content Enhancement**: Transforms raw extracted data into structured knowledge

### 3. Search & Retrieval

Indexes and makes content searchable:

- **Solr Integration**: Full-text search with faceting and filtering
- **Vector Indexing**: Semantic similarity search for concept-based retrieval
- **Hybrid Search**: Combines keyword and semantic search for optimal results

### 4. Browser Extension

Enhanced browsing experience:

- **Pre-Click Analysis**: Evaluate links before visiting them
- **Content Summary**: Quick overviews of page content
- **Visual Indicators**: Mark pages based on content analysis
- **Direct Crawling**: Add pages to the crawler from any browser

## Installation

### Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/kordless/gnosis-wraith.git
   cd gnosis-wraith
   ```

2. Build and start the Docker container:
   ```bash
   docker-compose up -d
   ```

3. Access the web interface at http://localhost:5678

### Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/kordless/gnosis-wraith.git
   cd gnosis-wraith
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Install Playwright browsers:
   ```bash
   playwright install chromium
   ```

4. Install NLTK data for text processing:
   ```bash
   python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
   ```

5. (Optional) Install and run Ollama for local AI models:
   ```bash
   # Follow instructions at https://ollama.ai/ for your platform
   ollama pull mistral:7b
   ```

6. Run the application:
   ```bash
   python app.py
   ```

7. Access the web interface at http://localhost:5678

## Usage

### Web Interface

1. Visit http://localhost:5678
2. Enter a URL or upload an image
3. Select desired AI processing level (none, local, remote)
4. Choose your output format
5. View the generated analysis with extracted content and AI insights

### Browser Extension

1. Install the extension from the `extension` directory
2. Configure connection to your Gnosis Wraith instance
3. Right-click on links to analyze before visiting
4. View AI-powered summaries and content analysis

### Command Line

```bash
# Crawl with basic mode (no AI)
python app.py crawl -u https://example.com --ai-mode none

# Crawl with local AI processing
python app.py crawl -u https://example.com --ai-mode local --model mistral:7b

# Crawl with remote AI processing
python app.py crawl -u https://example.com --ai-mode remote --provider anthropic

# Index crawled content in search
python app.py index --source-dir data/reports
```

## API Integration

### Client Library Example

```python
from gnosis_wraith import GnosisWraithClient

# Initialize client
client = GnosisWraithClient(
    api_base_url="http://localhost:5678/api",
    ai_mode="remote",
    ai_provider="anthropic"
)

# Start a crawl job
job_id = client.crawl(
    urls=["https://example.com"],
    depth=2,
    follow_external=False,
    index_content=True
)

# Monitor progress
status = client.get_status(job_id)
print(f"Progress: {status['progress']}%")

# Get results
results = client.get_results(job_id)
for page in results['pages']:
    print(f"URL: {page['url']}")
    print(f"Title: {page['title']}")
    print(f"AI Summary: {page['ai_summary']}")
```

## AI Model Configuration

Gnosis Wraith supports multiple AI backends:

### Local Models (via Ollama)

```yaml
ai:
  local:
    enabled: true
    models:
      - name: mistral:7b
        tasks: [summarization, classification]
      - name: llava:13b
        tasks: [image-analysis]
    default_model: mistral:7b
```

### Remote Models

```yaml
ai:
  remote:
    anthropic:
      enabled: true
      models:
        - name: claude-3-haiku-20240307
          tasks: [basic-analysis]
        - name: claude-3-opus-20240229
          tasks: [detailed-analysis]
    openai:
      enabled: true
      models:
        - name: gpt-3.5-turbo
          tasks: [summarization]
        - name: gpt-4o
          tasks: [complex-analysis]
    gemini:
      enabled: true
      models:
        - name: gemini-pro
          tasks: [general]
```

## Future Development

- **Gnosis Wright Integration**: Deeper connection with the agent system
- **Custom Model Training**: Specialized models for content analysis
- **Multi-Modal Processing**: Enhanced image, video, and audio analysis
- **Collaborative Crawling**: Distributed crawling across multiple instances
- **Knowledge Graph Construction**: Building semantic representations of content

## About the Project

Gnosis Wraith is part of the larger Gnosis ecosystem, designed to serve as an AI oracle that can gather, analyze, and present web content in enhanced ways. From powering autonomous agents to enabling voice-controlled data visualization in specialized environments (like marine applications with NMEA 2000 data), Gnosis aims to bridge the gap between the raw web and meaningful, actionable knowledge.

Created by Kord Campbell, founder of Loggly and creator of the Grub crawler, with extensive experience in web technologies and data analysis.

## License

This project is licensed under the The Gnosis AI-Sovereign License (v1.0)
# WebWraith: Advanced Web Content Analysis

A powerful web crawling and content analysis tool that outputs markdown and images, built with Python, Quart, and Playwright. Created by Kord Campbell (creator of Loggly and the Grub crawler). WebWraith can be run both as a command-line tool and as a web service.

## Features

- Crawl web pages and capture screenshots with advanced automation
- Extract text from web pages using OCR and multiple parsing methods
- Generate comprehensive markdown and HTML reports
- Upload images and extract text from them
- Smart content analysis with promotional content detection
- Browser extension integration for pre-click analysis
- Docker support for easy, isolated deployment

## Directory Structure

```
webwraith/
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
└── extension/             # Browser extension (optional)
    ├── manifest.json      # Extension manifest
    ├── popup.html         # Extension popup
    ├── background.js      # Extension background script
    └── content.js         # Extension content script
```

## Prerequisites

- Docker and Docker Compose (for containerized deployment)
- Python 3.10 or higher (for local development)
- Chrome/Chromium browser (for Playwright)

## Purpose and Integration

WebWraith is designed to work as a standalone tool and as an augmentation for other applications such as OpenWebUI and WebWright. Running within a Docker container, the server component stores analyzed web data and makes it accessible to these applications. The browser extension complements this system by handling scenarios where Playwright-based automation encounters obstacles, such as authentication barriers or dynamically loaded content.

## System Components

### 1. Server (Docker-Based API)

The WebWraith server provides a backend API for content analysis, enabling integration with other tools. It includes:

- **Content Extraction**: Uses Playwright, Newspaper3k, and Readability-lxml to parse web pages.
- **OCR Processing**: Extracts text from images using EasyOCR when standard methods fail.
- **Analysis Tools**: Detects promotional content, extracts keywords, and generates summaries.
- **Data Storage**: Maintains a repository of analyzed pages for future reference.

### 2. Browser Extension

A lightweight browser extension that enhances content analysis by:

- Allowing users to analyze links before clicking.
- Capturing screenshots when needed.
- Displaying visual indicators of analysis status.
- Providing quick access to stored reports.

### 3. Core Library

The foundational codebase that powers both the server and the extension, featuring:

- **Automated Browser Control** for structured content retrieval.
- **Text Processing** for summarization and classification.
- **Image Handling** for webpage snapshots.

## Installation

### Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/kordless/webwraith.git
   cd webwraith
   ```

2. Build and start the Docker container:
   ```bash
   docker-compose up -d
   ```

3. Access the web interface at http://localhost:5678

### Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/kordless/webwraith.git
   cd webwraith
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

5. Run the application:
   ```bash
   python app.py
   ```

6. Access the web interface at http://localhost:5678

## Usage

### As a Web Service

1. Start the server using Docker Compose or the manual method described above.
2. Open your browser and navigate to http://localhost:5678
3. Use the web interface to crawl URLs or upload images for text extraction.

### As a Command-Line Tool

Run the `app.py` script with appropriate command-line arguments:

```bash
# Crawl a single URL
python app.py crawl -u https://example.com -o markdown -t "Example Report"

# Crawl multiple URLs from a file
python app.py crawl -f urls.txt -o both -t "Multiple URLs Report"
```

### Using the Browser Extension

1. Install the extension from the `extension` directory.
2. Configure the extension to connect to your WebWraith instance (default: http://localhost:5678).
3. Right-click on a web page and select "Capture with WebWraith" to capture and analyze the page.

## Usage

### Web Interface

1. Visit http://localhost:5678
2. Enter a URL or upload an image
3. Select your desired output format (markdown, image, or both)
4. Click "Start Crawling" or "Upload & Extract Text"
5. View the generated report with screenshots and extracted text

### Browser Extension

1. Right-click a link or page and select "Analyze with WebWraith"
2. View the analysis in a new tab or in the extension popup
3. Use visual indicators to identify potentially problematic sites

### Command Line

For advanced users, WebWraith can be used directly from the command line:

```bash
# Analyze a single URL
python app.py crawl -u https://example.com -o both -t "Example Report"

# Crawl multiple URLs from a file
python app.py crawl -f urls.txt -o markdown -t "Multiple URLs Report"

# Convert a markdown report to HTML
python app.py convert_markdown report.md -o report.html
```

## API Endpoints

- `GET /` - Web interface homepage
- `GET /reports` - List generated reports
- `GET /reports/<filename>` - View a specific report
- `GET /screenshots/<filename>` - View a specific screenshot
- `POST /api/crawl` - Crawl URLs and generate reports
- `POST /api/upload` - Upload and analyze images

## Persistent Storage

When running with Docker, WebWraith stores data in the following locations:

- Reports: `/data/reports`
- Screenshots: `/data/screenshots`
- Logs: `/data/webwraith.log`

These directories are persisted using Docker volumes.

## Configuration

WebWraith can be configured using environment variables:

- `WEBWRAITH_STORAGE_PATH` - Path for storing data (default: ~/.webwraith)
- `QUART_APP` - Quart application name (default: app:app)
- `QUART_ENV` - Quart environment (default: production)

## Security Considerations

WebWraith interacts with web pages on the user's behalf. Ensure ethical use and compliance with legal and security standards. The Docker container provides an additional layer of isolation for safer web content analysis.

## About the Creator

WebWraith was created by Kord Campbell, founder of Loggly (cloud-based log management service) and creator of the Grub crawler. With extensive experience in web technologies and data analysis, Kord designed WebWraith to address the growing need for safer web browsing and content evaluation.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
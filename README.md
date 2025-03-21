# WebWraith: Advanced Web Content Analysis

A powerful web crawling and content analysis tool that outputs markdown and images, built with Python, Quart, and Playwright. WebWraith can be run both as a command-line tool and as a web service.

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


## API Crawling Example

Here's a basic example of how to use the WebWraith API for crawling:

```python
import requests
import json
import time
from urllib.parse import urljoin

class WebWraithCrawler:
    def __init__(self, api_base_url, api_key=None):
        """
        Initialize the WebWraith API crawler.
        
        Args:
            api_base_url (str): Base URL of the WebWraith API
            api_key (str, optional): API key for authentication
        """
        self.api_base_url = api_base_url
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'
    
    def start_crawl(self, start_urls, max_depth=3, follow_external=False, custom_settings=None):
        """
        Start a new crawling job.
        
        Args:
            start_urls (list): List of URLs to start crawling from
            max_depth (int): Maximum crawl depth
            follow_external (bool): Whether to follow external links
            custom_settings (dict): Additional crawler settings
            
        Returns:
            str: Job ID for the crawling task
        """
        payload = {
            'start_urls': start_urls,
            'max_depth': max_depth,
            'follow_external': follow_external
        }
        
        if custom_settings:
            payload.update(custom_settings)
        
        response = requests.post(
            urljoin(self.api_base_url, '/api/v1/crawl/start'),
            headers=self.headers,
            data=json.dumps(payload)
        )
        
        response.raise_for_status()
        return response.json().get('job_id')
    
    def get_crawl_status(self, job_id):
        """
        Check the status of a crawling job.
        
        Args:
            job_id (str): The job ID of the crawling task
            
        Returns:
            dict: Status information about the crawling job
        """
        response = requests.get(
            urljoin(self.api_base_url, f'/api/v1/crawl/status/{job_id}'),
            headers=self.headers
        )
        
        response.raise_for_status()
        return response.json()
    
    def get_crawl_results(self, job_id, page=1, per_page=100):
        """
        Retrieve results from a completed crawling job.
        
        Args:
            job_id (str): The job ID of the crawling task
            page (int): Page number for paginated results
            per_page (int): Number of results per page
            
        Returns:
            dict: Crawled data results
        """
        response = requests.get(
            urljoin(self.api_base_url, f'/api/v1/crawl/results/{job_id}'),
            headers=self.headers,
            params={'page': page, 'per_page': per_page}
        )
        
        response.raise_for_status()
        return response.json()
    
    def wait_for_completion(self, job_id, check_interval=10, timeout=3600):
        """
        Wait for a crawling job to complete.
        
        Args:
            job_id (str): The job ID of the crawling task
            check_interval (int): Time in seconds between status checks
            timeout (int): Maximum time to wait in seconds
            
        Returns:
            dict: Final job status
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_crawl_status(job_id)
            
            if status['status'] in ['completed', 'failed']:
                return status
            
            time.sleep(check_interval)
        
        raise TimeoutError(f"Crawling job did not complete within {timeout} seconds")


# Usage example
if __name__ == "__main__":
    # Initialize the crawler with API base URL and optional API key
    crawler = WebWraithCrawler(
        api_base_url="https://api.webwraith.example.com",
        api_key="your_api_key_here"
    )
    
    # Start a new crawling job
    job_id = crawler.start_crawl(
        start_urls=["https://example.com"],
        max_depth=2,
        follow_external=False,
        custom_settings={
            'user_agent': 'WebWraith Bot/1.0',
            'respect_robots_txt': True,
            'crawl_delay': 1.0,
            'extract_images': True,
            'extract_links': True
        }
    )
    
    print(f"Crawling job started with ID: {job_id}")
    
    # Wait for the job to complete
    try:
        final_status = crawler.wait_for_completion(job_id)
        print(f"Crawling job completed with status: {final_status['status']}")
        
        if final_status['status'] == 'completed':
            # Retrieve and process results
            results = crawler.get_crawl_results(job_id)
            
            print(f"Retrieved {results['total']} pages")
            for page in results['items']:
                print(f"URL: {page['url']}")
                print(f"Title: {page['title']}")
                print(f"Links found: {len(page['links'])}")
                print("-" * 50)
    
    except TimeoutError as e:
        print(f"Error: {e}")
```

## Advanced Features

- **Distributed Crawling**: Scale your crawling operations across multiple nodes
- **Custom Extractors**: Define custom data extraction patterns
- **Rate Limiting**: Respect website crawl policies
- **Data Export**: Export crawled data in various formats (JSON, CSV, XML)
- **Webhook Notifications**: Get notified when crawling jobs complete

## Configuration

The API crawler supports the following configuration options:

| Option | Description | Default |
|--------|-------------|---------|
| max_depth | Maximum depth to crawl | 3 |
| follow_external | Follow links to external domains | False |
| respect_robots_txt | Respect robots.txt directives | True |
| crawl_delay | Delay between requests (seconds) | 0.5 |
| user_agent | Custom User-Agent string | WebWraith/1.0 |
| timeout | Request timeout (seconds) | 30 |
| max_retries | Maximum number of retry attempts | 3 |
| extract_images | Extract image URLs | False |
| extract_links | Extract link URLs | True |


## Security Considerations

WebWraith interacts with web pages on the user's behalf. Ensure ethical use and compliance with legal and security standards. The Docker container provides an additional layer of isolation for safer web content analysis.

## About the Creator

WebWraith was created by Kord Campbell, founder of Loggly (cloud-based log management service) and creator of the Grub crawler. With extensive experience in web technologies and data analysis, Kord designed WebWraith to address the growing need for safer web browsing and content evaluation.

## License

This project is licensed under the The WebWraith AI-Sovereign License (v1.0)

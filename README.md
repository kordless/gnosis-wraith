# WebWraith: Advanced Web Content Analysis

## Overview

WebWraith is a powerful tool for analyzing web content before direct interaction. It enables users to extract, evaluate, and summarize web pages while minimizing exposure to deceptive or harmful elements. By integrating multiple analysis techniques, WebWraith provides a robust and flexible system for examining online content in various contexts.

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

## Installation and Setup

### Requirements

Install the required environment using Conda:

```bash
conda env create -f environment.yml
conda activate webwraith
python -m playwright install chromium
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

### Running the Server

```bash
cd server
python app.py
```

This launches the API at [http://localhost:5000](http://localhost:5000).

### Installing the Browser Extension

1. Open the browser’s extension manager.
2. Enable "Developer mode."
3. Load the `extension` directory as an unpacked extension.
4. Pin the extension for easy access.

## Usage

### Web Interface

1. Visit [http://localhost:5000](http://localhost:5000).
2. Enter a URL.
3. Analyze and review the report.

### Browser Extension

1. Right-click a link or page and select "Analyze with WebWraith."
2. View the results in a new tab.

### Command Line

```bash
python webwraith.py analyze https://example.com
python webwraith.py crawl -f urls.txt -o both
```

## Containerized Deployment

Run WebWraith within Docker for isolated and consistent execution:

```bash
docker build -t webwraith .
docker run -p 5000:5000 webwraith
```

The included `Dockerfile` configures the system with all dependencies pre-installed.

## Security Considerations

WebWraith interacts with web pages on the user’s behalf. Ensure ethical use and compliance with legal and security standards.

## Conclusion

WebWraith provides a comprehensive solution for pre-visit web content analysis, offering a secure and efficient approach to digital exploration. Its integration with other tools expands its utility, making it a valuable asset for automated workflows and intelligent browsing.

For inquiries or contributions, refer to the project repository.


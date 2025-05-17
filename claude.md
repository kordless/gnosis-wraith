# Gnosis Wraith Project Guide for Claude

## Purpose of This Document

This document serves as a primer for Claude to understand the Gnosis Wraith project without immediately exploring all files. When starting a new session with this project, Claude should:

1. First ask which directory it's currently in
2. Run `evolve_status` to check available tools before accessing any project files
3. Wait for specific user instructions rather than autonomously exploring files

## Project Overview

Gnosis Wraith is a web crawling and content analysis system that serves as the perception layer for the Gnosis ecosystem. The metaphor is apt - Gnosis is an AI oracle, and Wraith is its "eye" that perceives the web.

The system crawls websites, takes screenshots, analyzes content using OCR and AI, and provides structured data extraction. It operates as an "AI oracle" that gathers information from the web with various levels of intelligence - from basic crawling to advanced AI analysis.

## Project Structure

The project is organized into several key directories:

- `server/`: Core server components, including browser automation and crawling
- `ai/`: AI integration modules for different model providers (OpenAI, Anthropic, Gemini)
- `gnosis_wraith/`: Main package, including extension and server components
- `search/`: Search indexing components
- `lightning/`: Lightning Network integration for micropayments

Key files include:
- `Dockerfile`: Container configuration for deployment
- `app.py`: Main application entry point
- `requirements.txt`: Python dependencies
- `server/browser.py`: Browser automation and screenshot capture
- `server/crawler.py`: Web crawling functionality
- `ai/models.py`: Model management and selection

## Key Components

### Browser Automation

The `browser.py` file handles all browser interactions using Playwright, including:
- Page navigation and timing management
- Screenshot capture
- DOM stability monitoring
- Handling different JavaScript rendering scenarios

### Content Processing

The system processes web content through several methods:
- HTML parsing via Beautiful Soup in `crawler.py`
- OCR processing of screenshots using EasyOCR
- AI-based content analysis with multiple providers

### Crawling Engine

The `crawler.py` file implements the core crawling functionality:
- URL processing and navigation
- Content extraction and filtering
- Error handling and retry logic
- Integration with AI processing

## Recent Optimizations

### EasyOCR Model Preloading

The Dockerfile now preloads EasyOCR models during build time to avoid downloading them on each service startup.

### Beautiful Soup for HTML Parsing

Added Beautiful Soup for HTML content filtering to improve extraction quality.

### JavaScript-Heavy Page Handling

Enhanced browser.py with improved handling for complex JavaScript-rendered pages through DOM stability detection, extended wait times for known complex sites, and content existence verification.

### Browser Installation Optimization

Optimized Docker image size by only installing Chromium instead of all browsers.

## Deployment Configuration

The system uses Docker for containerization and can be deployed to environments like Google Cloud Run, with considerations for container size, ephemeral filesystems, memory requirements, and JavaScript execution.

---

**Important for Claude:** When starting a session with this project, first ask which directory you're in and use the `evolve_status` tool to check available capabilities. Don't automatically inspect individual files unless specifically requested. Wait for user instructions on which aspects of the project to focus on or which files to analyze.

Remember that your role is to assist with the Gnosis Wraith project based on user requests, not to autonomously explore all files immediately. This approach ensures you can provide targeted, relevant help as needed.

SEE NOTES.md
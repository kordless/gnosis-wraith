import os
import re
import sys
import json
import asyncio
import logging
import datetime
import uuid
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

import click
import aiofiles
import markdown
from quart import Quart, render_template, request, jsonify, send_from_directory, redirect, url_for
import numpy as np
import easyocr
from PIL import Image
from playwright.async_api import async_playwright

# Configuration
STORAGE_PATH = os.environ.get('WEBWRAITH_STORAGE_PATH', os.path.join(os.path.expanduser("~"), ".webwraith"))
SCREENSHOTS_DIR = os.path.join(STORAGE_PATH, "screenshots")
REPORTS_DIR = os.path.join(STORAGE_PATH, "reports")
LOG_FILE = os.path.join(STORAGE_PATH, "webwraith.log")

# Ensure directories exist
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Setup logging
logger = logging.getLogger("webwraith")
logger.setLevel(logging.INFO)

c_handler = logging.StreamHandler()
f_handler = logging.FileHandler(LOG_FILE)
c_handler.setLevel(logging.WARNING)
f_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
c_handler.setFormatter(formatter)
f_handler.setFormatter(formatter)

logger.addHandler(c_handler)
logger.addHandler(f_handler)

# Create Quart app
app = Quart(__name__, static_folder='server/static', template_folder='server/templates')

# Ensure the downloads directory exists
os.makedirs(os.path.join(os.path.dirname(__file__), 'server/static/downloads'), exist_ok=True)

# Browser Control class
class BrowserControl:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.ocr_reader = None
        self._initialize_ocr()

    def _initialize_ocr(self):
        """Initialize EasyOCR for text extraction."""
        try:
            self.ocr_reader = easyocr.Reader(['en'])
            logger.info("EasyOCR initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR: {str(e)}")
            self.ocr_reader = None

    async def start_browser(self):
        """Start a headless browser session."""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=True)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            logger.info("Browser started successfully")
        except Exception as e:
            logger.error(f"Failed to start browser: {str(e)}")
            raise

    async def navigate(self, url):
        """Navigate to a URL."""
        if not self.page:
            await self.start_browser()
        await self.page.goto(url)
        logger.info(f"Navigated to {url}")

    async def screenshot(self, path):
        """Take a screenshot and save it to the specified path."""
        if not self.page:
            raise Exception("Browser not started")
        await self.page.screenshot(path=path)
        logger.info(f"Screenshot saved to {path}")

    async def extract_text_from_screenshot(self, screenshot_path):
        """Extract text from a screenshot using OCR."""
        if not self.ocr_reader:
            self._initialize_ocr()
            if not self.ocr_reader:
                raise Exception("OCR reader not available")
                
        image = Image.open(screenshot_path)
        image_np = np.array(image)
        results = self.ocr_reader.readtext(image_np)
        extracted_text = ' '.join([result[1] for result in results])
        logger.info(f"Extracted {len(results)} text regions from {screenshot_path}")
        return extracted_text

    async def close(self):
        """Close the browser session."""
        if self.browser:
            await self.browser.close()
            logger.info("Browser closed")

# URL extraction function
def extract_urls(content):
    """Extract URLs from the given content."""
    url_pattern = re.compile(r'https?://\S+')
    return url_pattern.findall(content)

async def crawl_url(url, browser_control):
    """Crawl a single URL and return the results."""
    # Create a safe filename from the URL
    filename = url.replace('https://', '').replace('http://', '').replace('/', '_').replace('.', '_')
    filename = re.sub(r'[^\w\-_.]', '_', filename)
    screenshot_path = os.path.join(SCREENSHOTS_DIR, f"{filename}_{uuid.uuid4().hex[:8]}.png")
    
    try:
        await browser_control.navigate(url)
        await browser_control.screenshot(screenshot_path)
        
        # Extract text from the screenshot
        extracted_text = await browser_control.extract_text_from_screenshot(screenshot_path)
        
        # Get page title
        title = await browser_control.page.title()
        
        return {
            'url': url,
            'title': title,
            'screenshot': screenshot_path,
            'extracted_text': extracted_text
        }
        
    except Exception as e:
        logger.error(f"Error processing {url}: {str(e)}")
        return {
            'url': url,
            'error': str(e)
        }

async def crawl_urls(urls):
    """Crawl each URL and take screenshots, returning results."""
    browser_control = BrowserControl()
    await browser_control.start_browser()
    
    results = []
    for url in urls:
        result = await crawl_url(url, browser_control)
        results.append(result)

    await browser_control.close()
    return results

def generate_markdown_report(title, crawl_results):
    """Generate a markdown report from crawl results."""
    md = f"# {title}\n\n"
    md += f"*Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    
    for i, result in enumerate(crawl_results, 1):
        md += f"## {i}. {result.get('title', 'Untitled Page')}\n\n"
        md += f"**URL**: {result['url']}\n\n"
        
        if 'error' in result:
            md += f"**Error**: {result['error']}\n\n"
        else:
            # Add screenshot as image - use relative path
            relative_path = os.path.relpath(result['screenshot'], REPORTS_DIR)
            md += f"**Screenshot**:\n\n"
            md += f"![Screenshot of {result['url']}]({relative_path})\n\n"
            
            # Add extracted text
            md += f"**Extracted Text**:\n\n"
            md += f"```\n{result['extracted_text']}\n```\n\n"
        
        md += "---\n\n"
    
    return md

async def save_markdown_report(title, crawl_results):
    """Save a markdown report to disk and return the file path."""
    report_content = generate_markdown_report(title, crawl_results)
    filename = f"{re.sub(r'[^\w\-_]', '_', title)}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    report_path = os.path.join(REPORTS_DIR, filename)
    
    async with aiofiles.open(report_path, 'w') as f:
        await f.write(report_content)
    
    return report_path

async def convert_markdown_to_html(markdown_file):
    """Convert a markdown file to HTML."""
    html_file = f"{os.path.splitext(markdown_file)[0]}.html"
    
    async with aiofiles.open(markdown_file, 'r') as f:
        md_content = await f.read()
    
    html = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
    
    styled_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{os.path.basename(markdown_file)}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 900px; margin: 0 auto; padding: 20px; }}
        img {{ max-width: 100%; }}
        code {{ background-color: #f5f5f5; padding: 2px 5px; }}
        pre {{ background-color: #f5f5f5; padding: 15px; overflow-x: auto; }}
        h1, h2, h3 {{ color: #333; }}
    </style>
</head>
<body>
    {html}
</body>
</html>"""
    
    async with aiofiles.open(html_file, 'w') as f:
        await f.write(styled_html)
    
    return html_file

# CLI part using Click
@click.group()
def cli():
    """WebWraith CLI - A powerful web crawling tool that outputs markdown and images."""
    pass

@cli.command()
@click.option('-f', '--file', type=click.Path(exists=True), default=None, help="Path to the file containing URLs to crawl.")
@click.option('-u', '--uri', default=None, help="A single URI to crawl.")
@click.option('-o', '--output', default='markdown', type=click.Choice(['markdown', 'image', 'both']), 
              help="Output format: markdown, image, or both.")
@click.option('-t', '--title', default=None, help="Title for the markdown report.")
@click.option('-d', '--dir', default=None, help="Directory to save outputs. Defaults to current directory.")
def crawl(file, uri, output, title, dir):
    """Crawl specified URLs, capture screenshots, and generate output as markdown or images."""
    if bool(file) == bool(uri):
        click.echo("Error: Exactly one of --file or --uri must be provided.")
        return
    
    # Set output directory
    output_dir = dir if dir else REPORTS_DIR
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Set default title if not provided
    if not title:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if file:
            title = f"Web Crawl Report for URLs in {os.path.basename(file)} - {timestamp}"
        else:
            title = f"Web Crawl Report for {uri} - {timestamp}"
    
    # Extract URLs from file or use provided URI
    urls = []
    if file:
        with open(file, 'r') as f:
            content = f.read()
            urls = extract_urls(content)
    elif uri:
        urls = [uri]
    
    # Run the async crawl
    result = asyncio.run(async_crawl_cli(urls, output, title, output_dir))
    click.echo(json.dumps(result, indent=2))

async def async_crawl_cli(urls, output_format, title, output_dir):
    """Async function to crawl URLs and generate output for CLI."""
    try:
        crawl_results = await crawl_urls(urls)
        
        outputs = {}
        
        if output_format in ['markdown', 'both']:
            report_content = generate_markdown_report(title, crawl_results)
            filename = f"{re.sub(r'[^\w\-_]', '_', title)}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            markdown_path = os.path.join(output_dir, filename)
            
            async with aiofiles.open(markdown_path, 'w') as f:
                await f.write(report_content)
            
            outputs['markdown'] = markdown_path
            click.echo(f"Markdown report saved to {markdown_path}")
            
            # If both formats requested, convert markdown to HTML
            if output_format == 'both':
                html_path = await convert_markdown_to_html(markdown_path)
                outputs['html'] = html_path
                click.echo(f"HTML report saved to {html_path}")
            
        if output_format in ['image', 'both']:
            outputs['images'] = [result['screenshot'] for result in crawl_results if 'screenshot' in result]
            image_paths = ", ".join(outputs['images'])
            click.echo(f"Images saved to: {image_paths if outputs['images'] else 'None'}")
        
        click.echo(f"Crawling completed. {len(urls)} URLs processed.")
        return {
            "success": True,
            "result": {
                "output_format": output_format,
                "title": title,
                "urls_processed": urls,
                "url_count": len(urls),
                "outputs": outputs
            }
        }

    except Exception as e:
        error_message = f"An error occurred while processing: {str(e)}"
        click.echo(error_message)
        return {
            "success": False,
            "error": error_message
        }

# Web routes
@app.route('/')
async def index():
    """Render the index page."""
    return await render_template('index.html')

@app.route('/api/crawl', methods=['POST'])
async def api_crawl():
    """API endpoint to crawl URLs."""
    data = await request.get_json()
    
    urls = data.get('urls', [])
    if 'url' in data and data['url']:
        urls.append(data['url'])
    
    if not urls:
        return jsonify({
            "success": False,
            "error": "No URLs provided"
        }), 400
    
    title = data.get('title', f"Web Crawl Report - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output_format = data.get('output_format', 'markdown')
    
    try:
        crawl_results = await crawl_urls(urls)
        
        results = {
            "success": True,
            "urls_processed": urls,
            "results": []
        }
        
        for result in crawl_results:
            result_item = {
                "url": result['url'],
                "title": result.get('title', 'Untitled Page')
            }
            
            if 'error' in result:
                result_item['error'] = result['error']
            else:
                # Get relative paths for the web app
                result_item['screenshot'] = os.path.basename(result['screenshot'])
                # Truncate extracted text if too long
                result_item['extracted_text'] = result['extracted_text'][:1000] + '...' if len(result['extracted_text']) > 1000 else result['extracted_text']
            
            results['results'].append(result_item)
        
        if output_format in ['markdown', 'both']:
            markdown_path = await save_markdown_report(title, crawl_results)
            results['report_path'] = os.path.basename(markdown_path)
            
            # Convert to HTML if both formats requested
            if output_format == 'both':
                html_path = await convert_markdown_to_html(markdown_path)
                results['html_path'] = os.path.basename(html_path)
        
        return jsonify(results)
    
    except Exception as e:
        logger.error(f"API crawl error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/upload', methods=['POST'])
async def api_upload():
    """API endpoint to upload images."""
    files = await request.files
    
    if 'image' not in files:
        return jsonify({
            "success": False,
            "error": "No image file provided"
        }), 400
    
    try:
        file = files['image']
        filename = f"{uuid.uuid4().hex}.png"
        file_path = os.path.join(SCREENSHOTS_DIR, filename)
        await file.save(file_path)
        
        browser_control = BrowserControl()
        extracted_text = await browser_control.extract_text_from_screenshot(file_path)
        
        return jsonify({
            "success": True,
            "file_path": os.path.basename(file_path),
            "extracted_text": extracted_text
        })
    
    except Exception as e:
        logger.error(f"API upload error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/reports')
async def list_reports():
    """List all generated reports."""
    reports = []
    for file in os.listdir(REPORTS_DIR):
        if file.endswith('.md'):
            file_path = os.path.join(REPORTS_DIR, file)
            creation_time = os.path.getctime(file_path)
            reports.append({
                "filename": file,
                "created": datetime.datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S'),
                "size": os.path.getsize(file_path)
            })
    
    # Sort reports by creation time (newest first)
    reports.sort(key=lambda x: x['created'], reverse=True)
    
    return await render_template('reports.html', reports=reports)

@app.route('/reports/<path:filename>')
async def serve_report(filename):
    """Serve a report file."""
    return await send_from_directory(REPORTS_DIR, filename)

@app.route('/screenshots/<path:filename>')
async def serve_screenshot(filename):
    """Serve a screenshot file."""
    return await send_from_directory(SCREENSHOTS_DIR, filename)

@app.route('/extension')
async def serve_extension():
    """Generate and serve the extension zip file."""
    downloads_dir = os.path.join(os.path.dirname(__file__), 'server/static/downloads')
    zip_path = os.path.join(downloads_dir, 'webwraith-extension.zip')
    
    # Check if extension zip exists, create it if not
    if not os.path.exists(zip_path):
        extension_dir = os.path.join(os.path.dirname(__file__), 'webwraith/extension')
        if os.path.exists(extension_dir):
            # Create downloads directory if it doesn't exist
            os.makedirs(downloads_dir, exist_ok=True)
            
            # Create zip file
            import zipfile
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(extension_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, os.path.join(extension_dir, '..'))
                        zipf.write(file_path, arcname)
    
    # Redirect to the static file
    return redirect(url_for('static', filename='downloads/webwraith-extension.zip'))

# Main entry point
if __name__ == '__main__':
    # Check if running as CLI or as a web service
    if len(sys.argv) > 1:
        cli()
    else:
        print(f"Starting WebWraith service on port 5678")
        app.run(host='0.0.0.0', port=5678)
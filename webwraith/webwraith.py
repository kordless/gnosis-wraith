import os
import sys
import argparse
import logging
import asyncio
from typing import Dict, Any, List, Optional

# Import core modules
from webwraith.server.app import app as quart_app
from webwraith.server.browser_control import BrowserControl

# Set up logging
logger = logging.getLogger("webwraith")
logger.setLevel(logging.INFO)

# Configure console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def main():
    """Main entry point for WebWraith CLI"""
    parser = argparse.ArgumentParser(description="WebWraith - Advanced Web Content Analysis")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Add 'analyze' command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a URL")
    analyze_parser.add_argument("url", help="URL to analyze")
    analyze_parser.add_argument("-o", "--output", choices=["markdown", "html", "both"], 
                               default="both", help="Output format")
    analyze_parser.add_argument("-t", "--title", help="Title for the report")
    
    # Add 'serve' command
    serve_parser = subparsers.add_parser("serve", help="Start the web server")
    serve_parser.add_argument("-p", "--port", type=int, default=5678, 
                             help="Port to run the server on")
    serve_parser.add_argument("-h", "--host", default="0.0.0.0",
                             help="Host to bind the server to")
    
    # Add 'crawl' command
    crawl_parser = subparsers.add_parser("crawl", help="Crawl multiple URLs")
    crawl_parser.add_argument("-f", "--file", help="File containing URLs to crawl")
    crawl_parser.add_argument("-o", "--output", choices=["markdown", "html", "both"], 
                             default="both", help="Output format")
    crawl_parser.add_argument("-t", "--title", help="Title for the report")
    
    args = parser.parse_args()
    
    # Execute the specified command
    if args.command == "analyze":
        asyncio.run(analyze_url(args.url, args.output, args.title))
    elif args.command == "serve":
        start_server(args.host, args.port)
    elif args.command == "crawl":
        if not args.file:
            logger.error("File with URLs is required for crawl command")
            sys.exit(1)
        asyncio.run(crawl_urls(args.file, args.output, args.title))
    else:
        # Default to starting the server if no command is provided
        start_server("0.0.0.0", 5678)

async def analyze_url(url: str, output_format: str, title: Optional[str] = None) -> Dict[str, Any]:
    """Analyze a single URL"""
    logger.info(f"Analyzing URL: {url}")
    
    browser = BrowserControl()
    await browser.start_browser()
    
    try:
        # Navigate to URL
        await browser.navigate(url)
        
        # Generate a timestamp-based filename
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"webwraith_analyze_{timestamp}"
        
        # Take screenshot
        screenshot_path = os.path.join(os.environ.get('WEBWRAITH_STORAGE_PATH', '.'), 
                                       "screenshots", f"{filename}.png")
        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
        await browser.screenshot(screenshot_path)
        
        # Extract text
        extracted_text = await browser.extract_text_from_screenshot(screenshot_path)
        
        # Get page title
        title = title or await browser.page.title()
        
        result = {
            'url': url,
            'title': title,
            'screenshot': screenshot_path,
            'extracted_text': extracted_text
        }
        
        # Generate reports based on output format
        from webwraith.server.report_generator import generate_markdown_report, convert_markdown_to_html
        
        reports = {}
        if output_format in ['markdown', 'both']:
            md_path = os.path.join(os.environ.get('WEBWRAITH_STORAGE_PATH', '.'), 
                                  "reports", f"{filename}.md")
            os.makedirs(os.path.dirname(md_path), exist_ok=True)
            
            # Generate markdown report
            md_content = generate_markdown_report(title, [result])
            with open(md_path, 'w') as f:
                f.write(md_content)
            
            reports['markdown'] = md_path
            logger.info(f"Markdown report saved to: {md_path}")
            
            # Generate HTML if requested
            if output_format == 'both':
                html_path = await convert_markdown_to_html(md_path)
                reports['html'] = html_path
                logger.info(f"HTML report saved to: {html_path}")
        
        return {
            'success': True,
            'result': result,
            'reports': reports
        }
    
    except Exception as e:
        logger.error(f"Error analyzing URL: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        await browser.close()

async def crawl_urls(file_path: str, output_format: str, title: Optional[str] = None) -> Dict[str, Any]:
    """Crawl multiple URLs from a file"""
    logger.info(f"Crawling URLs from file: {file_path}")
    
    try:
        # Read URLs from file
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Extract URLs
        import re
        url_pattern = re.compile(r'https?://\S+')
        urls = url_pattern.findall(content)
        
        if not urls:
            logger.error("No URLs found in the file")
            return {
                'success': False,
                'error': "No URLs found in the file"
            }
        
        logger.info(f"Found {len(urls)} URLs to crawl")
        
        # Set default title if not provided
        if not title:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            title = f"WebWraith Crawl Report - {timestamp}"
        
        # Process each URL
        results = []
        for url in urls:
            try:
                result = await analyze_url(url, "none")  # Just analyze, don't generate individual reports
                if result['success']:
                    results.append(result['result'])
                else:
                    logger.warning(f"Failed to analyze {url}: {result['error']}")
                    results.append({
                        'url': url,
                        'error': result['error']
                    })
            except Exception as e:
                logger.warning(f"Error processing {url}: {str(e)}")
                results.append({
                    'url': url,
                    'error': str(e)
                })
        
        # Generate combined reports
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"webwraith_crawl_{timestamp}"
        
        reports = {}
        if output_format in ['markdown', 'both']:
            from webwraith.server.report_generator import generate_markdown_report, convert_markdown_to_html
            
            md_path = os.path.join(os.environ.get('WEBWRAITH_STORAGE_PATH', '.'), 
                                  "reports", f"{filename}.md")
            os.makedirs(os.path.dirname(md_path), exist_ok=True)
            
            # Generate markdown report
            md_content = generate_markdown_report(title, results)
            with open(md_path, 'w') as f:
                f.write(md_content)
            
            reports['markdown'] = md_path
            logger.info(f"Markdown report saved to: {md_path}")
            
            # Generate HTML if requested
            if output_format == 'both':
                html_path = await convert_markdown_to_html(md_path)
                reports['html'] = html_path
                logger.info(f"HTML report saved to: {html_path}")
        
        return {
            'success': True,
            'urls_processed': urls,
            'results_count': len(results),
            'reports': reports
        }
    
    except Exception as e:
        logger.error(f"Error during crawl: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def start_server(host: str = "0.0.0.0", port: int = 5678) -> None:
    """Start the WebWraith web server"""
    logger.info(f"Starting WebWraith server on {host}:{port}")
    quart_app.run(host=host, port=port)

if __name__ == "__main__":
    main()
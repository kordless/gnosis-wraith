import os
import random
import asyncio
import logging
from playwright.async_api import async_playwright
from PIL import Image

# Get logger from config
logger = logging.getLogger("gnosis_wraith")

class BrowserControl:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        # Import ModelManager inline to avoid circular imports
        from ai.models import ModelManager
        self.model_manager = ModelManager()
        
    async def extract_text_from_screenshot(self, screenshot_path):
        """Extract text from a screenshot using OCR."""
        return await self.model_manager.extract_text_from_image(screenshot_path)
        
    async def screenshot(self, path):
        """Take a screenshot and save it to the specified path."""
        if not self.page:
            raise Exception("Browser not started")
        
        try:
            # Take full page screenshot to capture everything
            await self.page.screenshot(path=path, full_page=True)
            logger.info(f"Screenshot saved to {path}")
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            
            # Create a simple error image if screenshot fails
            try:
                from PIL import Image, ImageDraw, ImageFont
                
                # Create a blank image
                img = Image.new('RGB', (1280, 800), color=(240, 240, 240))
                draw = ImageDraw.Draw(img)
                
                # Add error text
                try:
                    font = ImageFont.truetype("Arial", 20)
                except:
                    # Fallback to default font if Arial not available
                    font = ImageFont.load_default()
                    
                error_message = f"Failed to capture screenshot: {str(e)}"
                draw.text((50, 50), "Error Capturing Page", fill=(255, 0, 0), font=font)
                draw.text((50, 100), error_message, fill=(0, 0, 0), font=font)
                draw.text((50, 150), f"URL: {self.page.url}", fill=(0, 0, 0), font=font)
                
                # Save the error image
                img.save(path)
                logger.info(f"Created error image at {path}")
            except Exception as img_error:
                logger.error(f"Error creating error image: {str(img_error)}")
                raise e

    async def wait_for_render_stability(self, javascript_enabled=False):
        """
        Wait for the page to stabilize by checking element count and layout stability.
        This is more reliable than networkidle for JS-rendered content.
        """
        if not javascript_enabled:
            # No need for render stability checks without JavaScript
            await asyncio.sleep(1)
            return
        
        try:
            # Initial delay to allow JavaScript to start executing
            await asyncio.sleep(1)
            
            # Check DOM stability by comparing element counts
            previous_count = -1
            stable_checks = 0
            max_checks = 10
            check_interval = 0.5  # seconds
            
            for i in range(max_checks):
                # Count elements on the page
                current_count = await self.page.evaluate("""() => {
                    return document.querySelectorAll('*').length;
                }""")
                
                logger.info(f"DOM stability check {i+1}/{max_checks}: {current_count} elements (previous: {previous_count})")
                
                if current_count == previous_count and current_count > 10:
                    # DOM is potentially stable if element count hasn't changed
                    stable_checks += 1
                    if stable_checks >= 2:
                        logger.info(f"DOM appears stable after {i+1} checks")
                        break
                else:
                    # Reset stability counter
                    stable_checks = 0
                
                previous_count = current_count
                await asyncio.sleep(check_interval)
            
            # Additional wait for animations and final rendering
            await asyncio.sleep(2)
            
            # Verify content existence (check if main content area has elements)
            content_check = await self.page.evaluate("""() => {
                const mainContent = document.querySelector('main') || 
                                    document.querySelector('#content') || 
                                    document.querySelector('.content') ||
                                    document.querySelector('article') ||
                                    document.querySelector('body');
                                    
                return mainContent ? mainContent.querySelectorAll('*').length : 0;
            }""")
            
            logger.info(f"Content elements found: {content_check}")
            
            if content_check < 5:
                # Very few elements found, wait longer
                logger.warning("Few content elements detected, waiting longer for render...")
                await asyncio.sleep(3)
            
            return True
        except Exception as e:
            logger.warning(f"Error during render stability check: {str(e)}")
            # Fall back to simple wait
            await asyncio.sleep(3)
            return False

    async def navigate(self, url, javascript_enabled=False):
        """Navigate to a URL with improved error handling and retry logic."""
        if not self.page:
            logger.info("Browser not started, initializing before navigation")
            await self.start_browser(javascript_enabled=javascript_enabled)
        
        # Set maximum retries
        max_retries = 2
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                # Set a reasonable timeout for navigation
                logger.info(f"Navigating to {url} (attempt {retry_count + 1}/{max_retries + 1}) with JS {'enabled' if javascript_enabled else 'disabled'}")
                
                # Use consistent wait_until strategy regardless of JS setting
                # This ensures the page is at least initially loaded before we apply custom waiting
                await self.page.goto(url, timeout=60000, wait_until='domcontentloaded')
                
                # After basic loading, use our custom wait strategy
                logger.info(f"Basic page load complete, waiting for render stability...")
                await self.wait_for_render_stability(javascript_enabled)
                
                # Special case handling for known problematic sites
                site_keywords = ["splunk", "tableau", "dashboard", "visualize", "analytics"]
                is_complex_site = any(keyword in url.lower() for keyword in site_keywords)
                
                if javascript_enabled:
                    if is_complex_site:
                        # Force longer wait for complex sites when JS is enabled
                        logger.info(f"Detected complex JS site, applying extended waiting period...")
                        await asyncio.sleep(7)  # Long wait for complex JS sites
                    else:
                        # Default additional wait for JS-enabled sites
                        await asyncio.sleep(3)
                
                logger.info(f"Successfully navigated to {url}")
                return
            except Exception as e:
                retry_count += 1
                error_message = str(e)
                logger.warning(f"Navigation error on attempt {retry_count}/{max_retries + 1} for {url}: {error_message}")
                
                if "Page crashed" in error_message:
                    logger.info("Page crash detected, recreating page")
                    try:
                        # Close the crashed page if it exists
                        if self.page and not self.page.is_closed():
                            await self.page.close()
                        
                        # Create a new page
                        self.page = await self.context.new_page()
                        logger.info("Created new page after crash")
                        
                        # If we have retries left, continue to next attempt
                        if retry_count <= max_retries:
                            continue
                    except Exception as recovery_error:
                        logger.error(f"Error during page recreation: {str(recovery_error)}")
                
                # If we've reached max retries, raise the exception
                if retry_count > max_retries:
                    logger.error(f"Failed to navigate to {url} after {max_retries + 1} attempts")
                    raise
                
                # Wait before retrying
                await asyncio.sleep(2)
                
    def get_random_user_agent(self):
        """Return a random, realistic user agent string."""
        chrome_versions = ['112.0.5615.138', '114.0.5735.199', '115.0.5790.171', '116.0.5845.96', '117.0.5938.132', '118.0.5993.117', '119.0.6045.106', '120.0.6099.109', '121.0.6167.85', '122.0.6261.69', '123.0.6312.58', '134.0.0.0']
        
        os_versions = [
            ('Windows NT 10.0; Win64; x64', 'Windows 10'),
            ('Windows NT 11.0; Win64; x64', 'Windows 11'),
            ('Macintosh; Intel Mac OS X 10_15_7', 'macOS'),
            ('Macintosh; Intel Mac OS X 11_6_0', 'macOS'),
            ('X11; Linux x86_64', 'Linux'),
            ('X11; Ubuntu; Linux x86_64', 'Ubuntu')
        ]
        
        chrome_version = random.choice(chrome_versions)
        os_info, os_name = random.choice(os_versions)
        
        return f'Mozilla/5.0 ({os_info}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36'

    def get_random_viewport(self):
        """Return a random viewport size based on common screen resolutions."""
        common_resolutions = [
            {'width': 1366, 'height': 768},    # Most common
            {'width': 1920, 'height': 1080},   # Full HD
            {'width': 1536, 'height': 864},    # Common laptop
            {'width': 1440, 'height': 900},    # Common on Macs
            {'width': 1280, 'height': 800},    # Smaller laptops
            {'width': 1680, 'height': 1050},   # Larger monitors
            {'width': 1600, 'height': 900},    # Another common size
            {'width': 1280, 'height': 720},    # HD
            {'width': 1920, 'height': 1200},   # Widescreen monitors
            {'width': 2560, 'height': 1440}    # QHD screens
        ]
        
        # Add slight variations to make fingerprinting harder
        selected = random.choice(common_resolutions)
        jitter = random.randint(-10, 10)  # Small random adjustment
        
        return {
            'width': selected['width'] + jitter,
            'height': selected['height'] + jitter
        }

    async def start_browser(self, javascript_enabled=False):
        """Start a browser session with configurable JavaScript setting."""
        try:
            logger.info("Starting Playwright and browser")
            playwright = await async_playwright().start()
            
            # Configure browser with more robust settings
            browser_args = [
                '--disable-gpu',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-accelerated-video-decode',
                '--disable-features=site-per-process',
                '--disable-extensions',
                '--disable-background-networking',
                '--disable-default-apps',
                '--disable-sync',
                '--disable-translate',
                '--hide-scrollbars',
                '--metrics-recording-only',
                '--mute-audio',
                '--no-first-run'
            ]
            
            # Determine headless mode
            headless_mode = True
            if headless_mode:
                browser_args.extend([
                    '--headless=new',
                    '--disable-notifications',
                    '--disable-infobars'
                ])
            
            logger.info(f"Launching browser with enhanced arguments (headless={headless_mode}, js_enabled={javascript_enabled})")
            self.browser = await playwright.chromium.launch(
                headless=headless_mode,
                args=browser_args
            )
            
            # Get random viewport and user agent
            viewport = self.get_random_viewport()
            user_agent = self.get_random_user_agent()
            
            # Random timezone from common options
            timezone_ids = [
                'America/New_York', 
                'America/Chicago', 
                'America/Los_Angeles',
                'Europe/London', 
                'Europe/Paris',
                'Asia/Tokyo'
            ]
            timezone_id = random.choice(timezone_ids)
            
            # Random locale
            locales = ['en-US', 'en-GB', 'en-CA', 'fr-FR', 'de-DE', 'es-ES']
            locale = random.choice(locales)
            
            logger.info(f"Using viewport: {viewport}, user agent: {user_agent}, timezone: {timezone_id}")
            
            # Create browser context with configurable JavaScript setting
            self.context = await self.browser.new_context(
                viewport=viewport,
                user_agent=user_agent,
                locale=locale,
                timezone_id=timezone_id,
                has_touch=random.choice([True, False]),
                java_script_enabled=javascript_enabled,  # Use the provided JavaScript setting
                ignore_https_errors=True
            )
            
            logger.info("Creating new page")
            self.page = await self.context.new_page()
            
            # Set HTTP headers to appear more like a real browser
            await self.page.set_extra_http_headers({
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1'
            })
            
            logger.info(f"Browser started successfully with JavaScript {'enabled' if javascript_enabled else 'disabled'}")
        except Exception as e:
            logger.error(f"Failed to start browser: {str(e)}", exc_info=True)
            # Try to clean up resources if initialization fails
            try:
                if self.browser:
                    await self.browser.close()
            except:
                pass
            raise

    async def close(self):
        """Close the browser session and release resources."""
        try:
            if self.browser:
                logger.info("Closing browser")
                await self.browser.close()
                self.browser = None
                self.context = None
                self.page = None
                logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Error closing browser: {str(e)}")

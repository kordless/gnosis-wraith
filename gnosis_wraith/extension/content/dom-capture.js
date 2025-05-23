// dom-capture.js
// Extension Content Script for Gnosis Wraith
// This script captures the DOM content of the current page
// Version 1.2.1

/**
 * Captures the DOM content and page metadata
 * @returns {Object} An object containing the page's DOM, metadata and other details
 */
function captureDomContent() {
  try {
    console.log('Starting DOM content capture');
    
    // First, try to force lazy load images to load
    forceLazyImagesLoad();
    
    // Get the complete HTML content - use cloneNode for better reliability
    let docClone = document.documentElement.cloneNode(true);
    const html = docClone.outerHTML;
    docClone = null; // Help garbage collection
    
    if (!html) {
      console.error('Failed to capture HTML content');
      throw new Error('Could not capture page HTML');
    }
    
    console.log(`Captured HTML content (${html.length} bytes)`);
    
    // Log the size of the content for debugging
    const contentSizeKB = Math.round(html.length / 1024);
    console.log(`Content size: ${contentSizeKB} KB`);
    
    // Extract metadata from the page
    const metadata = {
      title: document.title || 'Untitled Page',
      url: window.location.href,
      baseUrl: window.location.origin,
      timestamp: new Date().toISOString(),
      pageStats: {
        linkCount: document.getElementsByTagName('a').length,
        imageCount: document.getElementsByTagName('img').length,
        scriptCount: document.getElementsByTagName('script').length,
        formCount: document.getElementsByTagName('form').length,
        tableCount: document.getElementsByTagName('table').length,
        wordCount: document.body ? document.body.innerText.split(/\s+/).filter(Boolean).length : 0
      }
    };
    
    console.log('Extracted page metadata');

    // Look for common main content selectors to help with content extraction
    const contentSelectors = [
      'main', 'article', '#content', '.content', '.main-content',
      '[role="main"]', '#main', '.article', '.post', '.post-content',
      '.entry-content', '.page-content', '.site-content', '.body-content',
      '#primary', '.primary', '#primary-content', '.primary-content',
      '.container .row', '.container-fluid .row'
    ];
    
    let mainContentSelector = null;
    
    // First try to find the most specific selector that has content
    for (const selector of contentSelectors) {
      const element = document.querySelector(selector);
      if (element && element.textContent && element.textContent.trim().length > 100) {
        // Check if it has substantial content
        mainContentSelector = selector;
        console.log(`Found main content selector with substantial content: ${selector}`);
        break;
      }
    }
    
    // If no selector with substantial content was found, try any with content
    if (!mainContentSelector) {
      for (const selector of contentSelectors) {
        if (document.querySelector(selector)) {
          mainContentSelector = selector;
          console.log(`Found main content selector: ${selector}`);
          break;
        }
      }
    }
    
    // Extract meta description if available
    let metaDescription = '';
    try {
      metaDescription = document.querySelector('meta[name="description"]')?.content || 
                        document.querySelector('meta[property="og:description"]')?.content || '';
    } catch (e) {
      console.warn('Error extracting meta description:', e);
    }
    
    // Extract favIcon if available
    let favIcon = '';
    try {
      const iconLinks = [
        'link[rel="icon"]',
        'link[rel="shortcut icon"]',
        'link[rel="apple-touch-icon"]',
        'link[rel="apple-touch-icon-precomposed"]'
      ];
      
      for (const selector of iconLinks) {
        const iconElement = document.querySelector(selector);
        if (iconElement && iconElement.href) {
          favIcon = iconElement.href;
          break;
        }
      }
      
      // If no icon found, use default favicon path
      if (!favIcon) {
        favIcon = `${window.location.origin}/favicon.ico`;
      }
    } catch (e) {
      console.warn('Error extracting favicon:', e);
      favIcon = `${window.location.origin}/favicon.ico`;
    }
    
    // Extract H1 and other important heading content
    let headings = {
      h1: [],
      h2: [],
      h3: []
    };
    
    try {
      document.querySelectorAll('h1').forEach(h => headings.h1.push(h.textContent.trim()));
      document.querySelectorAll('h2').forEach(h => headings.h2.push(h.textContent.trim()));
      document.querySelectorAll('h3').forEach(h => headings.h3.push(h.textContent.trim()));
      
      // Limit to first 10 of each to avoid excessive data
      headings.h1 = headings.h1.slice(0, 10);
      headings.h2 = headings.h2.slice(0, 10);
      headings.h3 = headings.h3.slice(0, 10);
    } catch (e) {
      console.warn('Error extracting headings:', e);
    }
    
    console.log('DOM capture complete');
    
    return {
      html: html,
      metadata: {
        ...metadata,
        description: metaDescription,
        favIcon: favIcon,
        mainContentSelector: mainContentSelector,
        headings: headings
      },
      captureMode: 'dom',
      captureSuccess: true
    };
  } catch (error) {
    console.error('Error in DOM capture:', error);
    
    // Return partial data if possible
    try {
      return {
        html: document.documentElement.innerHTML || '<html><body>Capture failed</body></html>',
        metadata: {
          title: document.title || 'Capture Error',
          url: window.location.href,
          timestamp: new Date().toISOString(),
          error: error.message
        },
        captureMode: 'dom',
        captureSuccess: false,
        error: error.message
      };
    } catch (fallbackError) {
      // Ultimate fallback with minimal data
      console.error('Fallback error in DOM capture:', fallbackError);
      return {
        html: '<html><body>DOM capture completely failed</body></html>',
        metadata: {
          title: 'Severe Capture Error',
          url: window.location.href || 'unknown',
          timestamp: new Date().toISOString(),
          error: `${error.message}; Fallback error: ${fallbackError.message}`
        },
        captureMode: 'dom',
        captureSuccess: false,
        error: `Multiple errors: ${error.message}; ${fallbackError.message}`
      };
    }
  }
}

/**
 * Takes a screenshot of the visible area
 * @returns {Promise<string>} Base64-encoded screenshot data
 */
async function captureVisibleArea() {
  return new Promise((resolve) => {
    // Request screenshot from background script
    chrome.runtime.sendMessage(
      { action: 'takeScreenshot' }, 
      response => resolve(response.screenshotData)
    );
  });
}

/**
 * Main handler for content capturing
 * @param {Object} options Capture options
 * @returns {Promise<Object>} Captured data
 */
async function captureContent(options = {}) {
  const domData = captureDomContent();
  
  // Only capture screenshot if requested
  if (options.includeScreenshot) {
    try {
      const screenshotData = await captureVisibleArea();
      domData.screenshot = screenshotData;
    } catch (err) {
      console.error('Screenshot capture failed:', err);
      domData.errors = {
        screenshot: `Screenshot failed: ${err.message}`
      };
    }
  }
  
  return domData;
}

// Listen for capture commands from popup or background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'capturePage') {
    const options = message.options || {};
    
    // Capture and respond
    captureContent(options)
      .then(data => {
        console.log('DOM capture complete', {
          url: data.metadata.url,
          title: data.metadata.title,
          htmlSize: data.html.length,
          hasScreenshot: !!data.screenshot
        });
        sendResponse({ success: true, data });
      })
      .catch(err => {
        console.error('DOM capture error:', err);
        sendResponse({ 
          success: false, 
          error: err.message || 'Unknown error during capture'
        });
      });
      
    // Return true to indicate we'll respond asynchronously
    return true;
  }
});

// Inject a small helper for popup UI to show capture is available
document.documentElement.setAttribute('data-gnosis-wraith-ready', 'true');
console.log('Gnosis Wraith DOM capture initialized');

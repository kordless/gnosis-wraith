// dom-capture.js
// Extension Content Script for Gnosis Wraith
// This script captures the DOM content of the current page

/**
 * Captures the DOM content and page metadata
 * @returns {Object} An object containing the page's DOM, metadata and other details
 */
function captureDomContent() {
  // Get the complete HTML content
  const html = document.documentElement.outerHTML;
  
  // Extract metadata from the page
  const metadata = {
    title: document.title,
    url: window.location.href,
    baseUrl: window.location.origin,
    timestamp: new Date().toISOString(),
    pageStats: {
      linkCount: document.getElementsByTagName('a').length,
      imageCount: document.getElementsByTagName('img').length,
      scriptCount: document.getElementsByTagName('script').length,
      formCount: document.getElementsByTagName('form').length,
      tableCount: document.getElementsByTagName('table').length,
      wordCount: document.body.innerText.split(/\s+/).filter(Boolean).length
    }
  };

  // Look for common main content selectors to help with content extraction
  const contentSelectors = [
    'main', 'article', '#content', '.content', '.main-content',
    '[role="main"]', '#main'
  ];
  
  let mainContentSelector = null;
  for (const selector of contentSelectors) {
    if (document.querySelector(selector)) {
      mainContentSelector = selector;
      break;
    }
  }
  
  // Extract meta description if available
  const metaDescription = document.querySelector('meta[name="description"]')?.content || '';
  
  // Extract favIcon if available
  const favIcon = document.querySelector('link[rel="icon"]')?.href || 
                  document.querySelector('link[rel="shortcut icon"]')?.href || 
                  `${window.location.origin}/favicon.ico`;
  
  return {
    html: html,
    metadata: {
      ...metadata,
      description: metaDescription,
      favIcon: favIcon,
      mainContentSelector: mainContentSelector
    },
    captureMode: 'dom'
  };
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

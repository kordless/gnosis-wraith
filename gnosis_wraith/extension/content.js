/**
 * Updated WebWraith content.js with support for job-based processing
 * Version 1.3.0
 */

// Keep track of overlay elements
let flashOverlay = null;
let captureOverlay = null;
let progressBar = null;  // New progress bar element
let isCapturing = false; // Flag to prevent multiple captures
let captureTimeout = null; // For auto-hiding the message

// Keep track of hidden elements
let hiddenNavbars = [];
let captureOverlayHidden = false;

// Create a flash effect for taking screenshots
function createFlashEffect() {
  // Remove any existing overlay
  if (flashOverlay) {
    document.body.removeChild(flashOverlay);
  }
  
  // Create flash element
  flashOverlay = document.createElement('div');
  flashOverlay.style.position = 'fixed';
  flashOverlay.style.top = '0';
  flashOverlay.style.left = '0';
  flashOverlay.style.width = '100%';
  flashOverlay.style.height = '100%';
  flashOverlay.style.backgroundColor = 'white';
  flashOverlay.style.opacity = '0.3';
  flashOverlay.style.zIndex = '999999';
  flashOverlay.style.pointerEvents = 'none';
  flashOverlay.style.transition = 'opacity 300ms ease-out';
  document.body.appendChild(flashOverlay);
  
  // Fade out effect
  setTimeout(() => {
    flashOverlay.style.opacity = '0';
    setTimeout(() => {
      if (flashOverlay && flashOverlay.parentNode) {
        document.body.removeChild(flashOverlay);
        flashOverlay = null;
      }
    }, 300);
  }, 50);
}

// Create a capturing indicator with progress bar
function showCapturingIndicator(message = 'Capturing screenshot...') {
  // Remove any existing overlay
  if (captureOverlay) {
    try {
      document.body.removeChild(captureOverlay);
    } catch (e) {
      console.warn('Failed to remove existing overlay:', e);
    }
  }
  
  // Clear any existing auto-hide timeout
  if (captureTimeout) {
    clearTimeout(captureTimeout);
    captureTimeout = null;
  }
  
  try {
    // Create indicator element
    captureOverlay = document.createElement('div');
    captureOverlay.id = 'gnosis-wraith-capture-overlay';
    captureOverlay.style.position = 'fixed';
    captureOverlay.style.top = '20px';
    captureOverlay.style.right = '20px';
    captureOverlay.style.padding = '14px 20px';
    captureOverlay.style.backgroundColor = '#3498db';
    captureOverlay.style.color = 'white';
    captureOverlay.style.borderRadius = '8px';
    captureOverlay.style.fontFamily = 'Arial, sans-serif';
    captureOverlay.style.fontSize = '14px';
    captureOverlay.style.fontWeight = 'bold';
    captureOverlay.style.boxShadow = '0 4px 15px rgba(0,0,0,0.3)';
    captureOverlay.style.zIndex = '2147483647'; // Max z-index value
    captureOverlay.style.transition = 'all 0.3s ease-in-out';
    captureOverlay.style.transform = 'translateY(0)';
    captureOverlay.style.opacity = '1';
    captureOverlay.style.minWidth = '250px';
    captureOverlay.style.backdropFilter = 'blur(5px)';
    captureOverlay.style.border = '1px solid rgba(255, 255, 255, 0.2)';
    captureOverlay.textContent = message;
    
    // Add icon (using emoji for simplicity)
    const iconSpan = document.createElement('span');
    iconSpan.textContent = '📷 ';
    iconSpan.style.marginRight = '8px';
    captureOverlay.insertBefore(iconSpan, captureOverlay.firstChild);
    
    // Add progress bar container
    const progressContainer = document.createElement('div');
    progressContainer.style.marginTop = '10px';
    progressContainer.style.width = '100%';
    progressContainer.style.height = '8px';
    progressContainer.style.backgroundColor = 'rgba(255, 255, 255, 0.2)';
    progressContainer.style.borderRadius = '4px';
    progressContainer.style.overflow = 'hidden';
    
    // Add progress bar
    progressBar = document.createElement('div');
    progressBar.style.width = '0%';
    progressBar.style.height = '100%';
    progressBar.style.backgroundColor = 'white';
    progressBar.style.borderRadius = '4px';
    progressBar.style.transition = 'width 0.3s ease-in-out';
    progressBar.style.boxShadow = '0 0 5px rgba(255, 255, 255, 0.5)';
    
    // Add animation effect for visual interest
    const keyframes = `
      @keyframes progress-pulse {
        0% { opacity: 0.8; }
        50% { opacity: 1; }
        100% { opacity: 0.8; }
      }
    `;
    const style = document.createElement('style');
    style.innerHTML = keyframes;
    document.head.appendChild(style);
    
    progressBar.style.animation = 'progress-pulse 2s ease-in-out infinite';
    
    progressContainer.appendChild(progressBar);
    captureOverlay.appendChild(progressContainer);
    
    // Create an entrance animation
    captureOverlay.style.transform = 'translateY(-20px)';
    captureOverlay.style.opacity = '0';
    
    document.body.appendChild(captureOverlay);
    
    // Trigger entrance animation
    setTimeout(() => {
      if (captureOverlay) {
        captureOverlay.style.transform = 'translateY(0)';
        captureOverlay.style.opacity = '1';
      }
    }, 10);
  } catch (error) {
    console.error('Error creating capture overlay:', error);
    // Create fallback overlay if something went wrong
    try {
      captureOverlay = document.createElement('div');
      captureOverlay.style.position = 'fixed';
      captureOverlay.style.top = '20px';
      captureOverlay.style.right = '20px';
      captureOverlay.style.padding = '10px';
      captureOverlay.style.backgroundColor = '#3498db';
      captureOverlay.style.color = 'white';
      captureOverlay.style.zIndex = '999999';
      captureOverlay.textContent = message;
      document.body.appendChild(captureOverlay);
    } catch (e) {
      console.error('Failed to create fallback overlay:', e);
    }
  }
}

// Update capturing indicator text and progress
function updateCapturingIndicator(message, progress = null) {
  if (captureOverlay) {
    // Update message
    if (typeof message === 'string') {
      // Replace only the text node, preserving the progress bar
      const textNodes = Array.from(captureOverlay.childNodes)
        .filter(node => node.nodeType === Node.TEXT_NODE);
      
      if (textNodes.length > 0) {
        textNodes[0].nodeValue = message;
      } else {
        // Insert text node at the beginning
        captureOverlay.insertBefore(
          document.createTextNode(message), 
          captureOverlay.firstChild
        );
      }
    }
    
    // Update progress bar if provided
    if (progress !== null && progressBar) {
      progressBar.style.width = `${progress}%`;
    }
  }
}

// Show success message and auto-hide
function showSuccessAndHide(message = 'Screenshot captured successfully!') {
  // Clear any existing timeout first
  if (captureTimeout) {
    clearTimeout(captureTimeout);
    captureTimeout = null;
  }
  
  // Create a new notification or update existing one
  showCapturingIndicator(message);
  
  if (captureOverlay) {
    captureOverlay.style.backgroundColor = '#27ae60'; // Change to green
    
    // Set progress to 100%
    if (progressBar) {
      progressBar.style.width = '100%';
    }
    
    // Auto-hide after 3 seconds
    captureTimeout = setTimeout(() => {
      if (captureOverlay) {
        captureOverlay.style.opacity = '0';
        setTimeout(() => {
          hideCapturingIndicator();
        }, 500);
      }
    }, 3000);
  }
}

// Show error message and auto-hide
function showErrorAndHide(message = 'Error capturing screenshot') {
  // Clear any existing timeout first
  if (captureTimeout) {
    clearTimeout(captureTimeout);
    captureTimeout = null;
  }
  
  // Create a new notification or update existing one
  showCapturingIndicator(message);
  
  if (captureOverlay) {
    captureOverlay.style.backgroundColor = '#e74c3c'; // Change to red
    
    // Set progress to 100%
    if (progressBar) {
      progressBar.style.width = '100%';
    }
    
    // Add a retry button
    const retryButton = document.createElement('button');
    retryButton.textContent = 'Retry';
    retryButton.style.marginTop = '10px';
    retryButton.style.padding = '5px 10px';
    retryButton.style.backgroundColor = 'white';
    retryButton.style.color = '#e74c3c';
    retryButton.style.border = 'none';
    retryButton.style.borderRadius = '4px';
    retryButton.style.cursor = 'pointer';
    retryButton.style.fontWeight = 'bold';
    retryButton.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
    
    // Add hover effect
    retryButton.onmouseover = function() {
      this.style.backgroundColor = '#f8f8f8';
    };
    retryButton.onmouseout = function() {
      this.style.backgroundColor = 'white';
    };
    
    // Add click handler
    retryButton.onclick = function() {
      hideCapturingIndicator();
      
      // Retry the capture after a short delay
      setTimeout(() => {
        captureVisibleScreen(true);
      }, 500);
    };
    
    captureOverlay.appendChild(retryButton);
    
    // Auto-hide after 8 seconds (longer to give time to use the retry button)
    captureTimeout = setTimeout(() => {
      if (captureOverlay) {
        captureOverlay.style.opacity = '0';
        setTimeout(() => {
          hideCapturingIndicator();
        }, 500);
      }
    }, 8000);
  }
  
  // Log the error for debugging
  console.error(`Gnosis Wraith Error: ${message}`);
}

// Remove capturing indicator
function hideCapturingIndicator() {
  if (captureOverlay && captureOverlay.parentNode) {
    document.body.removeChild(captureOverlay);
    captureOverlay = null;
    progressBar = null;
  }
  
  if (captureTimeout) {
    clearTimeout(captureTimeout);
    captureTimeout = null;
  }
}

// Hide UI elements before capturing a screenshot
function hideUIElementsForCapture() {
  // Hide capture overlay
  if (captureOverlay && !captureOverlayHidden) {
    captureOverlayHidden = true;
    if (captureOverlay.style.display !== 'none') {
      captureOverlay.style.display = 'none';
    }
  }
  
  // Array of common navbar class/id selectors
  const navbarSelectors = [
    'header', 'nav', '.navbar', '.navigation', '.nav-bar', '.site-header', '.header',
    '#navbar', '#nav', '#header', '#mainNav', '#top-nav', '.fixed-top', '.sticky-top'
  ];
  
  hiddenNavbars = [];
  
  // Try to identify and hide navigation elements
  navbarSelectors.forEach(selector => {
    const elements = document.querySelectorAll(selector);
    elements.forEach(el => {
      if (el.style.display !== 'none' && isVisible(el)) {
        hiddenNavbars.push({
          element: el,
          display: el.style.display || getComputedStyle(el).display,
          visibility: el.style.visibility || getComputedStyle(el).visibility
        });
        
        el.style.display = 'none';
      }
    });
  });
  
  return new Promise(resolve => setTimeout(resolve, 100));
}

// Check if an element is visible
function isVisible(element) {
  const style = window.getComputedStyle(element);
  return style.display !== 'none' && 
         style.visibility !== 'hidden' && 
         style.opacity !== '0' &&
         element.offsetWidth > 0 && 
         element.offsetHeight > 0;
}

// Restore UI elements after capturing
function restoreUIElements() {
  // Restore navbar elements
  hiddenNavbars.forEach(item => {
    item.element.style.display = item.display;
    item.element.style.visibility = item.visibility;
  });
  
  // Restore capture overlay
  if (captureOverlay && captureOverlayHidden) {
    captureOverlay.style.display = '';
    captureOverlayHidden = false;
  }
  
  hiddenNavbars = [];
}

// Function to handle user-initiated screenshots
async function captureVisibleScreen(sendToApi = false) {
  // Create visual indicator that screenshot is being taken
  createFlashEffect();
  showCapturingIndicator('Preparing to capture...', 0);
  
  try {
    // Hide UI elements first
    await hideUIElementsForCapture();
    
    updateCapturingIndicator('Taking screenshot...', 10);
    
    // Notify the background script to take the screenshot
    chrome.runtime.sendMessage({
      action: 'captureCurrentPage',
      url: window.location.href,
      title: document.title,
      sendToApi: sendToApi
    }, (response) => {
      // Restore UI regardless of response
      restoreUIElements();
      
      if (!response) {
        showErrorAndHide('Failed to capture screenshot');
      } else if (response.status === 'processing') {
        // We're just starting the process, status updates will come later
        updateCapturingIndicator('Processing screenshot...', 20);
      } else if (response.status !== 'capturing') {
        if (sendToApi) {
          showSuccessAndHide('Screenshot sent for processing!');
        } else {
          showSuccessAndHide('Screenshot saved!');
        }
      }
    });
  } catch (error) {
    // Make sure UI is restored if there's an error
    restoreUIElements();
    showErrorAndHide(`Error: ${error.message}`);
  }
}

// Add keyboard shortcut: Alt+Shift+W for local save, Alt+Shift+U for API upload
document.addEventListener('keydown', (e) => {
  // Alt+Shift+W for local save
  if (e.altKey && e.shiftKey && e.key === 'W') {
    captureVisibleScreen(false);
  }
  
  // Alt+Shift+U for API upload
  if (e.altKey && e.shiftKey && e.key === 'U') {
    captureVisibleScreen(true);
  }
});

// Listen for messages from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'captureVisibleTab') {
    createFlashEffect();
    showCapturingIndicator('Taking screenshot...', 10);
    sendResponse({ status: 'capturing' });
    return true;
  } else if (message.action === 'capturingStarted') {
    createFlashEffect();
    hideUIElementsForCapture().then(() => {
      showCapturingIndicator('Taking screenshot...', 10);
      sendResponse({ status: 'showing indicator' });
    });
    return true;
  } else if (message.action === 'uploadStarted') {
    updateCapturingIndicator('Uploading to server...', 30);
    sendResponse({ status: 'upload started' });
    return true;
  } else if (message.action === 'uploadJobStarted') {
    // New: Specific message for job-based processing
    updateCapturingIndicator('Processing initiated...', 40);
    sendResponse({ status: 'job started' });
    return true;
  } else if (message.action === 'uploadProgress') {
    // Updated to include percentage
    const progressMsg = message.status === 'processing' ? 
      'Processing image...' : 
      `${message.status.charAt(0).toUpperCase() + message.status.slice(1)}...`;
    
    updateCapturingIndicator(progressMsg, message.progress);
    sendResponse({ status: 'progress shown' });
    return true;
  } else if (message.action === 'uploadFinished') {
    restoreUIElements();
    showSuccessAndHide('Processing complete!');
    
    // If a report URL was provided, create a link
    if (message.reportUrl) {
      // Create a link to the report
      const linkDiv = document.createElement('div');
      linkDiv.style.position = 'fixed';
      linkDiv.style.bottom = '20px';
      linkDiv.style.right = '20px';
      linkDiv.style.backgroundColor = '#ffffff';
      linkDiv.style.padding = '10px';
      linkDiv.style.borderRadius = '5px';
      linkDiv.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
      linkDiv.style.zIndex = '999998';
      
      const link = document.createElement('a');
      link.href = message.reportUrl;
      link.target = '_blank';
      link.textContent = message.extractedText ? 'View Analysis Report' : 'View Report';
      link.style.color = '#3498db';
      link.style.textDecoration = 'none';
      link.style.fontFamily = 'Arial, sans-serif';
      link.style.fontWeight = 'bold';
      
      // If there's extracted text, show a preview
      if (message.extractedText) {
        const textPreview = document.createElement('div');
        textPreview.style.marginTop = '8px';
        textPreview.style.padding = '8px';
        textPreview.style.backgroundColor = '#f8f9fa';
        textPreview.style.borderRadius = '3px';
        textPreview.style.maxHeight = '100px';
        textPreview.style.overflow = 'auto';
        textPreview.style.fontSize = '12px';
        textPreview.style.fontFamily = 'monospace';
        textPreview.style.color = '#333';
        
        // Limit text length
        const previewText = message.extractedText.length > 200 ?
          message.extractedText.substring(0, 200) + '...' :
          message.extractedText;
        
        textPreview.textContent = 'Extracted Text: ' + previewText;
        linkDiv.appendChild(textPreview);
      }
      
      linkDiv.appendChild(link);
      document.body.appendChild(linkDiv);
      
      // Remove after 15 seconds
      setTimeout(() => {
        if (linkDiv.parentNode) {
          document.body.removeChild(linkDiv);
        }
      }, 15000);
    }
    
    sendResponse({ status: 'upload complete' });
    return true;
  } else if (message.action === 'uploadError') {
    showErrorAndHide(`Upload error: ${message.error}`);
    sendResponse({ status: 'error shown' });
    return true;
  } else if (message.action === 'capturingFinished') {
    restoreUIElements();
    console.log('Received capturingFinished message:', message);
    // Make sure any timeout is cleared
    if (captureTimeout) {
      clearTimeout(captureTimeout);
      captureTimeout = null;
    }
    // Fix ReferenceError by safely accessing the sendToApi property
    const wasApiSent = (message && message.sendToApi) ? true : false;
    const statusMessage = wasApiSent ? 'Screenshot sent for processing!' : 'Screenshot saved!';
    
    // Immediately hide any existing notification first
    hideCapturingIndicator();
    
    // Then show the success message with auto-hide
    showSuccessAndHide(statusMessage);
    sendResponse({ status: 'success shown' });
    return true;
  } else if (message.action === 'capturingError') {
    restoreUIElements();
    console.log('Received capturingError message:', message);
    // Make sure any timeout is cleared
    if (captureTimeout) {
      clearTimeout(captureTimeout);
      captureTimeout = null;
    }
    showErrorAndHide(`Error: ${message.error || 'Unknown error occurred'}`);
    sendResponse({ status: 'error shown' });
    return true;
  } else if (message.action === 'readyForFullPageCapture') {
    if (!isCapturing) {
      captureFullPage(message.sendToApi);
      sendResponse({ status: 'starting full page capture' });
    } else {
      sendResponse({ status: 'capture already in progress' });
    }
    return true;
  } else if (message.action === 'requestFullPageCapture') {
    if (!isCapturing) {
      captureFullPage(message.sendToApi);
      sendResponse({ status: 'capturing' });
    } else {
      sendResponse({ status: 'capture already in progress' });
    }
    return true;
  }
});

/**
 * Attempts to force lazy-loaded images to load by scrolling and simulating visibility
 */
function forceLazyImagesLoad() {
  try {
    // Get all images on the page
    const images = document.querySelectorAll('img');
    console.log(`Attempting to force load ${images.length} images`);
    
    // Find images with lazy loading attributes or empty src
    const lazyImages = Array.from(images).filter(img => {
      return img.loading === 'lazy' || 
             img.getAttribute('data-src') || 
             img.getAttribute('data-lazy-src') ||
             img.getAttribute('data-original') ||
             (!img.src || img.src === '' || img.src.indexOf('data:image') === 0);
    });
    
    console.log(`Found ${lazyImages.length} potentially lazy-loaded images`);
    
    // Common lazy load attribute patterns
    const lazyAttributes = [
      'data-src', 
      'data-original', 
      'data-lazy', 
      'data-lazy-src', 
      'data-srcset',
      'data-original-set'
    ];
    
    // For each lazy image
    lazyImages.forEach(img => {
      // Check for lazy load attributes and apply them to src
      for (const attr of lazyAttributes) {
        const lazyValue = img.getAttribute(attr);
        if (lazyValue && lazyValue !== img.src) {
          console.log(`Setting src=${lazyValue} for image with ${attr}`);
          img.src = lazyValue;
          break;
        }
      }
      
      // Create and dispatch a load event
      try {
        const loadEvent = new Event('load');
        img.dispatchEvent(loadEvent);
      } catch (e) {
        console.warn('Error dispatching load event:', e);
      }
    });
    
    // Attempt to trigger scroll events for frameworks that use scroll detection
    window.dispatchEvent(new Event('scroll'));
    document.dispatchEvent(new Event('scroll'));
    
    console.log('Lazy image loading attempt complete');
  } catch (error) {
    console.error('Error in forceLazyImagesLoad:', error);
  }
}

// Initialize
function initialize() {
  // Add to window object for debugging and direct access if needed
  window.webwraithCapture = captureVisibleScreen;
  
  // Let background script know content script is loaded
  chrome.runtime.sendMessage({ action: 'contentScriptReady' });
}

// Run initialization when DOM is fully loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initialize);
} else {
  initialize();
}

// Function to capture full page (scrolling)
async function captureFullPage(sendToApi = false) {
  // Prevent multiple captures from running simultaneously
  if (isCapturing) {
    console.log("Full page capture already in progress");
    return;
  }
  
  try {
    isCapturing = true;
    
    // Show capturing indicator
    showCapturingIndicator('Starting full page capture...', 0);
    
    // Hide UI elements first
    await hideUIElementsForCapture();
    
    // Get original scroll position to restore later
    const originalScrollTop = window.scrollY || document.documentElement.scrollTop;
    const originalScrollLeft = window.scrollX || document.documentElement.scrollLeft;
    
    // Force any lazy load elements to load by scrolling through the page first
    const scrollStep = Math.floor(window.innerHeight * 0.8);
    const maxScroll = document.documentElement.scrollHeight;
    
    // Quick scroll through the page to trigger lazy loading
    updateCapturingIndicator('Preparing page (loading content)...', 2);
    for (let currentScroll = 0; currentScroll < maxScroll; currentScroll += scrollStep) {
      window.scrollTo(0, currentScroll);
      // Small delay to allow for loading
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    // Scroll back to the top
    window.scrollTo(0, 0);
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Get the full page dimensions AFTER forcing lazy load content
    const fullHeight = Math.max(
      document.body.scrollHeight,
      document.body.offsetHeight,
      document.documentElement.clientHeight,
      document.documentElement.scrollHeight,
      document.documentElement.offsetHeight
    );
    
    const fullWidth = Math.max(
      document.body.scrollWidth,
      document.body.offsetWidth,
      document.documentElement.clientWidth,
      document.documentElement.scrollWidth,
      document.documentElement.offsetWidth
    );
    
    // Get viewport dimensions with a small buffer to account for potential rounding errors
    // Using 90% to ensure proper overlap between screenshots
    const viewportHeight = Math.floor(window.innerHeight * 0.9);
    const viewportWidth = Math.floor(window.innerWidth * 0.9);
    
    // Calculate the number of screenshots needed
    const numRows = Math.ceil(fullHeight / viewportHeight);
    const numCols = Math.ceil(fullWidth / viewportWidth);
    const totalScreenshots = numRows * numCols;
    
    console.log(`Full page capture: Dimensions ${fullWidth}x${fullHeight}, Viewport: ${viewportWidth}x${viewportHeight}, Grid: ${numCols}x${numRows}, Total: ${totalScreenshots} screenshots`);
    
    updateCapturingIndicator(`Preparing to capture full page (${numRows}x${numCols})...`, 5);
    
    // Notify background script to begin the process
    chrome.runtime.sendMessage({
      action: 'beginFullPageCapture',
      dimensions: {
        fullWidth,
        fullHeight,
        viewportWidth,
        viewportHeight,
        numCols,
        numRows
      },
      url: window.location.href,
      title: document.title,
      sendToApi
    });
    
    // Wait for a short timeout to ensure background script is ready
    await new Promise(resolve => setTimeout(resolve, 800));
    
    // Take screenshots by scrolling through the page
    let screenshotCount = 0;
    let screenshotPromises = [];
    let retryCount = 0;
    const maxRetries = 2;
    
    // Helper function to take a single screenshot with retry logic
    const takeScreenshotWithRetry = async (row, col) => {
      const scrollTop = row * viewportHeight;
      const scrollLeft = col * viewportWidth;
      let attempts = 0;
      
      while (attempts <= maxRetries) {
        try {
          // Scroll to position
          window.scrollTo(scrollLeft, scrollTop);
          
          // Wait for rendering and any lazy-loaded images to appear
          // Increase wait time on retry attempts
          await new Promise(resolve => setTimeout(resolve, 400 + (attempts * 200)));
          
          // Take screenshot of visible area
          const result = await new Promise((resolve, reject) => {
            const timeoutId = setTimeout(() => {
              reject(new Error('Screenshot request timed out'));
            }, 5000);
            
            chrome.runtime.sendMessage({
              action: 'captureVisibleArea',
              position: { row, col, scrollTop, scrollLeft },
              sendToApi
            }, (response) => {
              clearTimeout(timeoutId);
              if (response && response.success) {
                console.log(`Screenshot at row=${row}, col=${col} captured successfully`);
                resolve(true);
              } else {
                console.error(`Screenshot at row=${row}, col=${col} failed`, response?.error);
                resolve(false);
              }
            });
          });
          
          if (result) {
            return true;
          }
          
          console.warn(`Retrying screenshot at row=${row}, col=${col}, attempt ${attempts + 1}`);
          attempts++;
        } catch (err) {
          console.error(`Error capturing screenshot at row=${row}, col=${col}:`, err);
          if (attempts < maxRetries) {
            console.warn(`Retrying after error, attempt ${attempts + 1}`);
            attempts++;
          } else {
            return false;
          }
        }
      }
      
      retryCount++;
      return false;
    };
    
    for (let row = 0; row < numRows; row++) {
      for (let col = 0; col < numCols; col++) {
        // Create a promise for this screenshot
        const screenshotPromise = (async () => {
          const result = await takeScreenshotWithRetry(row, col);
          
          // Calculate progress regardless of result
          screenshotCount++;
          const progress = Math.floor((screenshotCount / totalScreenshots) * 70) + 5; // 5-75% progress
          updateCapturingIndicator(`Capturing screen ${screenshotCount}/${totalScreenshots}...`, progress);
          
          return result;
        })();
        
        screenshotPromises.push(screenshotPromise);
        
        // Process in batches of 3 screenshots at a time to avoid overwhelming the browser
        if (screenshotPromises.length >= 3) {
          await Promise.all(screenshotPromises);
          screenshotPromises = [];
        }
      }
    }
    
    // Wait for any remaining screenshot promises
    if (screenshotPromises.length > 0) {
      await Promise.all(screenshotPromises);
    }
    
    if (retryCount > 0) {
      console.warn(`Completed with ${retryCount} failed screenshots after retries`);
    }
    
    // Restore original scroll position
    window.scrollTo(originalScrollLeft, originalScrollTop);
    
    updateCapturingIndicator('Processing full page screenshot...', 80);
    
    // Send the completed message to background script for stitching
    chrome.runtime.sendMessage({
      action: 'finishFullPageCapture',
      url: window.location.href,
      title: document.title,
      dimensions: {
        fullWidth,
        fullHeight,
        viewportWidth,
        viewportHeight,
        numCols,
        numRows
      },
      sendToApi
    }, (response) => {
      if (response && response.success) {
        updateCapturingIndicator('Full page screenshot complete!', 100);
        // Restore UI elements
        restoreUIElements();
        
        // Show success message
        const statusMessage = sendToApi ? 
          'Full page screenshot sent for processing!' : 
          'Full page screenshot saved!';
        
        showSuccessAndHide(statusMessage);
      } else {
        // Show error message
        restoreUIElements();
        showErrorAndHide(`Error: ${response?.error || 'Failed to process full page screenshot'}`);
      }
    });
    
  } catch (error) {
    console.error('Error in full page capture process:', error);
    restoreUIElements();
    showErrorAndHide(`Error: ${error.message}`);
    
    // Notify background of failure
    chrome.runtime.sendMessage({
      action: 'fullPageCaptureFailed',
      error: error.message
    });
  } finally {
    // Always release the capture lock
    isCapturing = false;
  }
}

// Add full page capture to window object
window.webwraithCaptureFullPage = captureFullPage;

// Modify existing keyboard shortcut to include full page option
document.addEventListener('keydown', (e) => {
  // Alt+Shift+F for full page capture (local save)
  if (e.altKey && e.shiftKey && e.key === 'F') {
    captureFullPage(false);
  }
  
  // Alt+Shift+A for full page capture with API upload
  if (e.altKey && e.shiftKey && e.key === 'A') {
    captureFullPage(true);
  }
});

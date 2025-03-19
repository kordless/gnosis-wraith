// WebWraith content script for browser-based screenshot capture
// This script runs in the context of the browser tab

// Keep track of overlay elements
let flashOverlay = null;
let captureOverlay = null;
let isCapturing = false; // Flag to prevent multiple captures
let captureTimeout = null; // For auto-hiding the message

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

// Create a capturing indicator
function showCapturingIndicator(message = 'Capturing screenshot...') {
  // Remove any existing overlay
  if (captureOverlay) {
    document.body.removeChild(captureOverlay);
  }
  
  // Clear any existing auto-hide timeout
  if (captureTimeout) {
    clearTimeout(captureTimeout);
    captureTimeout = null;
  }
  
  // Create indicator element
  captureOverlay = document.createElement('div');
  captureOverlay.style.position = 'fixed';
  captureOverlay.style.top = '20px';
  captureOverlay.style.right = '20px';
  captureOverlay.style.padding = '12px 20px';
  captureOverlay.style.backgroundColor = '#3498db';
  captureOverlay.style.color = 'white';
  captureOverlay.style.borderRadius = '4px';
  captureOverlay.style.fontFamily = 'Arial, sans-serif';
  captureOverlay.style.fontSize = '14px';
  captureOverlay.style.fontWeight = 'bold';
  captureOverlay.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
  captureOverlay.style.zIndex = '999999';
  captureOverlay.style.transition = 'opacity 0.5s ease-in-out';
  captureOverlay.textContent = message;
  document.body.appendChild(captureOverlay);
}

// Update capturing indicator text
function updateCapturingIndicator(message) {
  if (captureOverlay) {
    captureOverlay.textContent = message;
  }
}

// Show success message and auto-hide
function showSuccessAndHide(message = 'Screenshot captured successfully!') {
  if (captureOverlay) {
    captureOverlay.style.backgroundColor = '#27ae60'; // Change to green
    captureOverlay.textContent = message;
    
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
  if (captureOverlay) {
    captureOverlay.style.backgroundColor = '#e74c3c'; // Change to red
    captureOverlay.textContent = message;
    
    // Auto-hide after 5 seconds
    captureTimeout = setTimeout(() => {
      if (captureOverlay) {
        captureOverlay.style.opacity = '0';
        setTimeout(() => {
          hideCapturingIndicator();
        }, 500);
      }
    }, 5000);
  }
}

// Remove capturing indicator
function hideCapturingIndicator() {
  if (captureOverlay && captureOverlay.parentNode) {
    document.body.removeChild(captureOverlay);
    captureOverlay = null;
  }
  
  if (captureTimeout) {
    clearTimeout(captureTimeout);
    captureTimeout = null;
  }
}

// Function to handle user-initiated screenshots
function captureVisibleScreen() {
  // Create visual indicator that screenshot is being taken
  createFlashEffect();
  showCapturingIndicator('Taking screenshot...');
  
  // Notify the background script to take the screenshot
  chrome.runtime.sendMessage({
    action: 'captureCurrentPage',
    url: window.location.href,
    title: document.title
  }, (response) => {
    if (!response || response.status !== 'capturing') {
      showSuccessAndHide('Screenshot saved!');
    }
  });
}

// Add keyboard shortcut: Alt+Shift+W
document.addEventListener('keydown', (e) => {
  // Alt+Shift+W
  if (e.altKey && e.shiftKey && e.key === 'W') {
    captureVisibleScreen();
  }
});

// Listen for messages from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'captureVisibleTab') {
    createFlashEffect();
    showCapturingIndicator('Taking screenshot...');
    sendResponse({ status: 'capturing' });
    return true;
  } else if (message.action === 'capturingStarted') {
    createFlashEffect();
    showCapturingIndicator('Taking screenshot...');
    sendResponse({ status: 'showing indicator' });
    return true;
  } else if (message.action === 'capturingFinished') {
    showSuccessAndHide('Screenshot saved!');
    sendResponse({ status: 'success shown' });
    return true;
  } else if (message.action === 'readyForFullPageCapture') {
    if (!isCapturing) {
      captureFullPage();
      sendResponse({ status: 'starting full page capture' });
    } else {
      sendResponse({ status: 'capture already in progress' });
    }
    return true;
  } else if (message.action === 'requestFullPageCapture') {
    if (!isCapturing) {
      captureFullPage();
      sendResponse({ status: 'capturing' });
    } else {
      sendResponse({ status: 'capture already in progress' });
    }
    return true;
  }
});

// Inject a button into certain sites if needed (optional)
function injectCaptureButton() {
  // Check if we're on a site where we want to add a capture button
  // For example, sites with login walls or paywalls
  const currentDomain = window.location.hostname;
  const sitesToInject = [
    'medium.com',
    'nytimes.com',
    'wsj.com'
    // Add more sites as needed
  ];
  
  if (!sitesToInject.some(site => currentDomain.includes(site))) {
    return;
  }
  
  // Create button
  const button = document.createElement('button');
  button.textContent = 'Capture Screenshot';
  button.style.position = 'fixed';
  button.style.bottom = '20px';
  button.style.right = '20px';
  button.style.padding = '10px 15px';
  button.style.backgroundColor = '#3498db';
  button.style.color = 'white';
  button.style.border = 'none';
  button.style.borderRadius = '4px';
  button.style.fontFamily = 'Arial, sans-serif';
  button.style.fontSize = '14px';
  button.style.fontWeight = 'bold';
  button.style.cursor = 'pointer';
  button.style.zIndex = '999999';
  button.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
  
  // Add click handler
  button.addEventListener('click', captureVisibleScreen);
  
  // Add to page
  document.body.appendChild(button);
}

// Initialize
function initialize() {
  // Add to window object for debugging and direct access if needed
  window.webwraithCapture = captureVisibleScreen;
  
  // Inject button for specific sites
  injectCaptureButton();
  
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
async function captureFullPage() {
  // Prevent multiple captures from running simultaneously
  if (isCapturing) {
    console.log("Full page capture already in progress");
    return;
  }
  
  try {
    isCapturing = true;
    
    // Show capturing indicator
    showCapturingIndicator('Starting full page capture...');
    
    // Get page dimensions
    const scrollHeight = Math.max(
      document.documentElement.scrollHeight,
      document.body.scrollHeight
    );
    const scrollWidth = Math.max(
      document.documentElement.scrollWidth,
      document.body.scrollWidth
    );
    
    // Get visible dimensions
    const viewportHeight = window.innerHeight;
    const viewportWidth = window.innerWidth;
    
    // Save original scroll position to restore later
    const originalScrollTop = window.scrollY;
    const originalScrollLeft = window.scrollX;
    
    // Notify background we're doing a full page capture
    updateCapturingIndicator('Preparing capture process...');
    
    try {
      const response = await new Promise((resolve, reject) => {
        chrome.runtime.sendMessage({
          action: 'startFullPageCapture',
          dimensions: {
            scrollHeight,
            scrollWidth,
            viewportHeight,
            viewportWidth
          }
        }, response => {
          if (chrome.runtime.lastError) {
            reject(chrome.runtime.lastError);
          } else if (!response || response.status !== 'ready') {
            reject(new Error("Background not ready: " + (response ? response.status : "No response")));
          } else {
            resolve(response);
          }
        });
      });
      
      // Calculate number of steps needed
      const verticalSteps = Math.ceil(scrollHeight / viewportHeight);
      const horizontalSteps = Math.ceil(scrollWidth / viewportWidth);
      
      // Track progress
      let capturesComplete = 0;
      const totalCaptures = verticalSteps * horizontalSteps;
      
      // Update indicator to show progress
      updateCapturingIndicator(`Capturing full page (0/${totalCaptures})`);
      
      // Capture each viewport section
      const sections = [];
      
      // Sequential capture to avoid race conditions
      for (let vStep = 0; vStep < verticalSteps; vStep++) {
        for (let hStep = 0; hStep < horizontalSteps; hStep++) {
          // Calculate scroll position
          const scrollTop = vStep * viewportHeight;
          const scrollLeft = hStep * viewportWidth;
          
          // Scroll to position
          window.scrollTo(scrollLeft, scrollTop);
          
          // Wait for any repaints/reflows to complete
          await new Promise(resolve => setTimeout(resolve, 300));
          
          // Request background to take screenshot
          try {
            updateCapturingIndicator(`Capturing section ${capturesComplete+1} of ${totalCaptures}`);
            
            const response = await new Promise((resolve, reject) => {
              chrome.runtime.sendMessage({
                action: 'captureViewport',
                position: {
                  x: scrollLeft,
                  y: scrollTop,
                  vStep,
                  hStep,
                  viewportWidth,
                  viewportHeight
                }
              }, response => {
                if (chrome.runtime.lastError) {
                  reject(chrome.runtime.lastError);
                } else if (!response) {
                  reject(new Error("No response from background"));
                } else if (response.error) {
                  reject(new Error(response.error));
                } else {
                  resolve(response);
                }
              });
            });
            
            // Store the section if we got a valid response
            if (response && response.dataUrl) {
              sections.push({
                dataUrl: response.dataUrl,
                position: {
                  x: scrollLeft,
                  y: scrollTop,
                  width: viewportWidth,
                  height: viewportHeight
                }
              });
            }
          } catch (error) {
            console.error(`Error capturing section ${capturesComplete+1}/${totalCaptures}:`, error);
          }
          
          // Update progress
          capturesComplete++;
          updateCapturingIndicator(`Captured ${capturesComplete} of ${totalCaptures} sections`);
        }
      }
      
      // Restore original scroll position
      window.scrollTo(originalScrollLeft, originalScrollTop);
      
      // Send all sections to background script for stitching
      updateCapturingIndicator('Creating full page image...');
      
      if (sections.length === 0) {
        throw new Error("No sections were captured");
      }
      
      await new Promise((resolve, reject) => {
        chrome.runtime.sendMessage({
          action: 'stitchFullPageScreenshot',
          sections: sections,
          dimensions: {
            scrollHeight,
            scrollWidth,
            viewportHeight,
            viewportWidth
          },
          url: window.location.href,
          title: document.title
        }, response => {
          if (chrome.runtime.lastError) {
            reject(chrome.runtime.lastError);
          } else if (!response) {
            reject(new Error("No response from stitching request"));
          } else if (response.error) {
            reject(new Error(response.error));
          } else {
            resolve(response);
          }
        });
      });
      
      // The background script will handle the download
      showSuccessAndHide('Full page screenshot saved!');
      
    } catch (error) {
      console.error("Error in capture/stitch process:", error);
      showErrorAndHide(`Error: ${error.message}`);
      
      // Notify background of failure
      chrome.runtime.sendMessage({
        action: 'fullPageCaptureFailed',
        error: error.message
      });
    }
  } catch (error) {
    console.error('Error in full page capture process:', error);
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
  // Alt+Shift+F for full page capture
  if (e.altKey && e.shiftKey && e.key === 'F') {
    captureFullPage();
  }
});
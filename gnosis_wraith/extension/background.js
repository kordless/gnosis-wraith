// background.js
// Background script for Gnosis Wraith extension

// Global API settings that can be configured from the options page
let apiSettings = {
  serverUrl: 'http://localhost:5678',
  captureOptions: {
    includeScreenshot: true,
    processingMode: 'enhanced'  // 'enhanced', 'basic', or 'none'
  }
};

// Track full page capture state
let fullPageCaptureState = {
  inProgress: false,
  dimensions: null,
  screenshots: [],
  tabId: null,
  sendToApi: false
};

// Load settings from storage when the extension starts
chrome.storage.sync.get(['serverUrl', 'captureOptions'], (result) => {
  if (result.serverUrl) {
    apiSettings.serverUrl = result.serverUrl;
  }
  if (result.captureOptions) {
    apiSettings.captureOptions = {...apiSettings.captureOptions, ...result.captureOptions};
  }
  console.log('Loaded settings:', apiSettings);
});

// Take a screenshot of the current tab
async function takeScreenshot() {
  try {
    const dataUrl = await chrome.tabs.captureVisibleTab(null, {format: 'png'});
    return dataUrl;
  } catch (error) {
    console.error('Error taking screenshot:', error);
    return null;
  }
}

// Function to stitch together screenshots for full page capture
async function stitchFullPageScreenshot() {
  try {
    if (!fullPageCaptureState.dimensions || fullPageCaptureState.screenshots.length === 0) {
      throw new Error('Missing capture data for stitching');
    }
    
    const { fullWidth, fullHeight, viewportWidth, viewportHeight, numCols, numRows } = fullPageCaptureState.dimensions;
    
    // Create a canvas to stitch the screenshots together
    const canvas = new OffscreenCanvas(fullWidth, fullHeight);
    const ctx = canvas.getContext('2d');
    
    // Draw each screenshot onto the canvas
    for (const screenshot of fullPageCaptureState.screenshots) {
      // Create an image from the dataUrl
      const img = await createImageBitmap(await (await fetch(screenshot.dataUrl)).blob());
      
      // Calculate position
      const x = screenshot.position.col * viewportWidth;
      const y = screenshot.position.row * viewportHeight;
      
      // Draw the image at the correct position
      ctx.drawImage(img, x, y);
    }
    
    // Convert canvas to dataURL
    const blob = await canvas.convertToBlob({type: 'image/png'});
    const reader = new FileReader();
    
    return new Promise((resolve) => {
      reader.onloadend = () => resolve(reader.result);
      reader.readAsDataURL(blob);
    });
  } catch (error) {
    console.error('Error stitching full page screenshot:', error);
    throw error;
  }
}

// Send captured data to the server
async function sendToServer(capturedData) {
  try {
    const response = await fetch(`${apiSettings.serverUrl}/api/extension-capture`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        ...capturedData,
        processingOptions: apiSettings.captureOptions
      })
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Server returned ${response.status}: ${errorText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error sending data to server:', error);
    return {
      success: false,
      error: error.message || 'Failed to communicate with server'
    };
  }
}

// Listen for messages from content scripts or popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // Handle screenshot requests from content script
  if (message.action === 'takeScreenshot') {
    takeScreenshot()
      .then(screenshotData => {
        sendResponse({ success: true, screenshotData });
      })
      .catch(error => {
        sendResponse({ 
          success: false, 
          error: error.message || 'Screenshot failed'
        });
      });
    return true; // Keep the message channel open for async response
  }
  
  // Handle visible area capture for full page screenshot
  if (message.action === 'captureVisibleArea') {
    if (!fullPageCaptureState.inProgress) {
      sendResponse({
        success: false,
        error: 'No full page capture in progress'
      });
      return true;
    }
    
    takeScreenshot()
      .then(dataUrl => {
        if (dataUrl) {
          // Store this screenshot
          fullPageCaptureState.screenshots.push({
            dataUrl,
            position: message.position
          });
          
          sendResponse({
            success: true,
            dataUrl
          });
        } else {
          sendResponse({
            success: false,
            error: 'Failed to capture screenshot'
          });
        }
      })
      .catch(error => {
        sendResponse({
          success: false,
          error: error.message || 'Screenshot failed'
        });
      });
    
    return true; // Keep the message channel open for async response
  }
  
  // Handle beginning of full page capture process
  if (message.action === 'beginFullPageCapture') {
    // Initialize the full page capture state
    fullPageCaptureState = {
      inProgress: true,
      dimensions: message.dimensions,
      screenshots: [],
      tabId: sender.tab?.id,
      sendToApi: message.sendToApi,
      url: message.url,
      title: message.title
    };
    
    console.log('Beginning full page capture with dimensions:', message.dimensions);
    sendResponse({ success: true });
    return true;
  }
  
  // Handle completion of full page capture
  if (message.action === 'finishFullPageCapture') {
    if (!fullPageCaptureState.inProgress) {
      sendResponse({
        success: false,
        error: 'No full page capture in progress'
      });
      return true;
    }
    
    console.log(`Finishing full page capture with ${fullPageCaptureState.screenshots.length} screenshots`);
    
    // Stitch together the screenshots
    stitchFullPageScreenshot()
      .then(async (dataUrl) => {
        // Reset the in-progress flag
        fullPageCaptureState.inProgress = false;
        
        if (fullPageCaptureState.sendToApi) {
          // Send to server
          try {
            const serverResponse = await sendToServer({
              screenshot: dataUrl,
              url: fullPageCaptureState.url,
              title: fullPageCaptureState.title,
              fullPage: true
            });
            
            sendResponse({
              success: true,
              dataUrl,
              serverResponse
            });
          } catch (error) {
            sendResponse({
              success: false,
              error: error.message || 'Failed to upload to server'
            });
          }
        } else {
          // Save locally
          try {
            // Create a download
            chrome.downloads.download({
              url: dataUrl,
              filename: `${sanitizeFilename(fullPageCaptureState.title || 'screenshot')}_full.png`,
              saveAs: true
            }, (downloadId) => {
              if (chrome.runtime.lastError) {
                sendResponse({
                  success: false,
                  error: chrome.runtime.lastError.message
                });
              } else {
                sendResponse({
                  success: true,
                  dataUrl,
                  downloadId
                });
              }
            });
          } catch (error) {
            sendResponse({
              success: false,
              error: error.message || 'Failed to save screenshot'
            });
          }
        }
      })
      .catch(error => {
        fullPageCaptureState.inProgress = false;
        sendResponse({
          success: false,
          error: error.message || 'Failed to stitch screenshot'
        });
      });
    
    return true; // Keep the message channel open for async response
  }
  
  // Handle full page capture failure
  if (message.action === 'fullPageCaptureFailed') {
    console.error('Full page capture failed:', message.error);
    fullPageCaptureState.inProgress = false;
    fullPageCaptureState.screenshots = [];
    sendResponse({ acknowledged: true });
    return true;
  }
  
  // Handle content capture and upload
  if (message.action === 'captureAndSend') {
    const tabId = sender.tab?.id || message.tabId;
    
    if (!tabId) {
      sendResponse({ 
        success: false, 
        error: 'No tab specified for capture'
      });
      return;
    }
    
    // Request the DOM capture from the content script
    chrome.tabs.sendMessage(
      tabId, 
      { action: 'capturePage', options: apiSettings.captureOptions },
      async (response) => {
        if (!response || !response.success) {
          sendResponse({
            success: false,
            error: response?.error || 'Content script did not respond'
          });
          return;
        }
        
        // Send to server
        const serverResponse = await sendToServer(response.data);
        
        // Pass the server response back
        sendResponse({
          success: serverResponse.success,
          data: serverResponse,
          error: serverResponse.error
        });
      }
    );
    
    return true; // Keep the message channel open for async response
  }
});

// Helper function to sanitize filenames
function sanitizeFilename(filename) {
  return filename
    .replace(/[\\/:*?"<>|]/g, '_') // Remove invalid characters
    .replace(/\s+/g, '_')          // Replace spaces with underscores
    .substring(0, 100);            // Limit length
}

// Add context menu for page capture
chrome.contextMenus.create({
  id: 'capturePageDom',
  title: 'Capture page with Gnosis Wraith',
  contexts: ['page']
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'capturePageDom') {
    chrome.tabs.sendMessage(
      tab.id, 
      { action: 'capturePage', options: apiSettings.captureOptions },
      async (response) => {
        if (!response || !response.success) {
          console.error('DOM capture failed:', response?.error);
          return;
        }
        
        // Send to server
        const serverResponse = await sendToServer(response.data);
        
        // Notify user of result
        chrome.tabs.sendMessage(tab.id, {
          action: 'showNotification',
          success: serverResponse.success,
          message: serverResponse.success 
            ? 'Page captured successfully' 
            : `Capture failed: ${serverResponse.error}`
        });
      }
    );
  }
});

console.log('Gnosis Wraith background script initialized');

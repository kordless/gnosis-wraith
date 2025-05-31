// background.js
// Background script for Gnosis Wraith extension
// Version 1.3.0

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
    
    console.log(`Starting stitching with dimensions: ${fullWidth}x${fullHeight}, viewportSize: ${viewportWidth}x${viewportHeight}, grid: ${numCols}x${numRows}, screenshots: ${fullPageCaptureState.screenshots.length}`);
    
    // Validate screenshot count
    const expectedScreenshots = numCols * numRows;
    if (fullPageCaptureState.screenshots.length < expectedScreenshots) {
      console.warn(`Warning: Received ${fullPageCaptureState.screenshots.length} screenshots, expected ${expectedScreenshots}`);
    }
    
    // Create a canvas to stitch the screenshots together
    let canvas;
    let ctx;
    
    try {
      // Try using OffscreenCanvas (more efficient)
      canvas = new OffscreenCanvas(fullWidth, fullHeight);
      ctx = canvas.getContext('2d');
    } catch (e) {
      // Fallback to regular canvas if OffscreenCanvas not supported
      console.log('Falling back to regular canvas');
      canvas = document.createElement('canvas');
      canvas.width = fullWidth;
      canvas.height = fullHeight;
      ctx = canvas.getContext('2d');
    }
    
    // Set white background to avoid transparent areas
    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(0, 0, fullWidth, fullHeight);
    
    // Sort screenshots by position to ensure correct order
    const sortedScreenshots = [...fullPageCaptureState.screenshots].sort((a, b) => {
      if (a.position.row !== b.position.row) {
        return a.position.row - b.position.row;
      }
      return a.position.col - b.position.col;
    });
    
    console.log(`Screenshots sorted, processing ${sortedScreenshots.length} images`);
    
    // Track successful/failed screenshots
    let successCount = 0;
    let errorCount = 0;
    
    // Draw each screenshot onto the canvas
    for (const screenshot of sortedScreenshots) {
      try {
        if (!screenshot.dataUrl) {
          console.warn(`Skipping screenshot with missing dataUrl at position row:${screenshot.position.row}, col:${screenshot.position.col}`);
          errorCount++;
          continue;
        }
        
        // Create an image from the dataUrl
        const imgBlob = await (await fetch(screenshot.dataUrl)).blob();
        const img = await createImageBitmap(imgBlob);
        
        // Calculate position
        const x = screenshot.position.col * viewportWidth;
        const y = screenshot.position.row * viewportHeight;
        
        // Verify position is valid
        if (x < 0 || y < 0 || x >= fullWidth || y >= fullHeight) {
          console.warn(`Invalid position for screenshot: ${x},${y}`);
          errorCount++;
          continue;
        }
        
        // Draw the image at the correct position
        ctx.drawImage(img, x, y);
        successCount++;
      } catch (imgError) {
        console.error(`Error processing screenshot at row ${screenshot.position.row}, col ${screenshot.position.col}:`, imgError);
        errorCount++;
      }
    }
    
    console.log(`Stitching status: ${successCount} successful, ${errorCount} failed`);
    
    if (successCount === 0) {
      throw new Error(`Failed to process any screenshots for stitching`);
    }
    
    // Convert canvas to dataURL
    let dataUrl;
    
    if (canvas instanceof OffscreenCanvas) {
      // For OffscreenCanvas
      const blob = await canvas.convertToBlob({type: 'image/png'});
      dataUrl = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result);
        reader.onerror = () => reject(new Error('Failed to convert blob to data URL'));
        reader.readAsDataURL(blob);
      });
    } else {
      // For regular canvas
      dataUrl = canvas.toDataURL('image/png');
    }
    
    if (!dataUrl || dataUrl === 'data:,') {
      throw new Error('Failed to generate data URL from canvas');
    }
    
    console.log('Stitching complete, data URL created');
    return dataUrl;
  } catch (error) {
    console.error('Error stitching full page screenshot:', error);
    throw error;
  }
}

// Send captured data to the server
async function sendToServer(capturedData) {
  try {
    // Make sure we're using the correct API endpoint
    const apiEndpoint = '/api/extension-capture';
    
    // Ensure server URL is properly formatted
    let serverUrl = apiSettings.serverUrl;
    if (!serverUrl.startsWith('http://') && !serverUrl.startsWith('https://')) {
      serverUrl = 'http://' + serverUrl;
    }
    serverUrl = serverUrl.replace(/\/$/, ''); // Remove trailing slash if present
    
    // Log the request for debugging
    console.log(`Sending data to ${serverUrl}${apiEndpoint}`, {
      url: capturedData.url,
      title: capturedData.title,
      hasScreenshot: !!capturedData.screenshot,
      processingOptions: apiSettings.captureOptions
    });
    
    const response = await fetch(`${serverUrl}${apiEndpoint}`, {
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
    
    const jsonResponse = await response.json();
    console.log('Server response:', jsonResponse);
    return jsonResponse;
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

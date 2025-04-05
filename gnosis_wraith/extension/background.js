// Background script for WebWraith Capture extension

// Configuration
let isCapturing = false;
let fullPageCaptureInProgress = false;

// Convert data URL to blob for download
function dataUrlToBlob(dataUrl) {
  let byteString;
  if (dataUrl.split(',')[0].indexOf('base64') >= 0) {
    byteString = atob(dataUrl.split(',')[1]);
  } else {
    byteString = unescape(dataUrl.split(',')[1]);
  }
  
  // Separate out the mime component
  const mimeString = dataUrl.split(',')[0].split(':')[1].split(';')[0];
  
  // Write the bytes of the string to an ArrayBuffer
  const ia = new Uint8Array(byteString.length);
  for (let i = 0; i < byteString.length; i++) {
    ia[i] = byteString.charCodeAt(i);
  }
  
  return new Blob([ia], {type: mimeString});
}

// Switch to capture icon to indicate processing
const setCaptureIcon = async () => {
  try {
    await chrome.action.setIcon({path: {
      16: "images/cursor-32.png",
      32: "images/cursor-32.png",
      48: "images/cursor-48.png",
      128: "images/icon-128.png"
    }});
  } catch(err) {
    console.error("Failed to set capture icon:", err);
  }
};

// Switch back to normal icon
const setNormalIcon = async () => {
  try {
    await chrome.action.setIcon({path: {
      16: "images/icon-16.png",
      32: "images/icon-32.png",
      48: "images/icon-48.png",
      128: "images/icon-128.png"
    }});
  } catch(err) {
    console.error("Failed to set normal icon:", err);
  }
};

// Initialize server URL settings
async function initializeServerUrl() {
  try {
    // Get current server URL from storage
    const { serverUrl } = await chrome.storage.local.get(['serverUrl']);
    
    // If no server URL is set, initialize with default
    if (!serverUrl) {
      await chrome.storage.local.set({ serverUrl: 'http://localhost:5678' });
      console.log("Set default server URL: http://localhost:5678");
    } else {
      console.log(`Using existing server URL: ${serverUrl}`);
    }
  } catch (error) {
    console.error("Error initializing server URL:", error);
  }
}

// Create context menu items when extension is installed
chrome.runtime.onInstalled.addListener(() => {
  // Initialize server URL
  initializeServerUrl();
  
  // Context menu for links
  chrome.contextMenus.create({
    id: 'capture-link',
    title: 'Capture screenshot of this link',
    contexts: ['link']
  });
  
  // Context menu for pages
  chrome.contextMenus.create({
    id: 'capture-page',
    title: 'Capture screenshot of this page',
    contexts: ['page']
  });
  
  // New context menu item for manual screenshot
  chrome.contextMenus.create({
    id: 'take-screenshot',
    title: 'Take screenshot',
    contexts: ['page']
  });
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'capture-link' && info.linkUrl) {
    captureUrl(info.linkUrl);
  } else if (info.menuItemId === 'capture-page' || info.menuItemId === 'take-screenshot') {
    captureAndDownload(tab);
  }
});

// Handle toolbar button clicks
chrome.action.onClicked.addListener((tab) => {
  captureAndDownload(tab);
});

// Listen for messages from popup or content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'captureUrl') {
    captureUrl(message.url, message.sendToApi);
    sendResponse({ status: 'capturing' });
    return true;
  }

  if (message.action === 'captureCurrentPage') {
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      if (tabs && tabs[0]) {
        // If fullPage flag is true, try to handle the request directly
        if (message.fullPage === true) {
          // Just use the existing content script if possible
          try {
            chrome.tabs.sendMessage(tabs[0].id, { 
              action: 'requestFullPageCapture',
              sendToApi: message.sendToApi
            }, 
              response => {
                if (chrome.runtime.lastError || !response) {
                  console.log("Content script not accessible, injecting script");
                  // Fallback - inject minimal script that just triggers the capture
                  chrome.scripting.executeScript({
                    target: { tabId: tabs[0].id },
                    function: (sendToApi) => {
                      chrome.runtime.sendMessage({
                        action: 'startFullPageCapture',
                        dimensions: {
                          scrollHeight: Math.max(document.documentElement.scrollHeight, document.body.scrollHeight),
                          scrollWidth: Math.max(document.documentElement.scrollWidth, document.body.scrollWidth),
                          viewportHeight: window.innerHeight,
                          viewportWidth: window.innerWidth
                        },
                        sendToApi: sendToApi
                      });
                    },
                    args: [message.sendToApi]
                  }).catch(error => {
                    console.error("Could not inject script:", error);
                    captureAndProcess(tabs[0], message.sendToApi);
                  });
                }
              });
          } catch (e) {
            console.error("Error communicating with content script:", e);
            // Still try to capture the visible part
            captureAndProcess(tabs[0], message.sendToApi);
          }
        } else {
          captureAndProcess(tabs[0], message.sendToApi);
        }
        sendResponse({ status: 'processing' });
      }
    });
    return true;
  }

  if (message.action === 'startFullPageCapture') {
    // If we already have a capture in progress, reject this new request
    if (fullPageCaptureInProgress) {
      console.log("Rejecting new capture request - capture already in progress");
      sendResponse({ status: 'busy', error: 'Capture already in progress' });
      return true;
    }
    
    console.log("Starting new full page capture process");
    fullPageCaptureInProgress = true;
    
    // Signal ready to begin capturing
    try {
      chrome.tabs.sendMessage(sender.tab.id, { 
        action: 'readyForFullPageCapture' 
      });
      console.log("Sent readyForFullPageCapture to tab", sender.tab.id);
    } catch (e) {
      console.error("Failed to send readyForFullPageCapture message:", e);
      fullPageCaptureInProgress = false;
    }
    
    sendResponse({ status: 'ready' });
    return true;
  }
  
  if (message.action === 'captureViewport') {
    if (!fullPageCaptureInProgress) {
      console.log("Received captureViewport but no capture in progress");
      sendResponse({ error: 'No full page capture in progress' });
      return true;
    }
    
    console.log("Capturing viewport", message.position ? `at ${message.position.x},${message.position.y}` : "");
    
    // Add a delay to avoid hitting quota limits
    setTimeout(() => {
      // Capture current viewport
      chrome.tabs.captureVisibleTab({ format: 'png' }, (dataUrl) => {
        if (!dataUrl) {
          console.error("Failed to capture viewport");
          sendResponse({ error: 'Failed to capture viewport' });
          return;
        }
        
        console.log("Viewport captured successfully");
        sendResponse({ dataUrl: dataUrl });
      });
    }, 300); // Add a 300ms delay between captures
    
    return true; // Will respond asynchronously
  }
  
  if (message.action === 'stitchFullPageScreenshot') {
    if (!fullPageCaptureInProgress) {
      console.log("Received stitchFullPageScreenshot but no capture in progress");
      sendResponse({ error: 'No full page capture in progress' });
      return true;
    }
    
    console.log("Received stitching request with", 
      message.sections ? message.sections.length : 0, "sections");
    
    // Get data from message
    const sections = message.sections || [];
    const dimensions = message.dimensions;
    const url = message.url;
    const title = message.title;
    const sendToApi = message.sendToApi || false;
    
    // Validate the sections data
    if (!Array.isArray(sections) || sections.length === 0) {
      console.error("Invalid sections data received");
      fullPageCaptureInProgress = false;
      sendResponse({ error: 'Invalid sections data' });
      return true;
    }
    
    // Create a canvas to stitch the screenshots together
    try {
      console.log("Starting stitching process");
      stitchAndProcessFullPageScreenshot(sections, dimensions, url, title, sender.tab.id, sendToApi);
      sendResponse({ status: 'stitching' });
    } catch (error) {
      console.error("Error in stitching process:", error);
      fullPageCaptureInProgress = false;
      sendResponse({ error: 'Stitching failed: ' + error.message });
    }
    
    return true;
  }
  
  if (message.action === 'fullPageCaptureFailed') {
    console.error(`Full page capture failed: ${message.error}`);
    fullPageCaptureInProgress = false;
    sendResponse({ status: 'error acknowledged' });
    return true;
  }
  
  if (message.action === 'serverUrlUpdated') {
    // Handle server URL update from popup
    const serverUrl = message.serverUrl;
    console.log(`Server URL updated to: ${serverUrl}`);
    
    // Test connection to the server
    fetch(`${serverUrl}/api/ping`, { 
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    })
    .then(response => {
      if (response.ok) {
        console.log("Connection to server successful");
      } else {
        console.warn(`Connection to server failed with status: ${response.status}`);
      }
    })
    .catch(error => {
      console.error(`Failed to connect to server: ${error.message}`);
    });
    
    sendResponse({ status: 'server url updated' });
    return true;
  }
});

// Function to capture URL and navigate to it for screenshot
async function captureUrl(url, sendToApi = false) {
  try {
    // Create a new tab with the specified URL
    let processedUrl = url;
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      processedUrl = 'https://' + url;
    }
    
    const tab = await chrome.tabs.create({ url: processedUrl, active: true });
    
    // Wait for page to load
    // This is a simple approach - a more robust solution would listen for tab loading events
    setTimeout(() => {
      captureAndProcess(tab, sendToApi);
    }, 5000); // Wait 5 seconds for the page to load
  } catch (error) {
    console.error("Error capturing URL:", error);
  }
}

// Function to upload image to Wraith API server
async function uploadImageToServer(dataUrl, tabInfo) {
  console.log("uploadImageToServer called with tabInfo:", JSON.stringify(tabInfo));
  try {
    // Get server URL from storage, default to localhost if not set
    let { serverUrl = 'http://localhost:5678' } = await chrome.storage.local.get(['serverUrl']);
    
    // Force the server URL to use the correct protocol, host and port
    if (!serverUrl.startsWith('http://')) {
      serverUrl = 'http://' + serverUrl;
    }
    
    // Ensure server URL ends without trailing slash
    serverUrl = serverUrl.replace(/\/$/, '');
    
    console.log(`Using server URL: ${serverUrl}`);
    const apiUrl = `${serverUrl}/api/upload`;
    
    // Convert dataUrl to Blob
    const blob = dataUrlToBlob(dataUrl);
    
    // Create FormData
    const formData = new FormData();
    formData.append('image', blob, 'screenshot.png');
    formData.append('title', `Screenshot of ${tabInfo.title || tabInfo.url}`);
    
    try {
      // Notify content script that upload is starting
      if (tabInfo.id) {
        chrome.tabs.sendMessage(tabInfo.id, { action: 'uploadStarted' });
      }
      
      // Use fetch instead of XMLHttpRequest (which isn't available in service workers)
      return new Promise((resolve, reject) => {
        fetch(apiUrl, {
          method: 'POST',
          headers: {
            'Origin': chrome.runtime.getURL('')
          },
          credentials: 'include',
          body: formData
        })
        .then(response => {
          if (response.ok) {
            return response.json();
          } else {
            if (tabInfo.id) {
              chrome.tabs.sendMessage(tabInfo.id, { 
                action: 'uploadError', 
                error: 'Server error: ' + response.status
              });
            }
            throw new Error('Server error: ' + response.status);
          }
        })
        .then(data => {
          // Notify content script of successful upload
          if (tabInfo.id) {
            // Get server base URL to construct report URL
            let reportUrl = `${serverUrl}/reports/${data.html_path}`;
            
            chrome.tabs.sendMessage(tabInfo.id, { 
              action: 'uploadFinished',
              reportUrl
            });
          }
          
          resolve(data);
        })
        .catch(error => {
          if (tabInfo.id) {
            chrome.tabs.sendMessage(tabInfo.id, { 
              action: 'uploadError', 
              error: error.message || 'Connection error'
            });
          }
          reject(error);
        });
      });
    } catch (error) {
      if (tabInfo.id) {
        chrome.tabs.sendMessage(tabInfo.id, { 
          action: 'uploadError', 
          error: error.message
        });
      }
      throw error;
    }
  } catch (error) {
    console.error("Error uploading to server:", error);
    throw error;
  }
}

// Function to capture and process
async function captureAndProcess(tab, sendToApi = false) {
  // Prevent multiple captures at once
  if (isCapturing) return;
  isCapturing = true;
  
  try {
    // Change icon to indicate processing
    await setCaptureIcon();
    
    // Notify content script that capture is starting
    try {
      chrome.tabs.sendMessage(tab.id, { action: 'capturingStarted' });
    } catch (e) {
      // Content script might not be ready, continue anyway
      console.log("Could not notify content script:", e);
    }
    
    // Capture the visible tab
    chrome.tabs.captureVisibleTab({format: "png"}, async (dataUrl) => {
      if (!dataUrl || !dataUrl.length) {
        console.error("Failed to capture screenshot");
        await setNormalIcon();
        isCapturing = false;
        return;
      }
      
      try {
        if (sendToApi) {
          // Upload to server
          try {
            await uploadImageToServer(dataUrl, tab);
            // History is updated in the uploadImageToServer function
          } catch (uploadError) {
            console.error("Error uploading to server:", uploadError);
            // Still save locally as fallback
            const filename = generateFilename(tab.title || tab.url);
            chrome.downloads.download({
              url: dataUrl,
              filename: filename,
              saveAs: true
            });
          }
        } else {
          // Generate filename based on page title or URL
          const filename = generateFilename(tab.title || tab.url);
          
          // Download directly from the data URL
          chrome.downloads.download({
            url: dataUrl,
            filename: filename,
            saveAs: true
          });
        }
        
        // Save to history
        saveToHistory(tab.url, tab.title);
      } catch (error) {
        console.error("Error processing screenshot:", error);
        console.error(`Failed to process screenshot: ${error.message}`);
      } finally {
        // Notify content script that capture has finished
        try {
          chrome.tabs.sendMessage(tab.id, { 
            action: 'capturingFinished',
            sendToApi: sendToApi
          });
        } catch (e) {
          console.log("Could not notify content script:", e);
        }
        
        await setNormalIcon();
        isCapturing = false;
      }
    });
  } catch (error) {
    console.error("Error in capture process:", error);
    await setNormalIcon();
    isCapturing = false;
  }
}

// For backward compatibility - just calls the new function with download mode
async function captureAndDownload(tab) {
  return captureAndProcess(tab, false);
}

// Function to generate a clean filename
function generateFilename(source) {
  // Remove invalid characters, replace spaces with underscores
  const cleanName = source.replace(/[\\\/\:\*\?\"\<\>\|]/g, "").replace(/\s+/g, "_");
  // Truncate if too long
  const truncated = cleanName.substring(0, 50);
  // Add timestamp and extension
  const timestamp = new Date().toISOString().replace(/[-:]/g, "").replace("T", "_").split(".")[0];
  return `screenshot_${truncated}_${timestamp}.png`;
}

// Save URL to history
function saveToHistory(url, title = "") {
  const MAX_HISTORY = 20;
  
  chrome.storage.local.get(['history'], function(result) {
    let history = result.history || [];
    
    // Remove duplicates
    history = history.filter(item => item.url !== url);
    
    // Add to beginning
    history.unshift({
      url: url,
      title: title,
      timestamp: Date.now()
    });
    
    // Limit size
    if (history.length > MAX_HISTORY) {
      history = history.slice(0, MAX_HISTORY);
    }
    
    // Save
    chrome.storage.local.set({history: history});
  });
}

// Function to stitch screenshots together and download
function stitchAndProcessFullPageScreenshot(sections, dimensions, url, title, tabId, sendToApi = false) {
  console.log("Creating canvas for stitching");
  
  // Create an offscreen canvas
  const canvas = new OffscreenCanvas(dimensions.scrollWidth, dimensions.scrollHeight);
  const ctx = canvas.getContext('2d');
  
  // Clear canvas
  ctx.fillStyle = 'white';
  ctx.fillRect(0, 0, dimensions.scrollWidth, dimensions.scrollHeight);
  
  // Track loaded images
  let loadedImages = 0;
  const totalImages = sections.length;
  
  console.log(`Processing ${totalImages} sections`);
  
  // Use ImageBitmap for better performance
  sections.forEach((section, index) => {
    // Check if section and dataUrl exist
    if (!section || !section.dataUrl) {
      console.error(`Invalid section data at index ${index}:`, section);
      loadedImages++;
      return; // Skip this section
    }
    
    try {
      console.log(`Processing section ${index+1}/${totalImages}`);
      
      // Extract the base64 data
      const base64Data = section.dataUrl.split(',')[1];
      // Convert to binary
      const binaryData = atob(base64Data);
      // Create array buffer
      const arrayBuffer = new ArrayBuffer(binaryData.length);
      const uint8Array = new Uint8Array(arrayBuffer);
      
      // Fill array with binary data
      for (let i = 0; i < binaryData.length; i++) {
        uint8Array[i] = binaryData.charCodeAt(i);
      }
      
      // Create blob
      const blob = new Blob([uint8Array], { type: 'image/png' });
      
      // Create image bitmap
      createImageBitmap(blob).then(bitmap => {
        // Check if position data is valid
        if (!section.position || typeof section.position.x === 'undefined') {
          console.error(`Invalid position data in section ${index+1}:`, section);
          loadedImages++;
          return;
        }
        
        console.log(`Drawing section ${index+1} at position ${section.position.x},${section.position.y}`);
        
        // Draw the bitmap at the correct position
        ctx.drawImage(bitmap, 
                    section.position.x, 
                    section.position.y, 
                    section.position.width, 
                    section.position.height);
        
        loadedImages++;
        console.log(`Processed ${loadedImages}/${totalImages} sections`);
        
        // When all images are loaded, convert canvas to blob and process
        if (loadedImages === totalImages) {
          finishStitching();
        }
      }).catch(error => {
        console.error(`Error creating image bitmap for section ${index+1}:`, error);
        loadedImages++;
        
        // If this was the last image, we still need to proceed with what we have
        if (loadedImages === totalImages) {
          finishStitching();
        }
      });
    } catch (error) {
      console.error(`Error processing section ${index+1}:`, error);
      loadedImages++;
      
      // If this was the last image, try to proceed with what we have
      if (loadedImages === totalImages) {
        finishStitching();
      }
    }
  });
  
  // Function to handle final steps of stitching and processing
  function finishStitching() {
    console.log("All sections processed, finalizing stitching and processing");
    fullPageCaptureInProgress = false; // Reset flag since we're done with the capture process
    
    try {
      // Convert canvas to blob
      canvas.convertToBlob({ type: 'image/png' }).then(blob => {
        // Try to notify tab that stitching is complete
        try {
          chrome.tabs.sendMessage(tabId, { 
            action: 'capturingFinished',
            sendToApi: sendToApi
          });
        } catch (e) {
          console.log("Could not notify content script:", e);
        }
        
        // In service workers, we need to handle blobs differently
        // We'll create a temporary URL for the blob
        try {
          const filename = generateFilename(title || url || "fullpage");
          
          if (sendToApi) {
            console.log("Sending stitched image to API server");
            
            // Convert blob to base64 using a different approach for service workers
            // Use a slightly different approach that works in service workers
            const blobUrl = URL.createObjectURL(blob);
            
            // Use fetch to get the blob data
            fetch(blobUrl)
              .then(response => response.arrayBuffer())
              .then(buffer => {
                // Convert array buffer to base64
                const base64 = btoa(
                  new Uint8Array(buffer)
                    .reduce((data, byte) => data + String.fromCharCode(byte), '')
                );
                
                const dataUrl = `data:image/png;base64,${base64}`;
                
                // Upload using our function
                return uploadImageToServer(dataUrl, { 
                  id: tabId, 
                  url: url, 
                  title: title 
                });
              })
              .catch(error => {
                console.error("Error processing blob:", error);
                // Fallback to download
                const downloadUrl = URL.createObjectURL(blob);
                chrome.downloads.download({
                  url: downloadUrl,
                  filename: "fullpage_" + filename,
                  saveAs: true
                });
                // Clean up the URL
                URL.revokeObjectURL(downloadUrl);
              })
              .finally(() => {
                // Clean up the URL
                URL.revokeObjectURL(blobUrl);
                
                // Save to history
                saveToHistory(url, title);
              });
            
          } else {
            // For direct download, we can use the blob URL directly
            console.log("Initiating download of stitched image");
            const blobUrl = URL.createObjectURL(blob);
            chrome.downloads.download({
              url: blobUrl,
              filename: "fullpage_" + filename,
              saveAs: true
            });
            
            // Clean up the URL after download starts
            setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
            
            // Save to history
            saveToHistory(url, title);
          }
        } catch (error) {
          console.error("Error in processing stitched image:", error);
        }
      }).catch(error => {
        console.error("Error converting canvas to blob:", error);
      });
    } catch (error) {
      console.error("Error in finishStitching:", error);
    }
  }
}
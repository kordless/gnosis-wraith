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

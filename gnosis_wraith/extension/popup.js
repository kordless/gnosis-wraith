// Popup script for Gnosis Wraith Capture extension
// Version 1.2.1

document.addEventListener('DOMContentLoaded', function() {
    const captureWithDomBtn = document.getElementById('capture-with-dom-btn');
    const captureFullPageBtn = document.getElementById('capture-full-page-btn');
    const messageDiv = document.getElementById('message');
    const serverUrlInput = document.getElementById('server-url-input');
    const saveSettingsBtn = document.getElementById('save-settings-btn');
    const reportsLink = document.getElementById('reports-link');
    
    // Load server settings
    loadServerSettings();
    
    // Add visual feedback on button hover (already handled in CSS)
    
    // Handle capture with DOM button click
    captureWithDomBtn.addEventListener('click', function() {
      capturePage(false);
    });
    
    // Handle full page capture button click
    captureFullPageBtn.addEventListener('click', function() {
      capturePage(true);
    });
    
    // Function to handle page capturing
    function capturePage(isFullPage) {
      chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        if (tabs && tabs[0] && tabs[0].url) {
          // Check if we're on a restricted page where content scripts can't run
          if (tabs[0].url.startsWith('chrome://') || 
              tabs[0].url.startsWith('chrome-extension://') || 
              tabs[0].url.startsWith('about:') ||
              tabs[0].url.startsWith('edge://') ||
              tabs[0].url.startsWith('brave://') ||
              tabs[0].url.startsWith('chrome-search://')) {
            
            showMessage('Cannot capture this page due to browser restrictions. Try a regular website.', 'error');
            return;
          }
          
          // Always send to API (Wraith) for analysis
          const sendToApi = true;
          
          if (isFullPage) {
            // First try sending a message to the background script
            chrome.runtime.sendMessage({
              action: 'captureCurrentPage',
              fullPage: true,
              tabId: tabs[0].id,
              sendToApi: sendToApi
            }, function(response) {
              showMessage('Capturing full page and DOM for analysis...', 'info');
              window.close(); // Close popup
            });
            
            // Also try sending to content script
            try {
              chrome.tabs.sendMessage(tabs[0].id, { 
                action: 'requestFullPageCapture',
                sendToApi: sendToApi
              }, function(response) {
                if (chrome.runtime.lastError) {
                  console.log("Content script not accessible, already handled via background script");
                }
              });
            } catch (e) {
              console.log("Error sending to content script, continuing with background script approach");
            }
          } else {
            // Send message to background script for regular capture
            chrome.runtime.sendMessage({
              action: 'captureCurrentPage',
              tabId: tabs[0].id,
              sendToApi: sendToApi
            }, function(response) {
              showMessage('Capturing screenshot and DOM for analysis...', 'info');
              window.close(); // Close popup
            });
          }
        } else {
          showMessage('Cannot access current tab', 'error');
        }
      });
    }
    
    // Function to show message with improved visibility
    function showMessage(text, type) {
      messageDiv.textContent = text;
      messageDiv.className = `message ${type}`;
      messageDiv.style.display = 'block';
      
      // Ensure the message is visible by scrolling to it
      messageDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
      
      // Add a pulsing animation for emphasis
      messageDiv.style.animation = 'none';
      setTimeout(() => {
        messageDiv.style.animation = 'pulse 1.5s ease-in-out';
      }, 10);
      
      // Add animation keyframes if they don't exist yet
      if (!document.getElementById('message-animation-styles')) {
        const style = document.createElement('style');
        style.id = 'message-animation-styles';
        style.textContent = `
          @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.03); }
            100% { transform: scale(1); }
          }
        `;
        document.head.appendChild(style);
      }
    }
    
    // Function to load server settings
    function loadServerSettings() {
      chrome.storage.local.get(['serverUrl'], function(result) {
        if (result.serverUrl) {
          serverUrlInput.value = result.serverUrl;
        } else {
          serverUrlInput.value = 'http://localhost:5678';
        }
      });
    }
    
    // Function to save server settings
    saveSettingsBtn.addEventListener('click', function() {
      const serverUrl = serverUrlInput.value.trim();
      
      if (serverUrl) {
        // Save server URL to storage
        chrome.storage.local.set({ serverUrl: serverUrl }, function() {
          showMessage('Server settings saved', 'info');
          
          // Notify background script of the change
          chrome.runtime.sendMessage({ 
            action: 'serverUrlUpdated', 
            serverUrl: serverUrl 
          });
        });
      } else {
        showMessage('Please enter a valid server URL', 'error');
      }
    });
    
    // Setup wraith link (main dashboard)
    const wraithLink = document.getElementById('wraith-link');
    
    wraithLink.addEventListener('click', function(e) {
      e.preventDefault();
      
      // Get server URL from storage
      chrome.storage.local.get(['serverUrl'], function(result) {
        let serverUrl = result.serverUrl || 'http://localhost:5678';
        
        // Force the server URL to use the correct protocol
        if (!serverUrl.startsWith('http://') && !serverUrl.startsWith('https://')) {
          serverUrl = 'http://' + serverUrl;
        }
        
        // Ensure server URL ends without trailing slash
        serverUrl = serverUrl.replace(/\/$/, '');
        
        // Open wraith page in a new tab - using the new URL structure
        chrome.tabs.create({ url: `${serverUrl}/wraith` });
      });
    });
    
    // Setup reports link
    reportsLink.addEventListener('click', function(e) {
      e.preventDefault();
      
      // Get server URL from storage
      chrome.storage.local.get(['serverUrl'], function(result) {
        let serverUrl = result.serverUrl || 'http://localhost:5678';
        
        // Force the server URL to use the correct protocol
        if (!serverUrl.startsWith('http://') && !serverUrl.startsWith('https://')) {
          serverUrl = 'http://' + serverUrl;
        }
        
        // Ensure server URL ends without trailing slash
        serverUrl = serverUrl.replace(/\/$/, '');
        
        // Open reports page in a new tab - using the new URL structure
        chrome.tabs.create({ url: `${serverUrl}/reports` });
      });
    });
    
    // Add help section toggle
    const helpLink = document.getElementById('help-link');
    const helpSection = document.getElementById('help-section');
    const closeHelpBtn = document.getElementById('close-help');
    
    helpLink.addEventListener('click', function(e) {
      e.preventDefault();
      helpSection.style.display = 'block';
      helpLink.style.display = 'none';
    });
    
    closeHelpBtn.addEventListener('click', function(e) {
      e.preventDefault();
      helpSection.style.display = 'none';
      helpLink.style.display = 'block';
    });
  });
  
  // Listen for content script messages
  chrome.runtime.onMessage.addListener(function(message, sender, sendResponse) {
    if (message.action === 'fullPageCaptureProgress') {
      // Update progress if popup is open
      const messageDiv = document.getElementById('message');
      if (messageDiv) {
        messageDiv.textContent = `Capturing: ${message.progress}%`;
        messageDiv.className = 'message info';
        messageDiv.style.display = 'block';
      }
    }
  });
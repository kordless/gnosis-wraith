// Popup script for WebWraith Capture extension

document.addEventListener('DOMContentLoaded', function() {
    const urlInput = document.getElementById('url-input');
    const captureUrlBtn = document.getElementById('capture-url-btn');
    const captureBtn = document.getElementById('capture-btn');
    const messageDiv = document.getElementById('message');
    const historyList = document.getElementById('history-list');
    const fullPageCheckbox = document.getElementById('full-page-checkbox');
    const serverUrlInput = document.getElementById('server-url-input');
    const saveSettingsBtn = document.getElementById('save-settings-btn');
    
    // Set focus on input
    urlInput.focus();
    
    // Load and display history
    loadHistory();
    
    // Load server settings
    loadServerSettings();
    
    // Handle Enter key in URL input
    urlInput.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        captureUrlBtn.click();
      }
    });
    
    // Handle capture URL button click
    captureUrlBtn.addEventListener('click', function() {
      const url = urlInput.value.trim();
      if (url) {
        // Check if we want to send to API
        const sendToApi = document.getElementById('url-send-to-api-checkbox').checked;
        
        // Send message to background script
        chrome.runtime.sendMessage({
          action: 'captureUrl',
          url: url,
          sendToApi: sendToApi
        }, function(response) {
          const message = sendToApi ? 
            'Opening page for capture and analysis...' : 
            'Opening page for capture...';
          showMessage(message, 'info');
        });
        
        window.close(); // Close popup
      } else {
        showMessage('Please enter a valid URL', 'error');
      }
    });
    
    // Handle capture current page button click
    captureBtn.addEventListener('click', function() {
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
          
          // Check if we want full page screenshot
          const isFullPage = fullPageCheckbox.checked;
          // Check if we want to send to API
          const sendToApi = document.getElementById('send-to-api-checkbox').checked;
          
          if (isFullPage) {
            // First try sending a message to the background script directly
            chrome.runtime.sendMessage({
              action: 'captureCurrentPage',
              fullPage: true,
              tabId: tabs[0].id,
              sendToApi: sendToApi
            }, function(response) {
              const message = sendToApi ? 
                'Capturing full page for analysis...' : 
                'Capturing full page...';
              showMessage(message, 'info');
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
              const message = sendToApi ? 
                'Capturing screenshot for analysis...' : 
                'Capturing screenshot...';
              showMessage(message, 'info');
              window.close(); // Close popup
            });
          }
        } else {
          showMessage('Cannot access current tab', 'error');
        }
      });
    });
    
    // Function to show message
    function showMessage(text, type) {
      messageDiv.textContent = text;
      messageDiv.className = `message ${type}`;
      messageDiv.style.display = 'block';
    }
    
    // Function to load history
    function loadHistory() {
      chrome.storage.local.get(['history'], function(result) {
        if (result.history && result.history.length > 0) {
          displayHistory(result.history);
        } else {
          historyList.innerHTML = '<div class="history-item">No recent captures</div>';
        }
      });
    }
    
    // Function to display history
    function displayHistory(history) {
      historyList.innerHTML = '';
      
      history.forEach(item => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        
        // Use title if available, otherwise use URL
        let displayText = item.title || item.url;
        
        // Truncate if too long
        if (displayText.length > 40) {
          displayText = displayText.substring(0, 37) + '...';
        }
        
        historyItem.textContent = displayText;
        historyItem.title = item.url;
        
        // Add timestamp if available
        if (item.timestamp) {
          const date = new Date(item.timestamp);
          const timeString = date.toLocaleDateString() + ' ' + 
                            date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
          
          const timeSpan = document.createElement('span');
          timeSpan.style.fontSize = '11px';
          timeSpan.style.color = '#999';
          timeSpan.style.float = 'right';
          timeSpan.textContent = timeString;
          
          historyItem.appendChild(timeSpan);
        }
        
        // Click to fill URL input
        historyItem.addEventListener('click', function() {
          urlInput.value = item.url;
        });
        
        historyList.appendChild(historyItem);
      });
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
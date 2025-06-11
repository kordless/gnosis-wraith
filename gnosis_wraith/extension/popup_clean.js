// Clean Popup Script for Gnosis Wraith Extension
// Minimalist version with slide switch and simplified controls

document.addEventListener('DOMContentLoaded', function() {
    const captureBtn = document.getElementById('capture-btn');
    const fullpageToggle = document.getElementById('fullpage-toggle');
    const serverSelect = document.getElementById('server-select');
    const messageDiv = document.getElementById('message');
    const topLabel = document.getElementById('top-label');
    const fullLabel = document.getElementById('full-label');
    
    // Load saved settings
    loadSettings();
    
    // Update labels when toggle changes
    fullpageToggle.addEventListener('change', function() {
        updateToggleLabels();
        saveSettings();
    });
    
    // Save settings when server changes
    serverSelect.addEventListener('change', function() {
        saveSettings();
    });
    
    // Handle capture button click
    captureBtn.addEventListener('click', function() {
        const isFullPage = fullpageToggle.checked;
        const serverUrl = serverSelect.value;
        
        if (serverUrl === 'no-server') {
            // Just capture without uploading
            capturePage(false, isFullPage, null);
        } else {
            // Capture and upload to selected server
            capturePage(true, isFullPage, serverUrl);
        }
    });
    
    // Update toggle label colors
    function updateToggleLabels() {
        if (fullpageToggle.checked) {
            topLabel.classList.remove('active');
            fullLabel.classList.add('active');
        } else {
            topLabel.classList.add('active');
            fullLabel.classList.remove('active');
        }
    }
    
    // Function to handle page capturing
    function capturePage(uploadImage, isFullPage, serverUrl) {
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            if (tabs && tabs[0] && tabs[0].url) {
                // Check if we're on a restricted page
                if (tabs[0].url.startsWith('chrome://') || 
                    tabs[0].url.startsWith('chrome-extension://') || 
                    tabs[0].url.startsWith('about:') ||
                    tabs[0].url.startsWith('edge://') ||
                    tabs[0].url.startsWith('brave://') ||
                    tabs[0].url.startsWith('chrome-search://')) {
                    
                    showMessage('Cannot capture browser pages', 'error');
                    return;
                }
                
                // Update server URL if uploading
                if (uploadImage && serverUrl) {
                    chrome.runtime.sendMessage({
                        action: 'updateServerUrl',
                        serverUrl: serverUrl
                    });
                }
                
                // Send capture request
                chrome.runtime.sendMessage({
                    action: 'captureCurrentPage',
                    fullPage: isFullPage,
                    tabId: tabs[0].id,
                    sendToApi: uploadImage
                }, function(response) {
                    const message = uploadImage ? 
                        `Capturing ${isFullPage ? 'full page' : 'viewport'}...` : 
                        `Taking ${isFullPage ? 'full page' : 'viewport'} screenshot...`;
                    showMessage(message, 'info');
                    
                    // Close popup after a short delay
                    setTimeout(() => {
                        window.close();
                    }, 1000);
                });
                
                // Also try sending to content script for full page captures
                if (isFullPage) {
                    try {
                        chrome.tabs.sendMessage(tabs[0].id, { 
                            action: 'requestFullPageCapture',
                            sendToApi: uploadImage
                        }, function(response) {
                            if (chrome.runtime.lastError) {
                                console.log("Content script not accessible");
                            }
                        });
                    } catch (e) {
                        console.log("Error sending to content script");
                    }
                }
            } else {
                showMessage('Cannot access current tab', 'error');
            }
        });
    }
    
    // Function to show message
    function showMessage(text, type) {
        messageDiv.textContent = text;
        messageDiv.className = `message ${type}`;
        messageDiv.style.display = 'block';
        
        // Auto-hide after 3 seconds
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 3000);
    }
    
    // Function to load settings
    function loadSettings() {
        chrome.storage.local.get(['serverUrl', 'fullPageEnabled'], function(result) {
            if (result.serverUrl) {
                serverSelect.value = result.serverUrl;
            }
            if (result.fullPageEnabled !== undefined) {
                fullpageToggle.checked = result.fullPageEnabled;
                updateToggleLabels();
            }
        });
    }
    
    // Function to save settings
    function saveSettings() {
        const settings = {
            serverUrl: serverSelect.value,
            fullPageEnabled: fullpageToggle.checked
        };
        
        chrome.storage.local.set(settings, function() {
            // Notify background script of server change
            if (serverSelect.value !== 'no-server') {
                chrome.runtime.sendMessage({ 
                    action: 'serverUrlUpdated', 
                    serverUrl: serverSelect.value 
                });
            }
        });
    }
    
    // Listen for keyboard shortcuts info from background
    chrome.runtime.onMessage.addListener(function(message, sender, sendResponse) {
        if (message.action === 'fullPageCaptureProgress') {
            // Update progress if popup is still open
            if (messageDiv) {
                messageDiv.textContent = `Capturing: ${message.progress}%`;
                messageDiv.className = 'message info';
                messageDiv.style.display = 'block';
            }
        }
    });
});
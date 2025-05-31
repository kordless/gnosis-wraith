// Popup script for Gnosis Wraith Capture extension
// Version 1.3.0 - Slider UI Update

document.addEventListener('DOMContentLoaded', function() {
    const captureBtn = document.getElementById('capture-btn');
    const uploadSlider = document.getElementById('upload-slider');
    const fullpageSlider = document.getElementById('fullpage-slider');
    const messageDiv = document.getElementById('message');
    const serverSelect = document.getElementById('server-select');
    
    // Load saved settings
    loadSettings();
    
    // Save settings when server changes
    serverSelect.addEventListener('change', function() {
        saveSettings();
    });
    
    // Handle capture button click
    captureBtn.addEventListener('click', function() {
        const uploadImage = uploadSlider.value === '1';
        const isFullPage = fullpageSlider.value === '1';
        const serverUrl = serverSelect.value;
        
        capturePage(uploadImage, isFullPage, serverUrl);
    });
    
    // Function to handle page capturing
    function capturePage(uploadImage, isFullPage, serverUrl) {
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
                
                // Update API settings with current server
                chrome.runtime.sendMessage({
                    action: 'updateServerUrl',
                    serverUrl: serverUrl
                });
                
                if (isFullPage) {
                    // Full page capture
                    chrome.runtime.sendMessage({
                        action: 'captureCurrentPage',
                        fullPage: true,
                        tabId: tabs[0].id,
                        sendToApi: uploadImage
                    }, function(response) {
                        const message = uploadImage ? 
                            'Capturing full page and uploading for analysis...' : 
                            'Capturing full page screenshot...';
                        showMessage(message, 'info');
                        window.close(); // Close popup
                    });
                    
                    // Also try sending to content script
                    try {
                        chrome.tabs.sendMessage(tabs[0].id, { 
                            action: 'requestFullPageCapture',
                            sendToApi: uploadImage
                        }, function(response) {
                            if (chrome.runtime.lastError) {
                                console.log("Content script not accessible, already handled via background script");
                            }
                        });
                    } catch (e) {
                        console.log("Error sending to content script, continuing with background script approach");
                    }
                } else {
                    // Regular capture
                    chrome.runtime.sendMessage({
                        action: 'captureCurrentPage',
                        tabId: tabs[0].id,
                        sendToApi: uploadImage
                    }, function(response) {
                        const message = uploadImage ? 
                            'Capturing screenshot and uploading for analysis...' : 
                            'Capturing screenshot...';
                        showMessage(message, 'info');
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
    
    // Function to load settings
    function loadSettings() {
        chrome.storage.local.get(['serverUrl', 'uploadEnabled', 'fullPageEnabled'], function(result) {
            if (result.serverUrl) {
                serverSelect.value = result.serverUrl;
            }
            if (result.uploadEnabled !== undefined) {
                uploadSlider.value = result.uploadEnabled ? '1' : '0';
            }
            if (result.fullPageEnabled !== undefined) {
                fullpageSlider.value = result.fullPageEnabled ? '1' : '0';
            }
        });
    }
    
    // Function to save settings
    function saveSettings() {
        const settings = {
            serverUrl: serverSelect.value,
            uploadEnabled: uploadSlider.value === '1',
            fullPageEnabled: fullpageSlider.value === '1'
        };
        
        chrome.storage.local.set(settings, function() {
            // Notify background script of the change
            chrome.runtime.sendMessage({ 
                action: 'serverUrlUpdated', 
                serverUrl: serverSelect.value 
            });
        });
    }
    
    // Save settings when sliders change
    uploadSlider.addEventListener('input', saveSettings);
    fullpageSlider.addEventListener('input', saveSettings);
    
    
    // Add help section toggle
    const helpLink = document.getElementById('help-link');
    const helpSection = document.getElementById('help-section');
    
    helpLink.addEventListener('click', function(e) {
        e.preventDefault();
        if (helpSection.style.display === 'block') {
            helpSection.style.display = 'none';
        } else {
            helpSection.style.display = 'block';
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
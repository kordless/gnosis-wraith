document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const settingsForm = document.getElementById('settings-form');
    // Server URL input has been removed from the UI
    const serverUrl = window.location.origin; // Use current origin as server URL
    const llmProviderSelect = document.getElementById('llm-provider');
    const llmApiTokenInput = document.getElementById('llm-api-token');
    const screenshotQualitySelect = document.getElementById('screenshot-quality');
    const javascriptEnabledSelect = document.getElementById('javascript-enabled');
    const storagePathInput = document.getElementById('storage-path');
    const resetBtn = document.getElementById('reset-btn');
    const gearStatus = document.getElementById('gear-status');
    
    // Track form changes
    let formModified = false;
    
    // Cookie utilities
    const Cookies = {
        set: function(name, value, days = 90) { // Changed from 365 to 90 days (3 months)
            const date = new Date();
            date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
            const expires = `expires=${date.toUTCString()}`;
            document.cookie = `${name}=${value};${expires};path=/;SameSite=Strict`;
        },
        get: function(name) {
            const nameEQ = `${name}=`;
            const ca = document.cookie.split(';');
            for (let i = 0; i < ca.length; i++) {
                let c = ca[i];
                while (c.charAt(0) === ' ') c = c.substring(1);
                if (c.indexOf(nameEQ) === 0) {
                    return c.substring(nameEQ.length, c.length);
                }
            }
            return '';
        },
        delete: function(name) {
            document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;`;
        }
    };
    
    // Load saved settings from cookies
    function loadSettings() {
        // Load general settings
        // Server URL cookie is no longer needed, use window.location.origin
        const screenshotQuality = Cookies.get('gnosis_wraith_screenshot_quality');
        const javascriptEnabled = Cookies.get('gnosis_wraith_javascript_enabled');
        const storagePath = Cookies.get('gnosis_wraith_storage_path');
        
        // Server URL input has been removed
        if (screenshotQuality) screenshotQualitySelect.value = screenshotQuality;
        if (javascriptEnabled) javascriptEnabledSelect.value = javascriptEnabled;
        if (storagePath) storagePathInput.value = storagePath;
        
        // Load LLM provider and corresponding token
        const provider = Cookies.get('gnosis_wraith_llm_provider') || 'anthropic';
        llmProviderSelect.value = provider;
        
        // Load the token for the current provider
        loadTokenForCurrentProvider();
    }
    
    // Load the token for the currently selected provider
    function loadTokenForCurrentProvider() {
        const provider = llmProviderSelect.value;
        const tokenCookieName = `gnosis_wraith_llm_token_${provider}`;
        const token = Cookies.get(tokenCookieName);
        
        if (token) {
            llmApiTokenInput.value = token;
        } else {
            llmApiTokenInput.value = '';
        }
    }
    
    // Update the gear icon status
    function updateGearStatus(status) {
        if (!gearStatus) return;
        
        // Remove all status classes
        gearStatus.classList.remove('modified', 'processing');
        
        // Update the gear icon according to status
        switch (status) {
            case 'saved':
                gearStatus.title = 'Settings Status: Saved';
                break;
            case 'modified':
                gearStatus.classList.add('modified');
                gearStatus.title = 'Settings Status: Modified (unsaved changes)';
                break;
            case 'processing':
                gearStatus.classList.add('processing');
                gearStatus.title = 'Settings Status: Processing...';
                break;
        }
    }
    
    // Function to track form changes
    function trackFormChanges() {
        if (!formModified) {
            formModified = true;
            updateGearStatus('modified');
        }
    }
    
    // Save settings to cookies and optionally to server
    async function saveSettings() {
        // Update gear status to processing
        updateGearStatus('processing');
        
        // Save general settings (server URL is now fixed to window.location.origin)
        Cookies.set('gnosis_wraith_screenshot_quality', screenshotQualitySelect.value);
        Cookies.set('gnosis_wraith_javascript_enabled', javascriptEnabledSelect.value);
        Cookies.set('gnosis_wraith_storage_path', storagePathInput.value);
        
        // Save the currently selected provider
        Cookies.set('gnosis_wraith_llm_provider', llmProviderSelect.value);
        
        // Save the token for the current provider
        const provider = llmProviderSelect.value;
        const tokenCookieName = `gnosis_wraith_llm_token_${provider}`;
        
        if (llmApiTokenInput.value) {
            Cookies.set(tokenCookieName, llmApiTokenInput.value);
        } else {
            // If the token field is empty, delete the cookie
            Cookies.delete(tokenCookieName);
        }
        
        try {
            // Optionally send non-sensitive settings to server
            // We don't send tokens to the server for security reasons
            const response = await fetch('/api/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    server_url: window.location.origin, // Use current origin
                    screenshot_quality: screenshotQualitySelect.value,
                    javascript_enabled: javascriptEnabledSelect.value === 'true',
                    storage_path: storagePathInput.value,
                    llm_provider: llmProviderSelect.value
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                showMessage('Settings saved successfully!', 'success');
                // Reset form modified state and update gear status
                formModified = false;
                updateGearStatus('saved');
            } else {
                showMessage(`Error saving settings: ${data.error}`, 'error');
                updateGearStatus('modified'); // Keep in modified state
            }
        } catch (error) {
            // If server request fails, still save cookies and show success
            // This allows the app to work even if the server settings endpoint is not implemented
            console.error('Error saving settings to server:', error);
            showMessage('Settings saved to browser (server update failed)', 'warning');
            
            // Still consider it saved since cookies were updated
            formModified = false;
            updateGearStatus('saved');
        }
    }
    
    // Reset settings to default values
    function resetSettings() {
        if (confirm('Are you sure you want to reset all settings to default values?')) {
            // Update gear status to processing
            updateGearStatus('processing');
            
            // Clear all cookies (server URL cookie is no longer needed)
            Cookies.delete('gnosis_wraith_screenshot_quality');
            Cookies.delete('gnosis_wraith_javascript_enabled');
            Cookies.delete('gnosis_wraith_storage_path');
            Cookies.delete('gnosis_wraith_llm_provider');
            
            // Clear all provider tokens
            Cookies.delete('gnosis_wraith_llm_token_anthropic');
            Cookies.delete('gnosis_wraith_llm_token_openai');
            Cookies.delete('gnosis_wraith_llm_token_gemini');
            
            // Reset form to default values (server URL input has been removed)
            llmProviderSelect.value = 'anthropic';
            llmApiTokenInput.value = '';
            screenshotQualitySelect.value = 'medium';
            javascriptEnabledSelect.value = 'false';
            storagePathInput.value = '';
            
            // Reset form modified state and update gear status after a brief delay
            setTimeout(() => {
                formModified = false;
                updateGearStatus('saved');
                
                // Show success message
                showMessage('Settings reset to default values.', 'success');
            }, 500); // Delay for visual effect
        }
    }
    
    // Display feedback message
    function showMessage(message, type = 'info') {
        // Check if a message container already exists
        let messageContainer = document.querySelector('.message-container');
        
        // Create message container if it doesn't exist
        if (!messageContainer) {
            messageContainer = document.createElement('div');
            messageContainer.className = 'message-container';
            settingsForm.parentNode.insertBefore(messageContainer, settingsForm);
        }
        
        // Create the message element
        const messageElement = document.createElement('div');
        messageElement.className = `message ${type}`;
        messageElement.textContent = message;
        
        // Add the message to the container
        messageContainer.appendChild(messageElement);
        
        // Remove the message after 3 seconds
        setTimeout(() => {
            messageElement.remove();
            
            // Remove the container if it's empty
            if (messageContainer.children.length === 0) {
                messageContainer.remove();
            }
        }, 3000);
    }
    
    // Event Listeners
    
    // Form submission
    settingsForm.addEventListener('submit', function(e) {
        e.preventDefault();
        saveSettings();
    });
    
    // Reset button
    resetBtn.addEventListener('click', resetSettings);
    
    // Provider selection change
    llmProviderSelect.addEventListener('change', function() {
        loadTokenForCurrentProvider();
        trackFormChanges();
    });
    
    // Add change listeners to all form inputs (server URL input removed)
    const formInputs = [
        llmProviderSelect, 
        llmApiTokenInput, 
        screenshotQualitySelect, 
        javascriptEnabledSelect, 
        storagePathInput
    ];
    
    // Attach change listeners to track modifications
    formInputs.forEach(input => {
        // Use either change or input event based on input type
        const eventType = input.tagName === 'SELECT' ? 'change' : 'input';
        input.addEventListener(eventType, trackFormChanges);
    });
    
    // Delete token button
    const deleteTokenBtn = document.getElementById('delete-token-btn');
    if (deleteTokenBtn) {
        deleteTokenBtn.addEventListener('click', function() {
            if (confirm('Are you sure you want to delete this API token?')) {
                // Get the current provider
                const provider = llmProviderSelect.value;
                const tokenCookieName = `gnosis_wraith_llm_token_${provider}`;
                
                // Delete the cookie
                Cookies.delete(tokenCookieName);
                
                // Clear the input field
                llmApiTokenInput.value = '';
                
                // Show success message
                showMessage(`API token for ${provider} deleted successfully.`, 'success');
            }
        });
    }
    
    // Initialize the gear status
    function initGearStatus() {
        if (gearStatus) {
            formModified = false;
            updateGearStatus('saved');
            
            // Add click handler for easy navigation to terminal
            gearStatus.addEventListener('click', function() {
                if (formModified) {
                    if (confirm('You have unsaved changes. Save settings now?')) {
                        saveSettings();
                    }
                }
            });
            
            // Highlight the gear with an orange color since we're on the settings page
            const gearIcon = gearStatus.querySelector('i');
            if (gearIcon) {
                gearIcon.style.color = '#FF8800'; // Orange color
                gearIcon.style.filter = 'drop-shadow(0 0 5px rgba(255, 136, 0, 0.7))';
            }
        }
    }
    
    // Initial load
    loadSettings();
    initGearStatus();
    
    // Make sure the header control buttons display correctly
    function ensureHeaderControlsWork() {
        // Get the header control buttons from the header
        const headerControlButtons = document.querySelector('.navbar .control-buttons');
        
        if (headerControlButtons) {
            // Make sure they're visible
            headerControlButtons.style.display = 'flex';
            headerControlButtons.style.zIndex = '2000'; // Higher than any other element
            
            console.log('Ensuring header control buttons are visible on settings page');
            
            // Fix any buttons that should be visible based on login state
            const powerButton = document.getElementById('power-button');
            const terminalButton = document.querySelector('.navbar .terminal-button');
            const settingsButton = document.querySelector('.navbar .settings-button');
            
            if (powerButton) {
                // Check if we're logged in based on localStorage
                const isLoggedIn = localStorage.getItem('logged_in_state') === 'true';
                
                if (isLoggedIn) {
                    // If logged in, show the terminal and settings buttons in header
                    if (terminalButton) terminalButton.style.display = 'flex';
                    if (settingsButton) settingsButton.style.display = 'flex';
                    
                    // Also style the power button to show logged-in state
                    const powerIcon = powerButton.querySelector('i');
                    if (powerIcon) {
                        powerIcon.style.color = '#6c63ff';
                        powerButton.style.boxShadow = '0 0 10px rgba(108, 99, 255, 0.3)';
                        powerButton.style.borderColor = 'rgba(108, 99, 255, 0.4)';
                        powerButton.style.background = 'rgba(108, 99, 255, 0.1)';
                    }
                }
            }
        }
    }
    
    // Run this after a short delay to ensure DOM is fully processed
    setTimeout(ensureHeaderControlsWork, 100);
});
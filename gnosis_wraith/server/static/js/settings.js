document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const settingsForm = document.getElementById('settings-form');
    const serverUrlInput = document.getElementById('server-url');
    const llmProviderSelect = document.getElementById('llm-provider');
    const llmApiTokenInput = document.getElementById('llm-api-token');
    const screenshotQualitySelect = document.getElementById('screenshot-quality');
    const javascriptEnabledSelect = document.getElementById('javascript-enabled');
    const storagePathInput = document.getElementById('storage-path');
    const resetBtn = document.getElementById('reset-btn');
    
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
        const serverUrl = Cookies.get('gnosis_wraith_server_url');
        const screenshotQuality = Cookies.get('gnosis_wraith_screenshot_quality');
        const javascriptEnabled = Cookies.get('gnosis_wraith_javascript_enabled');
        const storagePath = Cookies.get('gnosis_wraith_storage_path');
        
        if (serverUrl) serverUrlInput.value = serverUrl;
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
    
    // Save settings to cookies and optionally to server
    async function saveSettings() {
        // Save general settings
        Cookies.set('gnosis_wraith_server_url', serverUrlInput.value);
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
                    server_url: serverUrlInput.value,
                    screenshot_quality: screenshotQualitySelect.value,
                    javascript_enabled: javascriptEnabledSelect.value === 'true',
                    storage_path: storagePathInput.value,
                    llm_provider: llmProviderSelect.value
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                showMessage('Settings saved successfully!', 'success');
            } else {
                showMessage(`Error saving settings: ${data.error}`, 'error');
            }
        } catch (error) {
            // If server request fails, still save cookies and show success
            // This allows the app to work even if the server settings endpoint is not implemented
            console.error('Error saving settings to server:', error);
            showMessage('Settings saved to browser (server update failed)', 'warning');
        }
    }
    
    // Reset settings to default values
    function resetSettings() {
        if (confirm('Are you sure you want to reset all settings to default values?')) {
            // Clear all cookies
            Cookies.delete('gnosis_wraith_server_url');
            Cookies.delete('gnosis_wraith_screenshot_quality');
            Cookies.delete('gnosis_wraith_javascript_enabled');
            Cookies.delete('gnosis_wraith_storage_path');
            Cookies.delete('gnosis_wraith_llm_provider');
            
            // Clear all provider tokens
            Cookies.delete('gnosis_wraith_llm_token_anthropic');
            Cookies.delete('gnosis_wraith_llm_token_openai');
            Cookies.delete('gnosis_wraith_llm_token_gemini');
            
            // Reset form to default values
            serverUrlInput.value = 'http://localhost:5678';
            llmProviderSelect.value = 'anthropic';
            llmApiTokenInput.value = '';
            screenshotQualitySelect.value = 'medium';
            javascriptEnabledSelect.value = 'false';
            storagePathInput.value = '';
            
            // Show success message
            showMessage('Settings reset to default values.', 'success');
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
    llmProviderSelect.addEventListener('change', loadTokenForCurrentProvider);
    
    // Initial load
    loadSettings();
});
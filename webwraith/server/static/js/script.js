document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const crawlMethodSelect = document.getElementById('crawl-method');
    const singleUrlInput = document.getElementById('single-url-input');
    const multipleUrlsInput = document.getElementById('multiple-urls-input');
    const urlInput = document.getElementById('url');
    const urlsTextarea = document.getElementById('urls');
    const reportTitleInput = document.getElementById('report-title');
    const outputFormatSelect = document.getElementById('output-format');
    const crawlBtn = document.getElementById('crawl-btn');
    const crawlStatus = document.getElementById('crawl-status');
    const statusText = document.getElementById('status-text');
    const progressIndicator = document.getElementById('progress-indicator');
    const crawlResults = document.getElementById('crawl-results');
    const resultsSummary = document.getElementById('results-summary');
    const resultsContent = document.getElementById('results-content');
    const reportLink = document.getElementById('report-link');
    const htmlLink = document.getElementById('html-link');
    
    const imageUpload = document.getElementById('image-upload');
    const uploadBtn = document.getElementById('upload-btn');
    const uploadResult = document.getElementById('upload-result');
    const previewImage = document.getElementById('preview-image');
    const extractedTextContent = document.getElementById('extracted-text-content');
    
    const settingsBtn = document.getElementById('settings-btn');
    const settingsPanel = document.getElementById('settings-panel');
    const serverUrlInput = document.getElementById('server-url');
    const saveSettingsBtn = document.getElementById('save-settings-btn');
    const defaultSettingsBtn = document.getElementById('default-settings-btn');
    
    // Initialize settings if available
    initializeSettings();
    
    // Event listeners
    if (crawlMethodSelect) {
        crawlMethodSelect.addEventListener('change', () => {
            if (crawlMethodSelect.value === 'url') {
                singleUrlInput.style.display = 'block';
                multipleUrlsInput.style.display = 'none';
            } else {
                singleUrlInput.style.display = 'none';
                multipleUrlsInput.style.display = 'block';
            }
        });
    }
    
    if (crawlBtn) {
        crawlBtn.addEventListener('click', startCrawl);
    }
    
    if (uploadBtn) {
        uploadBtn.addEventListener('click', uploadImage);
    }
    
    if (imageUpload) {
        imageUpload.addEventListener('change', previewSelectedImage);
    }
    
    // Settings panel events
    if (settingsBtn) {
        settingsBtn.addEventListener('click', toggleSettingsPanel);
    }
    
    if (saveSettingsBtn) {
        saveSettingsBtn.addEventListener('click', saveSettings);
    }
    
    if (defaultSettingsBtn) {
        defaultSettingsBtn.addEventListener('click', resetDefaultSettings);
    }
    
    // Functions
    async function startCrawl() {
        // Validate input
        let urls = [];
        let url = null;
        
        if (crawlMethodSelect.value === 'url') {
            url = urlInput.value.trim();
            if (!url) {
                alert('Please enter a URL');
                return;
            }
            if (!isValidUrl(url)) {
                alert('Please enter a valid URL');
                return;
            }
        } else {
            const urlsText = urlsTextarea.value.trim();
            if (!urlsText) {
                alert('Please enter at least one URL');
                return;
            }
            
            urls = urlsText.split('\n')
                .map(u => u.trim())
                .filter(u => u.length > 0);
                
            if (urls.length === 0) {
                alert('Please enter at least one URL');
                return;
            }
            
            // Validate all URLs
            const invalidUrls = urls.filter(u => !isValidUrl(u));
            if (invalidUrls.length > 0) {
                alert(`Some URLs are invalid: ${invalidUrls.join(', ')}`);
                return;
            }
        }
        
        // Get report title
        let title = reportTitleInput.value.trim();
        if (!title) {
            title = `Web Crawl Report - ${new Date().toLocaleString()}`;
        }
        
        // Get output format
        const outputFormat = outputFormatSelect.value;
        
        // Show status
        crawlStatus.style.display = 'block';
        statusText.textContent = 'Crawling...';
        progressIndicator.style.width = '20%';
        crawlResults.style.display = 'none';
        
        // Disable form during crawl
        crawlBtn.disabled = true;
        
        try {
            // Prepare request data
            const requestData = {
                urls: urls,
                url: url,
                title: title,
                output_format: outputFormat
            };
            
            // Send request
            const response = await fetch('/api/crawl', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });
            
            progressIndicator.style.width = '80%';
            
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            progressIndicator.style.width = '100%';
            statusText.textContent = 'Complete';
            
            // Display results
            displayCrawlResults(result);
            
        } catch (error) {
            console.error('Error during crawl:', error);
            statusText.textContent = `Error: ${error.message}`;
            progressIndicator.style.width = '100%';
            progressIndicator.style.backgroundColor = 'var(--danger-color)';
        } finally {
            // Re-enable form
            crawlBtn.disabled = false;
        }
    }
    
    function displayCrawlResults(result) {
        if (!result.success) {
            alert(`Error: ${result.error}`);
            return;
        }
        
        // Show results section
        crawlResults.style.display = 'block';
        
        // Update summary
        resultsSummary.textContent = `Successfully crawled ${result.urls_processed.length} URL(s)`;
        
        // Clear previous results
        resultsContent.innerHTML = '';
        
        // Add result items
        result.results.forEach(item => {
            const resultItem = document.createElement('div');
            resultItem.className = 'result-item';
            
            // Title and URL
            const title = document.createElement('h3');
            title.textContent = item.title;
            resultItem.appendChild(title);
            
            const url = document.createElement('div');
            url.className = 'result-url';
            url.textContent = item.url;
            resultItem.appendChild(url);
            
            // Error or screenshot & text
            if (item.error) {
                const error = document.createElement('div');
                error.className = 'result-error';
                error.textContent = `Error: ${item.error}`;
                resultItem.appendChild(error);
            } else {
                // Screenshot
                if (item.screenshot) {
                    const screenshotContainer = document.createElement('div');
                    screenshotContainer.className = 'result-screenshot';
                    
                    const screenshotImg = document.createElement('img');
                    screenshotImg.src = `/screenshots/${item.screenshot}`;
                    screenshotImg.alt = `Screenshot of ${item.url}`;
                    
                    screenshotContainer.appendChild(screenshotImg);
                    resultItem.appendChild(screenshotContainer);
                }
                
                // Extracted text
                if (item.extracted_text) {
                    const textContainer = document.createElement('div');
                    textContainer.className = 'result-text';
                    
                    const textHeading = document.createElement('h4');
                    textHeading.textContent = 'Extracted Text';
                    textContainer.appendChild(textHeading);
                    
                    const text = document.createElement('pre');
                    text.textContent = item.extracted_text;
                    textContainer.appendChild(text);
                    
                    resultItem.appendChild(textContainer);
                }
            }
            
            resultsContent.appendChild(resultItem);
        });
        
        // Update report links
        if (result.report_path) {
            reportLink.href = `/reports/${result.report_path}`;
            reportLink.style.display = 'inline-block';
        } else {
            reportLink.style.display = 'none';
        }
        
        if (result.html_path) {
            htmlLink.href = `/reports/${result.html_path}`;
            htmlLink.style.display = 'inline-block';
        } else {
            htmlLink.style.display = 'none';
        }
        
        // Scroll to results
        crawlResults.scrollIntoView({ behavior: 'smooth' });
    }
    
    async function uploadImage() {
        const fileInput = imageUpload;
        
        if (!fileInput.files || fileInput.files.length === 0) {
            alert('Please select an image to upload');
            return;
        }
        
        const file = fileInput.files[0];
        
        // Check if it's an image
        if (!file.type.startsWith('image/')) {
            alert('Please select a valid image file');
            return;
        }
        
        // Create form data
        const formData = new FormData();
        formData.append('image', file);
        
        // Disable button during upload
        uploadBtn.disabled = true;
        uploadBtn.textContent = 'Uploading...';
        
        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                // Update UI
                previewImage.src = `/screenshots/${result.file_path}`;
                extractedTextContent.textContent = result.extracted_text;
                uploadResult.style.display = 'block';
                
                // Scroll to result
                uploadResult.scrollIntoView({ behavior: 'smooth' });
            } else {
                alert(`Error: ${result.error}`);
            }
            
        } catch (error) {
            console.error('Error during upload:', error);
            alert(`Error: ${error.message}`);
        } finally {
            // Re-enable button
            uploadBtn.disabled = false;
            uploadBtn.textContent = 'Upload & Extract Text';
        }
    }
    
    function previewSelectedImage() {
        const fileInput = imageUpload;
        
        if (!fileInput.files || fileInput.files.length === 0) {
            return;
        }
        
        const file = fileInput.files[0];
        
        // Check if it's an image
        if (!file.type.startsWith('image/')) {
            return;
        }
        
        // Create a temporary URL for the image
        const imageUrl = URL.createObjectURL(file);
        
        // Update preview
        previewImage.src = imageUrl;
        uploadResult.style.display = 'block';
        extractedTextContent.textContent = 'Upload to extract text';
        
        // Scroll to result
        uploadResult.scrollIntoView({ behavior: 'smooth' });
    }
    
    function isValidUrl(urlString) {
        try {
            const url = new URL(urlString);
            return url.protocol === 'http:' || url.protocol === 'https:';
        } catch (error) {
            return false;
        }
    }
    
    // Settings functions
    function initializeSettings() {
        // Load stored settings if available
        const storedSettings = localStorage.getItem('webwraith-settings');
        if (storedSettings) {
            const settings = JSON.parse(storedSettings);
            
            // Update UI with stored settings if elements exist
            if (serverUrlInput && settings.serverUrl) {
                serverUrlInput.value = settings.serverUrl;
            }
        } else {
            // Set default settings
            const defaultSettings = {
                serverUrl: window.location.origin,
                theme: 'light',
                autoSaveReports: true
            };
            
            // Store default settings
            localStorage.setItem('webwraith-settings', JSON.stringify(defaultSettings));
            
            // Update UI with default settings
            if (serverUrlInput) {
                serverUrlInput.value = defaultSettings.serverUrl;
            }
        }
    }
    
    function toggleSettingsPanel() {
        if (settingsPanel) {
            if (settingsPanel.style.display === 'block') {
                settingsPanel.style.display = 'none';
            } else {
                settingsPanel.style.display = 'block';
            }
        }
    }
    
    function saveSettings() {
        const settings = {};
        
        // Collect settings from UI
        if (serverUrlInput) {
            settings.serverUrl = serverUrlInput.value.trim();
            
            // Validate server URL
            if (!isValidUrl(settings.serverUrl)) {
                alert('Please enter a valid server URL');
                return;
            }
        }
        
        // Save settings
        localStorage.setItem('webwraith-settings', JSON.stringify(settings));
        
        // Hide settings panel
        if (settingsPanel) {
            settingsPanel.style.display = 'none';
        }
        
        // Show success message
        showNotification('Settings saved successfully', 'success');
    }
    
    function resetDefaultSettings() {
        // Set default settings
        const defaultSettings = {
            serverUrl: window.location.origin,
            theme: 'light',
            autoSaveReports: true
        };
        
        // Store default settings
        localStorage.setItem('webwraith-settings', JSON.stringify(defaultSettings));
        
        // Update UI with default settings
        if (serverUrlInput) {
            serverUrlInput.value = defaultSettings.serverUrl;
        }
        
        // Show success message
        showNotification('Default settings restored', 'success');
    }
    
    function showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.position = 'fixed';
        notification.style.bottom = '20px';
        notification.style.right = '20px';
        notification.style.padding = '10px 20px';
        notification.style.borderRadius = '4px';
        notification.style.zIndex = '9999';
        
        // Set color based on type
        switch (type) {
            case 'success':
                notification.style.backgroundColor = '#2ecc71';
                break;
            case 'error':
                notification.style.backgroundColor = '#e74c3c';
                break;
            case 'warning':
                notification.style.backgroundColor = '#f39c12';
                break;
            default:
                notification.style.backgroundColor = '#3498db';
        }
        
        notification.style.color = 'white';
        
        // Add to document
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 3000);
    }
    
    // Check for URL parameters on load
    function checkUrlParameters() {
        const urlParams = new URLSearchParams(window.location.search);
        
        // Check if auto-crawl is requested
        if (urlParams.has('crawl')) {
            const urlToCrawl = urlParams.get('crawl');
            if (isValidUrl(urlToCrawl) && urlInput) {
                urlInput.value = urlToCrawl;
                
                // Auto start crawl if specified
                if (urlParams.has('auto') && urlParams.get('auto') === 'true') {
                    // Wait a moment for the page to load fully
                    setTimeout(() => {
                        if (crawlBtn) {
                            crawlBtn.click();
                        }
                    }, 1000);
                }
            }
        }
    }
    
    // Call checkUrlParameters on page load
    checkUrlParameters();
});
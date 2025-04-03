document.addEventListener('DOMContentLoaded', function() {
    // Fetch GitHub repository star count
    fetchGitHubStars();
    
    // Initialize image upload functionality if we're on a page with that tab
    if (document.getElementById('upload-btn')) {
        setTimeout(initializeImageUpload, 300); // Small delay to ensure DOM is ready
    }
    
    // Copy code button functionality
    const copyButtons = document.querySelectorAll('.copy-btn');
    copyButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Find the code block (now using Prism structure)
            const codeBlock = button.closest('.code-container').querySelector('code');
            const codeText = codeBlock.textContent;
            
            // Copy to clipboard
            navigator.clipboard.writeText(codeText).then(() => {
                // Visual feedback
                button.classList.add('copied');
                
                // Store original content
                const originalHTML = button.innerHTML;
                button.innerHTML = '<i class="fas fa-check"></i> Copied!';
                
                // Revert after timeout
                setTimeout(() => {
                    button.innerHTML = originalHTML;
                    button.classList.remove('copied');
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy code:', err);
                button.innerHTML = '<i class="fas fa-times"></i> Failed';
                
                setTimeout(() => {
                    button.innerHTML = '<i class="fas fa-copy"></i>';
                }, 2000);
            });
        });
    });
    
    // Tab switching
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.getAttribute('data-tab');

            // Remove active class from all buttons and tabs
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Add active class to clicked button and corresponding tab
            button.classList.add('active');
            document.getElementById(tabId).classList.add('active');

            // Hide results when switching tabs
            document.getElementById('crawl-results').style.display = 'none';
            
            // Initialize upload functionality if this is the image-upload tab
            if (tabId === 'image-upload') {
                console.log('Image upload tab activated, reinitializing elements');
                // Initialize the image upload functionality when tab is clicked
                setTimeout(initializeImageUpload, 100); // Small delay to ensure DOM is ready
            }
        });
    });

    // Server URL from localStorage or default
    const serverUrl = localStorage.getItem('gnosis-wraith-server-url') || 'http://localhost:5678';

    // Single URL Crawl
    const crawlButton = document.getElementById('crawl-btn');
    if (crawlButton) {
        crawlButton.addEventListener('click', async () => {
            const url = document.getElementById('url').value.trim();
            const reportTitle = document.getElementById('report-title').value.trim() || 'Web Crawl Report';
            const outputFormat = document.getElementById('output-format').value;
            // Get JavaScript enabled/disabled option
            const javascriptEnabled = document.getElementById('javascript-enabled-single') ? 
                document.getElementById('javascript-enabled-single').value === 'true' : 
                false;

            if (!url) {
                alert('Please enter a URL');
                return;
            }

            try {
                // Update status
                const statusBox = document.getElementById('crawl-status');
                const statusText = document.getElementById('status-text');
                const progressIndicator = document.getElementById('progress-indicator');
                
                statusBox.style.display = 'block';
                statusText.textContent = 'Initializing crawler...';
                progressIndicator.style.width = '10%';

                // Prepare request data
                const requestData = {
                    url: url,
                    title: reportTitle,
                    output_format: outputFormat,
                    javascript_enabled: javascriptEnabled // Add JavaScript enabled option
                };

                // Make API request
                const response = await fetch(`${serverUrl}/api/crawl`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(requestData)
                });

                // Update progress
                statusText.textContent = 'Processing...';
                progressIndicator.style.width = '50%';

                if (!response.ok) {
                    throw new Error(`Server responded with status: ${response.status}`);
                }

                const result = await response.json();
                
                // Update progress
                statusText.textContent = 'Completed';
                progressIndicator.style.width = '100%';

                // Display results
                displayResults(result);
            } catch (error) {
                console.error('Error during crawl:', error);
                alert(`Crawl failed: ${error.message}`);
                
                const statusText = document.getElementById('status-text');
                statusText.textContent = `Error: ${error.message}`;
            }
        });
    }

    // Multi URL Crawl
    const multiCrawlButton = document.getElementById('multi-crawl-btn');
    if (multiCrawlButton) {
        multiCrawlButton.addEventListener('click', async () => {
            const urlsText = document.getElementById('urls').value.trim();
            const reportTitle = document.getElementById('multi-report-title').value.trim() || 'Multi-URL Crawl Report';
            const outputFormat = document.getElementById('multi-output-format').value;
            // Get JavaScript enabled/disabled option
            const javascriptEnabled = document.getElementById('javascript-enabled-multi') ? 
                document.getElementById('javascript-enabled-multi').value === 'true' : 
                false;

            if (!urlsText) {
                alert('Please enter at least one URL');
                return;
            }

            // Parse URLs (one per line)
            const urls = urlsText.split('\n')
                .map(url => url.trim())
                .filter(url => url.length > 0);

            if (urls.length === 0) {
                alert('No valid URLs found');
                return;
            }

            try {
                // Update status
                const statusBox = document.getElementById('multi-crawl-status');
                const statusText = document.getElementById('multi-status-text');
                const progressIndicator = document.getElementById('multi-progress-indicator');
                
                statusBox.style.display = 'block';
                statusText.textContent = 'Initializing crawler...';
                progressIndicator.style.width = '10%';

                // Prepare request data
                const requestData = {
                    urls: urls,
                    title: reportTitle,
                    output_format: outputFormat,
                    javascript_enabled: javascriptEnabled // Add JavaScript enabled option
                };

                // Make API request
                const response = await fetch(`${serverUrl}/api/crawl`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(requestData)
                });

                // Update progress
                statusText.textContent = 'Processing...';
                progressIndicator.style.width = '50%';

                if (!response.ok) {
                    throw new Error(`Server responded with status: ${response.status}`);
                }

                const result = await response.json();
                
                // Update progress
                statusText.textContent = 'Completed';
                progressIndicator.style.width = '100%';

                // Display results
                displayResults(result);
            } catch (error) {
                console.error('Error during multi-crawl:', error);
                alert(`Multi-crawl failed: ${error.message}`);
                
                const statusText = document.getElementById('multi-status-text');
                statusText.textContent = `Error: ${error.message}`;
            }
        });
    }

    // Image Upload - Using a function to ensure proper initialization
    function initializeImageUpload() {
        console.log('Initializing image upload functionality');
        const uploadButton = document.getElementById('upload-btn');
        console.log('Upload button found:', uploadButton);
        
        if (!uploadButton) {
            console.error('Upload button not found!');
            return; // Exit if button not found
        }
        
        // Remove any existing event listeners by cloning and replacing
        const newUploadButton = uploadButton.cloneNode(true);
        uploadButton.parentNode.replaceChild(newUploadButton, uploadButton);
        
        // Add the event listener to the new button
        newUploadButton.addEventListener('click', async () => {
            console.log('Upload button clicked');
            
            try {
                const fileInput = document.getElementById('image-file-input');
                console.log('File input element:', fileInput);
                
                if (!fileInput) {
                    console.error('File input element not found');
                    alert('Error: File input element not found');
                    return;
                }
                
                if (!fileInput.files || fileInput.files.length === 0) {
                    console.log('No file selected');
                    alert('Please select an image to upload');
                    return;
                }
                
                const file = fileInput.files[0];
                console.log('Selected file:', file);
                
                // Show status box and update progress
                const statusBox = document.getElementById('upload-status');
                const statusText = document.getElementById('upload-status-text');
                const progressIndicator = document.getElementById('upload-progress-indicator');
                
                statusBox.style.display = 'block';
                statusText.textContent = 'Uploading image...';
                progressIndicator.style.width = '25%';
                
                // Get the report title
                const reportTitle = document.getElementById('image-report-title').value || 'Image Analysis Report';
                
                // Prepare form data
                const formData = new FormData();
                formData.append('image', file);
                formData.append('title', reportTitle);
                console.log('FormData created with title:', reportTitle); // Debug log

                // Make API request
                console.log('Sending to URL:', `${serverUrl}/api/upload`); // Debug log
                
                // Update progress
                statusText.textContent = 'Processing...';
                progressIndicator.style.width = '50%';
                
                const response = await fetch(`${serverUrl}/api/upload`, {
                    method: 'POST',
                    body: formData
                });
                console.log('Response received:', response); // Debug log
                
                // Update progress
                progressIndicator.style.width = '75%';

                if (!response.ok) {
                    throw new Error(`Server responded with status: ${response.status}`);
                }

                const result = await response.json();
                console.log('Result JSON:', result); // Debug log
                
                // Update progress to complete
                statusText.textContent = 'Completed';
                progressIndicator.style.width = '100%';
                
                // Display upload result
                const uploadResult = document.getElementById('upload-result');
                const previewImage = document.getElementById('preview-image');
                const extractedTextContent = document.getElementById('extracted-text-content');
                
                uploadResult.style.display = 'block';
                previewImage.src = `${serverUrl}/screenshots/${result.file_path}`;
                extractedTextContent.textContent = result.extracted_text || 'No text extracted';
                
                // Add report link if available
                if (result.report_path) {
                    const reportLinkContainer = document.createElement('div');
                    reportLinkContainer.className = 'report-link-container';
                    reportLinkContainer.innerHTML = `
                        <h3>Generated Report</h3>
                        <p>
                            <a href="${serverUrl}/reports/${result.report_path}" target="_blank" class="btn secondary">
                                <i class="fas fa-file-alt"></i> View Report
                            </a>
                        </p>
                    `;
                    uploadResult.appendChild(reportLinkContainer);
                }
                
                // After a delay, hide the progress bar
                setTimeout(() => {
                    statusBox.style.display = 'none';
                }, 2000);
            } catch (error) {
                console.error('Error during upload:', error);
                
                // Update status for error
                if (statusBox && statusText) {
                    statusText.textContent = `Error: ${error.message}`;
                    if (progressIndicator) {
                        progressIndicator.style.width = '100%';
                        progressIndicator.style.backgroundColor = '#e74c3c'; // Red color for error
                    }
                    
                    // Hide status after delay
                    setTimeout(() => {
                        statusBox.style.display = 'none';
                        if (progressIndicator) {
                            progressIndicator.style.backgroundColor = ''; // Reset color
                        }
                    }, 3000);
                }
                
                alert(`Upload failed: ${error.message}`);
            }
        });
    }

    // Helper function to display crawl results
    function displayResults(result) {
        if (!result.success) {
            alert(`Operation failed: ${result.error}`);
            return;
        }

        const resultsSection = document.getElementById('crawl-results');
        const resultsSummary = document.getElementById('results-summary');
        const resultsContent = document.getElementById('results-content');
        const reportLink = document.getElementById('report-link');
        const htmlLink = document.getElementById('html-link');

        // Show results section
        resultsSection.style.display = 'block';

        // Update summary
        resultsSummary.textContent = `Processed ${result.results.length} URLs`;

        // Clear previous results
        resultsContent.innerHTML = '';

        // Add result items
        result.results.forEach(item => {
            const resultItem = document.createElement('div');
            resultItem.className = 'result-item';

            let itemContent = `
                <h3>${item.title}</h3>
                <div class="result-url">${item.url}</div>
            `;

            // Add JavaScript setting information
            if (typeof item.javascript_enabled !== 'undefined') {
                itemContent += `
                    <div class="result-javascript">
                        JavaScript: ${item.javascript_enabled ? 'Enabled' : 'Disabled'}
                    </div>
                `;
            }

            if (item.error) {
                itemContent += `<div class="result-error">Error: ${item.error}</div>`;
            } else {
                if (item.screenshot) {
                    itemContent += `
                        <div class="result-screenshot">
                            <img src="${serverUrl}/screenshots/${item.screenshot}" alt="Screenshot of ${item.url}">
                        </div>
                    `;
                }

                if (item.extracted_text) {
                    itemContent += `
                        <div class="result-text">
                            <h4>Extracted Text:</h4>
                            <pre>${item.extracted_text}</pre>
                        </div>
                    `;
                }
            }

            resultItem.innerHTML = itemContent;
            resultsContent.appendChild(resultItem);
        });

        // Update report links
        if (result.report_path) {
            reportLink.href = `${serverUrl}/reports/${result.report_path}`;
            reportLink.style.display = 'inline-block';
        } else {
            reportLink.style.display = 'none';
        }

        if (result.html_path) {
            htmlLink.href = `${serverUrl}/reports/${result.html_path}`;
            htmlLink.style.display = 'inline-block';
        } else {
            htmlLink.style.display = 'none';
        }

        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Function to fetch GitHub repository star count
    async function fetchGitHubStars() {
        const repoOwner = 'kordless';
        const repoName = 'gnosis-wraith';
        const githubApiUrl = `https://api.github.com/repos/${repoOwner}/${repoName}`;
        
        try {
            // Try to get cached star count first to avoid hitting API limits
            const cachedData = localStorage.getItem('github_stars_data');
            const now = new Date().getTime();
            
            // If we have cached data and it's less than 1 hour old, use it
            if (cachedData) {
                const data = JSON.parse(cachedData);
                if (now - data.timestamp < 60 * 60 * 1000) { // 1 hour in milliseconds
                    console.log('Using cached GitHub stars data');
                    updateStarCount(data.stars);
                    return data.stars;
                }
            }
            
            // If no cached data or it's old, fetch from API
            console.log('Fetching fresh GitHub stars data');
            const response = await fetch(githubApiUrl);
            
            if (!response.ok) {
                throw new Error(`GitHub API responded with status: ${response.status}`);
            }
            
            const data = await response.json();
            const starCount = data.stargazers_count;
            
            // Cache the result with timestamp
            localStorage.setItem('github_stars_data', JSON.stringify({
                stars: starCount,
                timestamp: now
            }));
            
            updateStarCount(starCount);
            return starCount;
        } catch (error) {
            console.error('Failed to fetch GitHub stars:', error);
            // Try to use cached data even if it's old
            const cachedData = localStorage.getItem('github_stars_data');
            if (cachedData) {
                const data = JSON.parse(cachedData);
                updateStarCount(data.stars);
                return data.stars;
            }
            return null;
        }
    }
    
    // Helper function to update star count in the UI
    function updateStarCount(count) {
        const starsElement = document.getElementById('github-stars');
        if (starsElement) {
            starsElement.textContent = count;
        }
    }
});
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
    const serverUrl = window.location.origin;

    // Single URL Crawl with improved progress updates
    const crawlButton = document.getElementById('crawl-btn');
    if (crawlButton) {
        crawlButton.addEventListener('click', async () => {
            const url = document.getElementById('url').value.trim();
            const reportTitle = document.getElementById('report-title').value.trim() || 'Web Crawl Report';
            
            // Get new parameters from the updated UI
            let takeScreenshot = false;
            if (document.getElementById('take-screenshot')) {
                const screenshotSelect = document.getElementById('take-screenshot');
                const screenshotValue = screenshotSelect.value;
                
                // Log the raw DOM element value
                console.log('Screenshot select DOM element:', screenshotSelect);
                console.log(`Screenshot select value: ${screenshotValue} (type: ${typeof screenshotValue})`);
                
                // Explicitly convert to boolean based on string value
                takeScreenshot = screenshotValue === 'true';
                
                // Log the final converted value
                console.log(`Final takeScreenshot value: ${takeScreenshot} (type: ${typeof takeScreenshot})`);
            }
            
            const ocrExtraction = document.getElementById('ocr-extraction') ? 
                document.getElementById('ocr-extraction').value === 'true' : true;
            const markdownExtraction = document.getElementById('markdown-extraction') ? 
                document.getElementById('markdown-extraction').value : 'enhanced';
            
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
                updateProgress(statusText, progressIndicator, 'Initializing browser...', 5);

                // Prepare request data with explicit boolean conversions
                const requestData = {
                    url: url,
                    title: reportTitle,
                    take_screenshot: Boolean(takeScreenshot),  // Force boolean type
                    ocr_extraction: Boolean(ocrExtraction),    // Force boolean type
                    markdown_extraction: markdownExtraction,
                    javascript_enabled: Boolean(javascriptEnabled)  // Force boolean type
                };
                
                // Add more detailed logging of what's being sent to the server
                console.log('Sending request with data:', requestData);
                console.log('DETAILED PARAMETER INFO:');
                console.log('- take_screenshot:', takeScreenshot, '(type:', typeof takeScreenshot, ')');
                console.log('- ocr_extraction:', ocrExtraction, '(type:', typeof ocrExtraction, ')');
                console.log('- Raw JSON being sent:', JSON.stringify(requestData));

                // Track whether the request is still active
                let requestActive = true;
                
                // Start smart progress tracking with OCR loitering
                const { progressUpdater, loiteringAtOcr } = smartProgressTracker(statusText, progressIndicator, {
                    takeScreenshot,
                    ocrExtraction,
                    markdownExtraction
                });

                // Convert to JSON string for request
                const jsonString = JSON.stringify(requestData);
                
                // Log the exact JSON string being sent
                console.log('REQUEST JSON STRING:', jsonString);
                console.log('PARSED BACK:', JSON.parse(jsonString));
                
                // Make API request
                const fetchPromise = fetch(`${serverUrl}/api/crawl`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: jsonString
                });

                // Once the request completes, mark it as inactive
                fetchPromise.then(() => {
                    requestActive = false;
                    // If the progress was loitering at OCR, release it to continue
                    if (loiteringAtOcr()) {
                        console.log('Request completed, resuming progress after OCR stage');
                        progressUpdater.resumeAfterOcr();
                    }
                }).catch(() => {
                    requestActive = false;
                });

                // Wait for the response
                const response = await fetchPromise;

                // Clear any remaining intervals
                progressUpdater.clear();

                if (!response.ok) {
                    // Get a clone of the response for reading the text if needed
                    const responseClone = response.clone();
                    
                    // Try to get error message from response if possible
                    try {
                        const errorData = await response.json();
                        throw new Error(`Server error: ${errorData.error || 'Unknown error'} (Status: ${response.status})`);
                    } catch (parseError) {
                        try {
                            const responseText = await responseClone.text();
                            throw new Error(`Server responded with status: ${response.status}. ${responseText || ''}`);
                        } catch (textError) {
                            throw new Error(`Server responded with status: ${response.status}`);
                        }
                    }
                }

                const result = await response.json();
                console.log('Received result:', result);
                
                // Update final progress
                updateProgress(statusText, progressIndicator, 'Processing complete!', 100);

                // Display results
                displayResults(result);

                // After a short delay, hide the progress bar
                setTimeout(() => {
                    statusBox.style.display = 'none';
                }, 3000);
            } catch (error) {
                console.error('Error during crawl:', error);
                
                const statusText = document.getElementById('status-text');
                const progressIndicator = document.getElementById('progress-indicator');
                
                statusText.textContent = `Error: ${error.message}`;
                progressIndicator.style.width = '100%';
                progressIndicator.style.backgroundColor = '#e74c3c'; // Red color for error
                
                // Change color but don't hide the status box
                progressIndicator.style.backgroundColor = '#e74c3c'; // Red color
                
                // Update status text to show detailed error
                statusText.textContent = `Error: ${error.message}`;
                
                // Don't hide the status box and don't show alert
            }
        });
    }
    
    // Helper function to update progress display
    function updateProgress(statusTextElement, progressIndicator, message, percentage) {
        statusTextElement.textContent = message;
        progressIndicator.style.width = `${percentage}%`;
    }
    
    // Smart progress tracker that loiters at OCR when needed
    function smartProgressTracker(statusTextElement, progressIndicator, options) {
        const { takeScreenshot, ocrExtraction, markdownExtraction } = options;
        
        // Define the crawling stages with expected percentages and messages
        const stages = [
            { percentage: 10, message: 'Starting browser...' },
            { percentage: 15, message: 'Browser initialized' },
            { percentage: 20, message: 'Navigating to URL...' },
            { percentage: 30, message: 'Retrieving page content...' }
        ];
        
        // Add conditional stages based on options
        if (takeScreenshot) {
            stages.push({ percentage: 40, message: 'Taking screenshot...' });
            
            if (ocrExtraction) {
                stages.push({ percentage: 50, message: 'Performing OCR analysis...' });
                stages.push({ percentage: 60, message: 'Extracting text from image...' });
            }
        }
        
        if (markdownExtraction !== 'none') {
            stages.push({ percentage: 70, message: 'Generating markdown content...' });
            
            if (markdownExtraction === 'enhanced') {
                stages.push({ percentage: 80, message: 'Applying content filtering...' });
            }
        }
        
        // Final stage
        stages.push({ percentage: 90, message: 'Creating report...' });
        
        let currentStageIndex = 0;
        let intervalId = null;
        let isLoiteringAtOcr = false;
        
        // Find OCR stage index if OCR is enabled
        const ocrStageIndex = (takeScreenshot && ocrExtraction) ? 
            stages.findIndex(stage => stage.message.includes('OCR analysis')) : -1;
        
        // Update immediately with the first stage
        updateProgress(statusTextElement, progressIndicator, stages[0].message, stages[0].percentage);
        
        // Function to check if we're currently loitering at the OCR stage
        function loiteringAtOcr() {
            return isLoiteringAtOcr;
        }
        
        // Function to resume progress after OCR is completed
        function resumeAfterOcr() {
            if (isLoiteringAtOcr) {
                isLoiteringAtOcr = false;
                // Start a new interval to continue progress
                if (!intervalId) {
                    advanceToNextStage(); // Move to the next stage immediately
                    intervalId = setInterval(advanceToNextStage, 1500);
                }
            }
        }
        
        // Function to advance to the next stage
        function advanceToNextStage() {
            currentStageIndex++;
            
            // If we've gone through all stages, stop advancing
            if (currentStageIndex >= stages.length) {
                currentStageIndex = stages.length - 1;
                if (intervalId) {
                    clearInterval(intervalId);
                    intervalId = null;
                }
                return;
            }
            
            // If we've reached the OCR stage, we should loiter here until the request completes
            if (currentStageIndex === ocrStageIndex) {
                isLoiteringAtOcr = true;
                if (intervalId) {
                    clearInterval(intervalId);
                    intervalId = null;
                }
            }
            
            // Update with the current stage
            const currentStage = stages[currentStageIndex];
            updateProgress(statusTextElement, progressIndicator, currentStage.message, currentStage.percentage);
        }
        
        // Start the interval to advance stages
        intervalId = setInterval(advanceToNextStage, 1500);
        
        // Return an object that can be used to control the progress
        return {
            progressUpdater: {
                clear: function() {
                    if (intervalId) {
                        clearInterval(intervalId);
                        intervalId = null;
                    }
                },
                resumeAfterOcr: resumeAfterOcr
            },
            loiteringAtOcr: loiteringAtOcr
        };
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
                
                // Set up progress updates for upload
                const uploadProgressStages = [
                    { percentage: 10, message: 'Preparing image...' },
                    { percentage: 25, message: 'Uploading image...' },
                    { percentage: 50, message: 'Server processing image...' },
                    { percentage: 70, message: 'Extracting text with OCR...' },
                    { percentage: 85, message: 'Generating report...' }
                ];
                
                let stageIndex = 0;
                updateProgress(statusText, progressIndicator, uploadProgressStages[0].message, uploadProgressStages[0].percentage);
                
                // Track whether the request is still active
                let requestActive = true;
                const ocrStageIndex = 3; // Index of OCR stage in uploadProgressStages
                let isLoiteringAtOcr = false;
                
                const progressUpdater = setInterval(() => {
                    stageIndex++;
                    
                    // If we've reached the OCR stage, loiter here while request is active
                    if (stageIndex === ocrStageIndex) {
                        isLoiteringAtOcr = true;
                        if (!requestActive) {
                            // If the request is already complete, don't loiter
                            stageIndex++;
                        } else {
                            // Otherwise, stay at this stage
                            return;
                        }
                    }
                    
                    if (stageIndex >= uploadProgressStages.length) {
                        stageIndex = uploadProgressStages.length - 1;
                        return;
                    }
                    
                    updateProgress(
                        statusText, 
                        progressIndicator, 
                        uploadProgressStages[stageIndex].message, 
                        uploadProgressStages[stageIndex].percentage
                    );
                }, 1200);
                
                // Get the report title - FIX: Add null check and default value
                let reportTitle = 'Image Analysis Report';
                const reportTitleElement = document.getElementById('image-report-title');
                if (reportTitleElement && reportTitleElement.value) {
                    reportTitle = reportTitleElement.value;
                }
                
                // Prepare form data
                const formData = new FormData();
                formData.append('image', file);
                formData.append('title', reportTitle);
                console.log('FormData created with title:', reportTitle); // Debug log

                // Make API request
                console.log('Sending to URL:', `${serverUrl}/api/upload`); // Debug log
                
                const fetchPromise = fetch(`${serverUrl}/api/upload`, {
                    method: 'POST',
                    body: formData
                });
                
                // Once the request completes, mark it as inactive
                fetchPromise.then(() => {
                    requestActive = false;
                    // If we were loitering at OCR, move to the next stage
                    if (isLoiteringAtOcr) {
                        stageIndex = ocrStageIndex + 1;
                        updateProgress(
                            statusText, 
                            progressIndicator, 
                            uploadProgressStages[stageIndex].message, 
                            uploadProgressStages[stageIndex].percentage
                        );
                    }
                }).catch(() => {
                    requestActive = false;
                });
                
                // Wait for the response
                const response = await fetchPromise;
                console.log('Response received:', response); // Debug log
                
                // Clear progress updates
                clearInterval(progressUpdater);

                if (!response.ok) {
                    throw new Error(`Server responded with status: ${response.status}`);
                }

                const result = await response.json();
                console.log('Result JSON:', result); // Debug log
                
                // Update progress to complete
                updateProgress(statusText, progressIndicator, 'Processing complete!', 100);
                
                // Display upload result
                const uploadResult = document.getElementById('upload-result');
                const previewImage = document.getElementById('preview-image');
                const extractedTextContent = document.getElementById('extracted-text-content');
                
                uploadResult.style.display = 'block';
                previewImage.src = `${serverUrl}/screenshots/${result.file_path}`;
                extractedTextContent.textContent = result.extracted_text || 'No text extracted';
                
                // Add report links if available
                if (result.report_path) {
                    const reportLinkContainer = document.createElement('div');
                    reportLinkContainer.className = 'report-link-container';
                    
                    let linksHtml = `<h3>Generated Reports</h3><p>`;
                    
                    // Add Markdown link
                    linksHtml += `
                        <a href="${serverUrl}/reports/${result.report_path}" target="_blank" class="btn secondary small">
                            <i class="fas fa-file-alt"></i> Markdown
                        </a>
                    `;
                    
                    // Add HTML link if available
                    if (result.html_path) {
                        linksHtml += `
                            <a href="${serverUrl}/reports/${result.html_path}" target="_blank" class="btn primary small">
                                <i class="fas fa-code"></i> HTML
                            </a>
                        `;
                    }
                    
                    linksHtml += `</p>`;
                    reportLinkContainer.innerHTML = linksHtml;
                    uploadResult.appendChild(reportLinkContainer);
                }
                
                // After a delay, hide the progress bar
                setTimeout(() => {
                    statusBox.style.display = 'none';
                }, 2000);
            } catch (error) {
                console.error('Error during upload:', error);
                
                // Update status for error
                const statusBox = document.getElementById('upload-status');
                const statusText = document.getElementById('upload-status-text');
                const progressIndicator = document.getElementById('upload-progress-indicator');
                
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
        
        // Get all link elements (both top and bottom)
        const reportLink = document.getElementById('report-link');
        const htmlLink = document.getElementById('html-link');
        const reportLinkTop = document.getElementById('report-link-top');
        const htmlLinkTop = document.getElementById('html-link-top');
        const deleteReportBtn = document.getElementById('delete-report-btn');

        // Show results section
        resultsSection.style.display = 'block';

        // Handle both old format (results array) and new format (single result)
        let resultsArray = [];
        
        if (result.results) {
            // Old format with multiple results
            resultsArray = result.results;
            resultsSummary.textContent = `Processed ${result.results.length} URLs`;
        } else if (result.result) {
            // New format with single result
            resultsArray = [result.result];
            resultsSummary.textContent = `Processed URL: ${result.url_processed || 'Unknown'}`;
        } else {
            // Fallback if neither format is found
            resultsArray = [];
            resultsSummary.textContent = 'No results found';
        }

        // Clear previous results
        resultsContent.innerHTML = '';

        // Add result items
        resultsArray.forEach(item => {
            const resultItem = document.createElement('div');
            resultItem.className = 'result-item';

            let itemContent = `
                <h3>${item.title || 'Untitled'}</h3>
                <div class="result-url">${item.url || 'Unknown URL'}</div>
            `;

            // Add JavaScript setting information
            if (typeof item.javascript_enabled !== 'undefined') {
                itemContent += `
                    <div class="result-javascript">
                        JavaScript: ${item.javascript_enabled ? 'Enabled' : 'Disabled'}
                    </div>
                `;
            }

            // Add Screenshot setting information
            if (typeof item.take_screenshot !== 'undefined') {
                itemContent += `
                    <div class="result-screenshot-setting">
                        Screenshot: ${item.take_screenshot ? 'Enabled' : 'Disabled'}
                    </div>
                `;
            }

            // Add OCR setting information
            if (typeof item.ocr_extraction !== 'undefined') {
                itemContent += `
                    <div class="result-ocr-setting">
                        OCR: ${item.ocr_extraction ? 'Enabled' : 'Disabled'}
                    </div>
                `;
            }

            // Add Markdown setting information
            if (item.markdown_extraction) {
                itemContent += `
                    <div class="result-markdown-setting">
                        Markdown: ${item.markdown_extraction}
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
                
                if (item.markdown) {
                    itemContent += `
                        <div class="result-markdown">
                            <h4>Markdown Content:</h4>
                            <pre>${item.markdown}</pre>
                        </div>
                    `;
                }
                
                if (item.filtered_content) {
                    itemContent += `
                        <div class="result-filtered-content">
                            <h4>Filtered Content:</h4>
                            <pre>${item.filtered_content}</pre>
                        </div>
                    `;
                }
            }

            resultItem.innerHTML = itemContent;
            resultsContent.appendChild(resultItem);
        });

        // Update report links - check both places where paths might be
        const reportPath = result.report_path || (result.result && result.result.report_path);
        
        // Store report path in a data attribute on the delete button for later use
        let storedReportPath = '';
        
        if (reportPath) {
            storedReportPath = reportPath;
            
            // Update both top and bottom links
            reportLink.href = `${serverUrl}/reports/${reportPath}`;
            reportLink.style.display = 'inline-block';
            
            reportLinkTop.href = `${serverUrl}/reports/${reportPath}`;
            reportLinkTop.style.display = 'inline-block';
        } else {
            reportLink.style.display = 'none';
            reportLinkTop.style.display = 'none';
        }

        const htmlPath = result.html_path || (result.result && result.result.html_path);
        if (htmlPath) {
            // Update both top and bottom links
            htmlLink.href = `${serverUrl}/reports/${htmlPath}`;
            htmlLink.style.display = 'inline-block';
            
            htmlLinkTop.href = `${serverUrl}/reports/${htmlPath}`;
            htmlLinkTop.style.display = 'inline-block';
        } else {
            htmlLink.style.display = 'none';
            htmlLinkTop.style.display = 'none';
        }
        
        // Set up delete button if we have a report path
        if (storedReportPath) {
            deleteReportBtn.style.display = 'inline-block';
            deleteReportBtn.setAttribute('data-report-path', storedReportPath);
            
            // Add click handler for delete button
            deleteReportBtn.onclick = async function() {
                if (confirm('Are you sure you want to delete this report? This action cannot be undone.')) {
                    try {
                        const response = await fetch(`${serverUrl}/api/reports/${storedReportPath}`, {
                            method: 'DELETE'
                        });
                        
                        if (!response.ok) {
                            throw new Error(`Server responded with status: ${response.status}`);
                        }
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            alert('Report deleted successfully');
                            
                            // Hide all report-related buttons
                            reportLink.style.display = 'none';
                            htmlLink.style.display = 'none';
                            reportLinkTop.style.display = 'none';
                            htmlLinkTop.style.display = 'none';
                            deleteReportBtn.style.display = 'none';
                            
                            // Add a note about deletion to results summary
                            resultsSummary.textContent += ' (Report has been deleted)';
                        } else {
                            throw new Error(result.error || 'Failed to delete report');
                        }
                    } catch (error) {
                        console.error('Error deleting report:', error);
                        alert(`Error deleting report: ${error.message}`);
                    }
                }
            };
        } else {
            deleteReportBtn.style.display = 'none';
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
            
            // If we have cached data and it's less than 3 months old, use it
            if (cachedData) {
                const data = JSON.parse(cachedData);
                if (now - data.timestamp < 90 * 24 * 60 * 60 * 1000) { // 90 days (3 months) in milliseconds
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
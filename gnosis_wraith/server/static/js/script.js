// Track the current progress tracker to avoid multiple instances
let currentProgressTracker = null;

document.addEventListener('DOMContentLoaded', function() {
    // Handle predefined search terms
    setupSearchHandler();
    
    // Fetch GitHub repository star count
    fetchGitHubStars();
    
    // Let upload.js handle all image upload functionality
    console.log('script.js: Delegating image upload handling to upload.js');
    
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
            console.log('Tab clicked:', tabId);

            // Remove active class from all buttons and tabs
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Add active class to clicked button and corresponding tab
            button.classList.add('active');
            document.getElementById(tabId).classList.add('active');

            // Hide results when switching tabs
            document.getElementById('crawl-results').style.display = 'none';
            
            // No special tab handling needed
        });
    });
    
    // Image upload tab has been removed

    // Server URL from localStorage or default
    const serverUrl = window.location.origin;

    // Single URL Crawl with improved progress updates and file upload support
    const crawlButton = document.getElementById('crawl-btn');
    if (crawlButton) {
        crawlButton.addEventListener('click', async () => {
            const urlInput = document.getElementById('url');
            const url = urlInput.value.trim();
            
            // Get report title if toggle is enabled, otherwise use default
            const reportTitleToggle = document.getElementById('report-title-toggle');
            const reportTitle = (reportTitleToggle && reportTitleToggle.checked) ? 
                document.getElementById('report-title').value.trim() || 'Web Crawl Report' : 
                'Web Crawl Report';
            
            // Get new parameters from the updated UI
            let takeScreenshot = false;
            if (document.getElementById('take-screenshot')) {
                const screenshotSelect = document.getElementById('take-screenshot');
                const screenshotValue = screenshotSelect.value;
                
                // Explicitly convert to boolean based on string value
                takeScreenshot = screenshotValue === 'true';
                console.log(`Screenshot setting: ${takeScreenshot}`);
            }
            
            const ocrExtraction = document.getElementById('ocr-extraction') ? 
                document.getElementById('ocr-extraction').value === 'true' : true;
            const markdownExtraction = document.getElementById('markdown-extraction') ? 
                document.getElementById('markdown-extraction').value : 'enhanced';
            
            // Get JavaScript enabled/disabled option
            const javascriptEnabled = document.getElementById('javascript-enabled-single') ? 
                document.getElementById('javascript-enabled-single').value === 'true' : 
                false;

            // Check if we're in file mode - if the input has the file-selected class
            const isFileMode = urlInput.classList.contains('file-selected');
            const mainFileInput = document.getElementById('main-file-input');
            
            if (!url && !isFileMode) {
                alert('Please enter a URL or select a file');
                return;
            }

            try {
                // Update status
                const statusBox = document.getElementById('crawl-status');
                const statusText = document.getElementById('status-text');
                const progressIndicator = document.getElementById('progress-indicator');
                
                statusBox.style.display = 'block';
                
                // Different starting messages based on mode
                if (isFileMode) {
                    updateProgress(statusText, progressIndicator, 'Preparing file...', 5);
                } else {
                    updateProgress(statusText, progressIndicator, 'Initializing browser...', 5);
                }

                // Handle file upload or URL crawl differently
                if (isFileMode && mainFileInput && mainFileInput.files && mainFileInput.files.length > 0) {
                    // File mode - create FormData and append file
                    console.log('File mode detected, preparing file upload');
                    
                    // First check for custom report title from the title toggle
                    let imageTitle = 'Image Analysis';
                    
                    // Check if custom report title toggle is enabled
                    const reportTitleToggle = document.getElementById('report-title-toggle');
                    if (reportTitleToggle && reportTitleToggle.checked) {
                        const titleInput = document.getElementById('report-title');
                        if (titleInput && titleInput.value.trim()) {
                            imageTitle = titleInput.value.trim();
                            console.log('Using custom report title:', imageTitle);
                        }
                    } 
                    // If no custom title but URL field contains user text, use that
                    else if (url && !url.startsWith('File:')) {
                        // User typed a description in the URL field - use this as title
                        imageTitle = url;
                        console.log('Using URL field text as title:', imageTitle);
                    }
                    
                    // Store report title in window for later reference
                    window.lastReportTitle = imageTitle;
                    
                    const formData = new FormData();
                    formData.append('image', mainFileInput.files[0]);
                    formData.append('title', imageTitle);
                    formData.append('ocr_extraction', ocrExtraction);
                    
                    updateProgress(statusText, progressIndicator, 'Uploading file...', 20);
                    
                    // Make API request to the file upload endpoint
                    // Use the correct endpoint for file uploads (should be /api/upload)
                    const response = await fetch(`${serverUrl}/api/upload`, {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (!response.ok) {
                        throw new Error(`Server error: ${response.status}`);
                    }
                    
                    const result = await response.json();
                    console.log('File processing result:', result);
                    
                    updateProgress(statusText, progressIndicator, 'Processing complete!', 100);
                    displayResults(result);
                    
                } else {
                    // Normal URL mode
                    console.log('URL mode detected, preparing crawl request');
                    
                    // Prepare request data with explicit boolean conversions
                    const requestData = {
                        url: url,
                        title: reportTitle,
                        take_screenshot: Boolean(takeScreenshot),  // Force boolean type
                        ocr_extraction: Boolean(ocrExtraction),    // Force boolean type
                        markdown_extraction: markdownExtraction,
                        javascript_enabled: Boolean(javascriptEnabled)  // Force boolean type
                    };
                
                // Track whether the request is still active
                    let requestActive = true;
                    
                    // Clear any existing progress tracker
                    if (currentProgressTracker && currentProgressTracker.progressUpdater) {
                        currentProgressTracker.progressUpdater.clear();
                    }
                    
                    // Start smart progress tracking with OCR loitering
                    currentProgressTracker = smartProgressTracker(statusText, progressIndicator, {
                        takeScreenshot,
                        ocrExtraction,
                        markdownExtraction
                    });
                    
                    const { progressUpdater, loiteringAtOcr } = currentProgressTracker;

                    // Make API request
                    const fetchPromise = fetch(`${serverUrl}/api/crawl`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(requestData)
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

                    // Clear the progress tracker intervals
                    if (progressUpdater) {
                        progressUpdater.clear();
                    }
                    
                    // Reset the global tracker
                    currentProgressTracker = null;
                    
                    if (!response.ok) {
                        throw new Error(`Server error: ${response.status}`);
                    }
                    
                    const result = await response.json();
                    console.log('Crawl result:', result);
                    
                    updateProgress(statusText, progressIndicator, 'Processing complete!', 100);
                    displayResults(result);
                }

                // After a short delay, hide the progress bar
                setTimeout(() => {
                    statusBox.style.display = 'none';
                }, 3000);
                
                // Note: We've already processed the response and displayed results above
                // No need to attempt additional response processing
            } catch (error) {
                console.error('Error during crawl:', error);
                
                const statusText = document.getElementById('status-text');
                const progressIndicator = document.getElementById('progress-indicator');
                
                // Clear any running progress tracker
                if (currentProgressTracker && currentProgressTracker.progressUpdater) {
                    currentProgressTracker.progressUpdater.clear();
                    currentProgressTracker = null;
                }
                
                statusText.textContent = `Error: ${error.message}`;
                progressIndicator.style.width = '100%';
                progressIndicator.style.backgroundColor = '#e74c3c'; // Red color for error
                
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

    // Removed conflicting image upload function - now handled entirely in upload.js

    // Helper function to display crawl results
    function displayResults(result) {
        console.log('Displaying results:', result);
        
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

        // Clear any existing report links and buttons before showing new ones
        reportLink.style.display = 'none';
        htmlLink.style.display = 'none';
        reportLinkTop.style.display = 'none';
        // Do NOT hide HTML top link by default
        // htmlLinkTop.style.display = 'none';
        deleteReportBtn.style.display = 'none';
        
        // Remove any existing click handlers on delete button
        if (deleteReportBtn) {
            deleteReportBtn.onclick = null;
        }

        // Show results section
        resultsSection.style.display = 'block';

        // Handle both old format (results array) and new format (single result or direct object)
        let resultsArray = [];
        
        if (result.results) {
            // Old format with multiple results
            resultsArray = result.results;
            resultsSummary.textContent = `Processed ${result.results.length} URLs`;
        } else if (result.result) {
            // New format with single result
            resultsArray = [result.result];
            resultsSummary.textContent = `Processed URL: ${result.url_processed || 'Unknown'}`;
        } else if (result.file_path || result.html_path || result.report_path) {
            // Direct result object (file upload response)
            resultsArray = [result];
            
            // Use the title from the result if available, otherwise use filename
            if (result.title) {
                resultsSummary.textContent = `${result.title}`;
            } else {
                resultsSummary.textContent = `Processed file: ${result.file_path ? result.file_path.split('/').pop() : 'Unknown'}`;
            }
        } else {
            // Fallback if no recognizable format is found
            console.warn('Unrecognized result format:', result);
            resultsArray = [];
            resultsSummary.textContent = 'No results found';
        }

        // Clear previous results
        resultsContent.innerHTML = '';

        // Add result items
        resultsArray.forEach(item => {
            const resultItem = document.createElement('div');
            resultItem.className = 'result-item';

            // Check if this is a file upload (no URL) or a URL crawl
            const isFileUpload = !item.url && (item.file_path || item.screenshot);
            
            // For debugging - log item details to help troubleshoot title issues
            console.log('Result item details:', {
                title: item.title,
                isFileUpload: isFileUpload,
                reportTitle: result.title, // Check if title exists at result level
                hasFilePath: !!item.file_path,
                reportPath: item.report_path
            });
            
            // For file uploads, check various places where the title might be
            let displayTitle = 'Untitled';
            if (item.title) {
                displayTitle = item.title;
            } else if (result.title) {
                displayTitle = result.title;
            } else if (window.lastReportTitle) {
                displayTitle = window.lastReportTitle;
            }
            
            // For debugging
            console.log('Title sources:', {
                itemTitle: item.title,
                resultTitle: result.title,
                windowTitle: window.lastReportTitle,
                finalTitle: displayTitle
            });
            
            let itemContent = `
                <h3>${displayTitle}</h3>
            `;
            
            // Only show URL info if this is not a file upload
            if (!isFileUpload) {
                itemContent += `<div class="result-url">${item.url || 'Unknown URL'}</div>`;
            }

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
                // Handle both file paths and screenshots depending on what's available in the response
                if (item.screenshot) {
                    itemContent += `
                        <div class="result-screenshot">
                            <img src="${serverUrl}/screenshots/${item.screenshot}" alt="Screenshot of ${item.url || 'content'}">
                        </div>
                    `;
                } else if (item.file_path) {
                    // For uploaded files, display the original image itself
                    console.log('File upload detected, showing image:', item.file_path);
                    itemContent += `
                        <div class="result-screenshot">
                            <img src="${serverUrl}/screenshots/${item.file_path}" alt="Uploaded image" style="max-width: 100%; border: 1px solid #eee; border-radius: 4px;">
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

        // Set up the HTML and report links - check both places where paths might be
        const reportPath = result.report_path || (result.result && result.result.report_path);
        const htmlPath = result.html_path || (result.result && result.result.html_path);
        
        // Store report path in a data attribute on the delete button for later use
        let storedReportPath = '';
        
        // Check for report path (markdown)
        if (reportPath) {
            storedReportPath = reportPath;
            
            // Update only bottom link for raw report (hiding top one)
            reportLink.href = `${serverUrl}/reports/${reportPath}`;
            reportLink.style.display = 'inline-block';
            
            // Hide the raw report button at the top
            reportLinkTop.style.display = 'none';
        } else {
            reportLink.style.display = 'none';
            reportLinkTop.style.display = 'none';
        }
        
        // Check for HTML path (preferred if available)
        if (htmlPath) {
            // Update both top and bottom links for HTML view
            htmlLink.href = `${serverUrl}/reports/${htmlPath}`;
            htmlLink.style.display = 'inline-block';
            
            htmlLinkTop.href = `${serverUrl}/reports/${htmlPath}`;
            htmlLinkTop.style.display = 'inline-block'; // Always show HTML button at top
            
            // Force reportLinkTop to be hidden again in case it was enabled elsewhere
            reportLinkTop.style.display = 'none';
        } else {
            // Even if no HTML path, try to use report path for HTML if available
            if (reportPath) {
                // Fallback to report path with .html extension
                const possibleHtmlPath = reportPath.replace('.md', '.html');
                htmlLink.href = `${serverUrl}/reports/${possibleHtmlPath}`;
                htmlLink.style.display = 'inline-block';
                
                htmlLinkTop.href = `${serverUrl}/reports/${possibleHtmlPath}`;
                htmlLinkTop.style.display = 'inline-block';
            } else {
                htmlLink.style.display = 'none';
                // Still keep the HTML top link visible with a fallback path
                htmlLinkTop.href = `${serverUrl}/reports/${result.id || 'latest'}.html`;
                htmlLinkTop.style.display = 'inline-block';
            }
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
    
    // Function to toggle between file upload mode and URL mode
    function toggleFileUploadMode(isFileMode) {
        console.log(`Toggling to ${isFileMode ? 'file upload' : 'URL'} mode`);
        
        // Find all control cards by searching for their titles
        let jsCard = null;
        let contentProcessingCard = null;
        let screenshotCard = null;
        let ocrCard = null;
        let reportTitleCard = null;
        
        // Find cards by their titles
        const allCards = document.querySelectorAll('.ghost-control-card');
        allCards.forEach(card => {
            const titleEl = card.querySelector('.ghost-control-title');
            if (titleEl) {
                const title = titleEl.innerText.trim();
                if (title === 'JavaScript') {
                    jsCard = card;
                } else if (title === 'Content Processing') {
                    contentProcessingCard = card;
                } else if (title === 'Screenshot Capture') {
                    screenshotCard = card;
                } else if (title === 'OCR Extraction') {
                    ocrCard = card;
                } else if (title === 'Custom Report Title') {
                    reportTitleCard = card;
                }
            }
        });
        
        // Toggle visibility based on mode
        if (isFileMode) {
            // Hide URL-specific options
            if (jsCard) jsCard.style.display = 'none';
            if (contentProcessingCard) contentProcessingCard.style.display = 'none';
            if (screenshotCard) screenshotCard.style.display = 'none';
            
            // Show file-specific options
            if (ocrCard) {
                ocrCard.style.display = 'block';
                
                // For file uploads, automatically check the OCR toggle
                const ocrToggle = document.getElementById('ocr-extraction-toggle');
                if (ocrToggle) {
                    ocrToggle.checked = true;
                    
                    // Also update the hidden select value
                    const ocrSelect = document.getElementById('ocr-extraction');
                    if (ocrSelect) {
                        ocrSelect.value = 'true';
                    }
                }
            }
            
            if (reportTitleCard) {
                reportTitleCard.style.display = 'block';
                
                // For file uploads, also auto-enable custom report title
                const titleToggle = document.getElementById('report-title-toggle');
                if (titleToggle) {
                    titleToggle.checked = true;
                    
                    // Trigger the change event to show the input field
                    const event = new Event('change', { bubbles: true });
                    titleToggle.dispatchEvent(event);
                    
                    // Set a default title based on the file
                    const mainFileInput = document.getElementById('main-file-input');
                    if (mainFileInput && mainFileInput.files && mainFileInput.files.length > 0) {
                        const titleInput = document.getElementById('report-title');
                        if (titleInput) {
                            const fileName = mainFileInput.files[0].name;
                            // Remove extension and convert to title case
                            const baseFileName = fileName.split('.')[0].replace(/_/g, ' ');
                            const titleCaseName = baseFileName.replace(/\w\S*/g, 
                                txt => txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase());
                            
                            titleInput.value = `${titleCaseName} Analysis`;
                        }
                    }
                }
            }
            
            // Update submit button text
            const crawlBtn = document.getElementById('crawl-btn');
            if (crawlBtn) {
                const iconSpan = crawlBtn.querySelector('i');
                if (iconSpan) {
                    iconSpan.className = 'fas fa-file-import pulse-animation';
                }
                
                // Update text content keeping the icon
                const buttonText = crawlBtn.innerHTML.split('</i>')[1];
                crawlBtn.innerHTML = crawlBtn.innerHTML.replace(buttonText, ' Process File');
            }
            
            // Disable screenshot related features in hidden fields
            const screenshotSelect = document.getElementById('take-screenshot');
            if (screenshotSelect) {
                screenshotSelect.value = 'false';
            }
            
            const screenshotToggle = document.getElementById('take-screenshot-toggle');
            if (screenshotToggle) {
                screenshotToggle.checked = false;
            }
            
        } else {
            // Show URL-specific options
            if (jsCard) jsCard.style.display = 'block';
            if (contentProcessingCard) contentProcessingCard.style.display = 'block';
            if (screenshotCard) screenshotCard.style.display = 'block';
            
            // Show all options for URL mode
            if (ocrCard) ocrCard.style.display = 'block';
            if (reportTitleCard) reportTitleCard.style.display = 'block';
            
            // Reset submit button text
            const crawlBtn = document.getElementById('crawl-btn');
            if (crawlBtn) {
                const iconSpan = crawlBtn.querySelector('i');
                if (iconSpan) {
                    iconSpan.className = 'fas fa-ghost pulse-animation';
                }
                
                // Update text content keeping the icon
                const buttonText = crawlBtn.innerHTML.split('</i>')[1];
                crawlBtn.innerHTML = crawlBtn.innerHTML.replace(buttonText, ' Unleash the Wraith');
            }
            
            // Reset screenshot settings to default
            const screenshotSelect = document.getElementById('take-screenshot');
            if (screenshotSelect) {
                screenshotSelect.value = 'true';
            }
            
            const screenshotToggle = document.getElementById('take-screenshot-toggle');
            if (screenshotToggle) {
                screenshotToggle.checked = true;
            }
        }
    }
    
    // Function to handle search queries, predefined URLs, and file selection
    function setupSearchHandler() {
        const urlInput = document.getElementById('url');
        if (!urlInput) return;
        
        // Set up file selection functionality
        const mainFileSelectBtn = document.getElementById('main-file-select-btn');
        const mainFileInput = document.getElementById('main-file-input');
        const searchBox = document.querySelector('.ghost-search-box');
        
        if (mainFileSelectBtn && mainFileInput) {
            console.log('Initializing file selection for main search box');
            
            mainFileSelectBtn.addEventListener('click', function(e) {
                e.preventDefault();
                console.log('Main file select button clicked');
                mainFileInput.click();
            });
            
            mainFileInput.addEventListener('change', function() {
                if (this.files && this.files.length > 0) {
                    const fileName = this.files[0].name;
                    const fileSize = this.files[0].size;
                    const fileSizeFormatted = formatFileSize(fileSize);
                    
                    console.log('File selected in main search:', fileName, '(', fileSizeFormatted, ')');
                    
                    // Update URL input to show selected file
                    urlInput.value = `File: ${fileName} (${fileSizeFormatted})`;
                    urlInput.classList.add('file-selected');
                    
                    // Add a subtle animation to highlight the change
                    urlInput.classList.add('highlight-input');
                    setTimeout(() => {
                        urlInput.classList.remove('highlight-input');
                    }, 500);
                    
                    // Show clear button and hide file select button
                    const clearFileBtn = document.getElementById('clear-file-btn');
                    if (clearFileBtn) {
                        clearFileBtn.style.display = 'inline-block';
                        mainFileSelectBtn.style.display = 'none';
                    }
                    
                    // Hide URL-specific options and only show file-relevant options
                    toggleFileUploadMode(true);
                    
                    // Optional: auto-submit
                    // document.getElementById('crawl-btn').click();
                }
            });
            
            // Set up clear file button functionality
            const clearFileBtn = document.getElementById('clear-file-btn');
            if (clearFileBtn) {
                clearFileBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    console.log('Clear file button clicked');
                    
                    // Clear the file input
                    if (mainFileInput) {
                        mainFileInput.value = '';
                    }
                    
                    // Reset the URL input
                    if (urlInput) {
                        urlInput.value = '';
                        urlInput.classList.remove('file-selected');
                    }
                    
                    // Hide clear button and show file select button
                    this.style.display = 'none';
                    if (mainFileSelectBtn) {
                        mainFileSelectBtn.style.display = 'inline-block';
                    }
                    
                    // Switch back to URL mode
                    toggleFileUploadMode(false);
                });
            }
            
            // Helper function to format file size
            function formatFileSize(bytes) {
                if (bytes < 1024) return bytes + ' bytes';
                else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
                else if (bytes < 1073741824) return (bytes / 1048576).toFixed(1) + ' MB';
                else return (bytes / 1073741824).toFixed(1) + ' GB';
            }
            
            // Set up drag and drop functionality for the search box
            if (searchBox) {
                console.log('Setting up drag and drop for search box');
                
                // Prevent default behavior for all drag events
                ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                    searchBox.addEventListener(eventName, function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                    });
                });
                
                // Add visual feedback for drag events
                searchBox.addEventListener('dragenter', function() {
                    console.log('Drag enter on search box');
                    searchBox.classList.add('highlight');
                });
                
                searchBox.addEventListener('dragover', function() {
                    searchBox.classList.add('highlight');
                });
                
                searchBox.addEventListener('dragleave', function() {
                    console.log('Drag leave from search box');
                    searchBox.classList.remove('highlight');
                });
                
                // Handle file drop
                searchBox.addEventListener('drop', function(e) {
                    console.log('File dropped on search box');
                    searchBox.classList.remove('highlight');
                    
                    const dt = e.dataTransfer;
                    if (dt.files && dt.files.length > 0) {
                        // Assign the dropped file to the file input
                        mainFileInput.files = dt.files;
                        
                        // Trigger the change event on the file input
                        const event = new Event('change', { bubbles: true });
                        mainFileInput.dispatchEvent(event);
                    }
                });
            }
        }
        
        // Only special case for tech news
        const techNewsUrl = 'https://news.ycombinator.com/';
        
        // Handle input event to check for matches as the user types
        urlInput.addEventListener('input', function() {
            const searchTerm = this.value.trim().toLowerCase();
            
            // If input starts with http:// or https://, it's a URL, don't try to match
            if (searchTerm.startsWith('http://') || searchTerm.startsWith('https://')) {
                return;
            }
            
            // Only handle tech news special case
            if (searchTerm === 'tech news') {
                // Add a small suggestion below the input field
                showSuggestion(`Press Enter to load Hacker News`);
            }
        });
        
        // Handle key press to execute search on Enter
        urlInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                const searchTerm = this.value.trim().toLowerCase();
                
                // If it's already a URL, don't modify it
                if (searchTerm.startsWith('http://') || searchTerm.startsWith('https://')) {
                    document.getElementById('crawl-btn').click();
                    return;
                }
                
                // Only handle tech news special case
                if (searchTerm === 'tech news') {
                    // Replace the input with Hacker News URL
                    this.value = techNewsUrl;
                    document.getElementById('crawl-btn').click();
                    return;
                }
                
                // If it's not tech news and not a URL, just submit as is
                document.getElementById('crawl-btn').click();
                e.preventDefault();
            }
        });
        
        // Function to show a suggestion below the input field
        function showSuggestion(text) {
            let suggestionEl = document.getElementById('url-suggestion');
            
            if (!suggestionEl) {
                suggestionEl = document.createElement('div');
                suggestionEl.id = 'url-suggestion';
                suggestionEl.style.color = '#6c63ff';
                suggestionEl.style.fontSize = '12px';
                suggestionEl.style.marginTop = '5px';
                suggestionEl.style.fontStyle = 'italic';
                
                // Insert after the search box
                const searchBox = document.querySelector('.ghost-search-box');
                if (searchBox && searchBox.parentNode) {
                    searchBox.parentNode.insertBefore(suggestionEl, searchBox.nextSibling);
                }
            }
            
            suggestionEl.textContent = text;
            
            // Auto-hide after 3 seconds
            setTimeout(() => {
                if (suggestionEl.parentNode) {
                    suggestionEl.textContent = '';
                }
            }, 3000);
        }
        
        // Function to show a message in a temporary floating div
        function showMessage(text) {
            let messageEl = document.getElementById('url-message');
            
            if (!messageEl) {
                messageEl = document.createElement('div');
                messageEl.id = 'url-message';
                messageEl.style.position = 'fixed';
                messageEl.style.top = '50%';
                messageEl.style.left = '50%';
                messageEl.style.transform = 'translate(-50%, -50%)';
                messageEl.style.padding = '15px 20px';
                messageEl.style.backgroundColor = '#6c63ff';
                messageEl.style.color = 'white';
                messageEl.style.borderRadius = '8px';
                messageEl.style.boxShadow = '0 4px 10px rgba(0,0,0,0.2)';
                messageEl.style.zIndex = '1000';
                messageEl.style.maxWidth = '80%';
                messageEl.style.textAlign = 'center';
                
                document.body.appendChild(messageEl);
            }
            
            messageEl.textContent = text;
            messageEl.style.display = 'block';
            
            // Hide after 3 seconds
            setTimeout(() => {
                messageEl.style.display = 'none';
            }, 3000);
        }
    }
});
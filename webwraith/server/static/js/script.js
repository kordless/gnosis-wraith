document.addEventListener('DOMContentLoaded', function() {
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
        });
    });

    // Server URL from localStorage or default
    const serverUrl = localStorage.getItem('webwraith-server-url') || 'http://localhost:5678';

    // Single URL Crawl
    const crawlButton = document.getElementById('crawl-btn');
    if (crawlButton) {
        crawlButton.addEventListener('click', async () => {
            const url = document.getElementById('url').value.trim();
            const reportTitle = document.getElementById('report-title').value.trim() || 'Web Crawl Report';
            const outputFormat = document.getElementById('output-format').value;

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
                    output_format: outputFormat
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
                    output_format: outputFormat
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

    // Image Upload
    const uploadButton = document.getElementById('upload-btn');
    if (uploadButton) {
        uploadButton.addEventListener('click', async () => {
            const fileInput = document.getElementById('image-upload');
            const file = fileInput.files[0];

            if (!file) {
                alert('Please select an image to upload');
                return;
            }

            try {
                // Prepare form data
                const formData = new FormData();
                formData.append('image', file);

                // Make API request
                const response = await fetch(`${serverUrl}/api/upload`, {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    throw new Error(`Server responded with status: ${response.status}`);
                }

                const result = await response.json();
                
                // Display upload result
                const uploadResult = document.getElementById('upload-result');
                const previewImage = document.getElementById('preview-image');
                const extractedTextContent = document.getElementById('extracted-text-content');
                
                uploadResult.style.display = 'block';
                previewImage.src = `${serverUrl}/screenshots/${result.file_path}`;
                extractedTextContent.textContent = result.extracted_text || 'No text extracted';
            } catch (error) {
                console.error('Error during upload:', error);
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
});
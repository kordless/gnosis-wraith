/**
 * Crawl Helper Functions
 * Contains functions for crawling URLs and processing suggestions
 */

// Try to crawl a URL directly
async function tryCrawl(url, options = {}) {
  try {
    const {
      title = `Crawl - ${url}`,
      takeScreenshot = true,
      screenshotMode = 'full',
      javascriptEnabled = false,
      javascriptSettleTime = 0,
      ocrExtraction = false,
      markdownExtraction = 'enhanced'
    } = options;
    
    // Log the crawl attempt
    console.log(`Direct crawl attempt: ${url}`);
    
    // Make the crawl request with content_only format for better performance
    const response = await fetch('/api/crawl', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        url: url,
        title: title,
        response_format: 'content_only',  // Use new lightweight response format
        take_screenshot: false,           // Don't generate screenshots for free users
        javascript_enabled: javascriptEnabled,
        markdown_extraction: markdownExtraction,
        timeout: 30
      })
    });
    
    // Check if the request was successful
    if (!response.ok) {
      return {
        success: false,
        error: `Server error: ${response.status} - ${response.statusText}`,
        status: response.status,
        direct: true
      };
    }
    
    // Parse the JSON response
    const result = await response.json();
    
    // Add a flag to indicate this was a direct crawl
    result.direct = true;
    
    return result;
  } catch (error) {
    return {
      success: false,
      error: error.message,
      direct: true
    };
  }
}

// Try to get a suggestion for non-URL input
async function trySuggest(input, provider = null) {
  try {
    // Ensure input is intact - log for debugging
    logQuery('/api/suggest', input);
    
    // Check if input has been truncated or modified
    if (input.includes(' ')) {
      console.log(`Multi-word query detected: "${input}"`);
    }
    
    // Get the selected provider and corresponding API key from cookies
    const selectedProvider = provider || localStorage.getItem('gnosis_wraith_llm_provider') || 'anthropic';
    
    // Determine the cookie name for the API key
    let cookieName;
    switch (selectedProvider) {
      case 'anthropic':
        cookieName = 'gnosis_wraith_llm_token_anthropic';
        break;
      case 'openai':
        cookieName = 'gnosis_wraith_llm_token_openai';
        break;
      case 'gemini':
        cookieName = 'gnosis_wraith_llm_token_gemini';
        break;
      default:
        cookieName = 'gnosis_wraith_llm_token_anthropic';
    }
    
    // Get the API key
    const apiKey = CookieUtils.getCookie(cookieName);
    
    // Create the request body
    const requestBody = {
      query: input,
      provider: selectedProvider,
      api_key: apiKey || null
    };
    
    // Log the actual data being sent
    console.log('Request body:', JSON.stringify(requestBody));
    
    // Make the suggestion request
    const response = await fetch('/api/suggest', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody)
    });
    
    // Check if the request was successful
    if (!response.ok) {
      return {
        success: false,
        error: `Suggestion API error: ${response.status} - ${response.statusText}`,
        status: response.status
      };
    }
    
    // Parse the JSON response
    return await response.json();
  } catch (error) {
    return {
      success: false,
      error: `Suggestion API error: ${error.message}`
    };
  }
}

// Log user queries being sent to the API
function logQuery(endpoint, query) {
  console.log(`Query to ${endpoint}: "${query}"`);
  
  // Add event for debugging
  const currentTime = new Date().toISOString();
  console.log(`${currentTime}\nDetected input: "${query}"`);
}

// Process and display crawl results (updated for content_only response format)
function displayCrawlResults(result, options = {}) {
  const { addLog, reportFormat, updateCrawlStats, updateLocalCrawlHistory } = options;
  
  if (!addLog) {
    console.error('displayCrawlResults requires addLog function');
    return;
  }
  
  if (result.success) {
    // Log successful crawl
    addLog('Crawl successful.');
    
    // For content_only format, we get the markdown content directly
    if (result.markdown_content) {
      const contentLength = result.markdown_content.length;
      const wordCount = result.markdown_content.split(/\s+/).length;
      
      addLog(`<span class="text-blue-400 font-semibold">Content extracted:</span> <span class="text-gray-300">${contentLength} characters, ~${wordCount} words</span>`);
      
      // Show content preview
      const previewText = result.markdown_content.slice(0, 200) + (result.markdown_content.length > 200 ? '...' : '');
      addLog(`<div class="content-preview bg-gray-900 rounded p-3 my-2 border-l-2 border-blue-500">
        <div class="text-xs text-blue-400 font-semibold mb-2">Content Preview:</div>
        <div class="text-gray-300 text-sm whitespace-pre-wrap">${previewText}</div>
      </div>`);
      
      // Show file links with format toggles if available
      if (result.report_path || result.html_path || result.json_path) {
        const reportId = 'report_' + Math.random().toString(36).substr(2, 9);
        let toggleButtons = '';
        let defaultPath = '';
        
        // Build toggle buttons for available formats
        if (result.report_path) {
          toggleButtons += `<button class="format-toggle text-xs px-2 py-1 bg-green-700 hover:bg-green-600 rounded mr-1 active" data-format="md" data-path="/reports/${result.report_path}">MD</button>`;
          defaultPath = `/reports/${result.report_path}`;
        }
        if (result.html_path) {
          toggleButtons += `<button class="format-toggle text-xs px-2 py-1 bg-blue-700 hover:bg-blue-600 rounded mr-1" data-format="html" data-path="/reports/${result.html_path}">HTML</button>`;
          if (!defaultPath) defaultPath = `/reports/${result.html_path}`;
        }
        if (result.json_path) {
          toggleButtons += `<button class="format-toggle text-xs px-2 py-1 bg-purple-700 hover:bg-purple-600 rounded mr-1" data-format="json" data-path="/reports/${result.json_path}">JSON</button>`;
          if (!defaultPath) defaultPath = `/reports/${result.json_path}`;
        }
        
        addLog(`<div class="report-files bg-gray-900 rounded p-3 my-2 border-l-2 border-green-500" id="${reportId}">
          <div class="flex justify-between items-center mb-2">
            <div class="text-xs text-green-400 font-semibold">Generated Reports:</div>
            <div class="format-toggles">${toggleButtons}</div>
          </div>
          <div class="flex items-center">
            <a href="${defaultPath}" target="_blank" class="report-link text-green-300 hover:text-green-200 underline px-2 py-1 bg-gray-800 rounded">
              <i class="fas fa-external-link-alt text-xs mr-1"></i><span class="link-text">Open Report</span>
            </a>
          </div>
        </div>`);
        
        // Add JavaScript for toggle functionality (only once)
        if (!window.reportToggleHandlerAdded) {
          window.reportToggleHandlerAdded = true;
          
          // Add event delegation for format toggles
          document.addEventListener('click', function(e) {
            if (e.target.classList.contains('format-toggle')) {
              e.preventDefault();
              
              // Find the parent report container
              const reportContainer = e.target.closest('.report-files');
              const reportLink = reportContainer.querySelector('.report-link');
              const linkText = reportContainer.querySelector('.link-text');
              
              // Update active button
              reportContainer.querySelectorAll('.format-toggle').forEach(btn => {
                btn.classList.remove('active', 'bg-green-700', 'bg-blue-700', 'bg-purple-700');
                if (btn.dataset.format === 'md') btn.classList.add('bg-green-700');
                else if (btn.dataset.format === 'html') btn.classList.add('bg-blue-700');
                else if (btn.dataset.format === 'json') btn.classList.add('bg-purple-700');
              });
              
              e.target.classList.add('active');
              if (e.target.dataset.format === 'md') e.target.classList.add('bg-green-700');
              else if (e.target.dataset.format === 'html') e.target.classList.add('bg-blue-700');
              else if (e.target.dataset.format === 'json') e.target.classList.add('bg-purple-700');
              
              // Update link
              reportLink.href = e.target.dataset.path;
              linkText.textContent = e.target.dataset.format === 'md' ? 'Open Markdown' : 
                                   e.target.dataset.format === 'html' ? 'Open HTML' : 'Open JSON';
            }
          });
        }
      } else {
        // Fallback message if no file paths available
        addLog(`<div class="text-xs text-blue-400 mt-2">
          <i class="fas fa-info-circle mr-1"></i>
          Content-only mode: Files generated in background (faster response)
        </div>`);
      }
    } else {
      addLog(`<span class="text-yellow-400">Content extracted but empty</span>`);
    }
    
    // Update stats if function is provided
    if (updateCrawlStats) {
      updateCrawlStats(true);
    }
    
    // Update local crawl history if function is provided
    if (updateLocalCrawlHistory) {
      try {
        // Create a new crawl history entry for content_only mode
        const crawlEntry = {
          url: result.url || 'Unknown URL',
          title: result.title || `Crawl - ${new Date().toLocaleString()}`,
          timestamp: new Date().toISOString(),
          created_str: new Date().toLocaleString(),
          success: true,
          content_length: result.markdown_content ? result.markdown_content.length : 0,
          mode: 'content_only',
          tags: [] // For future tag functionality
        };
        
        // Update the history
        updateLocalCrawlHistory(crawlEntry);
      } catch (error) {
        console.error('Error creating crawl history entry:', error);
      }
    }
  } else {
    // Log error
    addLog(`Crawl error: ${result.error || 'Unknown error'}`);
    
    // Update stats if function is provided
    if (updateCrawlStats) {
      updateCrawlStats(false);
    }
  }
  
  return result.success;
}

// Make these functions available globally
window.tryCrawl = tryCrawl;
window.trySuggest = trySuggest;
window.displayCrawlResults = displayCrawlResults;
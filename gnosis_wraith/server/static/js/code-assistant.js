/**
 * Gnosis Wraith Code Assistant
 * Handles the code examples display and syntax highlighting
 */

// Map of file extensions to language names and icon classes
const LANGUAGE_MAP = {
    'py': { name: 'Python', icon: 'fab fa-python', class: 'language-python' },
    'js': { name: 'JavaScript', icon: 'fab fa-js', class: 'language-javascript' },
    'html': { name: 'HTML', icon: 'fab fa-html5', class: 'language-html' },
    'css': { name: 'CSS', icon: 'fab fa-css3-alt', class: 'language-css' },
    'json': { name: 'JSON', icon: 'fas fa-code', class: 'language-json' },
    'sh': { name: 'Shell', icon: 'fas fa-terminal', class: 'language-bash' },
    'bash': { name: 'Bash', icon: 'fas fa-terminal', class: 'language-bash' },
    'ts': { name: 'TypeScript', icon: 'fab fa-js', class: 'language-typescript' },
    'jsx': { name: 'React JSX', icon: 'fab fa-react', class: 'language-jsx' },
    'tsx': { name: 'React TSX', icon: 'fab fa-react', class: 'language-tsx' },
    'sql': { name: 'SQL', icon: 'fas fa-database', class: 'language-sql' },
    'md': { name: 'Markdown', icon: 'fas fa-file-alt', class: 'language-markdown' },
    'java': { name: 'Java', icon: 'fab fa-java', class: 'language-java' },
    'c': { name: 'C', icon: 'fas fa-code', class: 'language-c' },
    'cpp': { name: 'C++', icon: 'fas fa-code', class: 'language-cpp' },
    'cs': { name: 'C#', icon: 'fas fa-code', class: 'language-csharp' },
    'go': { name: 'Go', icon: 'fas fa-code', class: 'language-go' },
    'rb': { name: 'Ruby', icon: 'fas fa-gem', class: 'language-ruby' },
    'php': { name: 'PHP', icon: 'fab fa-php', class: 'language-php' },
    'swift': { name: 'Swift', icon: 'fas fa-code', class: 'language-swift' },
    'r': { name: 'R', icon: 'fas fa-chart-line', class: 'language-r' },
    'yml': { name: 'YAML', icon: 'fas fa-file-code', class: 'language-yaml' },
    'yaml': { name: 'YAML', icon: 'fas fa-file-code', class: 'language-yaml' },
    'xml': { name: 'XML', icon: 'fas fa-file-code', class: 'language-xml' },
    'docker': { name: 'Dockerfile', icon: 'fab fa-docker', class: 'language-dockerfile' },
    'ps1': { name: 'PowerShell', icon: 'fab fa-windows', class: 'language-powershell' }
};

// Example code snippets for different languages
const EXAMPLE_CODE = {
    'python': `#!/usr/bin/env python3
"""
Basic example of using the Gnosis Wraith API to crawl a website.
"""
import requests
import json

# URL of your Gnosis Wraith server
SERVER_URL = "http://localhost:5678"  # Change this to match your server

def crawl_website(url, take_screenshot=True, javascript_enabled=False):
    """
    Crawl a website using the Gnosis Wraith API.
    
    Args:
        url (str): The URL to crawl
        take_screenshot (bool): Whether to take a screenshot
        javascript_enabled (bool): Whether to enable JavaScript during crawling
        
    Returns:
        dict: The API response
    """
    endpoint = f"{SERVER_URL}/api/crawl"
    
    # Configure the request payload
    payload = {
        "url": url,
        "title": f"Crawl Report: {url}",
        "take_screenshot": take_screenshot,
        "javascript_enabled": javascript_enabled,
        "ocr_extraction": False,
        "markdown_extraction": "enhanced"
    }
    
    # Make the API request
    response = requests.post(endpoint, json=payload)
    
    # Check if the request was successful
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return {"success": False, "error": f"API request failed with status code {response.status_code}"}

def main():
    # Example usage
    url_to_crawl = "https://news.ycombinator.com/"
    print(f"Crawling {url_to_crawl}...")
    
    # Call the API
    result = crawl_website(url_to_crawl)
    
    # Check if the crawl was successful
    if result.get("success"):
        print("Crawl successful!")
        
        # Print details about the results
        for item in result.get("results", []):
            print(f"\\nTitle: {item.get('title', 'No title')}")
            
            # Check if a screenshot was taken
            if "screenshot" in item:
                print(f"Screenshot: {SERVER_URL}/screenshots/{item['screenshot']}")
            
            # Print a snippet of the extracted text if available
            if "extracted_text" in item:
                text_preview = item["extracted_text"][:100] + "..." if len(item["extracted_text"]) > 100 else item["extracted_text"]
                print(f"Text preview: {text_preview}")
        
        # Print the report URL if available
        if "report_path" in result:
            print(f"\\nFull report: {SERVER_URL}/reports/{result['report_path']}")
            print(f"HTML report: {SERVER_URL}/reports/{result['report_path'].replace('.md', '.html')}")
    else:
        print(f"Crawl failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()`,
    
    'javascript': `/**
 * Basic example of using the Gnosis Wraith API to crawl a website with JavaScript.
 */

// URL of your Gnosis Wraith server
const SERVER_URL = "http://localhost:5678"; // Change this to match your server

/**
 * Crawl a website using the Gnosis Wraith API.
 * 
 * @param {string} url - The URL to crawl
 * @param {Object} options - Optional configuration
 * @param {boolean} options.takeScreenshot - Whether to take a screenshot
 * @param {boolean} options.javascriptEnabled - Whether to enable JavaScript during crawling
 * @returns {Promise<Object>} - The API response
 */
async function crawlWebsite(url, options = {}) {
    const { 
        takeScreenshot = true, 
        javascriptEnabled = false,
        ocrExtraction = false,
        markdownExtraction = "enhanced"
    } = options;
    
    const endpoint = `${SERVER_URL}/api/crawl`;
    
    // Configure the request payload
    const payload = {
        url,
        title: `Crawl Report: ${url}`,
        take_screenshot: takeScreenshot,
        javascript_enabled: javascriptEnabled,
        ocr_extraction: ocrExtraction,
        markdown_extraction: markdownExtraction
    };
    
    try {
        // Make the API request
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        // Check if the request was successful
        if (!response.ok) {
            throw new Error(`API request failed with status code ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error during crawl:', error);
        return { success: false, error: error.message };
    }
}

/**
 * Main function to demonstrate usage.
 */
async function main() {
    // Example usage
    const urlToCrawl = "https://news.ycombinator.com/";
    console.log(`Crawling ${urlToCrawl}...`);
    
    // Call the API
    const result = await crawlWebsite(urlToCrawl, {
        takeScreenshot: true,
        javascriptEnabled: true
    });
    
    // Check if the crawl was successful
    if (result.success) {
        console.log("Crawl successful!");
        
        // Print details about the results
        result.results?.forEach(item => {
            console.log(`\nTitle: ${item.title || 'No title'}`);
            
            // Check if a screenshot was taken
            if (item.screenshot) {
                console.log(`Screenshot: ${SERVER_URL}/screenshots/${item.screenshot}`);
            }
            
            // Print a snippet of the extracted text if available
            if (item.extracted_text) {
                const textPreview = item.extracted_text.length > 100 
                    ? item.extracted_text.substring(0, 100) + '...' 
                    : item.extracted_text;
                console.log(`Text preview: ${textPreview}`);
            }
        });
        
        // Print the report URL if available
        if (result.report_path) {
            console.log(`\nFull report: ${SERVER_URL}/reports/${result.report_path}`);
            console.log(`HTML report: ${SERVER_URL}/reports/${result.report_path.replace('.md', '.html')}`);
        }
    } else {
        console.error(`Crawl failed: ${result.error || 'Unknown error'}`);
    }
}

// Run the example
main().catch(console.error);`,
    
    'html': `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gnosis Wraith API Example</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input[type="text"], select {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        button {
            background-color: #4e9eff;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #3b87e0;
        }
        .result {
            margin-top: 20px;
            border: 1px solid #ddd;
            padding: 15px;
            border-radius: 4px;
            background-color: #f9f9f9;
        }
        .error {
            color: #e74c3c;
            font-weight: bold;
        }
        pre {
            background-color: #f0f0f0;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }
        img {
            max-width: 100%;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <h1>Gnosis Wraith Web Crawler</h1>
    
    <div class="form-group">
        <label for="url">URL to Crawl:</label>
        <input type="text" id="url" placeholder="https://example.com">
    </div>
    
    <div class="form-group">
        <label for="screenshot">Take Screenshot:</label>
        <select id="screenshot">
            <option value="true" selected>Yes</option>
            <option value="false">No</option>
        </select>
    </div>
    
    <div class="form-group">
        <label for="javascript">Enable JavaScript:</label>
        <select id="javascript">
            <option value="true">Yes</option>
            <option value="false" selected>No</option>
        </select>
    </div>
    
    <div class="form-group">
        <label for="markdown">Markdown Extraction:</label>
        <select id="markdown">
            <option value="enhanced" selected>Enhanced</option>
            <option value="basic">Basic</option>
            <option value="none">None</option>
        </select>
    </div>
    
    <button id="crawl-btn">Crawl Website</button>
    
    <div id="result" class="result" style="display: none;">
        <h2>Results</h2>
        <div id="result-content"></div>
    </div>
    
    <script>
        // URL of your Gnosis Wraith server
        const SERVER_URL = "http://localhost:5678";
        
        document.getElementById('crawl-btn').addEventListener('click', async () => {
            const url = document.getElementById('url').value.trim();
            
            if (!url) {
                alert('Please enter a URL');
                return;
            }
            
            const takeScreenshot = document.getElementById('screenshot').value === 'true';
            const javascriptEnabled = document.getElementById('javascript').value === 'true';
            const markdownExtraction = document.getElementById('markdown').value;
            
            // Show loading state
            const resultDiv = document.getElementById('result');
            resultDiv.style.display = 'block';
            const resultContent = document.getElementById('result-content');
            resultContent.innerHTML = '<p>Crawling... Please wait.</p>';
            
            try {
                // Configure the request payload
                const payload = {
                    url,
                    title: `Crawl Report: ${url}`,
                    take_screenshot: takeScreenshot,
                    javascript_enabled: javascriptEnabled,
                    ocr_extraction: false,
                    markdown_extraction: markdownExtraction
                };
                
                // Make the API request
                const response = await fetch(`${SERVER_URL}/api/crawl`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });
                
                if (!response.ok) {
                    throw new Error(`API request failed with status code ${response.status}`);
                }
                
                const result = await response.json();
                
                if (result.success) {
                    let html = '<h3>Crawl Successful!</h3>';
                    
                    result.results.forEach(item => {
                        html += `<h4>${item.title || 'No title'}</h4>`;
                        html += `<p>URL: ${item.url || 'Unknown'}</p>`;
                        
                        if (item.screenshot) {
                            html += `<h5>Screenshot:</h5>`;
                            html += `<img src="${SERVER_URL}/screenshots/${item.screenshot}" alt="Screenshot">`;
                        }
                        
                        if (item.extracted_text) {
                            html += `<h5>Extracted Text:</h5>`;
                            html += `<pre>${item.extracted_text}</pre>`;
                        }
                    });
                    
                    if (result.report_path) {
                        html += `<h5>Reports:</h5>`;
                        html += `<p><a href="${SERVER_URL}/reports/${result.report_path}" target="_blank">View Markdown Report</a></p>`;
                        html += `<p><a href="${SERVER_URL}/reports/${result.report_path.replace('.md', '.html')}" target="_blank">View HTML Report</a></p>`;
                    }
                    
                    resultContent.innerHTML = html;
                } else {
                    resultContent.innerHTML = `<p class="error">Crawl failed: ${result.error || 'Unknown error'}</p>`;
                }
            } catch (error) {
                resultContent.innerHTML = `<p class="error">Error: ${error.message}</p>`;
            }
        });
    </script>
</body>
</html>`,
    
    'bash': `#!/bin/bash
# Basic shell script example for interacting with Gnosis Wraith API

# URL of your Gnosis Wraith server
SERVER_URL="http://localhost:5678"

# Function to crawl a URL
crawl_url() {
    local url=$1
    local take_screenshot=${2:-true}
    local js_enabled=${3:-false}
    
    echo "Crawling $url..."
    
    # Create JSON payload
    payload=$(cat <<EOF
{
    "url": "$url",
    "title": "Crawl Report: $url",
    "take_screenshot": $take_screenshot,
    "javascript_enabled": $js_enabled,
    "ocr_extraction": false,
    "markdown_extraction": "enhanced"
}
EOF
    )
    
    # Make the API request with curl
    response=$(curl -s -X POST "$SERVER_URL/api/crawl" \
        -H "Content-Type: application/json" \
        -d "$payload")
    
    # Check if the request was successful
    if echo "$response" | grep -q '"success":true'; then
        echo "Crawl successful!"
        
        # Extract report path using grep and cut
        report_path=$(echo "$response" | grep -o '"report_path":"[^"]*"' | cut -d'"' -f4)
        
        if [ -n "$report_path" ]; then
            echo "Report available at: $SERVER_URL/reports/$report_path"
            echo "HTML report available at: $SERVER_URL/reports/${report_path/.md/.html}"
        fi
        
        # Extract screenshot path if available
        screenshot_path=$(echo "$response" | grep -o '"screenshot":"[^"]*"' | cut -d'"' -f4)
        
        if [ -n "$screenshot_path" ]; then
            echo "Screenshot available at: $SERVER_URL/screenshots/$screenshot_path"
        fi
    else
        echo "Crawl failed!"
        echo "$response"
    fi
}

# Function to delete a report
delete_report() {
    local report_path=$1
    
    echo "Deleting report: $report_path"
    
    # Make the API request with curl
    response=$(curl -s -X DELETE "$SERVER_URL/api/reports/$report_path")
    
    # Check if the request was successful
    if echo "$response" | grep -q '"success":true'; then
        echo "Report deleted successfully!"
    else
        echo "Failed to delete report!"
        echo "$response"
    fi
}

# Main menu
show_menu() {
    echo ""
    echo "Gnosis Wraith API Client"
    echo "========================"
    echo "1. Crawl a URL"
    echo "2. Delete a report"
    echo "3. Exit"
    echo ""
    read -p "Enter your choice (1-3): " choice
    
    case $choice in
        1)
            read -p "Enter URL to crawl: " url
            read -p "Take screenshot? (true/false): " screenshot
            read -p "Enable JavaScript? (true/false): " js_enabled
            
            crawl_url "$url" "${screenshot:-true}" "${js_enabled:-false}"
            show_menu
            ;;
        2)
            read -p "Enter report path to delete: " report_path
            delete_report "$report_path"
            show_menu
            ;;
        3)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "Invalid choice!"
            show_menu
            ;;
    esac
}

# Start the menu
show_menu`
};

// Initialize code assistant when document is ready
document.addEventListener('DOMContentLoaded', function() {
    const codeQuery = document.getElementById('code-query');
    const askWraithBtn = document.getElementById('ask-wraith-btn');
    const codeOutput = document.getElementById('code-output');
    const codeLanguageBadge = document.querySelector('.code-language-badge');
    
    if (!codeQuery || !askWraithBtn || !codeOutput || !codeLanguageBadge) {
        console.error('Code assistant elements not found!');
        return;
    }
    
    // Add event listener to the button
    askWraithBtn.addEventListener('click', function() {
        handleCodeRequest();
    });
    
    // Add event listener for Enter key
    codeQuery.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleCodeRequest();
        }
    });
    
    // Initial code example
    if (codeOutput.innerHTML.trim() === '') {
        updateCodeDisplay('python', EXAMPLE_CODE.python);
    }
    
    // Function to handle code requests
    function handleCodeRequest() {
        const query = codeQuery.value.trim();
        
        if (!query) {
            showErrorMessage('Please enter a code query');
            return;
        }
        
        // Show loading state
        codeOutput.textContent = 'Generating code...';
        
        // Make API call to /api/code
        callCodeAPI(query)
            .then(response => {
                // Update the display with the response code
                updateCodeDisplay(response.language, response.code, response.metadata?.file_info);
                
                // Clear input after short delay
                setTimeout(() => {
                    codeQuery.value = '';
                }, 500);
            })
            .catch(error => {
                // Handle error
                console.error('Error generating code:', error);
                codeOutput.textContent = `Error: ${error.message}. Please try again.`;
                codeOutput.className = 'language-plaintext';
                Prism.highlightElement(codeOutput);
            });
    }
    
    // Function to call the code generation API
    async function callCodeAPI(query) {
        // For development - simulate API response
        // In production, this would be a real API call
        
        // Currently simulating the API call
        return new Promise((resolve) => {
            // Short delay to simulate network request
            setTimeout(() => {
                // Detect language from query for the simulated API
                const language = detectLanguageFromQuery(query);
                const code = getCodeExample(language);
                
                // Get language info for proper file extension handling
                const langInfo = getLangInfoFromLanguage(language);
                const fileExtension = language === 'python' ? 'py' : 
                                     language === 'javascript' ? 'js' : 
                                     language === 'html' ? 'html' : 
                                     language === 'css' ? 'css' : 
                                     language === 'bash' || language === 'shell' ? 'sh' : 
                                     language === 'json' ? 'json' : 
                                     language === 'typescript' ? 'ts' : 
                                     'txt';
                
                // Generate a suitable filename based on language
                const fileName = `wraith_${language}_example`;
                
                // Simulate API response format with enhanced metadata for file downloads
                const response = {
                    success: true,
                    language: language,
                    code: code,
                    metadata: {
                        token_count: code.length,
                        model: "gnosis-wraith-code-v1",
                        query_time_ms: Math.floor(Math.random() * 500) + 300,  // Random time between 300-800ms
                        language_info: langInfo,
                        file_info: {
                            extension: fileExtension,
                            filename: fileName,
                            mime_type: getMimeTypeForLanguage(language),
                            suggested_name: `${fileName}.${fileExtension}`
                        }
                    }
                };
                
                // Log the response for debugging
                console.log('API Response:', response);
                
                resolve(response);
            }, 800);
        });
        
        /* 
        // This is what the actual API call would look like:
        
        const serverUrl = window.location.origin;
        
        const response = await fetch(`${serverUrl}/api/code`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                options: {
                    // Optional parameters
                    language_preference: detectLanguageFromQuery(query),
                    max_tokens: 2000,
                    format: "formatted" // or "raw"
                }
            })
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        return await response.json();
        */
    }
    
    // Function to detect language from query
    function detectLanguageFromQuery(query) {
        query = query.toLowerCase();
        
        // Check for explicit language mentions
        if (query.includes('python') || query.includes('py ')) {
            return 'python';
        } else if (query.includes('javascript') || query.includes('js ') || query.includes('node')) {
            return 'javascript';
        } else if (query.includes('html') || query.includes('webpage') || query.includes('web page')) {
            return 'html';
        } else if (query.includes('bash') || query.includes('shell') || query.includes('command line') || query.includes('terminal')) {
            return 'bash';
        } else if (query.includes('css') || query.includes('style')) {
            return 'css';
        } else if (query.includes('json')) {
            return 'json';
        }
        
        // Default to Python
        return 'python';
    }
    
    // Function to get code example for a language
    function getCodeExample(language) {
        return EXAMPLE_CODE[language] || EXAMPLE_CODE.python;
    }
    
    // Function to update the code display with proper syntax highlighting
    function updateCodeDisplay(language, code, fileInfo = null) {
        // Update the language badge
        const langInfo = getLangInfoFromLanguage(language);
        updateLanguageBadge(langInfo);
        
        // Update code content and apply syntax highlighting
        codeOutput.className = langInfo.class;
        codeOutput.textContent = code;
        
        // Apply Prism highlighting
        if (window.Prism) {
            Prism.highlightElement(codeOutput);
        }
        
        // Store file info as data attributes for download functionality
        if (codeOutput && fileInfo) {
            codeOutput.dataset.extension = fileInfo.extension || '';
            codeOutput.dataset.filename = fileInfo.filename || '';
            codeOutput.dataset.mimeType = fileInfo.mime_type || '';
            codeOutput.dataset.suggestedName = fileInfo.suggested_name || '';
        } else {
            // Default file info based on language
            const ext = language === 'python' ? 'py' : 
                        language === 'javascript' ? 'js' : 
                        language === 'html' ? 'html' : 
                        language === 'bash' ? 'sh' : 'txt';
            
            codeOutput.dataset.extension = ext;
            codeOutput.dataset.filename = `wraith_${language}_example`;
            codeOutput.dataset.mimeType = getMimeTypeForLanguage(language);
            codeOutput.dataset.suggestedName = `wraith_${language}_example.${ext}`;
        }
    }
    
    // Function to get language info from language string
    function getLangInfoFromLanguage(language) {
        if (LANGUAGE_MAP[language]) {
            return LANGUAGE_MAP[language];
        }
        
        // Check if we have a direct entry in LANGUAGE_MAP
        for (const [ext, info] of Object.entries(LANGUAGE_MAP)) {
            if (info.name.toLowerCase() === language.toLowerCase()) {
                return info;
            }
        }
        
        // Default to Python
        return LANGUAGE_MAP['py'];
    }
    
    // Function to get MIME type for a language
    function getMimeTypeForLanguage(language) {
        const mimeTypes = {
            'python': 'text/x-python',
            'javascript': 'text/javascript',
            'html': 'text/html',
            'css': 'text/css',
            'json': 'application/json',
            'bash': 'text/x-sh',
            'shell': 'text/x-sh',
            'typescript': 'text/typescript',
            'jsx': 'text/jsx',
            'tsx': 'text/tsx',
            'java': 'text/x-java',
            'c': 'text/x-c',
            'cpp': 'text/x-c++',
            'cs': 'text/x-csharp',
            'go': 'text/x-go',
            'php': 'application/x-php',
            'ruby': 'text/x-ruby',
            'swift': 'text/x-swift',
            'r': 'text/x-r',
            'yaml': 'text/yaml',
            'yml': 'text/yaml',
            'xml': 'text/xml',
            'md': 'text/markdown'
        };
        
        return mimeTypes[language] || 'text/plain';
    }
    
    // Function to update the language badge
    function updateLanguageBadge(langInfo) {
        if (!codeLanguageBadge) return;
        
        // Update the badge text and icon
        codeLanguageBadge.innerHTML = `<i class="${langInfo.icon}"></i> ${langInfo.name}`;
        
        // Remove all language classes
        codeLanguageBadge.className = 'code-language-badge';
        
        // Add the appropriate language class
        const langClass = `lang-${langInfo.name.toLowerCase().replace('#', 'sharp')}`;
        codeLanguageBadge.classList.add(langClass);
    }
    
    // Helper function to show error message
    function showErrorMessage(message) {
        // Flash the input field
        codeQuery.classList.add('error');
        setTimeout(() => {
            codeQuery.classList.remove('error');
        }, 1000);
        
        console.error(message);
    }
});

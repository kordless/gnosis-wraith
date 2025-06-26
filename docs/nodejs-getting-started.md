# Node.js Getting Started Guide for Gnosis Wraith

This guide will help you get started with using the Gnosis Wraith API from Node.js.

## Prerequisites

- Node.js installed (version 16 or higher)
- An API key for Gnosis Wraith

## Quick Start

### 1. Basic API Request

Create a file called `wraith-test.js`:

```javascript
const https = require('https');

// Configuration
const API_KEY = 'your-api-key-here';
const SERVER = 'https://wraith.nuts.services';

// Simple function to get markdown from a URL
async function getMarkdown(url) {
    const payload = JSON.stringify({
        url: url,
        javascript_enabled: false
    });

    const options = {
        hostname: 'wraith.nuts.services',
        path: '/api/markdown',
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${API_KEY}`,
            'Content-Length': payload.length
        }
    };

    return new Promise((resolve, reject) => {
        const req = https.request(options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    resolve(JSON.parse(data));
                } catch (e) {
                    reject(e);
                }
            });
        });
        
        req.on('error', reject);
        req.write(payload);
        req.end();
    });
}

// Use the function
getMarkdown('https://example.com')
    .then(result => {
        console.log('Success!');
        console.log('Markdown URL:', result.markdown_url);
        console.log('JSON URL:', result.json_url);
    })
    .catch(error => {
        console.error('Error:', error);
    });
```

### 2. Run the Script

```bash
node wraith-test.js
```

## Using npm Packages (Optional)

If you prefer using npm packages for cleaner code:

### 1. Initialize npm and install axios

```bash
npm init -y
npm install axios
```

### 2. Create `wraith-axios.js`:

```javascript
const axios = require('axios');

const API_KEY = 'your-api-key-here';
const SERVER = 'https://wraith.nuts.services';

async function getMarkdown(url) {
    try {
        const response = await axios.post(
            `${SERVER}/api/markdown`,
            {
                url: url,
                javascript_enabled: true
            },
            {
                headers: {
                    'Authorization': `Bearer ${API_KEY}`,
                    'Content-Type': 'application/json'
                }
            }
        );
        
        return response.data;
    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
        throw error;
    }
}

// Example usage
async function main() {
    try {
        const result = await getMarkdown('https://example.com');
        console.log('Success!');
        console.log('Markdown URL:', result.markdown_url);
        console.log('Stats:', result.stats);
    } catch (error) {
        console.error('Failed to get markdown');
    }
}

main();
```

## Batch Processing

To process multiple URLs at once:

```javascript
async function batchMarkdown(urls) {
    const payload = JSON.stringify({
        urls: urls,
        async: false,  // Wait for all to complete
        javascript_enabled: false
    });

    // ... same request setup as above ...
}

// Process multiple URLs
batchMarkdown([
    'https://example.com',
    'https://wikipedia.org',
    'https://python.org'
]).then(result => {
    console.log(`Processed ${result.results.length} URLs`);
    result.results.forEach((item, i) => {
        console.log(`${i + 1}. ${item.url} - ${item.status}`);
    });
});
```

## Common Options

### Request Options

```javascript
{
    url: 'https://example.com',           // Required: URL to process
    javascript_enabled: true,              // Enable JavaScript rendering
    screenshot_mode: 'viewport',           // Capture screenshot
    filter: 'pruning',                     // Apply content filter
    filter_options: {                      // Filter-specific options
        threshold: 0.5
    }
}
```

### Batch Options

```javascript
{
    urls: [...],                          // Array of URLs (max 50)
    async: true,                          // Don't wait for completion
    collate: true,                        // Merge results into one file
    collate_options: {
        title: 'My Collection',
        add_toc: true
    }
}
```

## Error Handling

Always include error handling:

```javascript
try {
    const result = await getMarkdown(url);
    // Process result
} catch (error) {
    if (error.response) {
        // API returned an error
        console.error('API Error:', error.response.status, error.response.data);
    } else if (error.request) {
        // Request failed
        console.error('Network Error:', error.message);
    } else {
        // Other error
        console.error('Error:', error.message);
    }
}
```

## Testing Your Setup

1. Save any of the example scripts above
2. Replace `'your-api-key-here'` with your actual API key
3. Run with Node.js: `node your-script.js`

## Next Steps

- Check out `test_api_markdown.js` for comprehensive examples
- See the API documentation for all available options
- Use the Python examples as reference (the API works the same way)

## Troubleshooting

- **SSL/Certificate errors**: Use `NODE_TLS_REJECT_UNAUTHORIZED=0` (development only)
- **Timeouts**: Increase timeout in request options
- **API key issues**: Ensure your key has the correct prefix "Bearer "

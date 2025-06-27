#!/usr/bin/env node
/**
 * Simple test for Gnosis Wraith /api/markdown endpoint
 * 
 * Usage:
 *   node simple_test_api_markdown.js                    # Uses staging, no filter
 *   node simple_test_api_markdown.js local              # Test local server
 *   node simple_test_api_markdown.js staging pruning    # Test staging with pruning filter
 *   node simple_test_api_markdown.js production bm25    # Test production with BM25 filter
 *   node simple_test_api_markdown.js staging bm25 "product automation"  # BM25 with custom query
 * 
 * Servers: local, staging, production
 * Filters: pruning (reduce duplicates), bm25 (relevance filtering)
 */

const https = require('https');
const http = require('http');

// Configuration - Select which server to test
const SERVERS = {
    local: "http://localhost:5678",
    staging: "https://gnosis-wraith-staging-949870462453.us-central1.run.app",
    production: "https://wraith.nuts.services"
};

// Get server from command line argument or default to staging
const serverArg = process.argv[2] || 'staging';
const REMOTE_SERVER = SERVERS[serverArg] || SERVERS.staging;

// API Key configuration
const API_KEYS = {
    local: "5YzHvCGETYkn3KzSV1gtugE70EAugPAXJvcV5MMbPui0H7YfN2sHg", // Local doesn't need a real key usually
    staging: "Ij8zhKKL_iKUcumU5oQKnpsECg9qvYTdXlH2IGth7k_ewGBdy6se_g",
    production: "Ij8zhKKL_iKUcumU5oQKnpsECg9qvYTdXlH2IGth7k_ewGBdy6se_g" // Same key for now
};

const API_KEY = API_KEYS[serverArg] || API_KEYS.staging;


/**
 * Make HTTP request helper
 */
function makeRequest(url, options, payload) {
    return new Promise((resolve, reject) => {
        const urlObj = new URL(url);
        const protocol = urlObj.protocol === 'https:' ? https : http;
        
        const reqOptions = {
            hostname: urlObj.hostname,
            port: urlObj.port || (urlObj.protocol === 'https:' ? 443 : 80),
            path: urlObj.pathname + urlObj.search,
            method: options.method || 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${API_KEY}`,
                ...options.headers
            }
        };

        const req = protocol.request(reqOptions, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    const jsonData = JSON.parse(data);
                    resolve({ status: res.statusCode, data: jsonData });
                } catch (e) {
                    resolve({ status: res.statusCode, data: data });
                }
            });
        });

        req.on('error', reject);
        
        if (payload) {
            req.write(JSON.stringify(payload));
        }
        
        req.end();
    });
}

/**
 * Test full HTML response format
 */
async function testFullHtmlResponse() {
    console.log("\n=== Testing Markdown Extraction ===\n");
    
    // Testing ProductBot.ai
    const testUrl = "https://productbot.ai";
    
    // Test markdown extraction
    console.log(`Crawling ${testUrl} for markdown extraction`);
    console.log("-".repeat(50));
    
    let payload = {
        url: testUrl,
        javascript_enabled: true,  // Enable JS for better content
        screenshot_mode: null
    };
    
    // Add command line filter option
    const filterArg = process.argv[3]; // e.g., 'pruning' or 'bm25'
    
    if (filterArg === 'pruning') {
        // Test with pruning filter to reduce duplicate content
        payload.filter = 'pruning';
        payload.filter_options = { 
            threshold: 0.48,  // Default threshold
            min_words: 2      // Minimum words to keep a block
        };
        console.log("Using PRUNING filter to reduce duplicates");
    } else if (filterArg === 'bm25') {
        // Test with BM25 filter for specific content
        const query = process.argv[4] || 'product feedback automation';
        payload.filter = 'bm25';
        payload.filter_options = { 
            query: query,      // Search query
            threshold: 0.5     // Relevance threshold
        };
        console.log(`Using BM25 filter with query: "${query}"`);
    } else {
        console.log("No filter applied - showing all content with citations");
    }

    
    try {
        const response = await makeRequest(
            `${REMOTE_SERVER}/api/markdown`,
            { method: 'POST' },
            payload
        );
        
        console.log(`Status: ${response.status}`);
        
        if (response.status === 200) {
            const data = response.data;
            console.log("✅ Success");
            console.log(`Response contains ${Object.keys(data).length} fields`);
            
            // Check for markdown content
            if ('markdown' in data) {
                console.log(`\n✓ Markdown field found!`);
                console.log(`  Length: ${data.markdown.length} characters`);
                
                // Show first 1000 chars of markdown for debugging
                console.log(`\n============ MARKDOWN CONTENT (first 1000 chars) ============\n`);
                console.log(data.markdown.substring(0, 1000));
                console.log("\n...[truncated]...");
                console.log(`\n============ END SAMPLE ============\n`);
                
                // Show the full markdown for debugging
                console.log(`\n============ FULL MARKDOWN CONTENT ============\n`);
                console.log(data.markdown);
                console.log(`\n============ END MARKDOWN ============\n`);
            }
            
            // Check for HTML content too
            if ('html_content' in data) {
                console.log(`\n✓ html_content field also found!`);
                console.log(`  Length: ${data.html_content.length} characters`);
            }
            
            // Show references if present (these explain the citation numbers)
            if ('references' in data) {
                console.log(`\n============ REFERENCES (Citation URLs) ============\n`);
                console.log(data.references);
                console.log(`\n============ END REFERENCES ============\n`);
            }
            
            // Show URLs if present
            if ('markdown_url' in data) {
                console.log(`\n📄 Markdown saved at: ${data.markdown_url}`);
            }
            if ('json_url' in data) {
                console.log(`📊 JSON saved at: ${data.json_url}`);
            }
            if ('screenshot_url' in data) {
                console.log(`📸 Screenshot saved at: ${data.screenshot_url}`);
            }
            
            // Show links array if present
            if ('links' in data && Array.isArray(data.links)) {
                console.log(`\n============ LINKS ARRAY (first 5) ============\n`);
                data.links.slice(0, 5).forEach((link, i) => {
                    console.log(`Link ${i}:`, JSON.stringify(link, null, 2));
                });
                console.log(`\nTotal links: ${data.links.length}`);
            }
            
            // Show URLs array if present
            if ('urls' in data && Array.isArray(data.urls)) {
                console.log(`\n============ URLS ARRAY (first 10) ============\n`);
                data.urls.slice(0, 10).forEach((url, i) => {
                    console.log(`${i}: ${url}`);
                });
                console.log(`\nTotal URLs: ${data.urls.length}`);
            }
            
            // List all fields returned
            console.log("\nAll fields in response:");
            Object.keys(data).forEach(key => {
                const value = data[key];
                if (typeof value === 'string' && value.length > 100) {
                    console.log(`  - ${key}: [string, ${value.length} chars]`);
                } else if (typeof value === 'object') {
                    console.log(`  - ${key}: [object]`);
                } else {
                    console.log(`  - ${key}: ${JSON.stringify(value)}`);
                }
            });
        } else {
            console.log(`❌ Error: ${response.status}`);
            console.log(response.data);
        }
        
    } catch (error) {
        console.log(`❌ Exception: ${error.message}`);
    }
    

}

/**
 * Main function
 */
async function main() {
    console.log("=".repeat(60));
    console.log("Simple Gnosis Wraith Markdown Test");
    console.log(`Environment: ${serverArg.toUpperCase()}`);
    console.log(`Server: ${REMOTE_SERVER}`);
    console.log(`API Key: ${API_KEY.substring(0, 10)}...`);
    console.log("=".repeat(60));
    
    await testFullHtmlResponse();
    
    console.log("\n" + "=".repeat(60));
    console.log("Test Complete!");
    console.log("=".repeat(60));

}

// Run the test
main().catch(console.error);

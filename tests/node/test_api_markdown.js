#!/usr/bin/env node
/**
 * Test script for Gnosis Wraith /api/markdown endpoint
 * Tests both single URL and batch URL processing
 * Node.js equivalent of test_api_markdown.py
 */

const https = require('https');
const http = require('http');

// Configuration
const REMOTE_SERVER = "https://wraith.nuts.services";
// const REMOTE_SERVER = "http://localhost:5678";
const API_KEY = "Ij8zhKKL_iKUcumU5oQKnpsECg9qvYTdXlH2IGth7k_ewGBdy6se_g"; // Your API key
// const API_KEY = "pfr3lKBeacc4W5ZiOA6jFYRFvywhd4_MoHg8MkFmeesSvdmPMNheA";

// Test URLs
const TEST_URLS = [
    "https://example.com",
    "https://www.wikipedia.org",
    "https://news.ycombinator.com",
    "https://www.python.org",
    "https://docs.python.org/3/"
];

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
 * Test single URL markdown extraction (backward compatible)
 */
async function testSingleUrlMarkdown() {
    console.log("\n=== Testing Single URL Markdown ===");
    
    const payload = {
        url: TEST_URLS[0],
        javascript_enabled: true,
        screenshot_mode: null // No screenshot for speed
    };
    
    try {
        const startTime = Date.now();
        const response = await makeRequest(
            `${REMOTE_SERVER}/api/markdown`,
            { method: 'POST' },
            payload
        );
        const elapsed = (Date.now() - startTime) / 1000;
        
        console.log(`URL: ${TEST_URLS[0]}`);
        console.log(`Status: ${response.status}`);
        console.log(`Time: ${elapsed.toFixed(2)}s`);
        
        if (response.status === 200) {
            const data = response.data;
            console.log("✅ Success");
            console.log(`Response keys: ${Object.keys(data).join(', ')}`);
            
            // Check various response fields
            if ('success' in data) {
                console.log(`Success: ${data.success}`);
            }
            if ('url' in data) {
                console.log(`URL: ${data.url}`);
            }
            if ('markdown_url' in data) {
                console.log(`Markdown URL: ${data.markdown_url}`);
            }
            if ('json_url' in data) {
                console.log(`JSON URL: ${data.json_url}`);
            }
            if ('stats' in data) {
                console.log(`Stats:`, data.stats);
            }
        } else {
            console.log(`❌ Error:`, response.data);
        }
        
        return response.status === 200;
        
    } catch (error) {
        console.log(`❌ Exception: ${error.message}`);
        return false;
    }
}

/**
 * Test synchronous batch processing
 */
async function testBatchSync() {
    console.log("\n=== Testing Batch Markdown (Sync) ===");
    
    const payload = {
        urls: TEST_URLS.slice(0, 3), // Test with 3 URLs
        async: false, // Wait for completion
        javascript_enabled: true,
        screenshot_mode: null
    };
    
    try {
        const startTime = Date.now();
        const response = await makeRequest(
            `${REMOTE_SERVER}/api/markdown`,
            { method: 'POST' },
            payload
        );
        const elapsed = (Date.now() - startTime) / 1000;
        
        console.log(`URLs: ${payload.urls.length} URLs`);
        console.log(`Status: ${response.status}`);
        console.log(`Time: ${elapsed.toFixed(2)}s`);
        
        if (response.status === 200) {
            const data = response.data;
            console.log("✅ Success");
            console.log(`Mode: ${data.mode || 'N/A'}`);
            console.log(`Job ID: ${data.job_id || 'N/A'}`);
            
            if ('results' in data) {
                console.log(`\nResults: ${data.results.length} items`);
                data.results.slice(0, 2).forEach((result, i) => {
                    console.log(`\nResult ${i + 1}:`);
                    console.log(`  URL: ${result.url || 'N/A'}`);
                    console.log(`  Status: ${result.status || 'N/A'}`);
                    console.log(`  Markdown URL: ${result.markdown_url || 'N/A'}`);
                    console.log(`  JSON URL: ${result.json_url || 'N/A'}`);
                });
            }
        } else {
            console.log(`❌ Error:`, response.data);
        }
        
        return response.status === 200;
        
    } catch (error) {
        console.log(`❌ Exception: ${error.message}`);
        return false;
    }
}

/**
 * Test asynchronous batch processing
 */
async function testBatchAsync() {
    console.log("\n=== Testing Batch Markdown (Async) ===");
    
    const payload = {
        urls: TEST_URLS.slice(0, 4), // Test with 4 URLs
        async: true, // Don't wait for completion
        javascript_enabled: false, // Faster without JS
        screenshot_mode: null
    };
    
    try {
        const startTime = Date.now();
        const response = await makeRequest(
            `${REMOTE_SERVER}/api/markdown`,
            { method: 'POST' },
            payload
        );
        const elapsed = (Date.now() - startTime) / 1000;
        
        console.log(`URLs: ${payload.urls.length} URLs`);
        console.log(`Status: ${response.status}`);
        console.log(`Time: ${elapsed.toFixed(2)}s (should be fast for async)`);
        
        if ([200, 202].includes(response.status)) { // 202 Accepted for async
            const data = response.data;
            console.log(`✅ Success (Status: ${response.status})`);
            console.log(`Mode: ${data.mode || 'N/A'}`);
            console.log(`Job ID: ${data.job_id || 'N/A'}`);
            console.log(`Status URL: ${data.status_url || 'N/A'}`);
            
            if ('results' in data) {
                console.log(`\nPredicted URLs: ${data.results.length} items`);
                data.results.slice(0, 2).forEach((result, i) => {
                    console.log(`  ${i + 1}. ${result.url || 'N/A'} - Status: ${result.status || 'N/A'}`);
                });
            }
        } else {
            console.log(`❌ Error:`, response.data);
        }
        
        return [200, 202].includes(response.status);
        
    } catch (error) {
        console.log(`❌ Exception: ${error.message}`);
        return false;
    }
}

/**
 * Test batch processing with collation
 */
async function testBatchWithCollation() {
    console.log("\n=== Testing Batch with Collation ===");
    
    const payload = {
        urls: [
            "https://docs.python.org/3/tutorial/introduction.html",
            "https://docs.python.org/3/tutorial/controlflow.html"
        ],
        async: false, // Wait for completion to get collated result
        collate: true,
        collate_options: {
            title: "Python Tutorial Collection",
            add_toc: true,
            add_source_headers: true
        },
        javascript_enabled: false
    };
    
    try {
        const startTime = Date.now();
        const response = await makeRequest(
            `${REMOTE_SERVER}/api/markdown`,
            { method: 'POST' },
            payload
        );
        const elapsed = (Date.now() - startTime) / 1000;
        
        console.log(`URLs: ${payload.urls.length} URLs`);
        console.log(`Status: ${response.status}`);
        console.log(`Time: ${elapsed.toFixed(2)}s`);
        
        if (response.status === 200) {
            const data = response.data;
            console.log("✅ Success");
            
            if ('collated_url' in data) {
                console.log(`Collated file URL: ${data.collated_url}`);
            }
            
            if ('results' in data) {
                console.log(`Individual results: ${data.results.length}`);
            }
        } else {
            console.log(`❌ Error:`, response.data);
        }
        
        return response.status === 200;
        
    } catch (error) {
        console.log(`❌ Exception: ${error.message}`);
        return false;
    }
}

/**
 * Test markdown extraction with content filters
 */
async function testWithFilters() {
    console.log("\n=== Testing with Content Filters ===");
    
    try {
        // Test with pruning filter
        console.log("Testing Pruning Filter...");
        let payload = {
            url: "https://en.wikipedia.org/wiki/Python_(programming_language)",
            filter: "pruning",
            filter_options: {
                threshold: 0.5,
                min_words: 3
            },
            javascript_enabled: false
        };
        
        let startTime = Date.now();
        let response = await makeRequest(
            `${REMOTE_SERVER}/api/markdown`,
            { method: 'POST' },
            payload
        );
        let elapsed = (Date.now() - startTime) / 1000;
        
        if (response.status === 200) {
            const data = response.data;
            console.log(`  ✅ Pruning filter success (Time: ${elapsed.toFixed(2)}s)`);
            if ('stats' in data) {
                console.log(`  Stats:`, data.stats);
            }
        } else {
            console.log(`  ❌ Pruning filter failed: Status ${response.status}`);
        }
        
        // Test with BM25 filter
        console.log("\nTesting BM25 Filter...");
        payload = {
            url: "https://en.wikipedia.org/wiki/Python_(programming_language)",
            filter: "bm25",
            filter_options: {
                query: "python programming syntax",
                threshold: 0.4
            },
            javascript_enabled: false
        };
        
        startTime = Date.now();
        response = await makeRequest(
            `${REMOTE_SERVER}/api/markdown`,
            { method: 'POST' },
            payload
        );
        elapsed = (Date.now() - startTime) / 1000;
        
        if (response.status === 200) {
            const data = response.data;
            console.log(`  ✅ BM25 filter success (Time: ${elapsed.toFixed(2)}s)`);
            if ('stats' in data) {
                console.log(`  Stats:`, data.stats);
            }
        } else {
            console.log(`  ❌ BM25 filter failed: Status ${response.status}`);
        }
        
        return true;
        
    } catch (error) {
        console.log(`❌ Exception: ${error.message}`);
        return false;
    }
}

/**
 * Test error handling with invalid URLs
 */
async function testErrorHandling() {
    console.log("\n=== Testing Error Handling ===");
    
    try {
        // Test invalid URL
        console.log("Testing invalid URL...");
        let response = await makeRequest(
            `${REMOTE_SERVER}/api/markdown`,
            { method: 'POST' },
            { url: "not-a-valid-url" }
        );
        console.log(`  Status: ${response.status}`);
        console.log(`  Response:`, response.data);
        
        // Test missing URL
        console.log("\nTesting missing URL...");
        response = await makeRequest(
            `${REMOTE_SERVER}/api/markdown`,
            { method: 'POST' },
            {}
        );
        console.log(`  Status: ${response.status}`);
        console.log(`  Response:`, response.data);
        
        // Test too many URLs
        console.log("\nTesting too many URLs...");
        response = await makeRequest(
            `${REMOTE_SERVER}/api/markdown`,
            { method: 'POST' },
            { urls: Array(51).fill("https://example.com") } // Over 50 limit
        );
        console.log(`  Status: ${response.status}`);
        console.log(`  Response:`, response.data);
        
        return true;
        
    } catch (error) {
        console.log(`❌ Exception: ${error.message}`);
        return false;
    }
}

/**
 * Test minimal response format
 */
async function testMinimalResponseFormat() {
    console.log("\n=== Testing Minimal Response Format ===");
    
    const payload = {
        url: "https://example.com",
        javascript_enabled: false, // Faster without JS
        screenshot_mode: null,
        response_format: "minimal" // Request minimal format
    };
    
    try {
        const startTime = Date.now();
        const response = await makeRequest(
            `${REMOTE_SERVER}/api/markdown`,
            { method: 'POST' },
            payload
        );
        const elapsed = (Date.now() - startTime) / 1000;
        
        console.log(`URL: ${payload.url}`);
        console.log(`Response Format: ${payload.response_format}`);
        console.log(`Status: ${response.status}`);
        console.log(`Time: ${elapsed.toFixed(2)}s`);
        
        if (response.status === 200) {
            const data = response.data;
            console.log("✅ Success");
            console.log(`Response keys: ${Object.keys(data).join(', ')}`);
            
            // Output the content
            console.log("\n--- CONTENT OUTPUT ---");
            if ('content' in data) {
                console.log("Content field:");
                console.log(data.content ? data.content.substring(0, 500) + '...' : 'No content');
            }
            if ('markdown' in data) {
                console.log("\nMarkdown field:");
                console.log(data.markdown ? data.markdown.substring(0, 500) + '...' : 'No markdown');
            }
            console.log("--- END CONTENT ---\n");
            
            // Check what fields are included in minimal format
            console.log("\nFields included:");
            const fields = ['success', 'url', 'title', 'content', 'markdown', 'markdown_url', 'json_url', 'stats', 'html_content', 'extracted_text'];
            fields.forEach(field => {
                if (field in data) {
                    console.log(`  ✓ ${field}: ${typeof data[field] === 'string' && data[field].length > 50 ? data[field].substring(0, 50) + '...' : JSON.stringify(data[field])}`);
                } else {
                    console.log(`  ✗ ${field}: not included`);
                }
            });
            
        } else {
            console.log(`❌ Error:`, response.data);
        }
        
        return response.status === 200;
        
    } catch (error) {
        console.log(`❌ Exception: ${error.message}`);
        return false;
    }
}

/**
 * Main test runner
 */
async function main() {
    console.log("=".repeat(60));
    console.log("Gnosis Wraith /api/markdown Endpoint Tests");
    console.log(`Server: ${REMOTE_SERVER}`);
    console.log(`API Key: ${API_KEY.substring(0, 10)}...`);
    console.log("=".repeat(60));
    
    // Run tests
    const tests = [
        { name: "Minimal Response Format", func: testMinimalResponseFormat }, // Run this first
        { name: "Single URL", func: testSingleUrlMarkdown },
        { name: "Batch Sync", func: testBatchSync },
        { name: "Batch Async", func: testBatchAsync },
        { name: "Batch with Collation", func: testBatchWithCollation },
        { name: "Content Filters", func: testWithFilters },
        { name: "Error Handling", func: testErrorHandling }
    ];

    
    const results = [];
    for (const test of tests) {
        try {
            const result = await test.func();
            results.push({ name: test.name, passed: result });
        } catch (error) {
            console.log(`\n❌ Test '${test.name}' crashed: ${error.message}`);
            results.push({ name: test.name, passed: false });
        }
    }
    
    // Summary
    console.log("\n" + "=".repeat(60));
    console.log("Test Summary");
    console.log("=".repeat(60));
    
    const passed = results.filter(r => r.passed).length;
    const total = results.length;
    
    results.forEach(result => {
        const status = result.passed ? "✅ PASSED" : "❌ FAILED";
        console.log(`${result.name}: ${status}`);
    });
    
    console.log(`\nTotal: ${passed}/${total} tests passed`);
    
    console.log("\n📝 Implementation Notes:");
    console.log("- The /api/markdown endpoint supports both single and batch URLs");
    console.log("- Batch mode is triggered by providing 'urls' array instead of 'url'");
    console.log("- Maximum 50 URLs per batch");
    console.log("- Supports async processing with webhooks");
    console.log("- Supports content filters (pruning, BM25)");
    console.log("- Supports collation to merge results");
}

// Run the tests
main().catch(console.error);
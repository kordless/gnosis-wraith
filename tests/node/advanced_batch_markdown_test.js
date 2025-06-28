#!/usr/bin/env node
/**
 * Advanced Batch Markdown API Test for Gnosis Wraith
 * 
 * Features:
 * - Batch processing multiple URLs in a single request
 * - Support for both synchronous and asynchronous batch modes
 * - Advanced filtering options (pruning, BM25, custom filters)
 * - Progress tracking and status polling for async jobs
 * - Error handling and retry logic
 * - CSV/JSON input support for URL lists
 * - Export results to various formats
 * 
 * Usage:
 *   node advanced_batch_markdown_test.js                           # Interactive mode
 *   node advanced_batch_markdown_test.js --urls url1,url2,url3    # Direct URLs
 *   node advanced_batch_markdown_test.js --file urls.txt          # From file
 *   node advanced_batch_markdown_test.js --site example.com       # Crawl entire site
 *   node advanced_batch_markdown_test.js --async                  # Async mode
 *   node advanced_batch_markdown_test.js --filter bm25 --query "search terms"
 */

const https = require('https');
const http = require('http');
const fs = require('fs').promises;
const path = require('path');
const readline = require('readline');

// Configuration
const SERVERS = {
    local: "http://localhost:5678",
    staging: "https://gnosis-wraith-staging-949870462453.us-central1.run.app",
    production: "https://wraith.nuts.services"
};

const API_KEYS = {
    local: "5YzHvCGETYkn3KzSV1gtugE70EAugPAXJvcV5MMbPui0H7YfN2sHg",
    staging: "Ij8zhKKL_iKUcumU5oQKnpsECg9qvYTdXlH2IGth7k_ewGBdy6se_g",
    production: "Ij8zhKKL_iKUcumU5oQKnpsECg9qvYTdXlH2IGth7k_ewGBdy6se_g"
};

// Parse command line arguments
function parseArgs() {
    const args = {
        server: 'staging',
        urls: [],
        file: null,
        site: null,
        async: false,
        collate: true,
        filter: null,
        filterOptions: {},
        output: 'console',
        outputFile: null,
        maxUrls: 50,
        javascript: true,
        screenshot: false,
        wait: 5000, // ms to wait between status checks
        maxWait: 300000, // 5 minutes max wait for async jobs
    };

    for (let i = 2; i < process.argv.length; i++) {
        const arg = process.argv[i];
        
        switch(arg) {
            case '--server':
                args.server = process.argv[++i] || 'staging';
                break;
            case '--urls':
                args.urls = (process.argv[++i] || '').split(',').filter(u => u);
                break;
            case '--file':
                args.file = process.argv[++i];
                break;
            case '--site':
                args.site = process.argv[++i];
                break;
            case '--async':
                args.async = true;
                break;
            case '--sync':
                args.async = false;
                break;
            case '--no-collate':
                args.collate = false;
                break;
            case '--filter':
                args.filter = process.argv[++i];
                break;
            case '--query':
                args.filterOptions.query = process.argv[++i];
                break;
            case '--threshold':
                args.filterOptions.threshold = parseFloat(process.argv[++i]);
                break;
            case '--output':
                args.output = process.argv[++i]; // console, json, csv, markdown
                break;
            case '--output-file':
                args.outputFile = process.argv[++i];
                break;
            case '--max-urls':
                args.maxUrls = parseInt(process.argv[++i]) || 50;
                break;
            case '--no-js':
                args.javascript = false;
                break;
            case '--screenshot':
                args.screenshot = true;
                break;
            case '--help':
                printHelp();
                process.exit(0);
        }
    }

    return args;
}

function printHelp() {
    console.log(`
Advanced Batch Markdown API Test for Gnosis Wraith

Usage:
  node advanced_batch_markdown_test.js [options]

Options:
  --server <name>        Server to use: local, staging, production (default: staging)
  --urls <url1,url2>     Comma-separated list of URLs to process
  --file <path>          Read URLs from file (one per line)
  --site <url>           Crawl site and batch process all found URLs
  --async                Use async batch mode (default: sync)
  --sync                 Use sync batch mode (default)
  --no-collate           Don't collate results into single document
  --filter <type>        Filter type: pruning, bm25
  --query <text>         Query for BM25 filter
  --threshold <float>    Threshold for filters (0.0-1.0)
  --output <format>      Output format: console, json, csv, markdown
  --output-file <path>   Save output to file
  --max-urls <n>         Maximum URLs to process (default: 50)
  --no-js                Disable JavaScript rendering
  --screenshot           Take screenshots
  --help                 Show this help

Examples:
  # Batch process multiple URLs
  node advanced_batch_markdown_test.js --urls "https://example.com,https://example.org"
  
  # Crawl site and process all pages with BM25 filter
  node advanced_batch_markdown_test.js --site https://example.com --filter bm25 --query "important topic"
  
  # Async batch from file with JSON output
  node advanced_batch_markdown_test.js --file urls.txt --async --output json --output-file results.json
`);
}

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
                'Authorization': `Bearer ${options.apiKey}`,
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
 * Read URLs from file
 */
async function readUrlsFromFile(filePath) {
    try {
        const content = await fs.readFile(filePath, 'utf8');
        return content.split('\n')
            .map(line => line.trim())
            .filter(line => line && !line.startsWith('#'));
    } catch (error) {
        throw new Error(`Failed to read file: ${error.message}`);
    }
}

/**
 * Crawl site to get all URLs
 */
async function crawlSiteForUrls(siteUrl, server, apiKey) {
    console.log(`\n🔍 Crawling ${siteUrl} to discover URLs...`);
    
    const response = await makeRequest(
        `${server}/api/markdown`,
        { method: 'POST', apiKey },
        {
            url: siteUrl,
            javascript_enabled: true
        }
    );
    
    if (response.status !== 200) {
        throw new Error(`Failed to crawl site: ${response.data.error || 'Unknown error'}`);
    }
    
    const urls = response.data.urls || [];
    const siteHost = new URL(siteUrl).hostname;
    
    // Filter to same domain
    const sameDomainUrls = urls.filter(url => {
        try {
            return new URL(url).hostname === siteHost;
        } catch (e) {
            return false;
        }
    });
    
    console.log(`✅ Found ${sameDomainUrls.length} same-domain URLs`);
    return sameDomainUrls;
}

/**
 * Batch process URLs
 */
async function batchProcessUrls(urls, options) {
    const { server, apiKey, async, collate, filter, filterOptions, javascript, screenshot } = options;
    
    console.log(`\n📋 Batch processing ${urls.length} URLs...`);
    console.log(`Mode: ${async ? 'Asynchronous' : 'Synchronous'}`);
    console.log(`Collate: ${collate ? 'Yes' : 'No'}`);
    if (filter) {
        console.log(`Filter: ${filter} ${JSON.stringify(filterOptions)}`);
    }
    
    const payload = {
        urls: urls,
        javascript_enabled: javascript,
        async: async,
        collate: collate,
        screenshot_mode: screenshot ? 'viewport' : null
    };
    
    // Add filter options if specified
    if (filter) {
        payload.filter = filter;
        payload.filter_options = filterOptions;
    }
    
    const response = await makeRequest(
        `${server}/api/markdown`,
        { method: 'POST', apiKey },
        payload
    );
    
    return response;
}

/**
 * Poll async job status
 */
async function pollJobStatus(statusUrl, apiKey, maxWait = 300000, interval = 5000) {
    const startTime = Date.now();
    
    console.log(`\n⏳ Polling job status...`);
    
    while (Date.now() - startTime < maxWait) {
        try {
            const response = await makeRequest(
                statusUrl,
                { method: 'GET', apiKey },
                null
            );
            
            if (response.status === 200) {
                const { status, progress, completed, total } = response.data;
                
                console.log(`Status: ${status} | Progress: ${completed}/${total} (${progress}%)`);
                
                if (status === 'completed' || status === 'failed') {
                    return response.data;
                }
            }
        } catch (error) {
            console.error(`Error polling status: ${error.message}`);
        }
        
        await new Promise(resolve => setTimeout(resolve, interval));
    }
    
    throw new Error('Job timed out');
}

/**
 * Format and output results
 */
async function outputResults(results, format, outputFile) {
    let output = '';
    
    switch (format) {
        case 'json':
            output = JSON.stringify(results, null, 2);
            break;
            
        case 'csv':
            // Create CSV with URL, success, markdown length, error
            output = 'URL,Success,Markdown Length,Error,Markdown URL,JSON URL\n';
            const items = results.results || results.items || [results];
            items.forEach(item => {
                const url = item.url || item.original_url || 'unknown';
                const success = item.success !== undefined ? item.success : true;
                const markdownLength = item.markdown ? item.markdown.length : 0;
                const error = item.error || '';
                const markdownUrl = item.markdown_url || '';
                const jsonUrl = item.json_url || '';
                
                output += `"${url}",${success},${markdownLength},"${error}","${markdownUrl}","${jsonUrl}"\n`;
            });
            break;
            
        case 'markdown':
            output = '# Batch Processing Results\n\n';
            output += `**Total URLs processed:** ${results.total || 1}\n`;
            output += `**Successful:** ${results.succeeded || 1}\n`;
            output += `**Failed:** ${results.failed || 0}\n\n`;
            
            if (results.collated_url) {
                output += `**Collated results:** ${results.collated_url}\n\n`;
            }
            
            output += '## Individual Results\n\n';
            const resultItems = results.results || results.items || [results];
            resultItems.forEach((item, i) => {
                output += `### ${i + 1}. ${item.url || item.original_url || 'Result'}\n`;
                output += `- **Success:** ${item.success !== undefined ? item.success : 'Yes'}\n`;
                if (item.markdown_url) output += `- **Markdown:** ${item.markdown_url}\n`;
                if (item.json_url) output += `- **JSON:** ${item.json_url}\n`;
                if (item.error) output += `- **Error:** ${item.error}\n`;
                output += '\n';
            });
            break;
            
        default: // console
            console.log('\n📊 Results Summary:');
            console.log(`Total: ${results.total || 1}`);
            console.log(`Succeeded: ${results.succeeded || 1}`);
            console.log(`Failed: ${results.failed || 0}`);
            
            if (results.collated_url) {
                console.log(`\n📄 Collated results: ${results.collated_url}`);
            }
            
            // Show sample results
            const sampleResults = results.results || results.items || [results];
            if (sampleResults.length > 0) {
                console.log('\n📋 Sample Results (first 5):');
                sampleResults.slice(0, 5).forEach((item, i) => {
                    console.log(`\n${i + 1}. ${item.url || item.original_url || 'Result'}`);
                    console.log(`   Success: ${item.success !== undefined ? item.success : 'Yes'}`);
                    if (item.markdown_url) console.log(`   Markdown: ${item.markdown_url}`);
                    if (item.json_url) console.log(`   JSON: ${item.json_url}`);
                    if (item.error) console.log(`   Error: ${item.error}`);
                });
            }
            return;
    }
    
    // Save to file if specified
    if (outputFile) {
        await fs.writeFile(outputFile, output, 'utf8');
        console.log(`\n💾 Results saved to: ${outputFile}`);
    } else if (format !== 'console') {
        console.log(output);
    }
}

/**
 * Interactive mode
 */
async function interactiveMode(args) {
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
    });
    
    const question = (prompt) => new Promise(resolve => rl.question(prompt, resolve));
    
    console.log('\n🎯 Interactive Batch Processing Mode\n');
    
    // Get URLs
    if (args.urls.length === 0) {
        const urlInput = await question('Enter URLs (comma-separated) or press Enter to input one by one: ');
        
        if (urlInput.trim()) {
            args.urls = urlInput.split(',').map(u => u.trim()).filter(u => u);
        } else {
            console.log('Enter URLs one per line (empty line to finish):');
            let url;
            while ((url = await question('URL: ')) !== '') {
                args.urls.push(url.trim());
            }
        }
    }
    
    // Get filter preference
    if (!args.filter) {
        const filterChoice = await question('\nApply filter? (none/pruning/bm25) [none]: ');
        if (filterChoice && filterChoice !== 'none') {
            args.filter = filterChoice;
            
            if (filterChoice === 'bm25') {
                args.filterOptions.query = await question('Enter search query for BM25: ');
            }
            
            const threshold = await question('Enter threshold (0.0-1.0) [0.5]: ');
            args.filterOptions.threshold = parseFloat(threshold) || 0.5;
        }
    }
    
    // Get processing mode
    const asyncChoice = await question('\nUse async mode? (y/n) [n]: ');
    args.async = asyncChoice.toLowerCase() === 'y';
    
    rl.close();
    return args;
}

/**
 * Main function
 */
async function main() {
    const args = parseArgs();
    const server = SERVERS[args.server] || SERVERS.staging;
    const apiKey = API_KEYS[args.server] || API_KEYS.staging;
    
    console.log("=".repeat(60));
    console.log("Advanced Batch Markdown API Test");
    console.log(`Server: ${args.server.toUpperCase()} (${server})`);
    console.log("=".repeat(60));
    
    try {
        // Collect URLs based on input method
        let urls = [...args.urls];
        
        // Read from file
        if (args.file) {
            const fileUrls = await readUrlsFromFile(args.file);
            urls.push(...fileUrls);
            console.log(`📄 Loaded ${fileUrls.length} URLs from ${args.file}`);
        }
        
        // Crawl site
        if (args.site) {
            const siteUrls = await crawlSiteForUrls(args.site, server, apiKey);
            urls.push(...siteUrls);
        }
        
        // Interactive mode if no URLs provided
        if (urls.length === 0) {
            const interactiveArgs = await interactiveMode(args);
            urls = interactiveArgs.urls;
            Object.assign(args, interactiveArgs);
        }
        
        // Validate URLs
        if (urls.length === 0) {
            console.error('❌ No URLs to process');
            process.exit(1);
        }
        
        // Limit URLs
        if (urls.length > args.maxUrls) {
            console.log(`⚠️ Limiting to first ${args.maxUrls} URLs`);
            urls = urls.slice(0, args.maxUrls);
        }
        
        // Process URLs
        console.log(`\n🎯 Processing ${urls.length} URLs`);
        
        const response = await batchProcessUrls(urls, {
            server,
            apiKey,
            async: args.async,
            collate: args.collate,
            filter: args.filter,
            filterOptions: args.filterOptions,
            javascript: args.javascript,
            screenshot: args.screenshot
        });
        
        let results;
        
        if (response.status === 202) {
            // Async mode - poll for results
            console.log(`\n✅ Batch job started`);
            console.log(`Job ID: ${response.data.job_id}`);
            console.log(`Status URL: ${response.data.status_url}`);
            
            if (response.data.status_url) {
                results = await pollJobStatus(
                    response.data.status_url,
                    apiKey,
                    args.maxWait,
                    args.wait
                );
            } else {
                results = response.data;
            }
        } else if (response.status === 200) {
            // Sync mode - results ready
            results = response.data;
            console.log('\n✅ Batch processing completed');
        } else {
            throw new Error(`Unexpected response: ${response.status} - ${JSON.stringify(response.data)}`);
        }
        
        // Output results
        await outputResults(results, args.output, args.outputFile);
        
    } catch (error) {
        console.error(`\n❌ Error: ${error.message}`);
        if (error.stack && args.server === 'local') {
            console.error(error.stack);
        }
        process.exit(1);
    }
}

// Run the script
if (require.main === module) {
    main().catch(console.error);
}

// Export for use as module
module.exports = {
    makeRequest,
    batchProcessUrls,
    pollJobStatus,
    crawlSiteForUrls
};

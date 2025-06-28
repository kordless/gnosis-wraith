#!/usr/bin/env node

/**
 * Test Batch URL Generation
 * 
 * This test verifies that batch crawling returns proper full URLs
 * that can be accessed, not just relative paths.
 */

// Load environment variables - first try local .env, then fall back to root
const path = require('path');
require('dotenv').config(); // This loads from tests/node/.env if it exists

const fetch = require('node-fetch');
const fs = require('fs').promises;



// Configuration
const BASE_URL = process.env.GNOSIS_URL || 'https://wraith.nuts.services';

const API_TOKEN = process.env.GNOSIS_API_TOKEN || '';

// Test configuration
const TEST_URLS = [
    'https://example.com',
    'https://google.com'
];

// Helper function to wait for async job completion
async function waitForJobCompletion(jobId, maxWaitTime = 30000) {
    const pollInterval = 1000; // 1 second
    const startTime = Date.now();
    
    console.log(`\nWaiting for job ${jobId} to complete...`);
    
    while (Date.now() - startTime < maxWaitTime) {
        try {
            const response = await fetch(`${BASE_URL}/api/jobs/${jobId}`, {
                headers: {
                    'Authorization': `Bearer ${API_TOKEN}`,
                    'X-API-Token': API_TOKEN
                }
            });
            
            if (!response.ok) {
                console.log(`Job status check failed: ${response.status}`);
                return null;
            }
            
            const jobStatus = await response.json();
            console.log(`Job status: ${jobStatus.status} (${jobStatus.completed}/${jobStatus.total})`);
            
            if (jobStatus.status === 'completed' || jobStatus.status === 'failed') {
                return jobStatus;
            }
            
            // Wait before next poll
            await new Promise(resolve => setTimeout(resolve, pollInterval));
            
        } catch (error) {
            console.error('Error checking job status:', error);
            return null;
        }
    }
    
    console.log('Job timed out');
    return null;
}

async function testBatchMarkdown() {

    console.log('='.repeat(60));
    console.log('BATCH URL GENERATION TEST');
    console.log('='.repeat(60));
    console.log(`Base URL: ${BASE_URL}`);
    console.log(`API Token: ${API_TOKEN ? 'Set' : 'Not set'}`);
    console.log('');

    try {
        // Test 1: Single URL (backward compatibility)
        console.log('TEST 1: Single URL Mode');
        console.log('-'.repeat(40));
        
        const singleResponse = await fetch(`${BASE_URL}/api/markdown`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${API_TOKEN}`
            },
            body: JSON.stringify({
                url: TEST_URLS[0],
                javascript_enabled: false,
                screenshot_mode: null
            })
        });

        const singleResult = await singleResponse.json();
        console.log('Single URL Response:');
        console.log(JSON.stringify(singleResult, null, 2));
        
        // Check URL formats
        if (singleResult.success) {
            console.log('\nURL Analysis:');
            console.log(`- Markdown URL: ${singleResult.markdown_url}`);
            console.log(`  Is full URL: ${singleResult.markdown_url?.startsWith('http')}`);
            console.log(`- JSON URL: ${singleResult.json_url}`);
            console.log(`  Is full URL: ${singleResult.json_url?.startsWith('http')}`);
        }
        
        console.log('\n' + '='.repeat(60) + '\n');

        // Test 2: Batch URLs (async mode)
        console.log('TEST 2: Batch URL Mode (Async)');
        console.log('-'.repeat(40));
        
        const batchResponse = await fetch(`${BASE_URL}/api/markdown`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${API_TOKEN}`
            },
            body: JSON.stringify({
                urls: TEST_URLS,
                javascript_enabled: false,
                async: true,
                collate: true
            })
        });

        const batchResult = await batchResponse.json();
        console.log('Batch Response:');
        console.log(JSON.stringify(batchResult, null, 2));
        
        // Analyze predicted URLs
        if (batchResult.success && batchResult.results) {
            console.log('\nPredicted URL Analysis:');
            batchResult.results.forEach((result, index) => {
                console.log(`\nURL ${index + 1}: ${result.url}`);
                console.log(`- Markdown URL: ${result.markdown_url}`);
                console.log(`  Is full URL: ${result.markdown_url?.startsWith('http')}`);
                console.log(`- JSON URL: ${result.json_url}`);
                console.log(`  Is full URL: ${result.json_url?.startsWith('http')}`);
            });
            
            if (batchResult.collated_url) {
                console.log(`\nCollated URL: ${batchResult.collated_url}`);
                console.log(`Is full URL: ${batchResult.collated_url?.startsWith('http')}`);
            }
            
            // Wait for async job to complete
            if (batchResult.job_id) {
                const completedJob = await waitForJobCompletion(batchResult.job_id);
                
                if (completedJob && completedJob.results) {
                    console.log('\n\nCompleted Job Results:');
                    console.log('='.repeat(40));
                    
                    // Fetch actual content from the first result
                    const firstResult = completedJob.results[0];
                    if (firstResult && firstResult.markdown_url) {
                        console.log(`\nFetching completed markdown from: ${firstResult.markdown_url}`);
                        
                        try {
                            const contentResponse = await fetch(firstResult.markdown_url, {
                                headers: {
                                    'Authorization': `Bearer ${API_TOKEN}`,
                                    'X-API-Token': API_TOKEN
                                }
                            });
                            
                            if (contentResponse.ok) {
                                const content = await contentResponse.text();
                                console.log('\nAsync Job Markdown Content:');
                                console.log('-'.repeat(40));
                                console.log(content);
                                console.log('-'.repeat(40));
                            } else {
                                console.log(`Failed to fetch content: ${contentResponse.status}`);
                            }
                        } catch (error) {
                            console.log(`Fetch error: ${error.message}`);
                        }
                    }
                    
                    // Also try the collated URL if it exists
                    if (completedJob.collated_url) {
                        console.log(`\nFetching collated content from: ${completedJob.collated_url}`);
                        
                        try {
                            const collatedResponse = await fetch(completedJob.collated_url, {
                                headers: {
                                    'Authorization': `Bearer ${API_TOKEN}`,
                                    'X-API-Token': API_TOKEN
                                }
                            });
                            
                            if (collatedResponse.ok) {
                                const content = await collatedResponse.text();
                                console.log('\nCollated Markdown Content:');
                                console.log('-'.repeat(40));
                                console.log(content.substring(0, 500) + '...');  // Preview
                                console.log('-'.repeat(40));
                            }
                        } catch (error) {
                            console.log(`Fetch error: ${error.message}`);
                        }
                    }
                }
            }
        }


        console.log('\n' + '='.repeat(60) + '\n');

        // Test 3: Batch URLs (sync mode)
        console.log('TEST 3: Batch URL Mode (Sync)');
        console.log('-'.repeat(40));
        
        const syncResponse = await fetch(`${BASE_URL}/api/markdown`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${API_TOKEN}`
            },
            body: JSON.stringify({
                urls: [TEST_URLS[0]], // Just one URL for faster sync test
                javascript_enabled: false,
                async: false
            })
        });

        const syncResult = await syncResponse.json();
        console.log('Sync Batch Response:');
        console.log(JSON.stringify(syncResult, null, 2));
        
        // Wait for sync results to complete and fetch the content
        if (syncResult.success && syncResult.results && syncResult.results[0]) {
            const result = syncResult.results[0];
            
            console.log('\nAttempting to fetch result URLs with authentication:');
            
            // Try markdown URL
            if (result.markdown_url) {
                console.log(`\nFetching markdown from: ${result.markdown_url}`);
                
                try {
                    // Fetch with authentication headers
                    const fetchResponse = await fetch(result.markdown_url, {
                        headers: {
                            'Authorization': `Bearer ${API_TOKEN}`,
                            'X-API-Token': API_TOKEN
                        }
                    });
                    console.log(`Response status: ${fetchResponse.status}`);
                    
                    if (fetchResponse.ok) {
                        const content = await fetchResponse.text();
                        console.log('\nMarkdown Content:');
                        console.log('-'.repeat(40));
                        console.log(content);
                        console.log('-'.repeat(40));
                    } else {
                        const errorText = await fetchResponse.text();
                        console.log(`Error response: ${errorText}`);
                    }
                } catch (error) {
                    console.log(`Fetch error: ${error.message}`);
                }
            }
            
            // Try JSON URL too
            if (result.json_url) {
                console.log(`\nFetching JSON from: ${result.json_url}`);
                
                try {
                    const fetchResponse = await fetch(result.json_url, {
                        headers: {
                            'Authorization': `Bearer ${API_TOKEN}`,
                            'X-API-Token': API_TOKEN
                        }
                    });
                    console.log(`Response status: ${fetchResponse.status}`);
                    
                    if (fetchResponse.ok) {
                        const jsonData = await fetchResponse.json();
                        console.log('\nJSON Data:');
                        console.log('-'.repeat(40));
                        console.log(JSON.stringify(jsonData, null, 2));
                        console.log('-'.repeat(40));
                    }
                } catch (error) {
                    console.log(`Fetch error: ${error.message}`);
                }
            }
        }


    } catch (error) {
        console.error('Test failed:', error);
    }
}

// Run the test
testBatchMarkdown().then(() => {
    console.log('\nTest complete!');
}).catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
});

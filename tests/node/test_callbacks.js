#!/usr/bin/env node

/**
 * Test Webhook Callbacks for Batch Jobs
 * 
 * This test creates a local webhook receiver and tests that
 * callbacks are sent correctly when batch jobs complete.
 */

require('dotenv').config();
const fetch = require('node-fetch');
const express = require('express');

// Configuration
const BASE_URL = process.env.GNOSIS_URL || 'http://localhost:5678';
const API_TOKEN = process.env.GNOSIS_API_TOKEN || '';
const WEBHOOK_PORT = 9999;

// Test URLs
const TEST_URLS = ['https://example.com'];

// Webhook receiver state
let receivedCallbacks = [];

// Create webhook receiver server
function createWebhookReceiver() {
    const app = express();
    app.use(express.json());
    
    // Webhook endpoint
    app.post('/webhook', (req, res) => {
        console.log('\n🔔 WEBHOOK RECEIVED:');
        console.log('Headers:', JSON.stringify(req.headers, null, 2));
        console.log('Body:', JSON.stringify(req.body, null, 2));
        
        receivedCallbacks.push({
            timestamp: new Date().toISOString(),
            headers: req.headers,
            body: req.body
        });
        
        res.json({ success: true, message: 'Webhook received' });
    });
    
    // Health check
    app.get('/health', (req, res) => {
        res.json({ status: 'ok', callbacks_received: receivedCallbacks.length });
    });
    
    return app;
}

async function testCallbacks() {
    console.log('='.repeat(60));
    console.log('BATCH JOB CALLBACK TEST');
    console.log('='.repeat(60));
    
    // Start webhook receiver
    const app = createWebhookReceiver();
    const server = app.listen(WEBHOOK_PORT, () => {
        console.log(`\n✅ Webhook receiver listening on port ${WEBHOOK_PORT}`);
    });
    
    try {
        // Test 1: Submit batch job with callback
        console.log('\n1. Submitting batch job with callback URL...');
        
        const callbackUrl = `http://localhost:${WEBHOOK_PORT}/webhook`;
        console.log(`   Callback URL: ${callbackUrl}`);
        
        const response = await fetch(`${BASE_URL}/api/markdown`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${API_TOKEN}`
            },
            body: JSON.stringify({
                urls: TEST_URLS,
                async: true,
                callback_url: callbackUrl,
                callback_headers: {
                    'X-Custom-Header': 'test-value',
                    'X-Job-Source': 'callback-test'
                }
            })
        });
        
        const result = await response.json();
        console.log('\nBatch job submitted:');
        console.log(JSON.stringify(result, null, 2));
        
        if (!result.success) {
            throw new Error('Failed to submit batch job');
        }
        
        // Test 2: Wait for callback
        console.log('\n2. Waiting for callback (max 30 seconds)...');
        
        const maxWait = 30000;
        const checkInterval = 1000;
        const startTime = Date.now();
        
        while (Date.now() - startTime < maxWait) {
            if (receivedCallbacks.length > 0) {
                console.log(`\n✅ Callback received after ${Math.round((Date.now() - startTime) / 1000)} seconds!`);
                break;
            }
            
            // Also check job status
            if (result.job_id) {
                try {
                    const statusResponse = await fetch(`${BASE_URL}/api/jobs/${result.job_id}`, {
                        headers: {
                            'Authorization': `Bearer ${API_TOKEN}`
                        }
                    });
                    
                    if (statusResponse.ok) {
                        const status = await statusResponse.json();
                        console.log(`   Job status: ${status.status} (${status.completed}/${status.total})`);
                    }
                } catch (e) {
                    // Job status endpoint might not exist yet
                }
            }
            
            await new Promise(resolve => setTimeout(resolve, checkInterval));
        }
        
        // Test 3: Analyze callbacks
        console.log('\n3. Callback Analysis:');
        console.log(`   Total callbacks received: ${receivedCallbacks.length}`);
        
        if (receivedCallbacks.length > 0) {
            const callback = receivedCallbacks[0];
            console.log('\n   First callback details:');
            console.log(`   - Timestamp: ${callback.timestamp}`);
            console.log(`   - Custom headers received: ${JSON.stringify(callback.headers['x-custom-header'])}`);
            console.log(`   - Job source: ${JSON.stringify(callback.headers['x-job-source'])}`);
            
            if (callback.body.job_id) {
                console.log(`   - Job ID: ${callback.body.job_id}`);
                console.log(`   - Status: ${callback.body.status}`);
                console.log(`   - Results count: ${callback.body.results?.length || 0}`);
            }
        } else {
            console.log('\n❌ No callbacks received within timeout period');
            console.log('   This might mean:');
            console.log('   - Callbacks are not implemented yet');
            console.log('   - The job is still processing');
            console.log('   - There\'s an issue with the callback URL');
        }
        
        // Test 4: Direct callback test endpoint
        console.log('\n4. Testing direct callback endpoint...');
        
        const testCallbackResponse = await fetch(`${BASE_URL}/api/test/callback`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${API_TOKEN}`,
                'X-Test-Header': 'direct-test'
            },
            body: JSON.stringify({
                test: true,
                message: 'Direct callback test',
                timestamp: new Date().toISOString()
            })
        });
        
        if (testCallbackResponse.ok) {
            const testResult = await testCallbackResponse.json();
            console.log('   ✅ Direct callback test succeeded:', testResult);
        } else {
            console.log(`   ❌ Direct callback test failed: ${testCallbackResponse.status}`);
        }
        
    } catch (error) {
        console.error('\nTest error:', error);
    } finally {
        // Cleanup
        server.close(() => {
            console.log('\n✅ Webhook receiver stopped');
        });
    }
    
    // Summary
    console.log('\n' + '='.repeat(60));
    console.log('TEST SUMMARY');
    console.log('='.repeat(60));
    console.log(`Callbacks received: ${receivedCallbacks.length}`);
    console.log(`Webhook receiver URL: http://localhost:${WEBHOOK_PORT}/webhook`);
    
    if (receivedCallbacks.length === 0) {
        console.log('\n💡 Next steps:');
        console.log('1. Implement job status tracking in BatchJob model');
        console.log('2. Update _process_batch_background to save job status');
        console.log('3. Implement callback triggering when job completes');
        console.log('4. Add /api/jobs/<job_id> endpoint for status checking');
    }
}

// Run the test
testCallbacks().then(() => {
    console.log('\nTest complete!');
    process.exit(0);
}).catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
});

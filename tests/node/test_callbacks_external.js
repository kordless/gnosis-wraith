#!/usr/bin/env node

/**
 * Test Webhook Callbacks with External URL
 * 
 * This test submits a batch job with a real external webhook URL
 * to verify callbacks are being sent correctly.
 */

require('dotenv').config();
const fetch = require('node-fetch');

// Configuration
const BASE_URL = process.env.GNOSIS_URL || 'http://localhost:5678';
const API_TOKEN = process.env.GNOSIS_API_TOKEN || '';
const WEBHOOK_URL = 'https://wraith.nuts.services/health';

// Test URLs
const TEST_URLS = ['https://example.com'];

async function testExternalCallbacks() {
    console.log('='.repeat(60));
    console.log('BATCH JOB EXTERNAL CALLBACK TEST');
    console.log('='.repeat(60));
    
    try {
        // Test 1: Submit batch job with external callback
        console.log('\n1. Submitting batch job with external callback URL...');
        console.log(`   Callback URL: ${WEBHOOK_URL}`);
        
        const response = await fetch(`${BASE_URL}/api/markdown`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${API_TOKEN}`
            },
            body: JSON.stringify({
                urls: TEST_URLS,
                async: true,
                callback_url: WEBHOOK_URL,
                callback_headers: {
                    'X-Custom-Header': 'gnosis-test',
                    'X-Job-Source': 'external-callback-test'
                }
            })
        });
        
        const result = await response.json();
        console.log('\nBatch job submitted:');
        console.log(JSON.stringify(result, null, 2));
        
        if (!result.success) {
            throw new Error('Failed to submit batch job');
        }
        
        const jobId = result.job_id;
        
        // Test 2: Monitor job status
        console.log('\n2. Monitoring job status...');
        
        let jobComplete = false;
        let attempts = 0;
        const maxAttempts = 30;
        
        while (!jobComplete && attempts < maxAttempts) {
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            const statusResponse = await fetch(`${BASE_URL}/api/jobs/${jobId}`, {
                headers: {
                    'Authorization': `Bearer ${API_TOKEN}`
                }
            });
            
            if (statusResponse.ok) {
                const status = await statusResponse.json();
                console.log(`   Attempt ${attempts + 1}: Status=${status.status}, Completed=${status.completed}/${status.total}`);
                
                if (status.status === 'completed' || status.status === 'failed') {
                    jobComplete = true;
                    console.log(`\n✅ Job ${status.status}!`);
                    console.log('Final job data:');
                    console.log(JSON.stringify(status, null, 2));
                }
            }
            
            attempts++;
        }
        
        if (!jobComplete) {
            console.log('\n⚠️ Job did not complete within timeout period');
        }
        
        // Test 3: Check if webhook was sent
        console.log('\n3. Webhook Status:');
        console.log('   The webhook should have been sent to:', WEBHOOK_URL);
        console.log('   Expected response: HTTP error (since /health doesn\'t accept POST)');
        console.log('   Check server logs for webhook send confirmation');
        
        // Test 4: Submit a sync job to verify immediate processing
        console.log('\n4. Testing synchronous job (no callback)...');
        
        const syncResponse = await fetch(`${BASE_URL}/api/markdown`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${API_TOKEN}`
            },
            body: JSON.stringify({
                urls: TEST_URLS,
                async: false
            })
        });
        
        const syncResult = await syncResponse.json();
        console.log('Sync job result:', syncResult.success ? 'Success' : 'Failed');
        
    } catch (error) {
        console.error('\nTest error:', error);
    }
    
    // Summary
    console.log('\n' + '='.repeat(60));
    console.log('TEST SUMMARY');
    console.log('='.repeat(60));
    console.log('External webhook URL used:', WEBHOOK_URL);
    console.log('\nTo verify webhook delivery:');
    console.log('1. Check Gnosis server logs for webhook send attempts');
    console.log('2. Check any error messages about failed webhook delivery');
    console.log('3. The webhook should fail with 405 (Method Not Allowed) since /health is GET only');
}

// Run the test
testExternalCallbacks().then(() => {
    console.log('\nTest complete!');
    process.exit(0);
}).catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
});
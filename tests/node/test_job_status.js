#!/usr/bin/env node

/**
 * Test Job Status Tracking
 * 
 * This test verifies that job status tracking works correctly
 * for batch processing jobs.
 */

require('dotenv').config();
const fetch = require('node-fetch');

// Configuration
const BASE_URL = process.env.GNOSIS_URL || 'http://localhost:5678';
const API_TOKEN = process.env.GNOSIS_API_TOKEN || '';

// Test URLs
const TEST_URLS = [
    'https://example.com',
    'https://www.wikipedia.org',
    'https://www.github.com'
];

async function testJobStatus() {
    console.log('='.repeat(60));
    console.log('JOB STATUS TRACKING TEST');
    console.log('='.repeat(60));
    
    try {
        // Test 1: Submit async batch job
        console.log('\n1. Submitting async batch job...');
        
        const response = await fetch(`${BASE_URL}/api/markdown`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${API_TOKEN}`
            },
            body: JSON.stringify({
                urls: TEST_URLS,
                async: true
            })
        });
        
        const result = await response.json();
        console.log('Submission result:', result.success ? 'Success' : 'Failed');
        
        if (!result.success) {
            throw new Error('Failed to submit batch job: ' + JSON.stringify(result));
        }
        
        const jobId = result.job_id;
        console.log('Job ID:', jobId);
        console.log('Status URL:', result.status_url);
        
        // Test 2: Check job status immediately
        console.log('\n2. Checking initial job status...');
        
        const statusResponse1 = await fetch(`${BASE_URL}/api/jobs/${jobId}`, {
            headers: {
                'Authorization': `Bearer ${API_TOKEN}`
            }
        });
        
        if (!statusResponse1.ok) {
            throw new Error(`Failed to get job status: ${statusResponse1.status}`);
        }
        
        const status1 = await statusResponse1.json();
        console.log('Initial status:', status1.status);
        console.log('Total URLs:', status1.total);
        console.log('Completed:', status1.completed);
        
        // Test 3: Poll for completion
        console.log('\n3. Polling for job completion...');
        
        let completed = false;
        let attempts = 0;
        const maxAttempts = 60; // 60 seconds timeout
        let finalStatus = null;
        
        while (!completed && attempts < maxAttempts) {
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            const statusResponse = await fetch(`${BASE_URL}/api/jobs/${jobId}`, {
                headers: {
                    'Authorization': `Bearer ${API_TOKEN}`
                }
            });
            
            if (statusResponse.ok) {
                const status = await statusResponse.json();
                console.log(`   Attempt ${attempts + 1}: ${status.status} (${status.completed}/${status.total})`);
                
                if (status.status === 'completed' || status.status === 'failed') {
                    completed = true;
                    finalStatus = status;
                }
            }
            
            attempts++;
        }
        
        if (!completed) {
            console.log('\n❌ Job did not complete within timeout period');
            return;
        }
        
        // Test 4: Verify final results
        console.log('\n4. Final job results:');
        console.log('   Status:', finalStatus.status);
        console.log('   Total:', finalStatus.total);
        console.log('   Completed:', finalStatus.completed);
        console.log('   Failed:', finalStatus.failed);
        console.log('   Created at:', finalStatus.created_at);
        console.log('   Updated at:', finalStatus.updated_at);
        
        if (finalStatus.results && finalStatus.results.length > 0) {
            console.log('\n   Results summary:');
            finalStatus.results.forEach((result, i) => {
                console.log(`   ${i + 1}. ${result.url}: ${result.status}`);
                if (result.markdown_url) {
                    console.log(`      Markdown: ${result.markdown_url}`);
                }
            });
        }
        
        // Test 5: Test non-existent job
        console.log('\n5. Testing non-existent job...');
        
        const badResponse = await fetch(`${BASE_URL}/api/jobs/nonexistent-job-id`, {
            headers: {
                'Authorization': `Bearer ${API_TOKEN}`
            }
        });
        
        console.log('   Expected 404, got:', badResponse.status);
        
        if (badResponse.status === 404) {
            console.log('   ✅ Correctly returned 404 for non-existent job');
        } else {
            console.log('   ❌ Unexpected status code');
        }
        
        // Summary
        console.log('\n' + '='.repeat(60));
        console.log('TEST SUMMARY');
        console.log('='.repeat(60));
        console.log('✅ Job submission:', result.success ? 'Passed' : 'Failed');
        console.log('✅ Status tracking:', completed ? 'Passed' : 'Failed');
        console.log('✅ Job completion:', finalStatus?.status === 'completed' ? 'Passed' : 'Failed');
        console.log('✅ 404 handling:', badResponse.status === 404 ? 'Passed' : 'Failed');
        
    } catch (error) {
        console.error('\nTest error:', error);
    }
}

// Run the test
testJobStatus().then(() => {
    console.log('\nTest complete!');
    process.exit(0);
}).catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
});
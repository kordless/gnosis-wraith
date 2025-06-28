#!/usr/bin/env node

/**
 * Test Batch Collation with Dynamic URLs
 * 
 * This test:
 * 1. Crawls productbot.ai to extract URLs
 * 2. Processes 10 URLs from the site
 * 3. Tests the collation feature
 */

require('dotenv').config();
const fetch = require('node-fetch');

// Configuration
const BASE_URL = process.env.GNOSIS_URL || 'http://localhost:5678';
const API_TOKEN = process.env.GNOSIS_API_TOKEN || '';

async function testCollateBatch() {
    console.log('='.repeat(60));
    console.log('BATCH COLLATION TEST');
    console.log('='.repeat(60));
    
    try {
        // Step 1: Crawl productbot.ai to get URLs
        console.log('\n1. Crawling productbot.ai to extract URLs...');
        
        const crawlResponse = await fetch(`${BASE_URL}/api/crawl`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${API_TOKEN}`
            },
            body: JSON.stringify({
                url: 'https://productbot.ai',
                extract_links: true,
                javascript_enabled: true
            })
        });
        
        if (!crawlResponse.ok) {
            throw new Error(`Crawl failed: ${crawlResponse.status}`);
        }
        
        const crawlResult = await crawlResponse.json();
        console.log('   Crawl successful:', crawlResult.success);
        
        // Extract internal links
        const links = crawlResult.extracted_links || [];
        const internalLinks = links
            .filter(link => link.includes('productbot.ai'))
            .filter(link => !link.includes('#'))
            .filter(link => !link.includes('mailto:'))
            .filter(link => !link.endsWith('.pdf'))
            .filter((link, index, self) => self.indexOf(link) === index); // unique
        
        console.log(`   Found ${internalLinks.length} unique internal links`);
        
        if (internalLinks.length === 0) {
            console.log('   No internal links found, using default URLs');
            internalLinks.push(
                'https://productbot.ai',
                'https://productbot.ai/about',
                'https://productbot.ai/features',
                'https://productbot.ai/pricing'
            );
        }
        
        // Take up to 10 URLs
        const urlsToProcess = internalLinks.slice(0, 10);
        console.log(`   Using ${urlsToProcess.length} URLs for batch processing`);
        urlsToProcess.forEach((url, i) => {
            console.log(`   ${i + 1}. ${url}`);
        });
        
        // Step 2: Submit batch job with collation
        console.log('\n2. Submitting batch job with collation...');
        
        const batchResponse = await fetch(`${BASE_URL}/api/markdown`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${API_TOKEN}`
            },
            body: JSON.stringify({
                urls: urlsToProcess,
                async: true,
                collate: true,
                javascript_enabled: false,  // Faster without JS
                collate_options: {
                    title: "ProductBot.ai Content Analysis",
                    include_stats: true
                }
            })
        });
        
        const batchResult = await batchResponse.json();
        console.log('   Submission result:', batchResult.success ? 'Success' : 'Failed');
        
        if (!batchResult.success) {
            throw new Error('Failed to submit batch job: ' + JSON.stringify(batchResult));
        }
        
        const jobId = batchResult.job_id;
        console.log('   Job ID:', jobId);
        console.log('   Predicted collated URL:', batchResult.collated_url);
        
        // Step 3: Monitor job progress
        console.log('\n3. Monitoring job progress...');
        
        let completed = false;
        let attempts = 0;
        const maxAttempts = 120; // 2 minutes for larger batch
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
                
                // Only log every 5 attempts to reduce noise
                if (attempts % 5 === 0 || status.status !== 'processing') {
                    console.log(`   Attempt ${attempts + 1}: ${status.status} (${status.completed}/${status.total})`);
                }
                
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
        
        // Step 4: Verify results and collation
        console.log('\n4. Job Results:');
        console.log('   Status:', finalStatus.status);
        console.log('   Total URLs:', finalStatus.total);
        console.log('   Completed:', finalStatus.completed);
        console.log('   Failed:', finalStatus.failed);
        
        if (finalStatus.collated_url) {
            console.log('   ✅ Collated URL:', finalStatus.collated_url);
            
            // Step 5: Fetch and preview collated content
            console.log('\n5. Fetching collated content...');
            
            // Extract the path from the full URL
            const url = new URL(finalStatus.collated_url);
            const collatedPath = url.pathname;
            
            const collatedResponse = await fetch(`${BASE_URL}${collatedPath}`, {
                headers: {
                    'Authorization': `Bearer ${API_TOKEN}`
                }
            });
            
            if (collatedResponse.ok) {
                const collatedContent = await collatedResponse.text();
                const lines = collatedContent.split('\n');
                
                console.log('   Collated document preview:');
                console.log('   ' + '─'.repeat(50));
                
                // Show first 20 lines
                lines.slice(0, 20).forEach(line => {
                    console.log('   ' + line);
                });
                
                if (lines.length > 20) {
                    console.log('   ...');
                    console.log(`   (${lines.length - 20} more lines)`);
                }
                
                console.log('   ' + '─'.repeat(50));
                console.log(`   Total size: ${collatedContent.length} characters`);
                console.log(`   Total lines: ${lines.length}`);
            } else {
                console.log('   ❌ Failed to fetch collated content:', collatedResponse.status);
            }
        } else {
            console.log('   ❌ No collated URL returned');
        }
        
        // Summary
        console.log('\n' + '='.repeat(60));
        console.log('TEST SUMMARY');
        console.log('='.repeat(60));
        console.log('✅ URL extraction:', internalLinks.length > 0 ? 'Passed' : 'Failed');
        console.log('✅ Batch submission:', batchResult.success ? 'Passed' : 'Failed');
        console.log('✅ Job completion:', finalStatus?.status === 'completed' ? 'Passed' : 'Failed');
        console.log('✅ Collation:', finalStatus?.collated_url ? 'Passed' : 'Failed');
        
        // Stats
        if (finalStatus?.stats) {
            console.log('\nProcessing Statistics:');
            console.log(`  Total time: ${finalStatus.stats.total_time?.toFixed(2)}s`);
            console.log(`  Total words: ${finalStatus.stats.total_words || 0}`);
            console.log(`  Total chars: ${finalStatus.stats.total_chars || 0}`);
            console.log(`  Avg time/URL: ${finalStatus.stats.average_time_per_url?.toFixed(2)}s`);
        }
        
    } catch (error) {
        console.error('\nTest error:', error);
    }
}

// Run the test
testCollateBatch().then(() => {
    console.log('\nTest complete!');
    process.exit(0);
}).catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
});
#!/usr/bin/env node

/**
 * Quick test to check if local server requires auth
 */

const fetch = require('node-fetch');

async function testLocalAuth() {
    console.log('Testing local Gnosis Wraith auth requirements...\n');
    
    // Test without auth
    console.log('1. Testing without authentication:');
    try {
        const response = await fetch('http://localhost:5678/api/health');
        console.log(`   Health endpoint: ${response.status} ${response.statusText}`);
        const data = await response.json();
        console.log(`   Response:`, data);
    } catch (e) {
        console.log(`   Error: ${e.message}`);
    }
    
    console.log('\n2. Testing markdown endpoint without auth:');
    try {
        const response = await fetch('http://localhost:5678/api/markdown', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: 'https://example.com' })
        });
        console.log(`   Markdown endpoint: ${response.status} ${response.statusText}`);
        const data = await response.json();
        console.log(`   Response:`, data);
    } catch (e) {
        console.log(`   Error: ${e.message}`);
    }
}

testLocalAuth();

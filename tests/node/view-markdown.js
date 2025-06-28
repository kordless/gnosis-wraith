#!/usr/bin/env node

/**
 * Quick markdown viewer for test results
 */

const fetch = require('node-fetch');
const fs = require('fs').promises;
const path = require('path');
const { exec } = require('child_process');

// Load environment
require('dotenv').config();

async function viewMarkdown(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            console.error(`Failed to fetch: ${response.status} ${response.statusText}`);
            return;
        }
        
        const content = await response.text();
        
        // Save to temp file
        const tempFile = path.join(__dirname, 'temp_preview.md');
        await fs.writeFile(tempFile, content);
        
        // Open in VS Code
        exec(`code ${tempFile}`, (error) => {
            if (error) {
                console.error('Failed to open in VS Code:', error);
                // Fallback: just print to console
                console.log('\n' + '='.repeat(60));
                console.log('MARKDOWN CONTENT:');
                console.log('='.repeat(60));
                console.log(content);
            } else {
                console.log(`Opened in VS Code: ${tempFile}`);
                console.log('Press Ctrl+K V to open preview side-by-side');
            }
        });
        
    } catch (error) {
        console.error('Error:', error);
    }
}

// Get URL from command line or use a default
const url = process.argv[2];
if (!url) {
    console.log('Usage: node view-markdown.js <markdown-url>');
    console.log('Example: node view-markdown.js http://localhost:5678/storage/abc123/report.md');
} else {
    viewMarkdown(url);
}

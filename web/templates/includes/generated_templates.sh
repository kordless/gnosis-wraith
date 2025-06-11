#!/bin/bash
# Generated Bash script for: ${query}

SERVER_URL="http://localhost:5678"

crawl_website() {
    local url="$1"
    
    if [[ -z "$url" ]]; then
        echo "Error: URL is required" >&2
        return 1
    fi
    
    local response
    response=$(curl -s -X POST "$SERVER_URL/api/crawl" \
        -H "Content-Type: application/json" \
        -d "{\"url\": \"$url\"}")
    
    if [[ $? -ne 0 ]]; then
        echo "Error: Failed to crawl $url" >&2
        return 1
    fi
    
    echo "$response" | jq '.'
}

# Usage example based on query: ${query}
crawl_website "https://example.com"
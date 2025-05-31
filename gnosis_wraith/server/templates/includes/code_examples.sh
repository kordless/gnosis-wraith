#!/bin/bash
# Bash script for Gnosis Wraith API

URL="https://example.com"
SERVER_URL="http://localhost:5678"

# Crawl website using curl
curl -X POST "$SERVER_URL/api/crawl" \
     -H "Content-Type: application/json" \
     -d "{\"url\": \"$URL\"}" \
     | jq '.'
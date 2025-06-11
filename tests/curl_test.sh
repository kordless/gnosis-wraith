#!/bin/bash
# Simple curl test to see raw JSON response

TOKEN="$1"

if [ -z "$TOKEN" ]; then
    echo "Usage: ./curl_test.sh YOUR_TOKEN"
    exit 1
fi

echo "🔍 Testing raw JSON response..."
echo "================================"

# Simple test
echo -e "\n📋 Test 1: Simple object return"
curl -s -X POST http://localhost:5678/api/v2/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "javascript": "return { test: \"hello\", count: 123 };"
  }' | jq .

# Hacker News test
echo -e "\n📋 Test 2: Hacker News titles"
curl -s -X POST http://localhost:5678/api/v2/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://news.ycombinator.com",
    "javascript": "const links = document.querySelectorAll(\".titleline > a\"); return { count: links.length, first: links[0] ? links[0].textContent : \"none\" };"
  }' | jq .
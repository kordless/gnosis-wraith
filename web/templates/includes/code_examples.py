# Python example for Gnosis Wraith API integration
import requests
import json

def crawl_website(url):
    """Crawl a website using Gnosis Wraith API"""
    response = requests.post('http://localhost:5678/api/crawl', 
                           json={'url': url})
    return response.json()

# Example usage
result = crawl_website('https://example.com')
print(json.dumps(result, indent=2))
# Generated Python code for Gnosis Wraith API integration
import requests
import json
from typing import Dict, Any

class GnosisWraithClient:
    def __init__(self, server_url: str = "http://localhost:5678"):
        self.server_url = server_url
    
    def crawl(self, url: str, **options) -> Dict[str, Any]:
        """Crawl a website with optional parameters"""
        payload = {"url": url, **options}
        
        try:
            response = requests.post(f"{self.server_url}/api/crawl", json=payload)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Crawl failed: {e}")

# Usage example
client = GnosisWraithClient()
result = client.crawl("https://example.com")
print(json.dumps(result, indent=2))

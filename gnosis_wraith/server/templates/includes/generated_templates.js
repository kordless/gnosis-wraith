// Generated JavaScript code for: ${query}
class GnosisWraithClient {
    constructor(serverUrl = 'http://localhost:5678') {
        this.serverUrl = serverUrl;
    }
    
    async crawl(url, options = {}) {
        const payload = { url, ...options };
        
        try {
            const response = await fetch(`${this.serverUrl}/api/crawl`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            throw new Error(`Crawl failed: ${error.message}`);
        }
    }
}

// Usage example based on query: ${query}
const client = new GnosisWraithClient();
client.crawl('https://example.com')
    .then(result => console.log(result))
    .catch(error => console.error(error));
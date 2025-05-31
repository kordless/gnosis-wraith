// JavaScript example for Gnosis Wraith API
async function crawlWebsite(url) {
    const response = await fetch('http://localhost:5678/api/crawl', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
    });
    return await response.json();
}

// Example usage
crawlWebsite('https://example.com')
    .then(result => console.log(result))
    .catch(error => console.error(error));
import logging
import aiohttp

# Get logger from config
logger = logging.getLogger("webwraith")

async def process_with_anthropic(text, token):
    """Process text with Anthropic's Claude API."""
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": token,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    payload = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 1000,
        "messages": [
            {
                "role": "user",
                "content": f"I've extracted text from a website. Please analyze it and provide a concise summary highlighting key information and main points:\n\n{text}"
            }
        ]
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                
                # Extract content from the response
                if 'content' in data and len(data['content']) > 0:
                    return data['content'][0]['text']
                else:
                    return "No content returned from Anthropic API"
            else:
                error_content = await response.text()
                logger.error(f"Anthropic API error ({response.status}): {error_content}")
                raise Exception(f"Anthropic API returned status {response.status}")
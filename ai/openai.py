import logging
import aiohttp

# Get logger from config
logger = logging.getLogger("webwraith")

async def process_with_openai(text, token):
    """Process text with OpenAI's API."""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant that analyzes and summarizes web content."
            },
            {
                "role": "user",
                "content": f"I've extracted text from a website. Please analyze it and provide a concise summary highlighting key information and main points:\n\n{text}"
            }
        ],
        "max_tokens": 1000
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                if 'choices' in data and len(data['choices']) > 0:
                    return data['choices'][0]['message']['content']
                else:
                    return "No content returned from OpenAI API"
            else:
                error_content = await response.text()
                logger.error(f"OpenAI API error ({response.status}): {error_content}")
                raise Exception(f"OpenAI API returned status {response.status}")
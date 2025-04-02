import logging
import aiohttp

# Get logger from config
logger = logging.getLogger("webwraith")

async def process_with_gemini(text, token):
    """Process text with Google's Gemini API."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={token}"
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"I've extracted text from a website. Please analyze it and provide a concise summary highlighting key information and main points:\n\n{text}"
                    }
                ]
            }
        ],
        "generationConfig": {
            "maxOutputTokens": 1000,
            "temperature": 0.2
        }
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                
                if 'candidates' in data and len(data['candidates']) > 0:
                    parts = data['candidates'][0].get('content', {}).get('parts', [])
                    if parts and 'text' in parts[0]:
                        return parts[0]['text']
                    else:
                        return "No text content returned from Gemini API"
                else:
                    return "No candidates returned from Gemini API"
            else:
                error_content = await response.text()
                logger.error(f"Gemini API error ({response.status}): {error_content}")
                raise Exception(f"Gemini API returned status {response.status}")
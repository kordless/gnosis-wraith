# OCR Microservice Migration Plan

## Overview
Move OCR processing to a separate service while keeping image handling in Gnosis Wraith.

## Architecture
```
Gnosis Wraith → captures images → stores images → returns image URLs
                                                ↓
                                         OCR Service (separate)
                                                ↓
                                         Returns markdown
```

## What to Keep in Gnosis Wraith

### 1. **Image/Screenshot Capture**
- Keep all screenshot functionality
- Keep image storage in GCS/local storage
- Keep image URL generation

### 2. **API Parameters**
- Keep `ocr_extraction` parameter
- Keep `take_screenshot` parameter
- Keep image-related response fields

### 3. **Storage**
- Keep image storage functionality
- Keep screenshot saving methods

## What to Remove

### 1. **requirements.txt**
```diff
- easyocr>=1.7.0
- numpy>=1.22.0,<2.0  # Only if not used elsewhere
```

### 2. **Dockerfile**
Remove only:
- EasyOCR pre-download section
- PyTorch installation (if only for OCR)
- CUDA installation (if only for OCR)

Keep:
- Playwright for screenshots
- Image handling libraries

### 3. **OCR Processing Code**
- Remove any EasyOCR imports
- Remove OCR processing logic
- Add OCR service client instead

## New Integration Pattern

### When `ocr_extraction=true`:
```python
# In crawler.py or appropriate location
if ocr_extraction and screenshot_data:
    # Save screenshot first
    screenshot_url = await storage.save_screenshot(screenshot_data, url)
    
    # Call OCR service (new code)
    if ocr_service_url:
        ocr_result = await call_ocr_service(screenshot_url)
        # Add OCR text to markdown or return separately
```

### OCR Service Client (new file)
```python
# core/ocr_client.py
import aiohttp

async def call_ocr_service(image_url: str) -> str:
    """Call external OCR service"""
    ocr_service_url = os.environ.get('OCR_SERVICE_URL')
    if not ocr_service_url:
        return ""
    
    async with aiohttp.ClientSession() as session:
        payload = {"image_url": image_url}
        async with session.post(f"{ocr_service_url}/ocr", json=payload) as response:
            if response.status == 200:
                result = await response.json()
                return result.get('text', '')
    return ""
```

## Environment Variables

Add new environment variable:
```
OCR_SERVICE_URL=https://your-ocr-service.run.app
```

## Benefits

1. **Lighter main service** - No CUDA/PyTorch/EasyOCR
2. **Independent scaling** - OCR service can use GPU instances
3. **Optional OCR** - Works without OCR service
4. **Better separation** - Clear service boundaries
5. **Easier updates** - Update OCR models independently

## Implementation Steps

1. Remove OCR dependencies from requirements.txt
2. Remove CUDA/PyTorch from Dockerfile
3. Create `core/ocr_client.py` for service calls
4. Update crawler to use OCR client when enabled
5. Add OCR_SERVICE_URL to environment config
6. Deploy separate OCR service

## API Compatibility

The API remains unchanged:
- Still accepts `ocr_extraction` parameter
- Still returns OCR results when available
- Gracefully handles when OCR service is unavailable

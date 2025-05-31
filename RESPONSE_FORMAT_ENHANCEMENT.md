# Gnosis Wraith API Enhancement: Selective Response Formats

## 🎯 Problem Solved

The Gnosis Wraith `/api/crawl` endpoint previously returned only a full structured response with metadata, reports, and debugging information. This caused issues for clients like the product management crawler that just needed the markdown content.

## ✨ New Feature: `response_format` Parameter

Added support for three response formats:

### 1. `'full'` (Default - Backward Compatible)
Returns the complete structured response as before:
```json
{
  "success": true,
  "urls_processed": [...],
  "results": [...],
  "report_path": "...",
  "json_path": "...",
  "raw_crawl_data": [...]
}
```

### 2. `'content_only'` (New - Simplified)
Returns just the essential content:
```json
{
  "success": true,
  "url": "https://example.com",
  "markdown_content": "# Page Title\n\nContent here...",
  "title": "Page Title"
}
```

### 3. `'minimal'` (New - Clean)
Returns structured data without truncation or file paths:
```json
{
  "success": true,
  "urls_processed": [...],
  "results": [{
    "url": "https://example.com",
    "title": "Page Title",
    "success": true,
    "markdown_content": "Full content without truncation..."
  }]
}
```

## 🔧 Usage

### In Request Payload:
```python
payload = {
    'url': 'https://example.com',
    'response_format': 'content_only',  # ← New parameter
    'markdown_extraction': 'enhanced',
    'take_screenshot': False,
    'javascript_enabled': True,
    'timeout': 30
}
```

### Product Management Crawler Updated:
The crawler now uses `response_format: 'content_only'` and expects:
- `result.get('markdown_content')` directly
- Simplified error handling
- No nested structure navigation needed

## 📁 Files Modified:

1. **`gnosis_wraith/server/routes/api.py`**
   - Added `response_format` parameter handling
   - Added conditional response formatting logic
   - Enhanced documentation

2. **`product_management_crawler.py`**
   - Updated request payload to use `response_format: 'content_only'`
   - Simplified content extraction logic
   - Improved error handling

3. **`test_response_formats.py`** (New)
   - Testing script for all three response formats
   - Backward compatibility verification

## ⚡ Benefits:

- **Backward Compatible**: Existing clients continue to work unchanged
- **Reduced Bandwidth**: `content_only` format is much smaller
- **Simplified Integration**: Clients don't need complex response parsing
- **Flexible**: Different formats for different use cases
- **Clean**: No more hunting through nested response structures

## 🧪 Testing:

Run the test script to verify all formats work correctly:
```bash
cd /path/to/gnosis-wraith
python test_response_formats.py
```

## 🚀 Next Steps:

1. **Start Gnosis Wraith** server
2. **Test the new functionality** with the test script
3. **Run the product management crawler** to see the improved integration
4. **Update other clients** to use appropriate response formats as needed

The product management crawler should now work seamlessly with the Wraith API! 🎉

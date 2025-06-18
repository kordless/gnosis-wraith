# OCR Crawl Test Suite

Tests to verify the OCR lazy loading fix is working correctly.

## Files

- `test_ocr_crawl.py` - Basic test suite with 4 test cases
- `test_ocr_advanced.py` - Advanced test with multiple URLs and detailed validation  
- `run_ocr_test.bat` - Windows batch file to run basic test

## Quick Start

1. **Start Gnosis Wraith server first**
   ```bash
   # Make sure your server is running on localhost:5000
   ```

2. **Run basic test**
   ```bash
   python test_ocr_crawl.py
   # or on Windows:
   run_ocr_test.bat
   ```

3. **Run advanced test**
   ```bash
   # Test with example.com
   python test_ocr_advanced.py

   # Test with specific URL
   python test_ocr_advanced.py --url "https://wikipedia.org"

   # Use preset URLs
   python test_ocr_advanced.py --preset text_heavy
   ```

## What to Look For

**In the server logs, you should see:**

✅ **Expected Behavior:**
- No EasyOCR warnings when OCR is disabled
- `🔄 Initializing OCR (lazy load)` message only appears the FIRST time OCR is used
- Subsequent OCR requests reuse the existing OCR instance
- Tests without OCR should be faster

❌ **Problems (if fix didn't work):**
- EasyOCR initialization warnings on server startup
- OCR initialization messages when OCR is disabled
- Slow performance even when OCR is disabled

## Test Cases

### Basic Test (`test_ocr_crawl.py`)
1. **No Screenshots, No OCR** - Baseline test
2. **Screenshots Only, No OCR** - Verify screenshots work without OCR
3. **Screenshots + OCR Enabled** - Should trigger OCR lazy loading
4. **Full Screenshots + OCR** - Should reuse existing OCR instance

### Advanced Test (`test_ocr_advanced.py`)
- More detailed validation
- Multiple URL presets
- Command line options
- Expectation checking

## Example Output

```
🧪 Test: Screenshots Only, No OCR
📋 Config: {
  "url": "https://example.com",
  "take_screenshot": true,
  "ocr_extraction": false
}
⏱️  Duration: 2.34s
📊 Status: 200
✅ Success: Crawl completed
📸 Screenshot: /screenshots/example_com_a1b2c3d4.png
🔍 OCR Text: No
```

## Troubleshooting

**Server not responding:**
- Check if Gnosis Wraith is running on localhost:5000
- Try accessing http://localhost:5000/health in browser

**Tests failing:**
- Check server logs for detailed error messages
- Verify network connectivity
- Try with different URLs

**OCR still initializing early:**
- Check if changes were applied correctly
- Restart the server to ensure fresh state
- Look for import/dependency loading issues

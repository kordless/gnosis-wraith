@echo off
echo 🧪 Running OCR Crawl Tests
echo.
echo Make sure Gnosis Wraith server is running first!
echo Press Ctrl+C to cancel, or any key to continue...
pause >nul

python test_ocr_crawl.py
echo.
echo ✅ Test completed! Check the server logs for OCR initialization behavior.
pause

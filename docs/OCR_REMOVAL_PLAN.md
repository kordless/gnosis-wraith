# OCR Removal Checklist for Gnosis Wraith

## Files to Edit

### 1. **requirements.txt**
- Remove: `easyocr>=1.7.0`
- Remove: `numpy>=1.22.0,<2.0` (if only needed for OCR)

### 2. **Dockerfile**
- Remove the entire EasyOCR pre-download section:
  ```dockerfile
  # Pre-download EasyOCR models
  RUN python -c "import easyocr; reader = easyocr.Reader(['en'])" && \
      mkdir -p /root/.cache && \
      # Create symlink for Cloud Run environment
      ln -s /root/.EasyOCR /root/.cache/EasyOCR
  ```

### 3. **web/routes/api.py**
- Remove all references to `ocr_extraction` parameter (lines ~109-111)
- Remove from crawl_url call parameters (line ~145)
- Remove from result_item dictionary (line ~280)

### 4. **core/crawl_functions.py**
- Remove `ocr_extraction` from crawl_url parameters (line ~111)

### 5. **Test files**
- Delete any OCR test files (like test_ocr_advanced.py if it exists)

## API Parameter Cleanup

The following endpoints currently accept but ignore `ocr_extraction`:
- `/api/crawl` (POST)
- `/api/v2/crawl` (POST)
- `/api/batch/md` (POST)

## Docker Image Size Impact

Removing EasyOCR will significantly reduce:
- Docker build time (no model downloads)
- Docker image size (EasyOCR models are several GB)
- Memory usage at runtime

## Migration to Separate OCR Service

Consider creating a separate service for OCR that:
- Accepts images via API
- Returns extracted text
- Can be scaled independently
- Uses GPU acceleration if needed

This separation allows:
- Lighter main Wraith service
- Optional OCR deployment
- Better resource management
- Independent scaling

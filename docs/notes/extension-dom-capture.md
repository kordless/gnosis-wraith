# Extension DOM Capture for Gnosis Wraith

## Overview

The DOM Capture feature enhances the Gnosis Wraith browser extension by allowing it to capture and send the complete DOM (Document Object Model) content of a webpage to the server. This approach ensures that what you see is exactly what gets processed, including all dynamically generated content from JavaScript.

## Benefits

- **Accuracy**: Captures the exact page content as rendered in the browser, including all JavaScript-generated content
- **Efficiency**: Eliminates the need for server-side JavaScript rendering
- **Consistency**: Provides more reliable results for complex web applications
- **Speed**: Reduces processing time by avoiding duplicate page rendering
- **Fidelity**: Preserves the exact layout and structure of the page

## How It Works

1. **DOM Capture**: When activated, the extension captures the complete HTML content of the current page
2. **Screenshot (Optional)**: The extension can also capture a screenshot of the visible area
3. **Server Processing**: The captured DOM is sent to the server for processing
4. **Markdown Conversion**: The server uses the same processing logic to convert HTML to markdown
5. **Report Generation**: A report is generated containing both the original DOM and the extracted content

## Usage

### Extension Commands

The extension offers several ways to trigger DOM capture:

- **Browser Action**: Click the extension icon and select "Capture DOM"
- **Context Menu**: Right-click anywhere on the page and select "Capture page with Gnosis Wraith"
- **Keyboard Shortcut**: Press `Alt+Shift+D` to capture the current page

### Processing Options

When capturing a page, you can choose from several processing modes:

- **Enhanced** (Default): Uses content filtering to extract the most relevant parts of the page
- **Basic**: Converts the entire HTML to markdown without content filtering
- **None**: Stores the raw HTML without markdown conversion

### Screenshot Options

You can configure whether screenshots are included with DOM captures:

- **Include Screenshot**: Captures the visible portion of the page
- **Skip Screenshot**: Only captures the DOM content

## Integration with Existing Features

The DOM Capture feature seamlessly integrates with existing Gnosis Wraith functionality:

- **Reports System**: Captured pages appear in the regular reports interface
- **Markdown Processing**: Uses the same markdown conversion as server-side crawling
- **OCR Integration**: For screenshots, the same OCR processing can be applied

## Technical Details

### API Endpoint

```
POST /api/extension-capture
```

### Request Format

```json
{
  "html": "<!DOCTYPE html>...",
  "metadata": {
    "title": "Page Title",
    "url": "https://example.com",
    "baseUrl": "https://example.com",
    "timestamp": "2025-05-14T23:45:22Z",
    "mainContentSelector": "#main-content",
    "pageStats": {
      "linkCount": 24,
      "imageCount": 8,
      "scriptCount": 12,
      "formCount": 2,
      "tableCount": 1,
      "wordCount": 1250
    }
  },
  "screenshot": "data:image/png;base64,...",
  "processingOptions": {
    "processingMode": "enhanced",
    "includeScreenshot": true
  }
}
```

### Response Format

```json
{
  "success": true,
  "url_processed": "https://example.com",
  "title": "Page Title",
  "processing_mode": "enhanced",
  "report_path": "Page_Title_20250515_0015.md",
  "html_report_path": "Page_Title_20250515_0015.html",
  "screenshot_path": "example_com_20250515_0015.png"
}
```

## Troubleshooting

If you encounter issues with the DOM Capture feature:

1. **Permissions**: Ensure the extension has permission to access the current page
2. **JavaScript Errors**: Check for console errors in the browser's developer tools
3. **Server Connection**: Verify that the server URL is correctly configured in the extension options
4. **Large Pages**: For extremely large pages, the server may need additional processing time

## Future Enhancements

- **Full-page Screenshots**: Support for capturing the entire page, not just the visible area
- **Element Selection**: Allow capturing specific elements rather than the entire page
- **Annotation**: Add support for highlighting and annotating captured content
- **Batch Capture**: Capture multiple pages in sequence for comparative analysis

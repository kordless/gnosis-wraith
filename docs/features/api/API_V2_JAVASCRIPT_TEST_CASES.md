# API v2 JavaScript Injection Test Cases

## Primary Test Case: Alert with Screenshot

### Test 1: Simple Alert Injection
**Purpose**: Verify JavaScript injection and visual confirmation via screenshot

**Request**:
```json
POST /api/v2/inject
{
  "url": "https://example.com",
  "request": "show an alert that says hello world",
  "capture_screenshot": true,
  "screenshot_delay": 500
}
```

**Expected LLM-Generated JavaScript**:
```javascript
alert('hello world');
```

**Expected Response**:
```json
{
  "success": true,
  "data": {
    "injected_code": "alert('hello world');",
    "execution_result": null,
    "screenshot": {
      "url": "/screenshots/inject_result_abc123.png",
      "captured_at": "2025-01-10T12:34:56Z",
      "shows_alert": true
    }
  }
}
```

### Test 2: Direct JavaScript Execution
**Purpose**: Test direct code execution without LLM

**Request**:
```json
POST /api/v2/execute
{
  "url": "https://example.com",
  "script": "alert('hello world');",
  "capture_screenshot": true,
  "screenshot_delay": 500
}
```

### Test 3: Complex Interaction Flow
**Purpose**: Multi-step interaction with visual confirmation

**Request**:
```json
POST /api/v2/workflow
{
  "url": "https://example.com",
  "workflow": {
    "steps": [
      {
        "action": "inject",
        "request": "highlight all links in red"
      },
      {
        "action": "screenshot",
        "label": "highlighted_links"
      },
      {
        "action": "inject", 
        "request": "show alert with the number of links found"
      },
      {
        "action": "screenshot",
        "label": "alert_count"
      }
    ]
  }
}
```

**Expected Generated JavaScript**:
```javascript
// Step 1: Highlight links
document.querySelectorAll('a').forEach(link => {
  link.style.border = '2px solid red';
  link.style.backgroundColor = 'rgba(255,0,0,0.1)';
});

// Step 3: Count and alert
const linkCount = document.querySelectorAll('a').length;
alert(`Found ${linkCount} links on this page`);
```

## Implementation Requirements

### Browser Automation Updates
1. **Playwright Configuration**:
   ```python
   # Handle alert dialogs
   page.on('dialog', lambda dialog: dialog.accept())
   
   # Wait for JavaScript execution
   await page.evaluate(generated_script)
   
   # Capture screenshot with alert visible
   await page.screenshot(full_page=False)
   ```

2. **Alert Detection**:
   ```python
   # Check if alert is present before screenshot
   alert_present = await page.evaluate("""
     () => {
       try {
         // Check if alert would block
         return false;
       } catch(e) {
         return true;
       }
     }
   """)
   ```

### Safety Validations
1. Prevent infinite loops
2. Block attempts to navigate away
3. Limit execution time
4. Sandbox dangerous operations

### Visual Confirmation Features
- Capture screenshot immediately after injection
- Option to capture before/after comparison
- Highlight changed elements
- Include timestamp overlay

## Success Criteria
✅ Alert appears in screenshot
✅ JavaScript executes without errors  
✅ Screenshot captures the alert dialog
✅ Response includes both code and visual proof
✅ Works across different websites
✅ Handles both simple and complex scripts

## Advanced Test Cases

### Form Interaction
```json
{
  "request": "Fill the search box with 'test query' and click search button"
}
```

### Data Extraction  
```json
{
  "request": "Extract all prices from the page and show them in an alert"
}
```

### Visual Manipulation
```json
{
  "request": "Make all images spin continuously"
}
```

### Combined Operations
```json
{
  "request": "Click the first button, wait 2 seconds, then take a screenshot of the result"
}
```

## Error Handling Test Cases

### Blocked Popups
- Detect when alerts are blocked
- Provide alternative visualization

### JavaScript Errors
- Catch and report syntax errors
- Provide helpful error messages

### Timeout Scenarios
- Handle long-running scripts
- Set reasonable timeout limits

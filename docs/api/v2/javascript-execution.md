# JavaScript Execution Endpoints

Execute custom JavaScript on web pages with LLM-powered code generation and safety validation.

## 💻 Direct JavaScript Execution

### POST `/api/v2/execute`

Execute JavaScript code directly on a webpage with full control.

#### Request

```json
{
  "url": "https://example.com",
  "javascript": "document.querySelectorAll('h1')[0].textContent",
  "wait_before": 2000,
  "wait_after": 1000,
  "timeout": 30000,
  "take_screenshot": true,
  "screenshot_options": {
    "full_page": false,
    "quality": 90
  },
  "extract_markdown": true,
  "markdown_options": {
    "include_links": true
  }
}
```

#### Response

```json
{
  "success": true,
  "result": "Welcome to Example.com",
  "screenshot": "data:image/png;base64,...",
  "markdown": "# Welcome to Example.com\n\nThis is an example page...",
  "execution_time_ms": 156,
  "console_logs": [
    {"type": "log", "message": "Page loaded"},
    {"type": "error", "message": "Resource failed to load"}
  ]
}
```

### Advanced Execution Examples

#### Extracting Structured Data

```javascript
// Extract all product information
const products = Array.from(document.querySelectorAll('.product')).map(p => ({
  name: p.querySelector('.name')?.textContent,
  price: p.querySelector('.price')?.textContent,
  image: p.querySelector('img')?.src,
  inStock: p.querySelector('.stock')?.textContent !== 'Out of Stock'
}));
JSON.stringify(products);
```

#### Interacting with Dynamic Content

```javascript
// Click "Load More" until all content is loaded
async function loadAllContent() {
  let loadMoreBtn;
  let clickCount = 0;
  
  while (loadMoreBtn = document.querySelector('.load-more:not(.disabled)')) {
    loadMoreBtn.click();
    await new Promise(resolve => setTimeout(resolve, 1000));
    clickCount++;
    if (clickCount > 10) break; // Safety limit
  }
  
  return document.querySelectorAll('.item').length;
}

await loadAllContent();
```

#### Form Interaction

```javascript
// Fill and submit a form
document.querySelector('#search-input').value = 'artificial intelligence';
document.querySelector('#category').value = 'technology';
document.querySelector('#search-form').submit();

// Wait for results (handled by wait_after parameter)
'Form submitted';
```

## 🤖 LLM-Generated JavaScript

### POST `/api/v2/inject`

Generate JavaScript from natural language descriptions using AI.

#### Request

```json
{
  "url": "https://news.ycombinator.com",
  "request": "Find all posts with more than 100 points and extract their titles and links",
  "llm_provider": "anthropic",
  "llm_token": "sk-ant-...",
  "options": {
    "temperature": 0.3,
    "max_attempts": 3
  },
  "take_screenshot": true,
  "extract_markdown": true
}
```

#### Response

```json
{
  "success": true,
  "generated_code": "// Find posts with >100 points\nconst posts = Array.from(document.querySelectorAll('.athing')).map((post, i) => {\n  const scoreElement = document.querySelectorAll('.score')[i];\n  const score = parseInt(scoreElement?.textContent) || 0;\n  if (score > 100) {\n    return {\n      title: post.querySelector('.titleline a')?.textContent,\n      link: post.querySelector('.titleline a')?.href,\n      score: score\n    };\n  }\n}).filter(Boolean);\nJSON.stringify(posts);",
  "result": [
    {
      "title": "Show HN: I built a better way to debug JavaScript",
      "link": "https://example.com/debugger",
      "score": 245
    },
    {
      "title": "The State of WebAssembly in 2025",
      "link": "https://example.com/wasm-2025", 
      "score": 189
    }
  ],
  "screenshot": "data:image/png;base64,...",
  "markdown": "# Hacker News\n\n## Top Stories\n\n### Show HN: I built a better way to debug JavaScript\n245 points..."
}
```

### Natural Language Examples

#### Data Extraction
```json
{
  "request": "Extract all email addresses from the page",
  "request": "Find all prices and convert them to USD",
  "request": "Get the main article text without ads or navigation"
}
```

#### Page Modification
```json
{
  "request": "Remove all images and replace them with their alt text",
  "request": "Highlight all mentions of 'AI' or 'machine learning' in yellow",
  "request": "Change all links to open in new tabs"
}
```

#### Interaction
```json
{
  "request": "Fill out the contact form with test data",
  "request": "Expand all collapsed sections on the page",
  "request": "Click the 'Show More' button until all results are visible"
}
```

## ✅ JavaScript Validation

### POST `/api/v2/validate`

Validate JavaScript code for safety before execution.

#### Request

```json
{
  "javascript": "document.cookie = 'stolen=' + document.cookie",
  "context": {
    "url": "https://example.com",
    "purpose": "Extract user data"
  }
}
```

#### Response (Unsafe Code)

```json
{
  "valid": false,
  "errors": [
    {
      "type": "security",
      "message": "Cookie access is not allowed",
      "line": 1,
      "pattern": "document.cookie"
    }
  ],
  "suggestions": [
    "Remove cookie access",
    "Use provided data extraction methods instead"
  ]
}
```

#### Response (Safe Code)

```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    {
      "type": "performance",
      "message": "Consider using querySelector instead of getElementsByTagName",
      "line": 3
    }
  ],
  "complexity_score": 3.5
}
```

### Security Rules

The validator blocks:
- Cookie access (`document.cookie`)
- External fetch requests
- Local storage access
- Eval and Function constructor
- Script injection attempts
- Window location changes
- Form submissions to external sites

## 🎯 Page Interaction

### POST `/api/v2/interact`

Perform complex interactions described in natural language.

#### Request

```json
{
  "url": "https://example.com/search",
  "interaction": "Search for 'quantum computing', filter by date (last month), sort by relevance, and get the first 5 results",
  "llm_provider": "openai",
  "llm_token": "sk-...",
  "capture_steps": true,
  "final_screenshot": true
}
```

#### Response

```json
{
  "success": true,
  "steps": [
    {
      "description": "Enter search term",
      "code": "document.querySelector('#search').value = 'quantum computing'",
      "result": "OK"
    },
    {
      "description": "Open filter dropdown",
      "code": "document.querySelector('.filters-toggle').click()",
      "result": "OK"
    },
    {
      "description": "Select date range",
      "code": "document.querySelector('#date-range').value = 'month'",
      "result": "OK"
    },
    {
      "description": "Apply filters and search",
      "code": "document.querySelector('#search-button').click()",
      "result": "OK"
    },
    {
      "description": "Extract results",
      "code": "Array.from(document.querySelectorAll('.result')).slice(0,5).map(r => ({title: r.querySelector('.title')?.textContent, url: r.querySelector('a')?.href}))",
      "result": [
        {
          "title": "Breakthrough in Quantum Error Correction",
          "url": "https://example.com/article1"
        }
      ]
    }
  ],
  "final_result": [...],
  "screenshot": "data:image/png;base64,...",
  "total_execution_time_ms": 4567
}
```

## 🛡️ Safety Features

### Sandboxing

All JavaScript executes in an isolated context with:
- No access to parent window
- Restricted network access
- Timeout protection
- Memory limits

### Pattern Detection

```json
{
  "blocked_patterns": [
    "eval(",
    "Function(",
    "document.cookie",
    "localStorage",
    "sessionStorage",
    "fetch(\"http",
    "XMLHttpRequest",
    "window.location.href =",
    ".innerHTML =",
    "document.write("
  ]
}
```

### Context Validation

Code is validated against the target URL:
- External domain requests blocked
- Credential access prevented
- Form submissions validated

## 📊 Debugging Support

### Console Output

All endpoints capture console output:

```json
{
  "console_logs": [
    {
      "type": "log",
      "message": "Found 42 items",
      "timestamp": "2025-01-06T10:30:45.123Z"
    },
    {
      "type": "error", 
      "message": "Cannot read property 'title' of null",
      "stack": "at extractData (eval:5:12)",
      "timestamp": "2025-01-06T10:30:45.234Z"
    },
    {
      "type": "warn",
      "message": "Slow operation detected",
      "timestamp": "2025-01-06T10:30:46.345Z"
    }
  ]
}
```

### Error Details

Execution errors include full context:

```json
{
  "success": false,
  "error": {
    "code": "EXECUTION_ERROR",
    "message": "JavaScript execution failed",
    "details": {
      "error_type": "TypeError",
      "error_message": "Cannot read property 'click' of null",
      "line": 3,
      "column": 15,
      "code_context": "document.querySelector('.missing').click()",
      "suggestion": "Element '.missing' not found. Verify the selector exists on the page."
    }
  }
}
```

## 🚀 Best Practices

### 1. Use Specific Selectors
```javascript
// Good
document.querySelector('#submit-button')
document.querySelector('[data-testid="search-input"]')

// Avoid
document.querySelectorAll('button')[2]
```

### 2. Handle Missing Elements
```javascript
const element = document.querySelector('.target');
if (element) {
  element.click();
} else {
  'Element not found';
}
```

### 3. Return Serializable Data
```javascript
// Good - returns JSON-serializable data
return {
  count: document.querySelectorAll('.item').length,
  firstItem: document.querySelector('.item')?.textContent
};

// Avoid - returns DOM element
return document.querySelector('.item');
```

### 4. Use Async/Await for Dynamic Content
```javascript
async function waitForContent() {
  // Wait for dynamic content to load
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  // Or wait for specific element
  while (!document.querySelector('.loaded')) {
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  
  return 'Content loaded';
}

await waitForContent();
```

## 📋 Common Use Cases

### Price Monitoring
```javascript
const prices = Array.from(document.querySelectorAll('.price')).map(p => ({
  item: p.closest('.product')?.querySelector('.name')?.textContent,
  price: parseFloat(p.textContent.replace(/[^0-9.]/g, '')),
  currency: p.textContent.match(/[$£€]/)?.[0] || 'USD'
}));
JSON.stringify(prices);
```

### Social Media Metrics
```javascript
{
  followers: document.querySelector('.followers-count')?.textContent,
  posts: document.querySelector('.posts-count')?.textContent,
  engagement: Array.from(document.querySelectorAll('.post')).map(p => ({
    likes: p.querySelector('.likes')?.textContent,
    comments: p.querySelector('.comments')?.textContent,
    shares: p.querySelector('.shares')?.textContent
  }))
}
```

### Form Testing
```javascript
// Test form validation
const form = document.querySelector('#signup-form');
const inputs = {
  email: 'invalid-email',
  password: '123',
  confirm: '456'
};

Object.entries(inputs).forEach(([name, value]) => {
  const input = form.querySelector(`[name="${name}"]`);
  if (input) {
    input.value = value;
    input.dispatchEvent(new Event('input', { bubbles: true }));
  }
});

// Collect validation errors
Array.from(form.querySelectorAll('.error')).map(e => e.textContent);
```
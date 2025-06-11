# Claude Code Directive Addendum: Fix Template Include Escaping

## Issue Identified
The default code examples are showing as escaped template strings instead of actual code content:

**Problem**: Shows `{{ include('includes/code_examples.ps1') | safe }}` instead of actual PowerShell code

**Root Cause**: Jinja2 include statements are inside JavaScript strings, so they're not being processed by the template engine.

## Current Broken Pattern
```javascript
const languages = {
    python: { 
        defaultCode: `{{ include('includes/code_examples.py') | safe }}`
    },
    javascript: { 
        defaultCode: `{{ include('includes/code_examples.js') | safe }}`
    },
    bash: { 
        defaultCode: `{{ include('includes/code_examples.sh') | safe }}`
    },
    powershell: { 
        defaultCode: `{{ include('includes/code_examples.ps1') | safe }}`
    }
};
```

## Required Fix Pattern
Move the includes outside the JavaScript and use template variables:

**Step 1**: Add template variables before the JavaScript section:
```html
<!-- Template code includes - BEFORE the JavaScript -->
<script>
window.FORGE_CODE_EXAMPLES = {
    python: `{{ include('includes/code_examples.py') | safe }}`,
    javascript: `{{ include('includes/code_examples.js') | safe }}`,
    bash: `{{ include('includes/code_examples.sh') | safe }}`,
    powershell: `{{ include('includes/code_examples.ps1') | safe }}`
};
</script>
```

**Step 2**: Update the JavaScript to use the window variables:
```javascript
const languages = {
    python: { 
        name: 'Python', 
        icon: 'fab fa-python', 
        color: 'text-blue-400',
        defaultCode: window.FORGE_CODE_EXAMPLES.python
    },
    javascript: { 
        name: 'JavaScript', 
        icon: 'fab fa-js-square', 
        color: 'text-yellow-400',
        defaultCode: window.FORGE_CODE_EXAMPLES.javascript
    },
    bash: { 
        name: 'Bash', 
        icon: 'fas fa-dollar-sign', 
        color: 'text-green-400',
        defaultCode: window.FORGE_CODE_EXAMPLES.bash
    },
    powershell: { 
        name: 'PowerShell', 
        icon: 'fas fa-terminal', 
        color: 'text-blue-300',
        defaultCode: window.FORGE_CODE_EXAMPLES.powershell
    }
};
```

## Files to Update
- `gnosis_wraith/server/templates/forge.html`

## Expected Result
After fix:
- Python button shows actual Python code with `import requests` etc.
- PowerShell button shows actual PowerShell with `$url = "https://example.com"` etc.
- JavaScript button shows actual JavaScript code
- Bash button shows actual bash script code

The default code examples should load properly when users switch between language buttons.
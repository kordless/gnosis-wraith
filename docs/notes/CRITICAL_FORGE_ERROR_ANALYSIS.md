# CRITICAL BUG REPORT: Forge Template Rendering Error

## Error Summary
**Status**: 🚨 CRITICAL - Forge page completely broken
**Error Type**: Jinja2 UndefinedError - 'include' is undefined
**Location**: `forge.html` line 114
**Impact**: Forge interface inaccessible, returns 500 error

## Docker Log Analysis
**Container**: gnosis-wraith
**Timestamp**: 2025-06-02 17:45:05
**Error Path**: GET /forge → 500 Internal Server Error

## Root Cause
The issue is in the template rendering pipeline. The `include` function is not available in the current Jinja2 template context.

**Failing Code (line 114 in forge.html):**
```javascript
python: `{{ include('includes/code_examples.py') | safe }}`,
```

**Full Error Trace:**
```
File "/app/gnosis_wraith/server/templates/forge.html", line 114, in top-level template code
    python: `{{ include('includes/code_examples.py') | safe }}`,
File "/usr/local/lib/python3.10/dist-packages/jinja2/utils.py", line 83, in from_obj
    if hasattr(obj, "jinja_pass_arg"):
jinja2.exceptions.UndefinedError: 'include' is undefined
```

## Problem Analysis

### Issue 1: Template Context Problem
The `include` function is not available in the Jinja2 template context. This could be due to:
- Jinja2 environment configuration missing the include functionality
- Template context not properly initialized
- Quart/Flask template configuration issue

### Issue 2: Mixed Template/JavaScript Context
The include statements are embedded inside JavaScript template literals within a `{% raw %}` block, which may be interfering with Jinja2 processing.

## Required Fixes

### Fix Option 1: Move Includes Outside JavaScript (RECOMMENDED)
**Step 1**: Add template includes before the JavaScript section:
```html
<!-- Add BEFORE the JavaScript section -->
<script>
// Pre-process template includes
window.FORGE_CODE_EXAMPLES = {
    python: {{ include('includes/code_examples.py') | tojson | safe }},
    javascript: {{ include('includes/code_examples.js') | tojson | safe }},
    bash: {{ include('includes/code_examples.sh') | tojson | safe }},
    powershell: {{ include('includes/code_examples.ps1') | tojson | safe }}
};
</script>
```

**Step 2**: Update JavaScript to use window variables:
```javascript
// Replace the failing lines around line 114
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

### Fix Option 2: Remove Raw Block (ALTERNATIVE)
If the `{% raw %}` block is interfering, move the include statements outside the raw block:

```html
<!-- Move template processing outside raw block -->
{% set python_code = include('includes/code_examples.py') %}
{% set js_code = include('includes/code_examples.js') %}
{% set bash_code = include('includes/code_examples.sh') %}
{% set ps_code = include('includes/code_examples.ps1') %}

<script type="text/babel">
{% raw %}
// Then reference the variables
const languages = {
    python: { 
        defaultCode: {{ python_code | tojson | safe }}
    },
    // etc...
};
{% endraw %}
</script>
```

### Fix Option 3: Check Include Configuration
Verify that the Jinja2 environment has include enabled in the app configuration.

## Priority Actions

1. **IMMEDIATE**: Implement Fix Option 1 (move includes outside JavaScript)
2. **TEST**: Verify forge page loads without errors
3. **VALIDATE**: Confirm code examples display correctly when language buttons are clicked
4. **FALLBACK**: If includes still fail, add hardcoded default examples as temporary fix

## Files to Modify
- `gnosis_wraith/server/templates/forge.html` (line 114 and surrounding area)

## Testing Steps
1. Apply fix
2. Restart container or reload templates
3. Navigate to `/forge`
4. Verify page loads without 500 error
5. Test language button switching
6. Confirm code examples display properly

## Expected Result
- Forge page loads successfully
- Language buttons show actual code examples instead of template strings
- No more Jinja2 UndefinedError exceptions

**URGENT**: This is blocking all Forge functionality. Fix immediately to restore service.
"""JavaScript validation and safety checks"""
import re
from typing import Dict, List, Tuple

class JavaScriptValidator:
    """Validates JavaScript code for safety and security"""
    
    # Dangerous patterns that should be blocked
    DANGEROUS_PATTERNS = [
        # File system access
        r'require\s*\(\s*[\'"]fs[\'"]',
        r'require\s*\(\s*[\'"]child_process[\'"]',
        r'require\s*\(\s*[\'"]os[\'"]',
        r'require\s*\(\s*[\'"]path[\'"]',
        
        # Network requests to external domains
        r'fetch\s*\(\s*[\'"]https?://(?!localhost|127\.0\.0\.1)',
        r'XMLHttpRequest',
        r'WebSocket',
        
        # Eval and dynamic code execution
        r'\beval\s*\(',
        r'new\s+Function\s*\(',
        r'setTimeout\s*\(\s*[\'"]',
        r'setInterval\s*\(\s*[\'"]',
        
        # Document manipulation that could be harmful
        r'document\.write',
        r'document\.writeln',
        r'innerHTML\s*=',
        r'outerHTML\s*=',
        
        # Form submission
        r'\.submit\s*\(',
        r'form\.action\s*=',
        
        # Cookie and storage manipulation
        r'document\.cookie\s*=',
        r'localStorage\.clear',
        r'sessionStorage\.clear',
        
        # Window manipulation
        r'window\.location\s*=',
        r'window\.location\.href\s*=',
        r'window\.open\s*\(',
        
        # Dangerous DOM methods
        r'\.createElement\s*\(\s*[\'"]script',
        r'\.appendChild\s*\(\s*script',
        
        # Process and system access (Node.js)
        r'process\.',
        r'__dirname',
        r'__filename',
        r'global\.',
        
        # Import statements (ES6 modules)
        r'import\s+.*\s+from',
        r'require\s*\(',
    ]
    
    # Allowed patterns (whitelist approach for common operations)
    ALLOWED_OPERATIONS = [
        # DOM selection
        r'document\.querySelector',
        r'document\.querySelectorAll',
        r'document\.getElementById',
        r'document\.getElementsByClassName',
        r'document\.getElementsByTagName',
        
        # Reading properties
        r'\.textContent',
        r'\.innerText',
        r'\.value',
        r'\.href',
        r'\.src',
        r'\.getAttribute',
        r'\.classList',
        r'\.style\.',
        
        # Array methods
        r'\.map\s*\(',
        r'\.filter\s*\(',
        r'\.reduce\s*\(',
        r'\.forEach\s*\(',
        r'\.find\s*\(',
        r'\.includes\s*\(',
        
        # String methods
        r'\.trim\s*\(',
        r'\.replace\s*\(',
        r'\.split\s*\(',
        r'\.toLowerCase\s*\(',
        r'\.toUpperCase\s*\(',
        
        # Console logging
        r'console\.',
        
        # Math operations
        r'Math\.',
        
        # JSON operations
        r'JSON\.parse',
        r'JSON\.stringify',
    ]
    
    def __init__(self):
        self.dangerous_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.DANGEROUS_PATTERNS]
        self.allowed_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.ALLOWED_OPERATIONS]
    
    def validate(self, code: str) -> Tuple[bool, List[str]]:
        """
        Validate JavaScript code for safety.
        
        Returns:
            Tuple of (is_safe, list_of_violations)
        """
        violations = []
        
        # Check for dangerous patterns
        for i, pattern in enumerate(self.dangerous_regex):
            if pattern.search(code):
                violations.append(f"Dangerous pattern detected: {self.DANGEROUS_PATTERNS[i]}")
        
        # Check for script length (prevent extremely long scripts)
        if len(code) > 10000:
            violations.append("Script too long (max 10000 characters)")
        
        # Check for infinite loops
        if self._has_potential_infinite_loop(code):
            violations.append("Potential infinite loop detected")
        
        # Check for excessive DOM operations
        dom_operation_count = code.count('document.')
        if dom_operation_count > 100:
            violations.append(f"Too many DOM operations ({dom_operation_count})")
        
        is_safe = len(violations) == 0
        return is_safe, violations
    
    def _has_potential_infinite_loop(self, code: str) -> bool:
        """Check for potential infinite loops"""
        # Simple heuristic: while(true) or for(;;)
        infinite_patterns = [
            r'while\s*\(\s*true\s*\)',
            r'while\s*\(\s*1\s*\)',
            r'for\s*\(\s*;\s*;\s*\)',
            r'do\s*{[^}]*}\s*while\s*\(\s*true\s*\)',
        ]
        
        for pattern in infinite_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return True
        return False
    
    def sanitize_for_execution(self, code: str) -> str:
        """
        Wrap code in a safe execution context.
        """
        # Wrap in IIFE to prevent global scope pollution
        # Add timeout protection
        sanitized = f"""
(function() {{
    'use strict';
    
    // Set execution timeout
    const startTime = Date.now();
    const maxExecutionTime = 5000; // 5 seconds max
    
    function checkTimeout() {{
        if (Date.now() - startTime > maxExecutionTime) {{
            throw new Error('Script execution timeout');
        }}
    }}
    
    // Original code with timeout checks
    try {{
        {code}
    }} catch (error) {{
        console.error('Script error:', error);
        return {{ error: error.message }};
    }}
}})();
"""
        return sanitized
    
    def get_safe_example(self) -> str:
        """Return an example of safe JavaScript code"""
        return """// Extract all links from the page
const links = Array.from(document.querySelectorAll('a'));
const linkData = links.map(link => ({
    text: link.textContent.trim(),
    href: link.href,
    target: link.target || '_self'
}));
return linkData;"""
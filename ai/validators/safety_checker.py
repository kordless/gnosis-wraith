"""General safety checker for LLM outputs"""
import re
from typing import Dict, List, Tuple

class SafetyChecker:
    """Checks various types of content for safety issues"""
    
    # Patterns that might indicate malicious intent
    SUSPICIOUS_PATTERNS = [
        # Personal information patterns
        r'\b(?:ssn|social.?security)\b',
        r'\b(?:credit.?card|cc.?number)\b',
        r'\b(?:bank.?account)\b',
        r'\b(?:password|passwd|pwd)\b',
        
        # Malicious actions
        r'\b(?:hack|exploit|vulnerability|vuln)\b',
        r'\b(?:malware|virus|trojan|ransomware)\b',
        r'\b(?:phishing|scam)\b',
        r'\b(?:ddos|dos.?attack)\b',
        
        # Sensitive operations
        r'\b(?:delete.?all|drop.?table|truncate)\b',
        r'\b(?:sudo|admin|root)\b',
        
        # Encoded content that might hide malicious code
        r'base64|atob|btoa',
        r'\\x[0-9a-f]{2}',  # Hex encoding
        r'%[0-9a-f]{2}',     # URL encoding
    ]
    
    def __init__(self):
        self.suspicious_regex = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.SUSPICIOUS_PATTERNS
        ]
    
    def check_content(self, content: str, content_type: str = "general") -> Tuple[bool, List[str]]:
        """
        Check content for safety issues.
        
        Args:
            content: The content to check
            content_type: Type of content (e.g., "javascript", "markdown", "general")
            
        Returns:
            Tuple of (is_safe, list_of_warnings)
        """
        warnings = []
        
        # Check for suspicious patterns
        for i, pattern in enumerate(self.suspicious_regex):
            if pattern.search(content):
                warnings.append(
                    f"Suspicious pattern detected: {self.SUSPICIOUS_PATTERNS[i]}"
                )
        
        # Check for excessive length
        if len(content) > 50000:
            warnings.append("Content exceeds maximum safe length")
        
        # Check for binary content
        if self._contains_binary(content):
            warnings.append("Content appears to contain binary data")
        
        # Type-specific checks
        if content_type == "javascript":
            js_warnings = self._check_javascript_specific(content)
            warnings.extend(js_warnings)
        elif content_type == "markdown":
            md_warnings = self._check_markdown_specific(content)
            warnings.extend(md_warnings)
        
        is_safe = len(warnings) == 0
        return is_safe, warnings
    
    def _contains_binary(self, content: str) -> bool:
        """Check if content contains binary data"""
        try:
            # Check for non-printable characters
            non_printable_count = sum(
                1 for char in content 
                if ord(char) < 32 and char not in '\n\r\t'
            )
            return non_printable_count > len(content) * 0.1  # More than 10%
        except:
            return True
    
    def _check_javascript_specific(self, content: str) -> List[str]:
        """JavaScript-specific safety checks"""
        warnings = []
        
        # Check for obfuscated code
        if 'eval(' in content and len(content) > 1000:
            warnings.append("Potentially obfuscated JavaScript detected")
        
        # Check for suspicious function names
        suspicious_functions = ['_0x', 'decrypt', 'decode', 'unescape']
        for func in suspicious_functions:
            if func in content:
                warnings.append(f"Suspicious function name: {func}")
        
        return warnings
    
    def _check_markdown_specific(self, content: str) -> List[str]:
        """Markdown-specific safety checks"""
        warnings = []
        
        # Check for hidden scripts in markdown
        if '<script' in content.lower():
            warnings.append("Script tags found in markdown")
        
        # Check for data URIs that might contain malicious content
        if 'data:' in content and 'base64' in content:
            warnings.append("Data URI with base64 encoding detected")
        
        # Check for excessive links
        link_count = content.count('http://') + content.count('https://')
        if link_count > 50:
            warnings.append(f"Excessive number of links ({link_count})")
        
        return warnings
    
    def sanitize_llm_input(self, prompt: str) -> str:
        """
        Sanitize user prompts before sending to LLM.
        """
        # Remove potential prompt injection attempts
        sanitized = prompt
        
        # Remove system-like commands
        system_patterns = [
            r'ignore.?previous.?instructions',
            r'disregard.?all',
            r'system.?prompt',
            r'###.?system',
            r'<\|system\|>',
        ]
        
        for pattern in system_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        # Limit length
        if len(sanitized) > 5000:
            sanitized = sanitized[:5000] + "... (truncated)"
        
        return sanitized.strip()
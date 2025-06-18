#!/usr/bin/env python3
"""
Run error handling tests
"""

import sys
import pytest
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

def main():
    """Run error handling test suite"""
    
    print("🚨 Running Error Handling Tests...")
    print("=" * 50)
    
    # Run pytest with appropriate arguments
    args = [
        "-v",  # Verbose
        "--tb=short",  # Short traceback
        "-ra",  # Show all test outcomes
        "--maxfail=20",  # Allow more failures for error tests
    ]
    
    # Add test directory
    test_dir = Path(__file__).parent
    
    # Check if specific tests requested
    if len(sys.argv) > 1:
        # Run specific test files
        for test_file in sys.argv[1:]:
            test_path = test_dir / f"test_{test_file}.py"
            if test_path.exists():
                args.append(str(test_path))
            else:
                print(f"Warning: Test file not found: {test_path}")
    else:
        # Run all tests in this directory
        args.append(str(test_dir))
    
    # Run tests
    exit_code = pytest.main(args)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
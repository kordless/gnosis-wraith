#!/usr/bin/env python3
"""
Run authentication tests
"""

import sys
import pytest
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

def main():
    """Run authentication test suite"""
    
    print("🔐 Running Authentication Tests...")
    print("=" * 50)
    
    # Run pytest with appropriate arguments
    args = [
        __file__,
        "-v",  # Verbose
        "--tb=short",  # Short traceback
        "-ra",  # Show all test outcomes
    ]
    
    # Add any command line arguments
    if len(sys.argv) > 1:
        args.extend(sys.argv[1:])
    else:
        # Run all tests in this directory
        args.append(str(Path(__file__).parent))
    
    # Run tests
    exit_code = pytest.main(args)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
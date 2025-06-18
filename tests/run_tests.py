#!/usr/bin/env python3
"""
Gnosis Wraith Test Runner

Run tests with proper configuration and API key handling.
"""

import sys
import os
import argparse
import pytest
from pathlib import Path

# Get paths
test_file_path = Path(__file__).resolve()
tests_dir = test_file_path.parent
project_root = tests_dir.parent

# Add to Python path
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(tests_dir))

# Import config after setting up paths
from rigging.config import config, TestConfig


def check_environment():
    """Check test environment and prompt for missing configuration"""
    print("🧪 Gnosis Wraith Test Runner")
    print("=" * 50)
    
    # Check if .env exists
    env_file = Path(__file__).parent / '.env'
    if not env_file.exists():
        print("\n⚠️  No .env file found!")
        print(f"   Copy {env_file.parent}/.env.example to {env_file}")
        print("   and add your API keys.\n")
        
        create = input("Would you like to create .env from .env.example? (y/n): ")
        if create.lower() == 'y':
            example_file = env_file.parent / '.env.example'
            if example_file.exists():
                import shutil
                shutil.copy(example_file, env_file)
                print(f"✓ Created {env_file}")
                print("  Please edit it and add your API keys.\n")
                sys.exit(0)
    
    print("\n📋 Test Configuration:")
    print(f"   Base URL: {config.BASE_URL}")
    print(f"   Screenshot Tests: {'✓' if config.ENABLE_SCREENSHOT_TESTS else '✗'}")
    print(f"   JavaScript Tests: {'✓' if config.ENABLE_JAVASCRIPT_TESTS else '✗'}")
    print(f"   AI Tests: {'✓' if config.ENABLE_AI_TESTS else '✗'}")
    
    print("\n🔐 Authentication:")
    has_gnosis_token = config.check_gnosis_auth()
    print(f"   Gnosis API Token: {'✓ Configured' if has_gnosis_token else '✗ Not configured'}")
    if not has_gnosis_token:
        print("   → Get token from UI after logging in")
    
    print("\n🔑 AI Provider Keys:")
    providers = ['openai', 'anthropic', 'google']
    for provider in providers:
        has_key = config.has_api_key(provider)
        print(f"   {provider.capitalize()}: {'✓ Configured' if has_key else '✗ Not configured'}")
    
    print()


def run_basic_tests():
    """Run basic functionality tests that don't require AI"""
    print("\n🏃 Running basic tests (no AI required)...\n")
    
    # Check if we have Gnosis auth token
    if config.check_gnosis_auth():
        print("✓ Gnosis API token found - will run authenticated tests\n")
        test_files = [
            'rigging/test_api_health.py',
            'rigging/test_basic_crawl.py',
            'rigging/test_authenticated_crawl.py',
            'rigging/test_quick_start.py'
        ]
    else:
        print("⚠️  No Gnosis API token - will skip authenticated tests")
        print("   Add GNOSIS_API_TOKEN to tests/.env to run all tests\n")
        test_files = [
            'rigging/test_api_health.py',
            'rigging/test_basic_crawl.py'
        ]
    
    # Filter only existing files
    existing_files = []
    for f in test_files:
        file_path = tests_dir / f
        if file_path.exists():
            existing_files.append(str(file_path))
    
    return pytest.main(existing_files + ['-v', '--tb=short'])


def run_ai_tests():
    """Run tests that require AI services"""
    if not config.ENABLE_AI_TESTS:
        print("\n⚠️  AI tests are disabled. Enable in .env to run.\n")
        return 0
    
    print("\n🤖 Running AI-powered tests...\n")
    
    # Check for at least one AI provider
    providers = ['openai', 'anthropic', 'google']
    available = [p for p in providers if config.has_api_key(p)]
    
    if not available:
        print("⚠️  No AI API keys configured!")
        print("   Add at least one API key to .env to run AI tests.\n")
        
        # Offer to prompt for keys
        for provider in providers:
            key = config.prompt_for_key(provider)
            if key:
                available.append(provider)
                break
    
    if not available:
        print("Skipping AI tests - no API keys provided.\n")
        return 0
    
    return pytest.main([
        'tests/rigging/content/',
        'tests/rigging/javascript/',
        '-v',
        '--tb=short'
    ])


def run_category(category: str):
    """Run tests from a specific category"""
    category_path = tests_dir / 'rigging' / category
    if not category_path.exists():
        print(f"\n❌ Category '{category}' not found!\n")
        print("Available categories:")
        for path in (tests_dir / 'rigging').iterdir():
            if path.is_dir() and not path.name.startswith('__'):
                print(f"  - {path.name}")
        return 1
    
    print(f"\n📁 Running {category} tests...\n")
    return pytest.main([str(category_path), '-v', '--tb=short'])


def run_all_tests():
    """Run all tests"""
    print("\n🎯 Running all tests...\n")
    return pytest.main([str(tests_dir / 'rigging'), '-v', '--tb=short'])


def run_specific_test(test_path: str):
    """Run a specific test file or test case"""
    print(f"\n🎯 Running specific test: {test_path}\n")
    return pytest.main([test_path, '-v', '--tb=short'])


def main():
    parser = argparse.ArgumentParser(description='Gnosis Wraith Test Runner')
    parser.add_argument('command', nargs='?', default='basic',
                      choices=['basic', 'ai', 'all', 'list'],
                      help='Test suite to run')
    parser.add_argument('--category', '-c', help='Run specific test category')
    parser.add_argument('--test', '-t', help='Run specific test file or test case')
    parser.add_argument('--markers', '-m', help='Run tests matching given mark expression')
    parser.add_argument('--keyword', '-k', help='Run tests matching given keyword expression')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Always check environment first
    check_environment()
    
    # Handle specific test file/case
    if args.test:
        return run_specific_test(args.test)
    
    # Handle category
    if args.category:
        return run_category(args.category)
    
    # Handle pytest markers/keywords
    if args.markers or args.keyword:
        pytest_args = [str(tests_dir / 'rigging'), '-v']
        if args.markers:
            pytest_args.extend(['-m', args.markers])
        if args.keyword:
            pytest_args.extend(['-k', args.keyword])
        return pytest.main(pytest_args)
    
    # Handle commands
    if args.command == 'list':
        print("\n📋 Available test categories:")
        for path in (tests_dir / 'rigging').iterdir():
            if path.is_dir() and not path.name.startswith('__'):
                # Count test files
                test_files = list(path.glob('test_*.py'))
                if test_files:
                    print(f"\n  {path.name}/")
                    for test_file in test_files:
                        print(f"    - {test_file.name}")
        print("\n💡 Usage examples:")
        print("   python tests/run_tests.py basic           # Run basic tests")
        print("   python tests/run_tests.py ai              # Run AI tests")
        print("   python tests/run_tests.py all             # Run all tests")
        print("   python tests/run_tests.py -c auth         # Run auth category")
        print("   python tests/run_tests.py -t test_api_health.py  # Run specific file")
        print("   python tests/run_tests.py -k 'test_simple_crawl' # Run by keyword")
        return 0
    
    elif args.command == 'basic':
        return run_basic_tests()
    
    elif args.command == 'ai':
        return run_ai_tests()
    
    elif args.command == 'all':
        return run_all_tests()


if __name__ == '__main__':
    sys.exit(main())
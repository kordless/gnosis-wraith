#!/usr/bin/env python3
"""
Gnosis Wraith API v2 Test Suite Runner
Main test orchestrator that manages test execution across all categories
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import subprocess
from dotenv import load_dotenv, set_key
import getpass

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

class TestRunner:
    """Main test runner that orchestrates all test suites"""
    
    def __init__(self, base_url: str = "http://localhost:5678/api/v2"):
        self.base_url = base_url
        self.test_dir = Path(__file__).parent
        self.env_file = self.test_dir / ".env"
        self.results_dir = self.test_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        # Test categories
        self.test_categories = {
            "auth": "Authentication Tests",
            "core": "Core Endpoints Tests",
            "javascript": "JavaScript Execution Tests",
            "content": "Content Processing Tests",
            "errors": "Error Handling Tests",
            "performance": "Performance Tests",
            "utils": "Utility Tests"
        }
        
        self.test_results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "categories": {}
        }
    
    def setup_environment(self, force_new: bool = False) -> bool:
        """Setup test environment and collect credentials"""
        
        print("🔧 Setting up test environment...")
        
        # Load existing .env if exists
        if self.env_file.exists() and not force_new:
            load_dotenv(self.env_file)
            
            # Check if required vars exist
            api_token = os.getenv("GNOSIS_API_TOKEN")
            if api_token:
                print("✅ Using existing API token from .env")
                return True
        
        # Collect credentials
        print("\n📝 Please provide test credentials:")
        print("   (These will be stored in tests/rigging/.env)")
        print()
        
        # API Token
        api_token = getpass.getpass("Gnosis Wraith API Token: ").strip()
        if not api_token:
            print("❌ API token is required!")
            return False
        
        # Base URL
        base_url = input(f"API Base URL [{self.base_url}]: ").strip()
        if base_url:
            self.base_url = base_url
        
        # LLM Tokens (optional)
        print("\n🤖 LLM Provider Tokens (optional, press Enter to skip):")
        anthropic_token = getpass.getpass("Anthropic API Key: ").strip()
        openai_token = getpass.getpass("OpenAI API Key: ").strip()
        gemini_token = getpass.getpass("Google Gemini API Key: ").strip()
        
        # Save to .env
        print("\n💾 Saving credentials to .env...")
        
        # Create .env content
        env_content = f"""# Gnosis Wraith Test Configuration
# Generated: {datetime.now().isoformat()}

# Required
GNOSIS_API_TOKEN={api_token}
GNOSIS_BASE_URL={self.base_url}

# Optional LLM Tokens
ANTHROPIC_API_KEY={anthropic_token}
OPENAI_API_KEY={openai_token}
GEMINI_API_KEY={gemini_token}

# Test Configuration
TEST_TIMEOUT=30
TEST_PARALLEL=false
TEST_VERBOSE=true
"""
        
        self.env_file.write_text(env_content)
        print("✅ Configuration saved!")
        
        # Load the new environment
        load_dotenv(self.env_file)
        return True
    
    def discover_tests(self, category: Optional[str] = None) -> Dict[str, List[str]]:
        """Discover all test files in categories"""
        
        discovered = {}
        
        categories = [category] if category else self.test_categories.keys()
        
        for cat in categories:
            cat_dir = self.test_dir / cat
            if not cat_dir.exists():
                continue
            
            test_files = list(cat_dir.glob("test_*.py"))
            if test_files:
                discovered[cat] = [f.stem for f in test_files]
        
        return discovered
    
    def run_category_tests(self, category: str, tests: Optional[List[str]] = None) -> Dict:
        """Run tests for a specific category"""
        
        print(f"\n🏃 Running {self.test_categories.get(category, category)} tests...")
        
        cat_dir = self.test_dir / category
        runner_script = cat_dir / "run_tests.py"
        
        if runner_script.exists():
            # Use category-specific runner
            cmd = [sys.executable, str(runner_script)]
            if tests:
                cmd.extend(tests)
        else:
            # Run pytest directly
            cmd = [sys.executable, "-m", "pytest", str(cat_dir), "-v"]
            if tests:
                for test in tests:
                    cmd.extend(["-k", test])
        
        # Add environment variables
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.test_dir.parent.parent)
        
        # Run tests
        start_time = time.time()
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        duration = time.time() - start_time
        
        # Parse results
        output = result.stdout + result.stderr
        
        # Simple parsing (can be enhanced with pytest-json-report)
        passed = output.count(" PASSED")
        failed = output.count(" FAILED")
        skipped = output.count(" SKIPPED")
        total = passed + failed + skipped
        
        return {
            "category": category,
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "duration": duration,
            "output": output,
            "exit_code": result.returncode
        }
    
    def run_all_tests(self, parallel: bool = False) -> None:
        """Run all test categories"""
        
        print("🚀 Gnosis Wraith API v2 Test Suite")
        print("=" * 50)
        
        discovered = self.discover_tests()
        
        if not discovered:
            print("❌ No tests found!")
            return
        
        print(f"\n📋 Discovered tests:")
        for cat, tests in discovered.items():
            print(f"  • {self.test_categories[cat]}: {len(tests)} test files")
        
        print(f"\n⏱️  Starting test run at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        start_time = time.time()
        
        # Run tests by category
        for category in discovered:
            result = self.run_category_tests(category)
            self.test_results["categories"][category] = result
            
            # Update totals
            self.test_results["total"] += result["total"]
            self.test_results["passed"] += result["passed"]
            self.test_results["failed"] += result["failed"]
            self.test_results["skipped"] += result["skipped"]
            
            # Show category summary
            status = "✅" if result["exit_code"] == 0 else "❌"
            print(f"{status} {category}: {result['passed']}/{result['total']} passed in {result['duration']:.2f}s")
        
        total_duration = time.time() - start_time
        
        # Generate report
        self.generate_report(total_duration)
    
    def generate_report(self, duration: float) -> None:
        """Generate test report"""
        
        print("\n" + "=" * 50)
        print("📊 Test Summary")
        print("=" * 50)
        
        # Overall stats
        total = self.test_results["total"]
        passed = self.test_results["passed"]
        failed = self.test_results["failed"]
        skipped = self.test_results["skipped"]
        
        if total > 0:
            pass_rate = (passed / total) * 100
        else:
            pass_rate = 0
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ({pass_rate:.1f}%)")
        print(f"Failed: {failed}")
        print(f"Skipped: {skipped}")
        print(f"Duration: {duration:.2f}s")
        
        # Category breakdown
        print("\n📁 Category Results:")
        for cat, result in self.test_results["categories"].items():
            status = "✅" if result["exit_code"] == 0 else "❌"
            print(f"  {status} {self.test_categories[cat]}: {result['passed']}/{result['total']}")
        
        # Save detailed report
        report_file = self.results_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "duration": duration,
            "base_url": self.base_url,
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "pass_rate": pass_rate
            },
            "categories": self.test_results["categories"]
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        # Exit code based on results
        if failed > 0:
            sys.exit(1)
        else:
            print("\n🎉 All tests passed!")
    
    def run_specific_tests(self, category: str, tests: List[str]) -> None:
        """Run specific tests from a category"""
        
        print(f"🎯 Running specific tests from {category}...")
        
        result = self.run_category_tests(category, tests)
        
        # Show results
        if result["exit_code"] == 0:
            print(f"✅ All tests passed!")
        else:
            print(f"❌ Some tests failed!")
        
        print(f"\nResults: {result['passed']}/{result['total']} passed")


def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(description="Gnosis Wraith API v2 Test Suite")
    parser.add_argument("--setup", action="store_true", help="Setup test environment")
    parser.add_argument("--category", "-c", help="Run specific test category")
    parser.add_argument("--test", "-t", nargs="+", help="Run specific tests")
    parser.add_argument("--parallel", "-p", action="store_true", help="Run tests in parallel")
    parser.add_argument("--base-url", default="http://localhost:5678/api/v2", help="API base URL")
    parser.add_argument("--list", "-l", action="store_true", help="List available tests")
    
    args = parser.parse_args()
    
    runner = TestRunner(base_url=args.base_url)
    
    # Setup environment if needed
    if args.setup or not runner.env_file.exists():
        if not runner.setup_environment(force_new=args.setup):
            sys.exit(1)
    else:
        # Load existing environment
        load_dotenv(runner.env_file)
    
    # List tests
    if args.list:
        discovered = runner.discover_tests()
        print("📋 Available tests:")
        for cat, tests in discovered.items():
            print(f"\n{runner.test_categories[cat]}:")
            for test in tests:
                print(f"  • {test}")
        return
    
    # Run specific tests
    if args.category and args.test:
        runner.run_specific_tests(args.category, args.test)
    elif args.category:
        result = runner.run_category_tests(args.category)
        if result["exit_code"] != 0:
            sys.exit(1)
    else:
        # Run all tests
        runner.run_all_tests(parallel=args.parallel)


if __name__ == "__main__":
    main()
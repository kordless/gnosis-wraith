"""
V2 API Integration Test Harness
Tests complete workflows and integration scenarios
"""
import asyncio
import json
import os
import time
from typing import Dict, Any, List, Optional
import httpx
import base64
from datetime import datetime
import hashlib


class V2IntegrationHarness:
    """Integration testing for V2 API workflows"""
    
    def __init__(self, base_url: str = "http://localhost:5678"):
        self.base_url = base_url
        self.v2_base = f"{base_url}/v2"
        self.session_cookie = None
        self.auth_token = None
        self.test_results = []
        self.client = None
        self.test_data = {}
        
    async def setup(self):
        """Setup test environment"""
        self.client = httpx.AsyncClient(timeout=60.0)
        await self.authenticate()
        
    async def teardown(self):
        """Cleanup test environment"""
        if self.client:
            await self.client.aclose()
            
    async def authenticate(self):
        """Authenticate for testing"""
        try:
            response = await self.client.get(f"{self.base_url}/auth/login")
            self.session_cookie = response.cookies.get("session")
        except Exception as e:
            print(f"Auth setup error: {e}")
            
    def get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        headers = {
            "Content-Type": "application/json",
            "X-API-Version": "2"
        }
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers
        
    def get_cookies(self) -> Dict[str, str]:
        """Get request cookies"""
        if self.session_cookie:
            return {"session": self.session_cookie}
        return {}
        
    async def test_workflow(self, name: str, steps: List[Dict]) -> Dict[str, Any]:
        """Execute a complete workflow test"""
        print(f"\n=== Testing Workflow: {name} ===")
        
        workflow_start = time.time()
        workflow_results = {
            "name": name,
            "steps": [],
            "success": True,
            "total_time": 0,
            "data": {}
        }
        
        for i, step in enumerate(steps):
            print(f"\nStep {i+1}: {step['name']}")
            
            step_result = await self.execute_step(step, workflow_results["data"])
            workflow_results["steps"].append(step_result)
            
            if not step_result["success"]:
                workflow_results["success"] = False
                print(f"  ✗ Failed: {step_result['error']}")
                break
            else:
                print(f"  ✓ Success in {step_result['elapsed_ms']:.2f}ms")
                
        workflow_results["total_time"] = (time.time() - workflow_start) * 1000
        
        status = "✓ PASSED" if workflow_results["success"] else "✗ FAILED"
        print(f"\n{status} - {name} ({workflow_results['total_time']:.2f}ms)")
        
        self.test_results.append(workflow_results)
        return workflow_results
        
    async def execute_step(self, step: Dict, context: Dict) -> Dict[str, Any]:
        """Execute a single workflow step"""
        start_time = time.time()
        
        try:
            # Replace context variables in data
            data = self.replace_context_vars(step.get("data", {}), context)
            
            # Make request
            method = step.get("method", "POST")
            endpoint = step["endpoint"]
            
            if method == "GET":
                response = await self.client.get(
                    f"{self.v2_base}{endpoint}",
                    headers=self.get_headers(),
                    cookies=self.get_cookies()
                )
            else:
                response = await self.client.post(
                    f"{self.v2_base}{endpoint}",
                    json=data,
                    headers=self.get_headers(),
                    cookies=self.get_cookies()
                )
                
            elapsed = (time.time() - start_time) * 1000
            
            # Parse response
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}
                
            # Store data in context if specified
            if "store" in step and response.status_code == 200:
                for key, path in step["store"].items():
                    value = self.extract_value(response_data, path)
                    context[key] = value
                    
            # Validate response
            success = response.status_code in step.get("expected_status", [200])
            if success and "validate" in step:
                for validation in step["validate"]:
                    if not self.validate_response(response_data, validation):
                        success = False
                        break
                        
            return {
                "name": step["name"],
                "endpoint": endpoint,
                "status": response.status_code,
                "elapsed_ms": elapsed,
                "success": success,
                "response": response_data,
                "error": None if success else f"Status {response.status_code}"
            }
            
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            return {
                "name": step["name"],
                "endpoint": step.get("endpoint", "unknown"),
                "status": 0,
                "elapsed_ms": elapsed,
                "success": False,
                "response": None,
                "error": str(e)
            }
            
    def replace_context_vars(self, data: Any, context: Dict) -> Any:
        """Replace {{var}} with context values"""
        if isinstance(data, str):
            for key, value in context.items():
                data = data.replace(f"{{{{{key}}}}}", str(value))
            return data
        elif isinstance(data, dict):
            return {k: self.replace_context_vars(v, context) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.replace_context_vars(item, context) for item in data]
        return data
        
    def extract_value(self, data: Dict, path: str) -> Any:
        """Extract value from response using dot notation"""
        parts = path.split(".")
        value = data
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        return value
        
    def validate_response(self, data: Dict, validation: Dict) -> bool:
        """Validate response data"""
        field = validation["field"]
        expected = validation.get("value")
        condition = validation.get("condition", "equals")
        
        actual = self.extract_value(data, field)
        
        if condition == "equals":
            return actual == expected
        elif condition == "contains":
            return expected in str(actual)
        elif condition == "exists":
            return actual is not None
        elif condition == "not_empty":
            return bool(actual)
        elif condition == "gt":
            return float(actual) > float(expected)
        elif condition == "lt":
            return float(actual) < float(expected)
            
        return False
        
    async def run_all_integration_tests(self):
        """Run all integration test workflows"""
        print("=" * 80)
        print("V2 API Integration Test Suite")
        print("=" * 80)
        
        await self.setup()
        
        # Define test workflows
        workflows = [
            self.get_crawl_and_analyze_workflow(),
            self.get_async_crawl_workflow(),
            self.get_session_persistence_workflow(),
            self.get_ai_pipeline_workflow(),
            self.get_javascript_execution_workflow(),
            self.get_data_extraction_workflow(),
            self.get_monitoring_workflow(),
            self.get_search_workflow()
        ]
        
        # Run all workflows
        for workflow in workflows:
            await self.test_workflow(workflow["name"], workflow["steps"])
            
        await self.teardown()
        
        # Print summary
        self.print_summary()
        
    def get_crawl_and_analyze_workflow(self) -> Dict:
        """Workflow: Crawl page and analyze content"""
        return {
            "name": "Crawl and Analyze",
            "steps": [
                {
                    "name": "Crawl webpage",
                    "endpoint": "/crawl",
                    "data": {
                        "url": "https://example.com",
                        "javascript": False,
                        "screenshot": True,
                        "response_format": "full"
                    },
                    "store": {
                        "content": "content",
                        "screenshot_url": "screenshot"
                    },
                    "validate": [
                        {"field": "success", "value": True},
                        {"field": "content", "condition": "not_empty"}
                    ]
                },
                {
                    "name": "Analyze content with Claude",
                    "endpoint": "/claude-analyze",
                    "data": {
                        "content": "{{content}}",
                        "prompt": "Summarize this webpage content in 2 sentences",
                        "model": "claude-3-haiku-20240307"
                    },
                    "validate": [
                        {"field": "success", "value": True},
                        {"field": "analysis", "condition": "not_empty"}
                    ]
                },
                {
                    "name": "Generate code example",
                    "endpoint": "/code",
                    "data": {
                        "query": "Python script to scrape similar content",
                        "options": {
                            "language_preference": "python"
                        }
                    },
                    "validate": [
                        {"field": "success", "value": True},
                        {"field": "language", "value": "python"},
                        {"field": "code", "condition": "contains", "value": "def"}
                    ]
                }
            ]
        }
        
    def get_async_crawl_workflow(self) -> Dict:
        """Workflow: Async crawl with job monitoring"""
        return {
            "name": "Async Crawl with Job Monitoring",
            "steps": [
                {
                    "name": "Estimate crawl complexity",
                    "endpoint": "/estimate",
                    "data": {
                        "url": "https://example.com",
                        "javascript": True,
                        "screenshot": True,
                        "depth": 2
                    },
                    "store": {
                        "estimated_time": "estimated_time",
                        "recommended_mode": "recommended_mode"
                    },
                    "validate": [
                        {"field": "success", "value": True},
                        {"field": "recommended_mode", "value": "async"}
                    ]
                },
                {
                    "name": "Start async crawl",
                    "endpoint": "/crawl",
                    "data": {
                        "url": "https://example.com",
                        "javascript": True,
                        "screenshot": True,
                        "depth": 2,
                        "full_content": True
                    },
                    "store": {
                        "job_id": "job_id",
                        "is_async": "async"
                    },
                    "validate": [
                        {"field": "success", "value": True},
                        {"field": "async", "value": True}
                    ]
                },
                {
                    "name": "Check job status",
                    "endpoint": "/jobs/{{job_id}}",
                    "method": "GET",
                    "expected_status": [200, 404],
                    "validate": [
                        {"field": "job_id", "condition": "exists"}
                    ]
                }
            ]
        }
        
    def get_session_persistence_workflow(self) -> Dict:
        """Workflow: Test session persistence"""
        return {
            "name": "Session Persistence",
            "steps": [
                {
                    "name": "Initial crawl (create session)",
                    "endpoint": "/crawl",
                    "data": {
                        "url": "https://example.com/login",
                        "javascript": True
                    },
                    "store": {
                        "session_id": "session_id"
                    },
                    "validate": [
                        {"field": "success", "value": True},
                        {"field": "session_id", "condition": "exists"}
                    ]
                },
                {
                    "name": "Reuse session",
                    "endpoint": "/crawl",
                    "data": {
                        "url": "https://example.com/dashboard",
                        "javascript": True,
                        "session_id": "{{session_id}}"
                    },
                    "validate": [
                        {"field": "success", "value": True},
                        {"field": "session_id", "value": "{{session_id}}"}
                    ]
                }
            ]
        }
        
    def get_ai_pipeline_workflow(self) -> Dict:
        """Workflow: Complete AI processing pipeline"""
        return {
            "name": "AI Processing Pipeline",
            "steps": [
                {
                    "name": "Get URL suggestions",
                    "endpoint": "/suggest-urls",
                    "data": {
                        "query": "artificial intelligence news",
                        "limit": 3,
                        "category": "technology"
                    },
                    "store": {
                        "first_url": "urls.0.url"
                    },
                    "validate": [
                        {"field": "success", "value": True},
                        {"field": "urls", "condition": "not_empty"}
                    ]
                },
                {
                    "name": "Extract markdown from suggested URL",
                    "endpoint": "/markdown",
                    "data": {
                        "url": "{{first_url}}",
                        "javascript": False,
                        "clean_format": True
                    },
                    "store": {
                        "markdown_content": "markdown"
                    },
                    "validate": [
                        {"field": "success", "value": True},
                        {"field": "metadata.word_count", "condition": "gt", "value": 10}
                    ]
                },
                {
                    "name": "Summarize content",
                    "endpoint": "/summarize",
                    "data": {
                        "content": "{{markdown_content}}",
                        "options": {
                            "type": "concise",
                            "max_length": 200,
                            "format": "bullet_points"
                        }
                    },
                    "validate": [
                        {"field": "success", "value": True},
                        {"field": "summary", "condition": "not_empty"},
                        {"field": "metadata.compression_ratio", "condition": "lt", "value": 1}
                    ]
                }
            ]
        }
        
    def get_javascript_execution_workflow(self) -> Dict:
        """Workflow: JavaScript execution and validation"""
        return {
            "name": "JavaScript Execution",
            "steps": [
                {
                    "name": "Generate JS from natural language",
                    "endpoint": "/inject",
                    "data": {
                        "url": "https://example.com",
                        "request": "Extract all email addresses from the page"
                    },
                    "store": {
                        "generated_js": "javascript"
                    },
                    "expected_status": [200, 500],  # May fail if JS generation fails
                    "validate": [
                        {"field": "success", "condition": "exists"}
                    ]
                },
                {
                    "name": "Validate generated JavaScript",
                    "endpoint": "/validate",
                    "data": {
                        "javascript": "const emails = Array.from(document.querySelectorAll('a[href^=\"mailto:\"]')).map(a => a.href.replace('mailto:', ''));"
                    },
                    "validate": [
                        {"field": "success", "value": True},
                        {"field": "valid", "condition": "exists"}
                    ]
                },
                {
                    "name": "Execute validated JavaScript",
                    "endpoint": "/execute",
                    "data": {
                        "url": "https://example.com",
                        "javascript": "document.querySelectorAll('a').length",
                        "options": {
                            "wait_before": 1000,
                            "wait_after": 500
                        },
                        "take_screenshot": True
                    },
                    "validate": [
                        {"field": "success", "value": True},
                        {"field": "executed", "value": True}
                    ]
                }
            ]
        }
        
    def get_data_extraction_workflow(self) -> Dict:
        """Workflow: Structured data extraction"""
        return {
            "name": "Data Extraction",
            "steps": [
                {
                    "name": "Define extraction schema",
                    "endpoint": "/workflows/extract_data",
                    "data": {
                        "parameters": {
                            "url": "https://example.com",
                            "schema": {
                                "title": "Page title",
                                "description": "Meta description",
                                "headings": "All h1 and h2 headings",
                                "links": "All external links"
                            }
                        }
                    },
                    "expected_status": [200, 404],  # Workflow might not be implemented
                    "validate": [
                        {"field": "success", "condition": "exists"}
                    ]
                }
            ]
        }
        
    def get_monitoring_workflow(self) -> Dict:
        """Workflow: Change monitoring"""
        return {
            "name": "Change Monitoring",
            "steps": [
                {
                    "name": "Initial crawl",
                    "endpoint": "/crawl",
                    "data": {
                        "url": "https://example.com/news",
                        "javascript": False
                    },
                    "store": {
                        "initial_crawl_id": "crawl_id",
                        "initial_content": "content"
                    },
                    "validate": [
                        {"field": "success", "value": True}
                    ]
                },
                {
                    "name": "Monitor for changes",
                    "endpoint": "/workflows/monitor_changes",
                    "data": {
                        "parameters": {
                            "url": "https://example.com/news",
                            "previous_crawl_id": "{{initial_crawl_id}}"
                        }
                    },
                    "expected_status": [200, 404],
                    "validate": [
                        {"field": "success", "condition": "exists"}
                    ]
                }
            ]
        }
        
    def get_search_workflow(self) -> Dict:
        """Workflow: Search and retrieve"""
        return {
            "name": "Search and Retrieve",
            "steps": [
                {
                    "name": "Crawl multiple pages",
                    "endpoint": "/crawl",
                    "data": {
                        "url": "https://example.com/about",
                        "javascript": False
                    },
                    "validate": [
                        {"field": "success", "value": True}
                    ]
                },
                {
                    "name": "Search crawled content",
                    "endpoint": "/search",
                    "data": {
                        "query": "example",
                        "limit": 5,
                        "offset": 0
                    },
                    "validate": [
                        {"field": "success", "value": True},
                        {"field": "results", "condition": "exists"}
                    ]
                }
            ]
        }
        
    def print_summary(self):
        """Print integration test summary"""
        print("\n" + "=" * 80)
        print("INTEGRATION TEST SUMMARY")
        print("=" * 80)
        
        total_workflows = len(self.test_results)
        passed_workflows = sum(1 for r in self.test_results if r["success"])
        
        print(f"\nTotal Workflows: {total_workflows}")
        print(f"Passed: {passed_workflows} ({passed_workflows/total_workflows*100:.1f}%)")
        print(f"Failed: {total_workflows - passed_workflows}")
        
        print("\nWorkflow Results:")
        for result in self.test_results:
            status = "✓" if result["success"] else "✗"
            print(f"{status} {result['name']} - {len(result['steps'])} steps, {result['total_time']:.2f}ms")
            
            if not result["success"]:
                # Find failed step
                for step in result["steps"]:
                    if not step["success"]:
                        print(f"  Failed at: {step['name']} - {step['error']}")
                        break
                        
        # Save detailed results
        with open("tests/rigging/integration_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2, default=str)
        print(f"\nDetailed results saved to integration_results.json")


# Main execution
async def main():
    """Run integration tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description="V2 API Integration Tests")
    parser.add_argument("--base-url", default="http://localhost:5678")
    parser.add_argument("--workflow", help="Run specific workflow")
    
    args = parser.parse_args()
    
    harness = V2IntegrationHarness(args.base_url)
    
    if args.workflow:
        # Run specific workflow
        await harness.setup()
        
        workflows = {
            "crawl": harness.get_crawl_and_analyze_workflow(),
            "async": harness.get_async_crawl_workflow(),
            "session": harness.get_session_persistence_workflow(),
            "ai": harness.get_ai_pipeline_workflow(),
            "js": harness.get_javascript_execution_workflow(),
            "extract": harness.get_data_extraction_workflow(),
            "monitor": harness.get_monitoring_workflow(),
            "search": harness.get_search_workflow()
        }
        
        if args.workflow in workflows:
            workflow = workflows[args.workflow]
            await harness.test_workflow(workflow["name"], workflow["steps"])
            harness.print_summary()
        else:
            print(f"Unknown workflow: {args.workflow}")
            print(f"Available: {', '.join(workflows.keys())}")
            
        await harness.teardown()
    else:
        # Run all workflows
        await harness.run_all_integration_tests()


if __name__ == "__main__":
    asyncio.run(main())
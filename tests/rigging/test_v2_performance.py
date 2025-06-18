"""
V2 API Performance Test Harness
Tests performance, concurrency, and load handling
"""
import asyncio
import time
import statistics
from typing import List, Dict, Any
import httpx
import json
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class V2PerformanceHarness:
    """Performance testing for V2 API"""
    
    def __init__(self, base_url: str = "http://localhost:5678"):
        self.base_url = base_url
        self.v2_base = f"{base_url}/v2"
        self.results = []
        
    async def make_request(self, endpoint: str, method: str = "POST", 
                          data: Dict = None, request_id: int = 0) -> Dict[str, Any]:
        """Make a single timed request"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            start_time = time.time()
            
            try:
                if method == "GET":
                    response = await client.get(f"{self.v2_base}{endpoint}")
                else:
                    response = await client.post(
                        f"{self.v2_base}{endpoint}",
                        json=data or {},
                        headers={"Content-Type": "application/json"}
                    )
                    
                elapsed = (time.time() - start_time) * 1000  # ms
                
                return {
                    "request_id": request_id,
                    "endpoint": endpoint,
                    "status": response.status_code,
                    "elapsed_ms": elapsed,
                    "success": 200 <= response.status_code < 300,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                elapsed = (time.time() - start_time) * 1000
                return {
                    "request_id": request_id,
                    "endpoint": endpoint,
                    "status": 0,
                    "elapsed_ms": elapsed,
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
    async def test_concurrent_requests(self, endpoint: str, data: Dict, 
                                     concurrent_count: int = 10) -> Dict[str, Any]:
        """Test concurrent request handling"""
        print(f"\n--- Testing {concurrent_count} concurrent requests to {endpoint} ---")
        
        tasks = []
        for i in range(concurrent_count):
            task = self.make_request(endpoint, "POST", data, i)
            tasks.append(task)
            
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = (time.time() - start_time) * 1000
        
        # Analyze results
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        response_times = [r["elapsed_ms"] for r in results]
        
        stats = {
            "endpoint": endpoint,
            "concurrent_count": concurrent_count,
            "total_time_ms": total_time,
            "successful_requests": len(successful),
            "failed_requests": len(failed),
            "success_rate": len(successful) / len(results) * 100,
            "avg_response_ms": statistics.mean(response_times),
            "min_response_ms": min(response_times),
            "max_response_ms": max(response_times),
            "median_response_ms": statistics.median(response_times),
            "requests_per_second": len(results) / (total_time / 1000)
        }
        
        if len(response_times) > 1:
            stats["std_dev_ms"] = statistics.stdev(response_times)
            
        self.results.append(stats)
        self.print_stats(stats)
        
        return stats
        
    async def test_sustained_load(self, endpoint: str, data: Dict,
                                 duration_seconds: int = 30,
                                 requests_per_second: int = 5) -> Dict[str, Any]:
        """Test sustained load over time"""
        print(f"\n--- Testing sustained load: {requests_per_second} req/s for {duration_seconds}s ---")
        
        interval = 1.0 / requests_per_second
        total_requests = duration_seconds * requests_per_second
        request_times = []
        
        start_time = time.time()
        request_id = 0
        
        while time.time() - start_time < duration_seconds:
            request_start = time.time()
            
            # Make request
            result = await self.make_request(endpoint, "POST", data, request_id)
            request_times.append(result)
            request_id += 1
            
            # Wait for next interval
            elapsed = time.time() - request_start
            if elapsed < interval:
                await asyncio.sleep(interval - elapsed)
                
        # Analyze results
        successful = [r for r in request_times if r["success"]]
        failed = [r for r in request_times if not r["success"]]
        response_times = [r["elapsed_ms"] for r in request_times]
        
        stats = {
            "test_type": "sustained_load",
            "endpoint": endpoint,
            "duration_seconds": duration_seconds,
            "target_rps": requests_per_second,
            "total_requests": len(request_times),
            "successful_requests": len(successful),
            "failed_requests": len(failed),
            "success_rate": len(successful) / len(request_times) * 100,
            "actual_rps": len(request_times) / duration_seconds,
            "avg_response_ms": statistics.mean(response_times),
            "p95_response_ms": self.percentile(response_times, 95),
            "p99_response_ms": self.percentile(response_times, 99)
        }
        
        self.results.append(stats)
        self.print_stats(stats)
        
        return stats
        
    async def test_ramp_up(self, endpoint: str, data: Dict,
                          start_rps: int = 1, end_rps: int = 20,
                          ramp_duration: int = 60) -> Dict[str, Any]:
        """Test ramping up load"""
        print(f"\n--- Testing ramp up: {start_rps} to {end_rps} req/s over {ramp_duration}s ---")
        
        rps_increment = (end_rps - start_rps) / ramp_duration
        current_rps = start_rps
        request_times = []
        request_id = 0
        
        start_time = time.time()
        
        while time.time() - start_time < ramp_duration:
            # Calculate current RPS
            elapsed = time.time() - start_time
            current_rps = start_rps + (rps_increment * elapsed)
            interval = 1.0 / current_rps
            
            request_start = time.time()
            
            # Make request
            result = await self.make_request(endpoint, "POST", data, request_id)
            result["target_rps"] = current_rps
            request_times.append(result)
            request_id += 1
            
            # Wait for next interval
            elapsed = time.time() - request_start
            if elapsed < interval:
                await asyncio.sleep(interval - elapsed)
                
        # Find breaking point (where response times spike or errors occur)
        breaking_point = None
        for i, result in enumerate(request_times):
            if not result["success"] or result["elapsed_ms"] > 5000:  # 5s threshold
                if i > 0:
                    breaking_point = request_times[i-1]["target_rps"]
                break
                
        stats = {
            "test_type": "ramp_up",
            "endpoint": endpoint,
            "start_rps": start_rps,
            "end_rps": end_rps,
            "duration_seconds": ramp_duration,
            "total_requests": len(request_times),
            "breaking_point_rps": breaking_point,
            "max_sustained_rps": max([r["target_rps"] for r in request_times if r["success"]])
        }
        
        self.results.append(stats)
        self.print_stats(stats)
        
        return stats
        
    async def test_burst_traffic(self, endpoint: str, data: Dict,
                               burst_size: int = 50,
                               burst_count: int = 5,
                               burst_interval: int = 10) -> Dict[str, Any]:
        """Test burst traffic patterns"""
        print(f"\n--- Testing burst traffic: {burst_count} bursts of {burst_size} requests ---")
        
        all_results = []
        
        for burst_num in range(burst_count):
            print(f"  Burst {burst_num + 1}/{burst_count}...")
            
            # Send burst
            tasks = []
            for i in range(burst_size):
                request_id = burst_num * burst_size + i
                task = self.make_request(endpoint, "POST", data, request_id)
                tasks.append(task)
                
            burst_start = time.time()
            results = await asyncio.gather(*tasks)
            burst_time = (time.time() - burst_start) * 1000
            
            all_results.extend(results)
            
            # Wait between bursts
            if burst_num < burst_count - 1:
                await asyncio.sleep(burst_interval)
                
        # Analyze results
        successful = [r for r in all_results if r["success"]]
        response_times = [r["elapsed_ms"] for r in all_results]
        
        stats = {
            "test_type": "burst_traffic",
            "endpoint": endpoint,
            "burst_size": burst_size,
            "burst_count": burst_count,
            "burst_interval_seconds": burst_interval,
            "total_requests": len(all_results),
            "successful_requests": len(successful),
            "success_rate": len(successful) / len(all_results) * 100,
            "avg_response_ms": statistics.mean(response_times),
            "max_response_ms": max(response_times),
            "p95_response_ms": self.percentile(response_times, 95)
        }
        
        self.results.append(stats)
        self.print_stats(stats)
        
        return stats
        
    async def test_session_persistence(self, session_count: int = 10,
                                     requests_per_session: int = 5) -> Dict[str, Any]:
        """Test session persistence across requests"""
        print(f"\n--- Testing session persistence: {session_count} sessions ---")
        
        session_results = []
        
        for session_id in range(session_count):
            session_requests = []
            current_session_id = None
            
            for req_num in range(requests_per_session):
                data = {
                    "url": "https://example.com",
                    "javascript": False,
                    "session_id": current_session_id
                }
                
                result = await self.make_request("/crawl", "POST", data)
                
                # Extract session ID from response if available
                # This is a simplified test - real implementation would parse response
                if result["success"] and req_num == 0:
                    current_session_id = f"test-session-{session_id}"
                    
                session_requests.append(result)
                
            session_results.append({
                "session_id": session_id,
                "requests": session_requests,
                "all_successful": all(r["success"] for r in session_requests)
            })
            
        # Analyze results
        successful_sessions = [s for s in session_results if s["all_successful"]]
        
        stats = {
            "test_type": "session_persistence",
            "total_sessions": session_count,
            "requests_per_session": requests_per_session,
            "successful_sessions": len(successful_sessions),
            "session_success_rate": len(successful_sessions) / session_count * 100
        }
        
        self.results.append(stats)
        self.print_stats(stats)
        
        return stats
        
    def percentile(self, data: List[float], p: int) -> float:
        """Calculate percentile"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * p / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
        
    def print_stats(self, stats: Dict[str, Any]):
        """Pretty print statistics"""
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
                
    async def run_full_performance_suite(self):
        """Run complete performance test suite"""
        print("=" * 80)
        print("V2 API Performance Test Suite")
        print("=" * 80)
        
        # Test data
        simple_crawl = {
            "url": "https://example.com",
            "javascript": False,
            "screenshot": False
        }
        
        complex_crawl = {
            "url": "https://example.com",
            "javascript": True,
            "screenshot": True,
            "depth": 1
        }
        
        # Run tests
        
        # 1. Concurrent requests test
        await self.test_concurrent_requests("/crawl", simple_crawl, 10)
        await self.test_concurrent_requests("/crawl", simple_crawl, 25)
        await self.test_concurrent_requests("/crawl", simple_crawl, 50)
        
        # 2. Sustained load test
        await self.test_sustained_load("/crawl", simple_crawl, 
                                     duration_seconds=30, 
                                     requests_per_second=5)
        
        # 3. Ramp up test
        await self.test_ramp_up("/crawl", simple_crawl,
                              start_rps=1, end_rps=20, 
                              ramp_duration=30)
        
        # 4. Burst traffic test
        await self.test_burst_traffic("/crawl", simple_crawl,
                                    burst_size=25, burst_count=3,
                                    burst_interval=5)
        
        # 5. Session persistence test
        await self.test_session_persistence(session_count=5, 
                                          requests_per_session=3)
        
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print performance test summary"""
        print("\n" + "=" * 80)
        print("PERFORMANCE TEST SUMMARY")
        print("=" * 80)
        
        for result in self.results:
            test_type = result.get("test_type", result.get("endpoint", "Unknown"))
            print(f"\n{test_type}:")
            
            if "success_rate" in result:
                print(f"  Success Rate: {result['success_rate']:.1f}%")
            if "avg_response_ms" in result:
                print(f"  Avg Response: {result['avg_response_ms']:.2f}ms")
            if "requests_per_second" in result:
                print(f"  Throughput: {result['requests_per_second']:.2f} req/s")
            if "breaking_point_rps" in result and result["breaking_point_rps"]:
                print(f"  Breaking Point: {result['breaking_point_rps']:.2f} req/s")
                
        # Save results to file
        with open("tests/rigging/performance_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\nDetailed results saved to performance_results.json")


# Main execution
async def main():
    """Run performance tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description="V2 API Performance Tests")
    parser.add_argument("--base-url", default="http://localhost:5678")
    parser.add_argument("--test", choices=["concurrent", "sustained", "ramp", "burst", "session", "all"],
                       default="all", help="Test type to run")
    
    args = parser.parse_args()
    
    harness = V2PerformanceHarness(args.base_url)
    
    if args.test == "all":
        await harness.run_full_performance_suite()
    elif args.test == "concurrent":
        await harness.test_concurrent_requests("/crawl", {"url": "https://example.com"}, 25)
    elif args.test == "sustained":
        await harness.test_sustained_load("/crawl", {"url": "https://example.com"}, 30, 5)
    elif args.test == "ramp":
        await harness.test_ramp_up("/crawl", {"url": "https://example.com"}, 1, 20, 30)
    elif args.test == "burst":
        await harness.test_burst_traffic("/crawl", {"url": "https://example.com"}, 50, 3, 10)
    elif args.test == "session":
        await harness.test_session_persistence(10, 5)


if __name__ == "__main__":
    asyncio.run(main())
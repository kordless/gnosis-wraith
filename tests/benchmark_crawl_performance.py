#!/usr/bin/env python3
"""
Gnosis Wraith Crawl Performance Benchmark Suite
Tests crawling speed across security/logging companies with various settings.

Configurations tested:
- Markdown: basic vs enhanced 
- Screenshots: off vs top
- OCR: disabled (for speed focus)

Tests ~50 security/logging/analytics companies to get real-world performance data.
"""

import requests
import time
import json
import csv
import statistics
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import argparse
from pathlib import Path

class CrawlBenchmark:
    def __init__(self, base_url: str = "http://localhost:5678"):
        self.base_url = base_url
        self.results = []
        self.session = requests.Session()
        
        # Security/Logging/Analytics Companies - All essentially log analytics
        self.test_companies = {
            # Core Security/SIEM Platforms
            "splunk.com": "SIEM/Log Analytics Leader",
            "elastic.co": "Elasticsearch/Kibana Analytics", 
            "crowdstrike.com": "Endpoint Security/Analytics",
            "sentinelone.com": "AI-Powered Security Analytics",
            "darktrace.com": "AI Cybersecurity Analytics",
            "vectra.ai": "Network Security Analytics",
            "exabeam.com": "Security Analytics Platform",
            "rapid7.com": "Security Analytics/InsightIDR",
            "logrhythm.com": "SIEM/Security Analytics",
            "securonix.com": "Security Analytics/UEBA",
            
            # Cloud Security & Monitoring
            "datadog.com": "Infrastructure Monitoring/Logs",
            "newrelic.com": "Application Performance/Logs",
            "dynatrace.com": "Application Analytics/Monitoring",
            "sumologic.com": "Cloud-Native Analytics",
            "loggly.com": "Log Management/Analytics",
            "papertrail.com": "Log Analytics/Search",
            "graylog.org": "Open Source Log Analytics",
            "fluentd.org": "Log Collection/Analytics",
            
            # Enterprise Security Analytics
            "qualys.com": "Vulnerability/Compliance Analytics",
            "tenable.com": "Vulnerability Analytics/Nessus",
            "rapid7.com": "InsightVM/Security Analytics", 
            "checkpoint.com": "Network Security Analytics",
            "fortinet.com": "FortiAnalyzer/Security Analytics",
            "paloaltonetworks.com": "Next-Gen Firewall Analytics",
            "zscaler.com": "Cloud Security Analytics",
            "proofpoint.com": "Email Security Analytics",
            
            # Threat Intelligence & Analytics
            "recordedfuture.com": "Threat Intelligence Analytics",
            "anomali.com": "Threat Intelligence Platform",
            "threatconnect.com": "Threat Intelligence Analytics",
            "riskiq.com": "Digital Risk Analytics",
            "cybersixgill.com": "Threat Intelligence Analytics",
            "flashpoint.io": "Threat Intelligence/Analytics",
            
            # Cloud & DevOps Analytics
            "honeycomb.io": "Observability/Event Analytics",
            "lightstep.com": "Distributed Tracing/Analytics",
            "jaegertracing.io": "Distributed Tracing Analytics",
            "prometheus.io": "Metrics/Monitoring Analytics",
            "grafana.com": "Metrics Visualization/Analytics",
            "influxdata.com": "Time Series Analytics",
            "wavefront.com": "Cloud Monitoring Analytics",
            
            # Business Intelligence with Security Focus
            "tableau.com": "Data Visualization/Analytics",
            "qlik.com": "Business Intelligence Analytics",
            "sisense.com": "Analytics Platform",
            "looker.com": "Modern BI/Analytics",
            "domo.com": "Cloud Analytics Platform",
            "databricks.com": "Analytics/ML Platform",
            
            # Specialized Security Analytics
            "cylance.com": "AI Endpoint Security Analytics",
            "carbon-black.com": "Endpoint Security Analytics",
            "fireeye.com": "Advanced Threat Analytics",
            "mcafee.com": "Enterprise Security Analytics",
            "symantec.com": "Endpoint Security Analytics",
            "trendmicro.com": "Security Analytics Platform",
            "kaspersky.com": "Security Analytics/Threat Intel",
            
            # Additional Log/Analytics Platforms
            "atlassian.com": "DevOps/Incident Analytics",
            "pagerduty.com": "Incident Response Analytics", 
            "opsgenie.com": "Incident Management Analytics",
            "victorops.com": "Incident Response Analytics"
        }
    
    def get_test_configurations(self) -> List[Dict]:
        """Define all test configuration combinations."""
        return [
            {
                "name": "baseline_no_extras",
                "description": "Basic markdown, no screenshot, no OCR",
                "params": {
                    "markdown_extraction": "basic",
                    "take_screenshot": False,
                }
            },
            {
                "name": "enhanced_markdown_only", 
                "description": "Enhanced markdown, no screenshot, no OCR",
                "params": {
                    "markdown_extraction": "enhanced", 
                    "take_screenshot": False,
                }
            },
            {
                "name": "basic_with_screenshot",
                "description": "Basic markdown, top screenshot, no OCR", 
                "params": {
                    "markdown_extraction": "basic",
                    "take_screenshot": True,
                    "screenshot_mode": "top",
                }
            },
            {
                "name": "enhanced_with_screenshot",
                "description": "Enhanced markdown, top screenshot, no OCR",
                "params": {
                    "markdown_extraction": "enhanced",
                    "take_screenshot": True, 
                    "screenshot_mode": "top",
                }
            }
        ]
    
    def crawl_url(self, url: str, config: Dict, timeout: int = 60) -> Dict:
        """Crawl a single URL with given configuration and measure performance."""
        full_url = f"https://{url}" if not url.startswith('http') else url
        
        crawl_params = {
            "url": full_url,
            "title": f"Benchmark Test - {url}",
            **config["params"]
        }
        
        print(f"  Crawling {url} with {config['name']}...")
        
        start_time = time.time()
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/crawl",
                json=crawl_params,
                timeout=timeout
            )
            
            end_time = time.time()
            crawl_time = end_time - start_time
            
            if response.status_code == 200:
                result_data = response.json()
                
                # Extract key metrics
                # Extract key metrics - try multiple possible content fields
                # The API can return content in various fields depending on response format
                markdown_content = (
                    result_data.get('markdown_content', '') or
                    result_data.get('extracted_text', '') or
                    (result_data.get('results', [{}])[0].get('extracted_text', '') if result_data.get('results') else '') or
                    ''
                )
                content_length = len(markdown_content)
                screenshot_taken = bool(result_data.get('screenshot'))
                success = result_data.get('success', False)
                
                return {
                    "url": url,
                    "config_name": config["name"],
                    "success": success,
                    "crawl_time": crawl_time,
                    "content_length": content_length,
                    "screenshot_taken": screenshot_taken,
                    "status_code": response.status_code,
                    "error": None,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "url": url,
                    "config_name": config["name"], 
                    "success": False,
                    "crawl_time": time.time() - start_time,
                    "content_length": 0,
                    "screenshot_taken": False,
                    "status_code": response.status_code,
                    "error": f"HTTP {response.status_code}",
                    "timestamp": datetime.now().isoformat()
                }
                
        except requests.exceptions.Timeout:
            return {
                "url": url,
                "config_name": config["name"],
                "success": False, 
                "crawl_time": timeout,
                "content_length": 0,
                "screenshot_taken": False,
                "status_code": 0,
                "error": "Timeout",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "url": url,
                "config_name": config["name"],
                "success": False,
                "crawl_time": time.time() - start_time,
                "content_length": 0, 
                "screenshot_taken": False,
                "status_code": 0,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def run_benchmark(self, max_companies: int = 50, delay_between_requests: float = 1.0):
        """Run the complete benchmark suite."""
        configurations = self.get_test_configurations()
        companies = list(self.test_companies.items())[:max_companies]
        
        print(f"🚀 Starting Gnosis Wraith Performance Benchmark")
        print(f"📊 Testing {len(companies)} companies with {len(configurations)} configurations")
        print(f"⚡ Total requests: {len(companies) * len(configurations)}")
        print(f"⏱️  Estimated time: {(len(companies) * len(configurations) * 10) / 60:.1f} minutes")
        print()
        
        total_requests = len(companies) * len(configurations)
        current_request = 0
        
        for config in configurations:
            print(f"\n🔧 Configuration: {config['name']} - {config['description']}")
            print("=" * 60)
            
            for company_url, description in companies:
                current_request += 1
                progress = (current_request / total_requests) * 100
                
                print(f"[{current_request}/{total_requests}] ({progress:.1f}%) {company_url}")
                
                result = self.crawl_url(company_url, config)
                self.results.append(result)
                
                if result["success"]:
                    print(f"    ✅ {result['crawl_time']:.2f}s | {result['content_length']:,} chars")
                else:
                    print(f"    ❌ {result['crawl_time']:.2f}s | Error: {result['error']}")
                
                # Delay between requests to be respectful
                if delay_between_requests > 0:
                    time.sleep(delay_between_requests)
        
        print(f"\n🎯 Benchmark completed! {len(self.results)} total requests processed.")
    
    def analyze_results(self) -> Dict:
        """Analyze benchmark results and generate performance statistics."""
        if not self.results:
            return {"error": "No results to analyze"}
        
        analysis = {
            "summary": {
                "total_requests": len(self.results),
                "successful_requests": len([r for r in self.results if r["success"]]),
                "failed_requests": len([r for r in self.results if not r["success"]]),
                "success_rate": len([r for r in self.results if r["success"]]) / len(self.results) * 100
            },
            "performance_by_config": {},
            "fastest_sites": [],
            "slowest_sites": [],
            "error_analysis": {}
        }
        
        # Analyze performance by configuration
        for config in self.get_test_configurations():
            config_results = [r for r in self.results if r["config_name"] == config["name"]]
            successful_results = [r for r in config_results if r["success"]]
            
            if successful_results:
                times = [r["crawl_time"] for r in successful_results]
                content_lengths = [r["content_length"] for r in successful_results]
                
                analysis["performance_by_config"][config["name"]] = {
                    "description": config["description"],
                    "successful_crawls": len(successful_results),
                    "failed_crawls": len(config_results) - len(successful_results),
                    "success_rate": len(successful_results) / len(config_results) * 100,
                    "avg_time": statistics.mean(times),
                    "median_time": statistics.median(times),
                    "min_time": min(times),
                    "max_time": max(times),
                    "std_dev_time": statistics.stdev(times) if len(times) > 1 else 0,
                    "avg_content_length": statistics.mean(content_lengths),
                    "total_data_crawled": sum(content_lengths)
                }
        
        # Find fastest and slowest sites
        successful_results = [r for r in self.results if r["success"]]
        if successful_results:
            sorted_by_time = sorted(successful_results, key=lambda x: x["crawl_time"])
            analysis["fastest_sites"] = sorted_by_time[:10]
            analysis["slowest_sites"] = sorted_by_time[-10:]
        
        # Error analysis
        failed_results = [r for r in self.results if not r["success"]]
        error_counts = {}
        for result in failed_results:
            error = result["error"] or "Unknown"
            error_counts[error] = error_counts.get(error, 0) + 1
        analysis["error_analysis"] = error_counts
        
        return analysis
    
    def save_results(self, output_dir: str = "benchmark_results"):
        """Save benchmark results to files."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save raw results as JSON
        json_file = output_path / f"benchmark_results_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Save results as CSV
        csv_file = output_path / f"benchmark_results_{timestamp}.csv"
        if self.results:
            fieldnames = self.results[0].keys()
            with open(csv_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.results)
        
        # Save analysis report
        analysis = self.analyze_results()
        report_file = output_path / f"benchmark_analysis_{timestamp}.txt"
        with open(report_file, 'w') as f:
            f.write(self.generate_report(analysis))
        
        print(f"\n📁 Results saved to {output_dir}/")
        print(f"   📄 Raw data: {json_file.name}")
        print(f"   📊 CSV data: {csv_file.name}")
        print(f"   📋 Analysis: {report_file.name}")
    
    def generate_report(self, analysis: Dict) -> str:
        """Generate a human-readable performance report."""
        if "error" in analysis:
            return f"Error generating report: {analysis['error']}"
        
        report = []
        report.append("🚀 GNOSIS WRAITH PERFORMANCE BENCHMARK REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary
        summary = analysis["summary"]
        report.append("📊 OVERALL SUMMARY")
        report.append("-" * 20)
        report.append(f"Total Requests: {summary['total_requests']}")
        report.append(f"Successful: {summary['successful_requests']} ({summary['success_rate']:.1f}%)")
        report.append(f"Failed: {summary['failed_requests']}")
        report.append("")
        
        # Performance by configuration
        report.append("⚡ PERFORMANCE BY CONFIGURATION")
        report.append("-" * 35)
        
        config_performances = analysis["performance_by_config"]
        for config_name, perf in config_performances.items():
            report.append(f"\n🔧 {config_name.upper()}")
            report.append(f"   Description: {perf['description']}")
            report.append(f"   Success Rate: {perf['success_rate']:.1f}% ({perf['successful_crawls']}/{perf['successful_crawls'] + perf['failed_crawls']})")
            report.append(f"   Average Time: {perf['avg_time']:.2f}s")
            report.append(f"   Median Time: {perf['median_time']:.2f}s")
            report.append(f"   Time Range: {perf['min_time']:.2f}s - {perf['max_time']:.2f}s")
            report.append(f"   Std Deviation: {perf['std_dev_time']:.2f}s")
            report.append(f"   Avg Content: {perf['avg_content_length']:,} characters")
            report.append(f"   Total Data: {perf['total_data_crawled']:,} characters")
        
        # Speed comparison
        report.append("\n🏎️  SPEED COMPARISON")
        report.append("-" * 20)
        if config_performances:
            sorted_configs = sorted(
                config_performances.items(),
                key=lambda x: x[1]['avg_time']
            )
            
            fastest = sorted_configs[0]
            slowest = sorted_configs[-1]
            
            report.append(f"Fastest Config: {fastest[0]} ({fastest[1]['avg_time']:.2f}s avg)")
            report.append(f"Slowest Config: {slowest[0]} ({slowest[1]['avg_time']:.2f}s avg)")
            
            if len(sorted_configs) > 1:
                speed_diff = slowest[1]['avg_time'] - fastest[1]['avg_time']
                speed_ratio = slowest[1]['avg_time'] / fastest[1]['avg_time']
                report.append(f"Speed Difference: {speed_diff:.2f}s ({speed_ratio:.1f}x slower)")
        
        # Fastest and slowest sites
        if analysis["fastest_sites"]:
            report.append("\n🏆 TOP 10 FASTEST SITES")
            report.append("-" * 25)
            for i, site in enumerate(analysis["fastest_sites"], 1):
                report.append(f"{i:2d}. {site['url']:<25} {site['crawl_time']:.2f}s ({site['config_name']})")
        
        if analysis["slowest_sites"]:
            report.append("\n🐌 TOP 10 SLOWEST SITES")
            report.append("-" * 25)
            for i, site in enumerate(analysis["slowest_sites"], 1):
                report.append(f"{i:2d}. {site['url']:<25} {site['crawl_time']:.2f}s ({site['config_name']})")
        
        # Error analysis
        if analysis["error_analysis"]:
            report.append("\n❌ ERROR ANALYSIS")
            report.append("-" * 15)
            for error, count in analysis["error_analysis"].items():
                report.append(f"{error}: {count} occurrences")
        
        # Performance insights
        report.append("\n💡 PERFORMANCE INSIGHTS")
        report.append("-" * 22)
        
        if config_performances:
            # Compare screenshot vs no screenshot
            no_screenshot_configs = [k for k, v in config_performances.items() if "no screenshot" in v["description"]]
            screenshot_configs = [k for k, v in config_performances.items() if "screenshot" in v["description"] and "no screenshot" not in v["description"]]
            
            if no_screenshot_configs and screenshot_configs:
                no_ss_avg = statistics.mean([config_performances[k]["avg_time"] for k in no_screenshot_configs])
                ss_avg = statistics.mean([config_performances[k]["avg_time"] for k in screenshot_configs])
                
                ss_overhead = ss_avg - no_ss_avg
                ss_ratio = ss_avg / no_ss_avg
                
                report.append(f"Screenshot Impact:")
                report.append(f"  No Screenshot Avg: {no_ss_avg:.2f}s")
                report.append(f"  With Screenshot Avg: {ss_avg:.2f}s")
                report.append(f"  Screenshot Overhead: +{ss_overhead:.2f}s ({ss_ratio:.1f}x slower)")
            
            # Compare markdown types
            basic_configs = [k for k, v in config_performances.items() if "Basic markdown" in v["description"]]
            enhanced_configs = [k for k, v in config_performances.items() if "Enhanced markdown" in v["description"]]
            
            if basic_configs and enhanced_configs:
                basic_avg = statistics.mean([config_performances[k]["avg_time"] for k in basic_configs])
                enhanced_avg = statistics.mean([config_performances[k]["avg_time"] for k in enhanced_configs])
                
                md_overhead = enhanced_avg - basic_avg
                md_ratio = enhanced_avg / basic_avg if basic_avg > 0 else 1
                
                report.append(f"\nMarkdown Processing Impact:")
                report.append(f"  Basic Markdown Avg: {basic_avg:.2f}s")
                report.append(f"  Enhanced Markdown Avg: {enhanced_avg:.2f}s")
                report.append(f"  Enhanced Overhead: +{md_overhead:.2f}s ({md_ratio:.1f}x slower)")
        
        report.append("")
        report.append("🎯 Benchmark completed successfully!")
        
        return "\n".join(report)
    
    def print_live_results(self):
        """Print results in real-time during benchmark."""
        if not self.results:
            return
        
        analysis = self.analyze_results()
        
        print("\n" + "="*60)
        print("🔥 LIVE PERFORMANCE SUMMARY")
        print("="*60)
        
        if "performance_by_config" in analysis:
            for config_name, perf in analysis["performance_by_config"].items():
                if perf["successful_crawls"] > 0:
                    print(f"{config_name:25} | {perf['avg_time']:6.2f}s avg | {perf['success_rate']:5.1f}% success")

def main():
    parser = argparse.ArgumentParser(description="Gnosis Wraith Performance Benchmark")
    parser.add_argument("--companies", type=int, default=50, help="Max number of companies to test (default: 50)")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests in seconds (default: 1.0)")
    parser.add_argument("--url", default="http://localhost:5678", help="Gnosis Wraith server URL")
    parser.add_argument("--output", default="benchmark_results", help="Output directory for results")
    parser.add_argument("--quick", action="store_true", help="Quick test with 10 companies")
    
    args = parser.parse_args()
    
    if args.quick:
        args.companies = 10
        args.delay = 0.5
        print("🏃 Quick benchmark mode: 10 companies, 0.5s delay")
    
    benchmark = CrawlBenchmark(args.url)
    
    try:
        benchmark.run_benchmark(args.companies, args.delay)
        benchmark.print_live_results()
        benchmark.save_results(args.output)
        
        analysis = benchmark.analyze_results()
        print("\n" + benchmark.generate_report(analysis))
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Benchmark interrupted by user")
        if benchmark.results:
            print("💾 Saving partial results...")
            benchmark.save_results(args.output)
    except Exception as e:
        print(f"\n❌ Benchmark failed: {str(e)}")
        if benchmark.results:
            print("💾 Saving partial results...")
            benchmark.save_results(args.output)

if __name__ == "__main__":
    main()

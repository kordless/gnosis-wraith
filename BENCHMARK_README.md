# Gnosis Wraith Performance Benchmark Suite

A comprehensive benchmarking system to measure crawling performance across security, logging, and analytics companies with various configuration settings.

## 🎯 Purpose

Tests real-world crawling performance to understand the speed impact of:
- **Markdown Processing**: Basic vs Enhanced markdown extraction
- **Screenshot Capture**: Off vs Top viewport screenshots  
- **OCR Processing**: Disabled for speed-focused testing

## 🏢 Test Companies

~50 security/logging/analytics companies (they're all essentially log analytics):

### Core Security/SIEM Platforms
- Splunk, Elastic, CrowdStrike, SentinelOne, Darktrace, Vectra AI
- Exabeam, Rapid7, LogRhythm, Securonix

### Cloud Security & Monitoring  
- Datadog, New Relic, Dynatrace, Sumo Logic, Loggly
- Graylog, Fluentd, Papertrail

### Enterprise Security Analytics
- Qualys, Tenable, Check Point, Fortinet, Palo Alto Networks
- Zscaler, Proofpoint

### Threat Intelligence & Analytics
- Recorded Future, Anomali, ThreatConnect, RiskIQ
- CyberSixgill, Flashpoint

### Cloud & DevOps Analytics
- Honeycomb, Lightstep, Jaeger, Prometheus, Grafana
- InfluxData, Wavefront

### Business Intelligence with Security Focus
- Tableau, Qlik, Sisense, Looker, Domo, Databricks

## ⚙️ Test Configurations

1. **baseline_no_extras**
   - Basic markdown, no screenshot, no OCR
   - Fastest possible crawling

2. **enhanced_markdown_only** 
   - Enhanced markdown, no screenshot, no OCR
   - Tests markdown processing overhead

3. **basic_with_screenshot**
   - Basic markdown, top screenshot, no OCR
   - Tests screenshot capture overhead

4. **enhanced_with_screenshot**
   - Enhanced markdown, top screenshot, no OCR
   - Full-featured crawling (minus OCR)

## 🚀 Quick Start

### Windows (Recommended)
```bash
# Run the interactive batch file
run_benchmark.bat

# Choose from:
# 1. Full Benchmark (50 companies) - ~30 minutes
# 2. Quick Test (10 companies) - ~5 minutes  
# 3. Lightning Test (5 companies) - ~2 minutes
# 4. Custom configuration
```

### Python Direct
```bash
# Full benchmark
python benchmark_crawl_performance.py

# Quick test
python benchmark_crawl_performance.py --quick

# Custom options
python benchmark_crawl_performance.py --companies 20 --delay 0.5
```

## 📊 Output

### Files Generated
- `benchmark_results_YYYYMMDD_HHMMSS.json` - Raw results data
- `benchmark_results_YYYYMMDD_HHMMSS.csv` - Spreadsheet-friendly data  
- `benchmark_analysis_YYYYMMDD_HHMMSS.txt` - Human-readable report

### Report Includes
- **Overall Summary**: Success rates, total requests
- **Performance by Configuration**: Average times, median, std deviation
- **Speed Comparison**: Fastest vs slowest configs with ratios
- **Top 10 Fastest/Slowest Sites**: Individual site performance
- **Error Analysis**: Failed requests breakdown
- **Performance Insights**: Screenshot vs no-screenshot impact, markdown overhead

## 🔧 Command Line Options

```bash
python benchmark_crawl_performance.py [options]

Options:
  --companies N     Max companies to test (default: 50)
  --delay SECONDS   Delay between requests (default: 1.0) 
  --url URL         Gnosis Wraith server URL (default: http://localhost:5678)
  --output DIR      Output directory (default: benchmark_results)
  --quick           Quick test: 10 companies, 0.5s delay
```

## 📈 Expected Results

Based on configuration complexity:

1. **baseline_no_extras**: ~2-5 seconds per site
2. **enhanced_markdown_only**: ~3-6 seconds per site (+markdown overhead)
3. **basic_with_screenshot**: ~4-8 seconds per site (+screenshot overhead)  
4. **enhanced_with_screenshot**: ~5-10 seconds per site (+both overheads)

### Performance Factors
- **Screenshot Capture**: Typically adds 1-3 seconds
- **Enhanced Markdown**: Typically adds 0.5-2 seconds
- **Site Complexity**: Security dashboards often have heavy JavaScript
- **Network Latency**: Varies by geographic location

## 🏎️ Performance Insights

### Screenshot Impact
- **Overhead**: Usually 1.5-3x slower than no-screenshot
- **Value**: Essential for visual dashboards and security interfaces
- **Mode**: "top" captures viewport (faster than full-page)

### Markdown Processing Impact  
- **Basic**: Fast text extraction
- **Enhanced**: Better structure, links, formatting (+20-50% time)
- **Value**: Enhanced better for analysis, basic better for speed

### Security/Analytics Sites Characteristics
- **Heavy JavaScript**: Many sites require full rendering
- **Authentication Pages**: Often redirect to login (expected)
- **Dashboard Complexity**: Varies significantly by vendor
- **CDN Usage**: Global CDNs can improve speed

## 🔍 Troubleshooting

### Common Issues
1. **Connection Refused**: Ensure Gnosis Wraith server is running on localhost:5678
2. **Timeouts**: Increase delay with `--delay 2.0` for slower connections
3. **High Failure Rate**: Some sites block automated requests (expected)
4. **Memory Usage**: Large benchmarks may use significant RAM

### Server Requirements
- Gnosis Wraith server running locally
- Sufficient disk space for screenshots (if enabled)
- Stable internet connection
- 4GB+ RAM recommended for large benchmarks

## 📋 Example Output

```
🚀 GNOSIS WRAITH PERFORMANCE BENCHMARK REPORT
============================================================
Generated: 2025-05-30 23:45:00

📊 OVERALL SUMMARY
--------------------
Total Requests: 200
Successful: 168 (84.0%)
Failed: 32

⚡ PERFORMANCE BY CONFIGURATION
-----------------------------------

🔧 BASELINE_NO_EXTRAS
   Description: Basic markdown, no screenshot, no OCR
   Success Rate: 87.5% (42/48)
   Average Time: 3.24s
   Median Time: 2.89s
   Time Range: 1.45s - 8.23s
   Std Deviation: 1.45s

🔧 ENHANCED_WITH_SCREENSHOT  
   Description: Enhanced markdown, top screenshot, no OCR
   Success Rate: 81.2% (39/48)
   Average Time: 6.78s
   Median Time: 6.12s
   Time Range: 3.21s - 15.67s
   Std Deviation: 2.34s

🏎️ SPEED COMPARISON
--------------------
Fastest Config: baseline_no_extras (3.24s avg)
Slowest Config: enhanced_with_screenshot (6.78s avg)  
Speed Difference: 3.54s (2.1x slower)

💡 PERFORMANCE INSIGHTS
------------------------
Screenshot Impact:
  No Screenshot Avg: 3.65s
  With Screenshot Avg: 6.42s
  Screenshot Overhead: +2.77s (1.8x slower)

Markdown Processing Impact:
  Basic Markdown Avg: 4.12s
  Enhanced Markdown Avg: 5.23s
  Enhanced Overhead: +1.11s (1.3x slower)
```

## 🎯 Use Cases

- **Performance Optimization**: Identify bottlenecks in crawling pipeline
- **Configuration Selection**: Choose optimal settings for use case
- **Infrastructure Planning**: Estimate crawling capacity and timing
- **Regression Testing**: Monitor performance changes over time
- **Competitive Analysis**: Compare against other crawling solutions

---

*Part of the Gnosis ecosystem - intelligent web crawling and analytics*

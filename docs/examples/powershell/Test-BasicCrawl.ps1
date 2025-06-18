# Test Basic Crawling with Gnosis Wraith
# This script demonstrates basic web crawling functionality

# Load helper functions
. "$env:USERPROFILE\.gnosis-wraith\GnosisHelper.ps1"

Write-Host "`nGnosis Wraith Basic Crawl Tests" -ForegroundColor Cyan
Write-Host "===============================" -ForegroundColor Cyan

# Test 1: Simple crawl
Write-Host "`n1. Simple Crawl Test" -ForegroundColor Yellow
$result = Invoke-GnosisApi -Endpoint "/api/crawl" -Body @{
    url = "https://example.com"
    markdown_extraction = "enhanced"
    take_screenshot = $true
    screenshot_mode = "top"
}

if ($result.success) {
    Write-Host "✓ Crawl successful!" -ForegroundColor Green
    Write-Host "  Title: $($result.results[0].title)" -ForegroundColor Gray
    Write-Host "  Content length: $($result.results[0].markdown_content.Length) chars" -ForegroundColor Gray
    if ($result.results[0].screenshot) {
        Write-Host "  Screenshot: $($result.results[0].screenshot)" -ForegroundColor Gray
    }
} else {
    Write-Host "✗ Crawl failed: $($result.error)" -ForegroundColor Red
}

# Test 2: Multiple URLs
Write-Host "`n2. Multiple URLs Test" -ForegroundColor Yellow
$result = Invoke-GnosisApi -Endpoint "/api/crawl" -Body @{
    urls = @(
        "https://example.com",
        "https://httpbin.org/html"
    )
    markdown_extraction = "basic"
    response_format = "minimal"
}

if ($result.success) {
    Write-Host "✓ Multi-crawl successful!" -ForegroundColor Green
    foreach ($item in $result.results) {
        Write-Host "  - $($item.url): $($item.title)" -ForegroundColor Gray
    }
} else {
    Write-Host "✗ Multi-crawl failed: $($result.error)" -ForegroundColor Red
}

# Test 3: JavaScript-enabled crawl
Write-Host "`n3. JavaScript-Enabled Crawl" -ForegroundColor Yellow
$result = Invoke-GnosisApi -Endpoint "/api/crawl" -Body @{
    url = "https://news.ycombinator.com"
    javascript_enabled = $true
    javascript_settle_time = 2000
    markdown_extraction = "enhanced"
}

if ($result.success) {
    Write-Host "✓ JS crawl successful!" -ForegroundColor Green
    Write-Host "  Found content: $($result.results[0].markdown_content.Substring(0, [Math]::Min(100, $result.results[0].markdown_content.Length)))..." -ForegroundColor Gray
} else {
    Write-Host "✗ JS crawl failed: $($result.error)" -ForegroundColor Red
}

# Test 4: Custom report name
Write-Host "`n4. Custom Report Name Test" -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$result = Invoke-GnosisApi -Endpoint "/api/crawl" -Body @{
    url = "https://github.com/trending"
    title = "GitHub Trending - $timestamp"
    markdown_extraction = "enhanced"
    take_screenshot = $true
}

if ($result.success) {
    Write-Host "✓ Custom report created!" -ForegroundColor Green
    if ($result.report_path) {
        Write-Host "  Report: $($result.report_path)" -ForegroundColor Gray
    }
} else {
    Write-Host "✗ Custom report failed: $($result.error)" -ForegroundColor Red
}

# Test 5: Response formats
Write-Host "`n5. Response Format Test" -ForegroundColor Yellow
$formats = @("full", "content_only", "minimal")

foreach ($format in $formats) {
    Write-Host "  Testing format: $format" -ForegroundColor Gray
    $result = Invoke-GnosisApi -Endpoint "/api/crawl" -Body @{
        url = "https://example.com"
        response_format = $format
    }
    
    if ($result.success) {
        $size = ($result | ConvertTo-Json -Compress).Length
        Write-Host "    ✓ Response size: $size bytes" -ForegroundColor Green
    }
}

Write-Host "`nBasic crawl tests completed!" -ForegroundColor Cyan
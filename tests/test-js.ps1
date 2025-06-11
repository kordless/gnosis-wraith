#!/usr/bin/env pwsh
# Test JavaScript execution features

Write-Host "🧪 Testing JavaScript Execution Features" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check if Python is available
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Run the quick validator tests (no server required)
Write-Host "`n📋 Running validator tests..." -ForegroundColor Yellow
python tests/test_js_quick.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Validator tests passed!" -ForegroundColor Green
} else {
    Write-Host "`n❌ Validator tests failed!" -ForegroundColor Red
}

# Check if server is running
Write-Host "`n🔍 Checking if server is running..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5678/api/v2/health" -Method GET -ErrorAction Stop
    Write-Host "✅ Server is running" -ForegroundColor Green
    
    # Run full API tests if server is up
    Write-Host "`n📋 Running API endpoint tests..." -ForegroundColor Yellow
    
    # Set API token if available
    if ($env:GNOSIS_API_TOKEN) {
        Write-Host "🔑 Using API token from environment" -ForegroundColor Cyan
    } else {
        Write-Host "⚠️  No API token found - some tests may fail" -ForegroundColor Yellow
    }
    
    python tests/test_javascript_execution.py
    
} catch {
    Write-Host "⚠️  Server not running at http://localhost:5678" -ForegroundColor Yellow
    Write-Host "   Start the server with: python app.py" -ForegroundColor Gray
    Write-Host "   Or run in Docker with: docker-compose up" -ForegroundColor Gray
}

Write-Host "`n✅ Test suite completed!" -ForegroundColor Green
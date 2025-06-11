# Debug JavaScript API - Simple test with error handling
param(
    [string]$Token = $env:GNOSIS_API_TOKEN
)

if (-not $Token) {
    Write-Host "Error: No token provided!" -ForegroundColor Red
    exit 1
}

Write-Host "🔍 Debugging JavaScript API" -ForegroundColor Cyan
Write-Host "Token: $($Token.Substring(0,10))..." -ForegroundColor Gray
Write-Host "URL: http://localhost:5678" -ForegroundColor Gray

# Test 1: Simple health check
Write-Host "`n📋 Test 1: API Health Check" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5678/api/v2/health" -Method GET
    Write-Host "✅ API is responding! Status: $($response.StatusCode)" -ForegroundColor Green
    $response.Content | ConvertFrom-Json | ConvertTo-Json
} catch {
    Write-Host "❌ API health check failed: $_" -ForegroundColor Red
    Write-Host "Make sure the server is running!" -ForegroundColor Yellow
    exit 1
}

# Test 2: Simple validation test
Write-Host "`n📋 Test 2: Validate Endpoint" -ForegroundColor Yellow
$headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type" = "application/json"
}

$body = @{
    javascript = "return 123;"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "http://localhost:5678/api/v2/validate" `
        -Method POST -Headers $headers -Body $body -ErrorAction Stop
    
    Write-Host "✅ Validation response:" -ForegroundColor Green
    $response | ConvertTo-Json
} catch {
    Write-Host "❌ Validation failed:" -ForegroundColor Red
    Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Yellow
    Write-Host "Error: $_" -ForegroundColor Yellow
    
    # Try to get more error details
    if ($_.ErrorDetails.Message) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
    }
}

# Test 3: Simple execute without extras
Write-Host "`n📋 Test 3: Simple Execute" -ForegroundColor Yellow
$body = @{
    url = "https://example.com"
    javascript = "return document.title;"
} | ConvertTo-Json

try {
    Write-Host "Sending request..." -ForegroundColor Gray
    $response = Invoke-RestMethod -Uri "http://localhost:5678/api/v2/execute" `
        -Method POST -Headers $headers -Body $body -ErrorAction Stop
    
    Write-Host "✅ Execute response:" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "❌ Execute failed:" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Yellow
    
    if ($_.ErrorDetails.Message) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
    }
}

# Test 4: Execute with markdown
Write-Host "`n📋 Test 4: Execute with Markdown Extraction" -ForegroundColor Yellow
$body = @{
    url = "https://example.com"
    javascript = "document.body.innerHTML += '<h2>Added by JS</h2>'; return true;"
    extract_markdown = $true
} | ConvertTo-Json

try {
    Write-Host "Sending request with markdown extraction..." -ForegroundColor Gray
    $response = Invoke-RestMethod -Uri "http://localhost:5678/api/v2/execute" `
        -Method POST -Headers $headers -Body $body -ErrorAction Stop -Verbose
    
    Write-Host "✅ Response received!" -ForegroundColor Green
    
    if ($response.success) {
        Write-Host "  Success: $($response.success)" -ForegroundColor Green
        Write-Host "  Result: $($response.result)" -ForegroundColor Gray
        
        if ($response.markdown) {
            Write-Host "  Markdown length: $($response.markdown.length) chars" -ForegroundColor Gray
            Write-Host "  First 200 chars:" -ForegroundColor Gray
            Write-Host ($response.markdown.content.Substring(0, [Math]::Min(200, $response.markdown.content.Length))) -ForegroundColor White
        } else {
            Write-Host "  No markdown in response" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  Success: false" -ForegroundColor Red
        Write-Host "  Error: $($response.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Request failed:" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Yellow
    Write-Host "Exception type: $($_.Exception.GetType().FullName)" -ForegroundColor Yellow
    
    # Try to read the response stream
    if ($_.Exception.Response) {
        $stream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($stream)
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response body: $responseBody" -ForegroundColor Yellow
    }
}
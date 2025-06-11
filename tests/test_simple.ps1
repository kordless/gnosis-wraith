# Simple JavaScript Execution Test
# Debug the exact response structure

param(
    [string]$Token = $env:GNOSIS_API_TOKEN
)

if (-not $Token) {
    Write-Host "Error: No API token provided!" -ForegroundColor Red
    exit 1
}

$headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type" = "application/json"
}

# Test 1: Simple execution to see response structure
Write-Host "📋 Testing Simple JavaScript Execution" -ForegroundColor Cyan
$body = @{
    url = "https://example.com"
    javascript = "return { message: 'Hello from JavaScript!', linkCount: document.querySelectorAll('a').length };"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "http://localhost:5678/api/v2/execute" `
        -Method POST -Headers $headers -Body $body
    
    Write-Host "`nFull Response:" -ForegroundColor Yellow
    $response | ConvertTo-Json -Depth 10
    
    Write-Host "`nParsed Values:" -ForegroundColor Green
    Write-Host "Success: $($response.success)" -ForegroundColor Gray
    Write-Host "URL: $($response.url)" -ForegroundColor Gray
    Write-Host "Result Type: $($response.result.GetType().Name)" -ForegroundColor Gray
    Write-Host "Result: $($response.result | ConvertTo-Json)" -ForegroundColor Gray
    
    if ($response.execution_time) {
        Write-Host "Execution Time: $($response.execution_time)ms" -ForegroundColor Gray
    }
    
} catch {
    Write-Host "❌ Request failed: $_" -ForegroundColor Red
}

# Test 2: Extract specific data from Hacker News
Write-Host "`n📋 Testing Hacker News Data Extraction" -ForegroundColor Cyan
$body = @{
    url = "https://news.ycombinator.com"
    javascript = @'
// Get first 3 story titles
const titles = Array.from(document.querySelectorAll('.titleline > a'))
    .slice(0, 3)
    .map(link => link.textContent);
return titles;
'@
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "http://localhost:5678/api/v2/execute" `
        -Method POST -Headers $headers -Body $body
    
    Write-Host "`nResponse Structure:" -ForegroundColor Yellow
    Write-Host "Success: $($response.success)" -ForegroundColor Gray
    Write-Host "Result is array: $($response.result -is [array])" -ForegroundColor Gray
    
    if ($response.result -is [array]) {
        Write-Host "`nFirst 3 HN Stories:" -ForegroundColor Green
        $i = 1
        foreach ($title in $response.result) {
            Write-Host "$i. $title" -ForegroundColor White
            $i++
        }
    } else {
        Write-Host "Result: $($response.result | ConvertTo-Json)" -ForegroundColor Gray
    }
    
} catch {
    Write-Host "❌ Request failed: $_" -ForegroundColor Red
}
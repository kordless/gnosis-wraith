# Debug JavaScript Execution Response
# This script helps understand the exact response structure

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

Write-Host "🔍 Debugging JavaScript Execution Response Structure" -ForegroundColor Cyan
Write-Host ("=" * 50) -ForegroundColor Cyan

# Test 1: Return a simple string
Write-Host "`n📋 Test 1: Simple String Return" -ForegroundColor Yellow
$body = @{
    url = "https://example.com"
    javascript = "return 'Hello World';"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:5678/api/v2/execute" `
    -Method POST -Headers $headers -Body $body

Write-Host "Response type: $($response.GetType().Name)" -ForegroundColor Gray
Write-Host "Response.result: $($response.result)" -ForegroundColor Green
Write-Host "Response.result type: $($response.result.GetType().Name)" -ForegroundColor Gray

# Test 2: Return a number
Write-Host "`n📋 Test 2: Number Return" -ForegroundColor Yellow
$body = @{
    url = "https://example.com"
    javascript = "return document.querySelectorAll('a').length;"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:5678/api/v2/execute" `
    -Method POST -Headers $headers -Body $body

Write-Host "Response.result: $($response.result)" -ForegroundColor Green
Write-Host "Response.result type: $($response.result.GetType().Name)" -ForegroundColor Gray

# Test 3: Return an array
Write-Host "`n📋 Test 3: Array Return" -ForegroundColor Yellow
$body = @{
    url = "https://example.com"
    javascript = "return ['item1', 'item2', 'item3'];"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:5678/api/v2/execute" `
    -Method POST -Headers $headers -Body $body

Write-Host "Response.result: $($response.result)" -ForegroundColor Green
Write-Host "Response.result type: $($response.result.GetType().Name)" -ForegroundColor Gray
Write-Host "Is array: $($response.result -is [array])" -ForegroundColor Gray
if ($response.result -is [array]) {
    Write-Host "Array items:" -ForegroundColor Gray
    foreach ($item in $response.result) {
        Write-Host "  - $item" -ForegroundColor White
    }
}

# Test 4: Return an object
Write-Host "`n📋 Test 4: Object Return" -ForegroundColor Yellow
$body = @{
    url = "https://example.com"
    javascript = "return { message: 'test', count: 42, items: ['a', 'b', 'c'] };"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:5678/api/v2/execute" `
    -Method POST -Headers $headers -Body $body

Write-Host "Response.result type: $($response.result.GetType().Name)" -ForegroundColor Gray
Write-Host "Full response.result:" -ForegroundColor Gray
$response.result | ConvertTo-Json

# Try different ways to access the data
Write-Host "`nAccessing object properties:" -ForegroundColor Yellow
Write-Host "result.message: $($response.result.message)" -ForegroundColor Green
Write-Host "result.count: $($response.result.count)" -ForegroundColor Green
Write-Host "result.items: $($response.result.items)" -ForegroundColor Green

# Test 5: Complex Hacker News test
Write-Host "`n📋 Test 5: Hacker News Complex Object" -ForegroundColor Yellow
$body = @{
    url = "https://news.ycombinator.com"
    javascript = @'
const titles = document.querySelectorAll('.titleline > a');
return {
    debug: "This is a debug message",
    count: titles.length,
    firstTitle: titles[0] ? titles[0].textContent : "No title found",
    stories: Array.from(titles).slice(0, 3).map((link, index) => ({
        index: index,
        title: link.textContent,
        url: link.href
    }))
};
'@
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:5678/api/v2/execute" `
    -Method POST -Headers $headers -Body $body

Write-Host "`nFull response as JSON:" -ForegroundColor Yellow
$response | ConvertTo-Json -Depth 10

Write-Host "`nDirect property access:" -ForegroundColor Yellow
Write-Host "response.success: $($response.success)" -ForegroundColor Gray
Write-Host "response.result: $($response.result)" -ForegroundColor Gray
Write-Host "response.result.debug: $($response.result.debug)" -ForegroundColor Green
Write-Host "response.result.count: $($response.result.count)" -ForegroundColor Green
Write-Host "response.result.firstTitle: $($response.result.firstTitle)" -ForegroundColor Green

if ($response.result.stories) {
    Write-Host "`nStories array:" -ForegroundColor Yellow
    foreach ($story in $response.result.stories) {
        Write-Host "  $($story.index). $($story.title)" -ForegroundColor White
        Write-Host "     URL: $($story.url)" -ForegroundColor Gray
    }
}
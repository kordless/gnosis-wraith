# PowerShell script for Gnosis Wraith API
$url = "https://example.com"
$serverUrl = "http://localhost:5678"

$body = @{
    url = $url
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "$serverUrl/api/crawl" -Method Post -Body $body -ContentType "application/json"
$response | ConvertTo-Json -Depth 10
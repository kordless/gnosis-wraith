Write-Host "Deleting kordless@gmail.com from datastore..." -ForegroundColor Yellow

# Read the current data
$dataPath = ".\local_datastore\user\data.json"
$data = Get-Content $dataPath | ConvertFrom-Json

# Remove the user
$data.PSObject.Properties.Remove("kordless@gmail.com")

# Save back
$data | ConvertTo-Json -Depth 10 | Set-Content $dataPath

Write-Host "User deleted. Current users:" -ForegroundColor Green
$data | ConvertTo-Json -Depth 10

Write-Host "`nNow you can start fresh with a new login." -ForegroundColor Cyan
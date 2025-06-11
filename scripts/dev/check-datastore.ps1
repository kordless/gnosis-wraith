Write-Host "Checking datastore in container..." -ForegroundColor Yellow
docker exec gnosis-wraith-dev ls -la /app/local_datastore/
Write-Host "`nChecking user data:" -ForegroundColor Cyan
docker exec gnosis-wraith-dev cat /app/local_datastore/user/data.json
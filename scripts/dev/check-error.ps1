Write-Host "Checking for errors in logs..." -ForegroundColor Yellow
docker logs gnosis-wraith-dev --tail 100 | Select-String -Pattern "ERROR|Exception|Traceback|500" -Context 2,2
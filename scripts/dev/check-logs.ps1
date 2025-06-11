Write-Host "Showing last 50 lines of logs..." -ForegroundColor Yellow
docker logs gnosis-wraith-dev --tail 50

Write-Host "`nTo follow logs in real-time:" -ForegroundColor Cyan
Write-Host "docker logs -f gnosis-wraith-dev"
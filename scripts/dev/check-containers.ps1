# Check if Redis Commander is running
Write-Host "Checking containers..." -ForegroundColor Yellow
docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}"

Write-Host "`nChecking Redis Commander specifically:" -ForegroundColor Cyan
docker ps | findstr redis-commander

Write-Host "`nIf Redis Commander is not running, start it with:" -ForegroundColor Green
Write-Host "docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d redis-commander"
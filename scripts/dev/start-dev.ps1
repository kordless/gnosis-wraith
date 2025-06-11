# Gnosis Wraith Development Start Script
Write-Host "Starting Gnosis Wraith in development mode with Redis..." -ForegroundColor Green

# Stop existing containers
Write-Host "Stopping existing containers..." -ForegroundColor Yellow
docker compose -f docker-compose.yml -f docker-compose.dev.yml down

# Build and start services
Write-Host "Building and starting services..." -ForegroundColor Yellow
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

# Wait for services to start
Write-Host "Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Show running containers
Write-Host "`nRunning containers:" -ForegroundColor Cyan
docker compose -f docker-compose.yml -f docker-compose.dev.yml ps

Write-Host "`nServices available at:" -ForegroundColor Green
Write-Host "  - Main app: http://localhost:5678" -ForegroundColor White
Write-Host "  - Queue monitor: http://localhost:5678/dev/queue-monitor" -ForegroundColor White
Write-Host "  - Redis Commander: http://localhost:8081" -ForegroundColor White

Write-Host "`nUseful commands:" -ForegroundColor Cyan
Write-Host "  - View logs: docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f" -ForegroundColor Gray
Write-Host "  - Stop services: docker compose -f docker-compose.yml -f docker-compose.dev.yml down" -ForegroundColor Gray
Write-Host "  - Access Redis CLI: docker exec -it gnosis-wraith-redis redis-cli" -ForegroundColor Gray
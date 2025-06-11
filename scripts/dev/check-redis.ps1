# Check what's using port 6379
Write-Host "Checking what's using port 6379..." -ForegroundColor Yellow

# Check for processes using the port
Write-Host "`nProcesses using port 6379:" -ForegroundColor Cyan
netstat -ano | findstr :6379

# Check for Docker containers using Redis
Write-Host "`nDocker containers with Redis:" -ForegroundColor Cyan
docker ps --filter "publish=6379" --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}"

# Check all Redis-related containers (running or stopped)
Write-Host "`nAll Redis containers:" -ForegroundColor Cyan
docker ps -a | findstr redis
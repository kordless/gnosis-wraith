# Gnosis Wraith Jobs System Rebuild Script
# This script stops and removes the existing Gnosis Wraith containers,
# rebuilds the image using the jobs-enabled Dockerfile, and starts a fresh container

Write-Host "Gnosis Wraith Jobs System Rebuild Script"
Write-Host "========================================"

# Stop and remove the existing containers (both original and jobs versions)
Write-Host "Stopping and removing existing containers..."
docker stop gnosis-wraith 2>$null
docker rm gnosis-wraith 2>$null
docker stop gnosis-wraith-jobs 2>$null
docker rm gnosis-wraith-jobs 2>$null

# Remove the images
Write-Host "Removing existing Docker images..."
docker rmi gnosis-wraith-jobs 2>$null

# Rebuild the image using the jobs Dockerfile
Write-Host "Building new Docker image with job system..."
docker build -t gnosis-wraith-jobs -f Dockerfile.jobs .

# Run the new container
Write-Host "Starting new container with job system..."
docker run -d -p 5678:5678 --name gnosis-wraith-jobs gnosis-wraith-jobs

# Display container status
Write-Host "Container Status:"
docker ps --filter "name=gnosis-wraith-jobs"

Write-Host ""
Write-Host "Gnosis Wraith with Job System is available at: http://localhost:5678"
Write-Host ""
Write-Host "Quick Commands:"
Write-Host "  - View logs: docker logs gnosis-wraith-jobs"
Write-Host "  - Shell access: docker exec -it gnosis-wraith-jobs /bin/bash"
Write-Host "  - Redis CLI: docker exec -it gnosis-wraith-jobs redis-cli"
Write-Host "  - Stop container: docker stop gnosis-wraith-jobs"

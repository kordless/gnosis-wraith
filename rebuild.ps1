# Gnosis Wraith Rebuild Script
# This script stops and removes the existing Gnosis Wraith container,
# rebuilds the image, and starts a fresh container with the jobs-enabled app

Write-Host "Gnosis Wraith Rebuild Script"
Write-Host "==========================="

# Stop and remove the existing containers
Write-Host "Stopping and removing existing containers..."
docker stop gnosis-wraith 2>$null
docker rm gnosis-wraith 2>$null
docker stop gnosis-wraith-jobs 2>$null
docker rm gnosis-wraith-jobs 2>$null

# Remove the image
Write-Host "Removing existing Docker image..."
docker rmi gnosis-wraith 2>$null

# Rebuild the image with the jobs-enabled Dockerfile
Write-Host "Building new Docker image..."
docker build -t gnosis-wraith -f Dockerfile.jobs .

# Update startup script to use app.py instead of app_with_jobs.py
Write-Host "Updating container startup script..."
docker run --rm -v ${PWD}:/mnt gnosis-wraith bash -c "echo '#!/bin/bash' > /mnt/startup.sh && \
    echo 'service redis-server start' >> /mnt/startup.sh && \
    echo 'exec hypercorn --bind 0.0.0.0:5678 app:app' >> /mnt/startup.sh && \
    chmod +x /mnt/startup.sh"

# Run the new container with the updated startup script
Write-Host "Starting new container..."
docker run -d -p 5678:5678 --name gnosis-wraith -v ${PWD}/startup.sh:/app/startup.sh gnosis-wraith

# Display container status
Write-Host "Container Status:"
docker ps --filter "name=gnosis-wraith"

Write-Host ""
Write-Host "Gnosis Wraith is available at: http://localhost:5678"
Write-Host ""
Write-Host "Quick Commands:"
Write-Host "  - View logs: docker logs gnosis-wraith"
Write-Host "  - Shell access: docker exec -it gnosis-wraith /bin/bash"
Write-Host "  - Redis CLI: docker exec -it gnosis-wraith redis-cli"
Write-Host "  - Stop container: docker stop gnosis-wraith"

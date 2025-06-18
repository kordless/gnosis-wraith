# Quick restart script for development with Docker image rebuild
Write-Host "Gnosis Wraith Development Restart Script" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan

# Get extension version from manifest.json
$manifestPath = Join-Path -Path $PSScriptRoot -ChildPath "..\..\gnosis_wraith\extension\manifest.json"
Write-Host "Reading extension version from manifest.json..." -ForegroundColor Yellow

if (Test-Path $manifestPath) {
    try {
        $manifest = Get-Content -Path $manifestPath -Raw | ConvertFrom-Json
        $extensionVersion = $manifest.version
        Write-Host "Found extension version: $extensionVersion" -ForegroundColor Green
    } catch {
        Write-Host "Error reading manifest.json: $_" -ForegroundColor Red
        $extensionVersion = "1.4.1"  # Default fallback
        Write-Host "Using default version: $extensionVersion" -ForegroundColor Yellow
    }
} else {
    Write-Host "manifest.json not found!" -ForegroundColor Red
    $extensionVersion = "1.4.1"  # Default fallback
    Write-Host "Using default version: $extensionVersion" -ForegroundColor Yellow
}



# Change to project root directory
$projectRoot = Join-Path -Path $PSScriptRoot -ChildPath "..\..\"
Push-Location $projectRoot

# Stop existing containers
Write-Host "`nStopping existing containers..." -ForegroundColor Yellow
docker compose -f docker-compose.yml -f docker-compose.dev.yml down

# Build the extension first
Write-Host "`nBuilding browser extension..." -ForegroundColor Yellow
& "$PSScriptRoot\..\deployment\build_extension.ps1"

# Rebuild Docker image with extension version
Write-Host "`nRebuilding Docker image with version $extensionVersion..." -ForegroundColor Yellow
docker build --build-arg EXTENSION_VERSION=$extensionVersion -t gnosis-wraith .

if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`nDocker image rebuilt successfully!" -ForegroundColor Green

# Start containers with the new image
Write-Host "`nStarting development containers..." -ForegroundColor Yellow
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Wait a moment for services to start
Write-Host "`nWaiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 3


# Check container status
Write-Host "`nContainer Status:" -ForegroundColor Cyan
docker ps --filter "name=gnosis"

Write-Host "`nDevelopment environment restarted!" -ForegroundColor Green
Write-Host "`nServices available at:" -ForegroundColor Cyan
Write-Host "  - Main app: http://localhost:5678" -ForegroundColor White
Write-Host "  - Queue monitor: http://localhost:5678/dev/queue-monitor" -ForegroundColor White
Write-Host "  - Redis Commander: http://localhost:8081" -ForegroundColor White
Write-Host "`nExtension version: $extensionVersion" -ForegroundColor Green
Write-Host "`nQuick commands:" -ForegroundColor Cyan
Write-Host "  - View logs: docker logs gnosis-wraith" -ForegroundColor Gray
Write-Host "  - View compose logs: docker compose logs -f" -ForegroundColor Gray
Write-Host "  - Shell access: docker exec -it gnosis-wraith /bin/bash" -ForegroundColor Gray

# Return to original directory
Pop-Location
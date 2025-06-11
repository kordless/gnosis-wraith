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

# Check if old Docker volume exists and offer migration
$volumeExists = docker volume ls -q | Select-String -Pattern "gnosis-wraith_wraith-data"
if ($volumeExists) {
    Write-Host "`nDetected old Docker volume 'wraith-data'" -ForegroundColor Yellow
    $migrate = Read-Host "Would you like to migrate data from the old Docker volume? (y/N)"
    
    if ($migrate -eq 'y' -or $migrate -eq 'Y') {
        Write-Host "Migrating data from Docker volume to host directory..." -ForegroundColor Yellow
        
        # Create a temporary container to copy data
        docker run --rm -v gnosis-wraith_wraith-data:/source -v ${PWD}/storage:/target alpine sh -c "cp -av /source/* /target/" 2>&1 | Out-Null
        
        Write-Host "Migration complete!" -ForegroundColor Green
        Write-Host "Old volume will be preserved. To remove it later, run: docker volume rm gnosis-wraith_wraith-data" -ForegroundColor Gray
    }
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

# Run migration scripts if needed
Write-Host "`nChecking for storage migrations..." -ForegroundColor Yellow

# First run the old user storage migration if needed
$migrationPath = "$PSScriptRoot\..\maintenance\migrate_to_user_storage.py"
if (Test-Path $migrationPath) {
    docker exec gnosis-wraith python /app/scripts/maintenance/migrate_to_user_storage.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "User storage migration completed successfully!" -ForegroundColor Green
    } else {
        Write-Host "User storage migration was not needed or already completed" -ForegroundColor Gray
    }
}

# Then run the NDB migration
$ndbMigrationPath = "$PSScriptRoot\..\maintenance\migrate_to_ndb_storage.py"
if (Test-Path $ndbMigrationPath) {
    docker exec gnosis-wraith python /app/scripts/maintenance/migrate_to_ndb_storage.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "NDB storage migration completed successfully!" -ForegroundColor Green
    } else {
        Write-Host "NDB storage migration was not needed or already completed" -ForegroundColor Gray
    }
} else {
    Write-Host "NDB migration script not found, skipping..." -ForegroundColor Gray
}

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
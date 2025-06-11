# Gnosis Wraith Rebuild Script
# This script stops and removes the existing Gnosis Wraith container,
# rebuilds the image, and starts a fresh container with the jobs-enabled app

# Define the log file path
$logFilePath = Join-Path -Path $PSScriptRoot -ChildPath "rebuild_log.txt"

# Function to log messages to both console and file
function Log-Message {
    param (
        [Parameter(Mandatory = $true)]
        [string]$Message,
        
        [Parameter(Mandatory = $false)]
        [string]$ForegroundColor = "White"
    )
    
    # Write to console with color
    Write-Host $Message -ForegroundColor $ForegroundColor
    
    # Add timestamp and write to log file
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Out-File -FilePath $logFilePath -Append
}

# Start with a fresh log file
"# Gnosis Wraith Rebuild Log - Started at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File -FilePath $logFilePath -Force

Log-Message "Gnosis Wraith Rebuild Script" -ForegroundColor Cyan
Log-Message "===========================" -ForegroundColor Cyan

# Stop and remove the existing containers
Log-Message "Stopping and removing existing containers..." -ForegroundColor Yellow
$stopOutput = docker stop gnosis-wraith 2>&1
Log-Message "  Stop result: $stopOutput"
$rmOutput = docker rm gnosis-wraith 2>&1
Log-Message "  Remove result: $rmOutput"
$stopJobsOutput = docker stop gnosis-wraith-jobs 2>&1
Log-Message "  Stop jobs result: $stopJobsOutput"
$rmJobsOutput = docker rm gnosis-wraith-jobs 2>&1
Log-Message "  Remove jobs result: $rmJobsOutput"

# Remove the image
Log-Message "Removing existing Docker image..." -ForegroundColor Yellow
$rmiOutput = docker rmi gnosis-wraith 2>&1
Log-Message "  Remove image result: $rmiOutput"

# Get extension version from manifest.json
$manifestPath = Join-Path -Path $PSScriptRoot -ChildPath "gnosis_wraith\extension\manifest.json"
Log-Message "Checking extension version in manifest.json..." -ForegroundColor Yellow
Log-Message "  Manifest path: $manifestPath"

if (Test-Path $manifestPath) {
    try {
        $manifestContent = Get-Content -Path $manifestPath -Raw | ConvertFrom-Json
        $extensionVersion = $manifestContent.version
        Log-Message "Found extension version $extensionVersion in manifest.json" -ForegroundColor Green
        Log-Message "Using manifest.json as the source of truth for extension version" -ForegroundColor Green
        
        # Now we don't need to check the Dockerfile version, as it reads from manifest.json dynamically
        Log-Message "Both Dockerfiles now read version directly from manifest.json" -ForegroundColor Cyan
        
        # Export the version to environment so PowerShell scripts can use it too
        $env:EXTENSION_VERSION = $extensionVersion
        Log-Message "Exported EXTENSION_VERSION=$extensionVersion to environment" -ForegroundColor Green
        
        # Get manifest content for logging
        $manifestLines = Get-Content -Path $manifestPath
        Log-Message "  Manifest content preview:" -ForegroundColor Gray
        foreach ($line in $manifestLines | Select-Object -First 10) {
            Log-Message "    $line" -ForegroundColor Gray
        }
    } catch {
        Log-Message "Error reading manifest.json: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Log-Message "ERROR: manifest.json not found at $manifestPath" -ForegroundColor Red
    Log-Message "This file is required as the source of truth for extension version" -ForegroundColor Red
    exit 1
}

# Update extension icons with favicon and update version to 1.1.1
Log-Message "Updating extension icons and version..." -ForegroundColor Yellow
$extensionDir = Join-Path -Path $PSScriptRoot -ChildPath "gnosis_wraith\extension"
$faviconDir = Join-Path -Path $PSScriptRoot -ChildPath "web\static\images"
$imagesDir = Join-Path -Path $extensionDir -ChildPath "images"

# Copy favicon.ico to icon-32.png
Log-Message "  Copying favicon.ico to icon-32.png..." -ForegroundColor Gray
Copy-Item -Path "$faviconDir\favicon.ico" -Destination "$imagesDir\icon-32.png" -Force

# Update manifest.json - use safer method
Log-Message "  Updating manifest.json - name, description and version..." -ForegroundColor Gray
$manifestPath = Join-Path -Path $extensionDir -ChildPath "manifest.json"
$manifestJson = Get-Content -Path $manifestPath | ConvertFrom-Json

# Update values
$manifestJson.name = "Gnosis Wraith Ghost"
$manifestJson.description = "Gnosis Wraith - DOM capture, screenshot, and content extraction for web pages"
# Keep the existing version from manifest

# Save updated manifest
$manifestJson | ConvertTo-Json -Depth 10 | Set-Content -Path $manifestPath

# Report updates
Log-Message "  Updated extension name to '$($manifestJson.name)'" -ForegroundColor Green
Log-Message "  Updated version to $($manifestJson.version)" -ForegroundColor Green

# Rebuild the image
Log-Message "Building new Docker image..." -ForegroundColor Yellow
Log-Message "  Using Dockerfile"

# Read the version directly from manifest.json for build argument
Log-Message "  Reading extension version from manifest.json for Docker build..." -ForegroundColor Yellow
$manifestVersion = $manifestJson.version

# Execute the build with output capturing and pass version as build argument
Log-Message "  Starting Docker build with version $manifestVersion..." -ForegroundColor Yellow
Log-Message "  Command: docker build --build-arg EXTENSION_VERSION=$manifestVersion -t gnosis-wraith ." -ForegroundColor Gray
Log-Message "  Build output will be logged to $logFilePath" -ForegroundColor Gray

# Execute the build and capture output
$buildOutput = & docker build --build-arg EXTENSION_VERSION=$manifestVersion -t gnosis-wraith . 2>&1

# Log each line of the build output
Log-Message "Docker Build Output:" -ForegroundColor Cyan
foreach ($line in $buildOutput) {
    Log-Message "  $line" -ForegroundColor Gray
}

# Check build success
$buildSuccess = $LASTEXITCODE -eq 0
if ($buildSuccess) {
    Log-Message "Docker build completed successfully!" -ForegroundColor Green
} else {
    Log-Message "Docker build failed with exit code $LASTEXITCODE" -ForegroundColor Red
    Log-Message "Please check the log file for details: $logFilePath" -ForegroundColor Red
    
    # Continue script execution even if build fails, so we can see complete logs
    Log-Message "Continuing script execution to log all steps..." -ForegroundColor Yellow
}

# Update startup script to use app.py instead of app_with_jobs.py
Log-Message "Updating container startup script..." -ForegroundColor Yellow

# Create the startup.sh file directly with Unix line endings
$startupContent = @"
#!/bin/bash
service redis-server start
exec hypercorn --bind 0.0.0.0:5678 app:app
"@

# Convert to Unix line endings (LF only) and save without BOM
$startupContent = $startupContent.Replace("`r`n", "`n")
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText("$PSScriptRoot\startup.sh", $startupContent, $utf8NoBom)

# Verify the file was created
if (Test-Path "$PSScriptRoot\startup.sh") {
    Log-Message "  Created startup.sh with Unix line endings" -ForegroundColor Green
    
    # Log the file content (with byte inspection to confirm no CR)
    $bytes = [System.IO.File]::ReadAllBytes("$PSScriptRoot\startup.sh")
    $hasCR = $bytes -contains 13 # Check for CR (13)
    Log-Message "  Startup.sh content (has CR: $hasCR):" -ForegroundColor Gray
    $fileContent = [System.IO.File]::ReadAllText("$PSScriptRoot\startup.sh")
    foreach ($line in $fileContent -split "`n") {
        Log-Message "    $line" -ForegroundColor Gray
    }
} else {
    Log-Message "  Failed to create startup.sh" -ForegroundColor Red
    exit 1
}

# We don't need to run the docker command to create this file anymore
# The file is already created locally with proper line endings
Log-Message "  Startup script updated successfully" -ForegroundColor Green

# The environment variable is already set from the manifest version earlier
Log-Message "  EXTENSION_VERSION environment variable is set to $env:EXTENSION_VERSION" -ForegroundColor Green

# Check if .env file exists and load it
$envFilePath = Join-Path -Path $PSScriptRoot -ChildPath ".env"
$envFileExists = Test-Path $envFilePath
$envFileMessage = if ($envFileExists) { "found" } else { "not found" }
Log-Message "Checking for .env file: $envFileMessage" -ForegroundColor $(if ($envFileExists) { "Green" } else { "Yellow" })

# Build the environment variables argument
$envVarsArg = "-e EXTENSION_VERSION=$($manifestJson.version)"

# If .env file exists, use --env-file
if ($envFileExists) {
    $envVarMessage = "--env-file ./.env"
    Log-Message "  Using environment variables from .env file" -ForegroundColor Green
} else {
    $envVarMessage = "-e EXTENSION_VERSION only"
    Log-Message "  Warning: No .env file found. API features may be limited." -ForegroundColor Yellow
    Log-Message "  Create a .env file with your ANTHROPIC_API_KEY for AI features" -ForegroundColor Yellow
}

# Run the new container with the updated startup script
Log-Message "Starting new container..." -ForegroundColor Yellow
$dockerRunCommand = if ($envFileExists) {
    "docker run -d -p 5678:5678 -e EXTENSION_VERSION=$($manifestJson.version) --env-file ./.env --name gnosis-wraith -v ${PWD}/startup.sh:/app/startup.sh gnosis-wraith"
} else {
    "docker run -d -p 5678:5678 -e EXTENSION_VERSION=$($manifestJson.version) --name gnosis-wraith -v ${PWD}/startup.sh:/app/startup.sh gnosis-wraith"
}
Log-Message "  Command: $dockerRunCommand" -ForegroundColor Gray

# Run the container with the appropriate environment setup
if ($envFileExists) {
    $containerOutput = docker run -d -p 5678:5678 -e EXTENSION_VERSION=$($manifestJson.version) --env-file ./.env --name gnosis-wraith -v ${PWD}/startup.sh:/app/startup.sh gnosis-wraith 2>&1
} else {
    $containerOutput = docker run -d -p 5678:5678 -e EXTENSION_VERSION=$($manifestJson.version) --name gnosis-wraith -v ${PWD}/startup.sh:/app/startup.sh gnosis-wraith 2>&1
}
Log-Message "  Container ID: $containerOutput"

# Display container status
Log-Message "Container Status:" -ForegroundColor Cyan
$containerStatus = docker ps --filter "name=gnosis-wraith" 2>&1
foreach ($line in $containerStatus) {
    Log-Message "  $line" -ForegroundColor Gray
}

Log-Message " " 
Log-Message "Gnosis Wraith is available at: http://localhost:5678" -ForegroundColor Green
Log-Message " "
Log-Message "Quick Commands:" -ForegroundColor Cyan
Log-Message "  - View logs: docker logs gnosis-wraith"
Log-Message "  - Shell access: docker exec -it gnosis-wraith /bin/bash"
Log-Message "  - Redis CLI: docker exec -it gnosis-wraith redis-cli"
Log-Message "  - Stop container: docker stop gnosis-wraith"

# Final message about the log file
Log-Message " "
Log-Message "Rebuild process complete. Full log is available at:" -ForegroundColor Cyan
Log-Message "  $logFilePath" -ForegroundColor Cyan
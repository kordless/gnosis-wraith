# deploy.ps1
# Universal deployment script for Gnosis Wraith to Google Cloud Run
# Compatible with both PowerShell 5 and PowerShell 7

# PowerShell version detection
$isPowerShell7 = $PSVersionTable.PSVersion.Major -ge 7
$useUnicode = $isPowerShell7 -and (-not $env:NO_UNICODE)

# Define symbols based on PowerShell version
$symbols = @{
    "CheckMark" = if ($useUnicode) { "✅" } else { "√" }
    "CrossMark" = if ($useUnicode) { "❌" } else { "✘" }
    "Warning" = if ($useUnicode) { "⚠️" } else { "⚠" }
    "Rocket" = if ($useUnicode) { "🚀" } else { "" }
    "Key" = if ($useUnicode) { "🔑" } else { "" }
    "Building" = if ($useUnicode) { "🏗️" } else { "" }
    "Tag" = if ($useUnicode) { "🏷️" } else { "" }
    "Cloud" = if ($useUnicode) { "☁️" } else { "" }
    "Info" = if ($useUnicode) { "📊" } else { "" }
    "Sparkles" = if ($useUnicode) { "✨" } else { "✨" }
}

# Display header
Write-Host "`n$($symbols.Rocket) Gnosis Wraith Deployment Script" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host "Using PowerShell $($PSVersionTable.PSVersion.ToString())" -ForegroundColor Gray

# Function to execute commands based on PowerShell version
function Invoke-CommandSafely {
    param([string]$Command)
    
    if ($isPowerShell7) {
        # PowerShell 7: Use the ampersand for safer execution
        return & ([scriptblock]::Create($Command))
    } else {
        # PowerShell 5: Use Invoke-Expression
        return Invoke-Expression $Command
    }
}

# Check if gcloud is installed
try {
    $gcloudVersion = Invoke-CommandSafely "gcloud --version | Select-Object -First 1"
    Write-Host "$($symbols.CheckMark) Found gcloud: $gcloudVersion" -ForegroundColor Green
}
catch {
    Write-Host "$($symbols.CrossMark) Error: gcloud CLI not found or not in PATH. Please install Google Cloud SDK first." -ForegroundColor Red
    exit 1
}

# Ensure we're properly authenticated
Write-Host "`n$($symbols.Key) Checking gcloud authentication status..." -ForegroundColor Yellow
$authStatus = Invoke-CommandSafely "gcloud auth list --filter=status:ACTIVE --format='value(account)'"

if (-not $authStatus) {
    Write-Host "$($symbols.Warning) Not authenticated to gcloud. Running login..." -ForegroundColor Yellow
    Invoke-CommandSafely "gcloud auth login"
}
else {
    Write-Host "$($symbols.CheckMark) Authenticated as: $authStatus" -ForegroundColor Green
}

# Step 1: Build the Docker image
Write-Host "`n$($symbols.Building) Building Docker image..." -ForegroundColor Yellow
try {
    Invoke-CommandSafely "docker build -t gnosis-wraith ."
    Write-Host "$($symbols.CheckMark) Docker image built successfully" -ForegroundColor Green
}
catch {
    Write-Host "$($symbols.CrossMark) Failed to build Docker image" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

# Step 2: Tag the image for Google Container Registry
Write-Host "`n$($symbols.Tag) Tagging Docker image..." -ForegroundColor Yellow
try {
    Invoke-CommandSafely "docker tag gnosis-wraith gcr.io/gnosis-459403/gnosis-wraith:latest"
    Write-Host "$($symbols.CheckMark) Docker image tagged successfully" -ForegroundColor Green
}
catch {
    Write-Host "$($symbols.CrossMark) Failed to tag Docker image" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

# Step 3: Push the image to Google Container Registry
Write-Host "`n$($symbols.Cloud) Pushing Docker image to Google Container Registry..." -ForegroundColor Yellow
try {
    Invoke-CommandSafely "docker push gcr.io/gnosis-459403/gnosis-wraith:latest"
    Write-Host "$($symbols.CheckMark) Docker image pushed successfully" -ForegroundColor Green
}
catch {
    Write-Host "$($symbols.CrossMark) Failed to push Docker image" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

# Step 4: Deploy to Cloud Run
Write-Host "`n$($symbols.Rocket) Deploying to Google Cloud Run..." -ForegroundColor Yellow
try {
    # Build the gcloud command with backticks for both PS5 and PS7
    $gcloudCmd = @"
gcloud run deploy gnosis-wraith ``
    --image gcr.io/gnosis-459403/gnosis-wraith:latest ``
    --platform managed ``
    --region us-central1 ``
    --memory 4Gi ``
    --timeout 3600 ``
    --port 5678 ``
    --allow-unauthenticated
"@
    Invoke-CommandSafely $gcloudCmd
    Write-Host "$($symbols.CheckMark) Deployment completed successfully" -ForegroundColor Green
}
catch {
    Write-Host "$($symbols.CrossMark) Deployment failed" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

# Display deployment info
Write-Host "`n$($symbols.Info) Deployment Information:" -ForegroundColor Cyan
Invoke-CommandSafely "gcloud run services describe gnosis-wraith --platform managed --region us-central1 --format='value(status.url)'"

Write-Host "`n$($symbols.Sparkles) Gnosis Wraith has been successfully deployed! $($symbols.Sparkles)" -ForegroundColor Green

# Remove the PS7-specific file if it exists (cleanup)
if (Test-Path "$PSScriptRoot\deploy-ps7.ps1") {
    Write-Host "`nNote: You can now safely remove the deploy-ps7.ps1 file as this script supports both PS5 and PS7." -ForegroundColor Yellow
}

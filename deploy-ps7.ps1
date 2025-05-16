# deploy-ps7.ps1
# Script to build, push, and deploy Gnosis Wraith to Google Cloud Run
# Optimized for PowerShell 7

# Display header
Write-Host "`n🚀 Gnosis Wraith Deployment Script" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan

# Check if gcloud is installed
try {
    $gcloudVersion = & gcloud --version | Select-Object -First 1
    Write-Host "✅ Found gcloud: $gcloudVersion" -ForegroundColor Green
}
catch {
    Write-Host "❌ Error: gcloud CLI not found or not in PATH. Please install Google Cloud SDK first." -ForegroundColor Red
    exit 1
}

# Ensure we're properly authenticated
Write-Host "`n🔑 Checking gcloud authentication status..." -ForegroundColor Yellow
$authStatus = & gcloud auth list --filter=status:ACTIVE --format="value(account)"

if (-not $authStatus) {
    Write-Host "⚠️ Not authenticated to gcloud. Running login..." -ForegroundColor Yellow
    & gcloud auth login
}
else {
    Write-Host "✅ Authenticated as: $authStatus" -ForegroundColor Green
}

# Step 1: Build the Docker image
Write-Host "`n🏗️ Building Docker image..." -ForegroundColor Yellow
try {
    & docker build -t gnosis-wraith .
    Write-Host "✅ Docker image built successfully" -ForegroundColor Green
}
catch {
    Write-Host "❌ Failed to build Docker image" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

# Step 2: Tag the image for Google Container Registry
Write-Host "`n🏷️ Tagging Docker image..." -ForegroundColor Yellow
try {
    & docker tag gnosis-wraith gcr.io/gnosis-459403/gnosis-wraith:latest
    Write-Host "✅ Docker image tagged successfully" -ForegroundColor Green
}
catch {
    Write-Host "❌ Failed to tag Docker image" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

# Step 3: Push the image to Google Container Registry
Write-Host "`n☁️ Pushing Docker image to Google Container Registry..." -ForegroundColor Yellow
try {
    & docker push gcr.io/gnosis-459403/gnosis-wraith:latest
    Write-Host "✅ Docker image pushed successfully" -ForegroundColor Green
}
catch {
    Write-Host "❌ Failed to push Docker image" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

# Step 4: Deploy to Cloud Run
Write-Host "`n🚀 Deploying to Google Cloud Run..." -ForegroundColor Yellow
try {
    & gcloud run deploy gnosis-wraith `
        --image gcr.io/gnosis-459403/gnosis-wraith:latest `
        --platform managed `
        --region us-central1 `
        --memory 4Gi `
        --timeout 3600 `
        --port 5678 `
        --allow-unauthenticated
    
    Write-Host "✅ Deployment completed successfully" -ForegroundColor Green
}
catch {
    Write-Host "❌ Deployment failed" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

# Display deployment info
Write-Host "`n📊 Deployment Information:" -ForegroundColor Cyan
& gcloud run services describe gnosis-wraith --platform managed --region us-central1 --format="value(status.url)"

Write-Host "`n✨ Gnosis Wraith has been successfully deployed! ✨" -ForegroundColor Green

# deploy-cloud-run.ps1 - Windows PowerShell deployment helper for Gnosis Wraith

Write-Host "Gnosis Wraith Cloud Run Deployment Helper" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green

# Generate a secure secret key
Write-Host "`nGenerating secure SECRET_KEY..." -ForegroundColor Yellow
$bytes = New-Object byte[] 32
[Security.Cryptography.RNGCryptoServiceProvider]::Create().GetBytes($bytes)
$secretKey = [Convert]::ToBase64String($bytes)
Write-Host "SECRET_KEY generated: $secretKey" -ForegroundColor Green

# Get bucket name
$defaultBucket = "gnosis-wraith-storage-$(Get-Random -Maximum 9999)"
$bucketName = Read-Host -Prompt "`nEnter GCS bucket name (press Enter for default: $defaultBucket)"
if ([string]::IsNullOrWhiteSpace($bucketName)) {
    $bucketName = $defaultBucket
}

# Get project ID
$projectId = Read-Host -Prompt "`nEnter your Google Cloud Project ID"

# Generate environment variables
$envVars = @"
RUNNING_IN_CLOUD=true
GCS_BUCKET_NAME=$bucketName
SECRET_KEY=$secretKey
APP_DOMAIN=will-be-set-after-deployment.run.app
BRAND=Gnosis Wraith
BRAND_FAVICON=/static/images/favicon.ico
BRAND_COLOR=#6c63ff
BRAND_SERVICE=Gnosis Wraith
BRAND_SERVICE_URL=https://gnosis-wraith.com
BRAND_GITHUB_URL=https://github.com/$($env:USERNAME)/gnosis-wraith
ENVIRONMENT=production
ENABLE_DEV_ENDPOINTS=false
STORAGE_PATH=/data
GNOSIS_WRAITH_STORAGE_PATH=/data
"@

# Save to file
$envVars | Out-File -FilePath "cloud-run-env-vars.txt" -Encoding UTF8
Write-Host "`nEnvironment variables saved to: cloud-run-env-vars.txt" -ForegroundColor Green
Write-Host "You can copy and paste this into the Cloud Run console." -ForegroundColor Yellow

# Display gcloud commands
Write-Host "`n=== Docker Build Command ===" -ForegroundColor Cyan
Write-Host "docker build -t gcr.io/$projectId/gnosis-wraith:latest ."

Write-Host "`n=== Docker Push Command ===" -ForegroundColor Cyan
Write-Host "docker push gcr.io/$projectId/gnosis-wraith:latest"

Write-Host "`n=== Create GCS Bucket Command ===" -ForegroundColor Cyan
Write-Host "gsutil mb -p $projectId -c STANDARD -l us-central1 gs://$bucketName/"

Write-Host "`n=== Cloud Run Deploy Command ===" -ForegroundColor Cyan
$deployCmd = @"
gcloud run deploy gnosis-wraith `
  --image gcr.io/$projectId/gnosis-wraith:latest `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --memory 2Gi `
  --cpu 2 `
  --timeout 300 `
  --port 5678 `
  --env-vars-file cloud-run-env-vars.txt
"@
Write-Host $deployCmd

Write-Host "`n=== Next Steps ===" -ForegroundColor Green
Write-Host "1. Copy the contents of cloud-run-env-vars.txt"
Write-Host "2. Paste into the Cloud Run environment variables section"
Write-Host "3. Or use the gcloud commands above to deploy from command line"
Write-Host "4. After deployment, update APP_DOMAIN with your actual Cloud Run URL"

# Option to copy to clipboard
$copyToClipboard = Read-Host -Prompt "`nCopy environment variables to clipboard? (y/n)"
if ($copyToClipboard -eq 'y') {
    $envVars | Set-Clipboard
    Write-Host "Environment variables copied to clipboard!" -ForegroundColor Green
}

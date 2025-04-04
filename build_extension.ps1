# PowerShell script to build the extension zip
$downloadsDir = "gnosis_wraith/server/static/downloads"
$extensionDir = "gnosis_wraith/extension"

# Create downloads directory if it doesn't exist
if (-not (Test-Path $downloadsDir)) {
    New-Item -ItemType Directory -Path $downloadsDir -Force
    Write-Host "Created downloads directory: $downloadsDir"
}

# Check if extension directory exists
if (Test-Path $extensionDir) {
    # Remove old zip if it exists
    $zipPath = "$downloadsDir/gnosis-wraith-extension.zip"
    if (Test-Path $zipPath) {
        Remove-Item $zipPath -Force
        Write-Host "Removed old extension zip"
    }
    
    # Create the zip file
    Compress-Archive -Path $extensionDir/* -DestinationPath $zipPath
    Write-Host "Created new extension zip: $zipPath"
} else {
    Write-Host "Error: Extension directory not found: $extensionDir"
}
# PowerShell script to build the extension zip with version number in filename
$downloadsDir = "gnosis_wraith/server/static/downloads"
$extensionDir = "gnosis_wraith/extension"
$manifestPath = "gnosis_wraith/extension/manifest.json"

# Get version from manifest.json
if (Test-Path $manifestPath) {
    $manifestContent = Get-Content $manifestPath -Raw
    # Use regex to extract version
    $versionMatch = [regex]::Match($manifestContent, '"version":\s*"([^"]+)"')
    if ($versionMatch.Success) {
        $version = $versionMatch.Groups[1].Value
        Write-Host "Found version $version in manifest.json"
    } else {
        $version = "1.0.5"  # Default version if not found
        Write-Host "Warning: Could not determine version from manifest.json, using default: $version"
    }
} else {
    $version = "1.0.5"  # Default version if manifest not found
    Write-Host "Warning: manifest.json not found, using default version: $version"
}

# Create downloads directory if it doesn't exist
if (-not (Test-Path $downloadsDir)) {
    New-Item -ItemType Directory -Path $downloadsDir -Force
    Write-Host "Created downloads directory: $downloadsDir"
}

# Remove any old versioned extension zips
Get-ChildItem -Path $downloadsDir -Filter "gnosis-wraith-extension-*.zip" | Remove-Item -Force
Write-Host "Removed old extension zip files"

# Check if extension directory exists
if (Test-Path $extensionDir) {
    # Create the zip file with version in filename
    $versionedZipPath = "$downloadsDir/gnosis-wraith-extension-$version.zip"
    Compress-Archive -Path "$extensionDir/*" -DestinationPath $versionedZipPath
    Write-Host "Created new versioned extension zip: $versionedZipPath"
    
    # Create a copy for backward compatibility (PowerShell doesn't easily support symlinks)
    $legacyZipPath = "$downloadsDir/gnosis-wraith-extension.zip"
    Copy-Item -Path $versionedZipPath -Destination $legacyZipPath -Force
    Write-Host "Created copy for backward compatibility: $legacyZipPath"
} else {
    Write-Host "Error: Extension directory not found: $extensionDir"
}
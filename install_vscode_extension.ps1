# PowerShell script to install the Gnosis Wraith VSCode extension
# This script creates the extension directory and copies the files

# Define paths
$extensionSourceDir = "C:\Users\kord\Code\gnosis\gnosis-wraith\vscode-extension"
$extensionTargetDir = "C:\Users\kord\.vscode\extensions\gnosis-wraith-extension-0.1.0"

# Create the extension directory if it doesn't exist
if (-not (Test-Path $extensionTargetDir)) {
    Write-Host "Creating extension directory: $extensionTargetDir"
    New-Item -Path $extensionTargetDir -ItemType Directory -Force | Out-Null
}

# Copy the extension files
Write-Host "Copying extension files from $extensionSourceDir to $extensionTargetDir"
Copy-Item -Path "$extensionSourceDir\*" -Destination $extensionTargetDir -Recurse -Force

# Verify the installation
if (Test-Path "$extensionTargetDir\package.json") {
    Write-Host "Extension installed successfully!"
    Write-Host "Please restart VSCode to activate the extension."
} else {
    Write-Host "Error: Failed to install the extension."
}

# List the installed files
Write-Host "`nInstalled files:"
Get-ChildItem -Path $extensionTargetDir -Recurse | ForEach-Object {
    Write-Host " - $($_.FullName.Replace($extensionTargetDir, ''))"
}

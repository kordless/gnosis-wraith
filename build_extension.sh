#!/bin/bash
# Bash script to build the extension zip with version number in filename

# Get the current version from manifest.json
MANIFEST_PATH="gnosis_wraith/extension/manifest.json"
VERSION=$(grep -o '"version": "[^"]*"' "$MANIFEST_PATH" | cut -d'"' -f4)

if [ -z "$VERSION" ]; then
    VERSION="1.0.4"  # Default version if not found
    echo "Warning: Could not determine version from manifest.json, using default: $VERSION"
else
    echo "Found version $VERSION in manifest.json"
fi

DOWNLOADS_DIR="gnosis_wraith/server/static/downloads"
EXTENSION_DIR="gnosis_wraith/extension"
ZIP_PATH="$DOWNLOADS_DIR/gnosis-wraith-extension-$VERSION.zip"

# Create downloads directory if it doesn't exist
mkdir -p "$DOWNLOADS_DIR"
echo "Created downloads directory: $DOWNLOADS_DIR"

# Remove any old versioned extension zips
find "$DOWNLOADS_DIR" -name "gnosis-wraith-extension-*.zip" -delete
echo "Removed old extension zip files"

# Check if extension directory exists
if [ -d "$EXTENSION_DIR" ]; then
    # Create the zip file with version in filename
    cd gnosis_wraith
    zip -r "../$ZIP_PATH" extension
    cd ..
    echo "Created new versioned extension zip: $ZIP_PATH"
    
    # Create a symbolic link for backward compatibility
    ln -sf "gnosis-wraith-extension-$VERSION.zip" "$DOWNLOADS_DIR/gnosis-wraith-extension.zip"
    echo "Created symbolic link for backward compatibility"
else
    echo "Error: Extension directory not found: $EXTENSION_DIR"
fi
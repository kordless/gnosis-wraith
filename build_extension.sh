#!/bin/bash
# Bash script to build the extension zip

DOWNLOADS_DIR="gnosis_wraith/server/static/downloads"
EXTENSION_DIR="gnosis_wraith/extension"
ZIP_PATH="$DOWNLOADS_DIR/gnosis-wraith-extension.zip"

# Create downloads directory if it doesn't exist
mkdir -p "$DOWNLOADS_DIR"
echo "Created downloads directory: $DOWNLOADS_DIR"

# Check if extension directory exists
if [ -d "$EXTENSION_DIR" ]; then
    # Remove old zip if it exists
    if [ -f "$ZIP_PATH" ]; then
        rm "$ZIP_PATH"
        echo "Removed old extension zip"
    fi
    
    # Create the zip file
    cd gnosis_wraith
    zip -r "../$ZIP_PATH" extension
    cd ..
    echo "Created new extension zip: $ZIP_PATH"
else
    echo "Error: Extension directory not found: $EXTENSION_DIR"
fi
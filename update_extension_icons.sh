#!/bin/bash

# This script updates the extension icons with the Gnosis Wraith favicon

# Set directory paths
FAVICON_PATH="/app/gnosis_wraith/server/static/images"
EXTENSION_PATH="/app/gnosis_wraith/extension/images"

# Install required tools if they don't exist
apt-get update && apt-get install -y imagemagick librsvg2-bin

# Function to convert SVG to PNG of different sizes
convert_svg_to_png() {
  local size=$1
  
  # Create PNG from SVG
  rsvg-convert -w $size -h $size $FAVICON_PATH/favicon.svg -o $EXTENSION_PATH/icon-$size.png
  
  # Log result
  echo "Created icon-$size.png"
}

# Copy the favicon.ico file to icon-32.png
cp $FAVICON_PATH/favicon.ico $EXTENSION_PATH/icon-32.png
echo "Copied favicon.ico to icon-32.png"

# Convert SVG to PNG in various sizes
convert_svg_to_png 16
convert_svg_to_png 48
convert_svg_to_png 128

echo "All extension icons have been updated!"

# Rebuild the extension zip
cd /app
mkdir -p /app/gnosis_wraith/server/static/downloads
cd /app/gnosis_wraith/extension
zip -r /app/gnosis_wraith/server/static/downloads/gnosis-wraith-extension-1.1.0.zip *
echo "Extension ZIP rebuilt with new icons!"

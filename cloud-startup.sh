#!/bin/bash
# startup.sh - Cloud Run startup script with debugging

echo "Starting Gnosis Wraith..."
echo "PORT environment variable: ${PORT}"
echo "All environment variables:"
env | sort

# Create storage directory if it doesn't exist
mkdir -p /data

# Start the application with the PORT from environment
echo "Starting Hypercorn on port ${PORT:-5678}..."
exec hypercorn --bind 0.0.0.0:${PORT:-5678} app:app

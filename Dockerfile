# Use the official Playwright Python image 
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Accept extension version as build argument
ARG EXTENSION_VERSION=1.4.1

# Install basic dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    wget \
    zip \
    && rm -rf /var/lib/apt/lists/*

# Set extension version environment variable
ENV EXTENSION_VERSION=${EXTENSION_VERSION}

# Set working directory
WORKDIR /app

# Upgrade pip, setuptools, and wheel, and install required Python packages
RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install openai openai[datalib] tenacity playwright aiohttp

# Install Quart and Hypercorn
RUN pip install --no-cache-dir quart httpx werkzeug hypercorn quart_cors

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Beautiful Soup for HTML parsing
RUN pip install --no-cache-dir beautifulsoup4

# Install all browsers supported by this version of Playwright
RUN playwright install chromium

# Copy application code
COPY . .

# Set a default extension version that will be used if reading from manifest fails
ENV EXTENSION_VERSION=1.2.1

# Copy manifest and attempt to read it (but don't break the build if it fails)
COPY gnosis_wraith/extension/manifest.json /tmp/manifest.json
RUN if [ -f /tmp/manifest.json ]; then \
      VERSION=$(grep -oP '"version": *"\K[^"]+' /tmp/manifest.json || echo "$EXTENSION_VERSION"); \
      if [ ! -z "$VERSION" ]; then \
        echo "Using extension version from manifest.json: $VERSION"; \
        echo "export EXTENSION_VERSION=$VERSION" >> /etc/environment; \
        echo "EXTENSION_VERSION=$VERSION" >> /.env; \
        echo "ENV EXTENSION_VERSION=$VERSION" >> /tmp/version.txt; \
      fi; \
    fi

# We continue to use the ENV value which is either the default or was updated by the previous step

# Create build_extension.sh script to help with extension packaging
RUN mkdir -p /app/web/static/downloads

# Create the build_extension.sh script in a simpler way to avoid issues
COPY gnosis_wraith/extension /app/gnosis_wraith/extension

# Write the script directly (avoiding complex variable interpolation in Docker)
RUN echo '#!/bin/bash' > /app/build_extension.sh && \
    echo 'set -e  # Exit on error' >> /app/build_extension.sh && \
    echo 'VERSION=${EXTENSION_VERSION:-1.2.1}' >> /app/build_extension.sh && \
    echo 'echo "Building extension version $VERSION..."' >> /app/build_extension.sh && \
    echo 'DIR="/app/web/static/downloads"' >> /app/build_extension.sh && \
    echo 'TARGET="$DIR/gnosis-wraith-extension-$VERSION.zip"' >> /app/build_extension.sh && \
    echo 'WEB_TARGET="$DIR/webwraith-extension-$VERSION.zip"' >> /app/build_extension.sh && \
    echo 'mkdir -p "$DIR"' >> /app/build_extension.sh && \
    echo 'HOST_FILE="/host-files/gnosis-wraith-extension-$VERSION.zip"' >> /app/build_extension.sh && \
    echo 'if [ -f "$HOST_FILE" ]; then' >> /app/build_extension.sh && \
    echo '  echo "Found pre-built extension in host-files - copying it"' >> /app/build_extension.sh && \
    echo '  cp "$HOST_FILE" "$TARGET"' >> /app/build_extension.sh && \
    echo '  cp "$HOST_FILE" "$WEB_TARGET"' >> /app/build_extension.sh && \
    echo 'elif [ -d "/app/gnosis_wraith/extension" ]; then' >> /app/build_extension.sh && \
    echo '  echo "Creating extension zip with version $VERSION"' >> /app/build_extension.sh && \
    echo '  cd /app/gnosis_wraith && zip -r "$TARGET" extension' >> /app/build_extension.sh && \
    echo '  if [ -f "$TARGET" ]; then' >> /app/build_extension.sh && \
    echo '    cp "$TARGET" "$WEB_TARGET"' >> /app/build_extension.sh && \
    echo '    echo "Extension zip files created successfully:"' >> /app/build_extension.sh && \
    echo '    ls -la "$TARGET" "$WEB_TARGET"' >> /app/build_extension.sh && \
    echo '  else' >> /app/build_extension.sh && \
    echo '    echo "ERROR: Failed to create extension zip file"' >> /app/build_extension.sh && \
    echo '    exit 1' >> /app/build_extension.sh && \
    echo '  fi' >> /app/build_extension.sh && \
    echo 'else' >> /app/build_extension.sh && \
    echo '  echo "ERROR: Extension directory not found - cannot create extension zip"' >> /app/build_extension.sh && \
    echo '  exit 1' >> /app/build_extension.sh && \
    echo 'fi' >> /app/build_extension.sh && \
    chmod +x /app/build_extension.sh && \
    /app/build_extension.sh && \
    ls -la /app/web/static/downloads/


# Volume for persistent storage
VOLUME /data

# Define environment variables
ENV GNOSIS_WRAITH_STORAGE_PATH=/data
ENV QUART_APP=app:app
ENV QUART_ENV=production
ENV PYTHONPATH=/app:$PYTHONPATH

# Expose the port
EXPOSE 5678

# Command to run using Hypercorn
CMD hypercorn --bind 0.0.0.0:${PORT:-5678} app:app

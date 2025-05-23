# Use the official Playwright Python image 
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Install dependencies for NVIDIA CUDA
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    gnupg \
    wget \
    zip \
    && rm -rf /var/lib/apt/lists/*

# Add NVIDIA CUDA Repository
RUN wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb \
    && dpkg -i cuda-keyring_1.1-1_all.deb \
    && rm cuda-keyring_1.1-1_all.deb

# Install CUDA libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    cuda-cudart-12-3 \
    cuda-libraries-12-3 \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for CUDA
ENV PATH="/usr/local/cuda-12.3/bin:${PATH}"
ENV LD_LIBRARY_PATH="/usr/local/cuda-12-3/lib64:${LD_LIBRARY_PATH:-/usr/local/lib}"

# Disable NVIDIA driver capabilities that might cause conflicts
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility
ENV NVIDIA_DISABLE_REQUIRE=true

# Set working directory
WORKDIR /app

# Upgrade pip, setuptools, and wheel, and install required Python packages
RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install openai openai[datalib] tenacity playwright aiohttp

# Install PyTorch with CUDA 12.3 support
RUN pip install --no-cache-dir torch==2.2.0 torchvision==0.17.0 torchaudio==2.2.0 --index-url https://download.pytorch.org/whl/cu121

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

# Pre-download EasyOCR models
RUN python -c "import easyocr; reader = easyocr.Reader(['en'])" && \
    mkdir -p /root/.cache && \
    # Create symlink for Cloud Run environment
    ln -s /root/.EasyOCR /root/.cache/EasyOCR

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
RUN mkdir -p /app/gnosis_wraith/server/static/downloads

# Create the build_extension.sh script in a simpler way to avoid issues
COPY gnosis_wraith/extension /app/gnosis_wraith/extension

# Write the script directly (avoiding complex variable interpolation in Docker)
RUN echo '#!/bin/bash' > /app/build_extension.sh && \
    echo 'set -e  # Exit on error' >> /app/build_extension.sh && \
    echo 'VERSION=${EXTENSION_VERSION:-1.2.1}' >> /app/build_extension.sh && \
    echo 'echo "Building extension version $VERSION..."' >> /app/build_extension.sh && \
    echo 'DIR="/app/gnosis_wraith/server/static/downloads"' >> /app/build_extension.sh && \
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
    ls -la /app/gnosis_wraith/server/static/downloads/

# Volume for persistent storage
VOLUME /data

# Define environment variables
ENV GNOSIS_WRAITH_STORAGE_PATH=/data
ENV QUART_APP=gnosis_wraith.server.app:app
ENV QUART_ENV=production

# Expose the port
EXPOSE 5678

# Command to run using Hypercorn
CMD ["hypercorn", "--bind", "0.0.0.0:5678", "gnosis_wraith.server.app:app"]
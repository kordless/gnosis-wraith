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
ENV LD_LIBRARY_PATH="/usr/local/cuda-12.3/lib64:${LD_LIBRARY_PATH:-}"

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

# Install all browsers supported by this version of Playwright
RUN playwright install

# Copy application code
COPY . .

# Set extension version
ENV EXTENSION_VERSION=1.0.5

# Create extension zip file with a shell script that handles checking for existing files
RUN mkdir -p /app/gnosis_wraith/server/static/downloads && \
    echo "#!/bin/bash" > /app/build_extension.sh && \
    echo "TARGET_FILE=\"/app/gnosis_wraith/server/static/downloads/gnosis-wraith-extension-${EXTENSION_VERSION}.zip\"" >> /app/build_extension.sh && \
    echo "if [ -f \"/host-files/gnosis-wraith-extension-${EXTENSION_VERSION}.zip\" ]; then" >> /app/build_extension.sh && \
    echo "  echo \"Found pre-built extension in host-files - copying it\"" >> /app/build_extension.sh && \
    echo "  cp \"/host-files/gnosis-wraith-extension-${EXTENSION_VERSION}.zip\" \"\$TARGET_FILE\"" >> /app/build_extension.sh && \
    echo "elif [ ! -f \"\$TARGET_FILE\" ] && [ -d \"/app/gnosis_wraith/extension\" ]; then" >> /app/build_extension.sh && \
    echo "  echo \"No extension zip found - creating new one with version ${EXTENSION_VERSION}\"" >> /app/build_extension.sh && \
    echo "  cd /app/gnosis_wraith && zip -r \"\$TARGET_FILE\" extension" >> /app/build_extension.sh && \
    echo "else" >> /app/build_extension.sh && \
    echo "  echo \"Found existing extension zip at \$TARGET_FILE - using that\"" >> /app/build_extension.sh && \
    echo "fi" >> /app/build_extension.sh && \
    chmod +x /app/build_extension.sh && \
    /app/build_extension.sh

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
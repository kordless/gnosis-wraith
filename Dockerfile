# Use the official Playwright Python image 
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set working directory
WORKDIR /app

# Upgrade pip, setuptools, and wheel, and install required Python packages
RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install openai openai[datalib] tenacity playwright aiohttp

# Install PyTorch with CUDA support
RUN pip install torch==2.0.0+cu118 torchvision==0.15.0+cu118 torchaudio==2.0.0+cu118 -f https://download.pytorch.org/whl/cu118/torch_stable.html

# Install Quart and Hypercorn
RUN pip install --no-cache-dir quart httpx werkzeug hypercorn quart_cors

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install all browsers supported by this version of Playwright
RUN playwright install

# Update the package list and install required packages
RUN apt-get update && \
    apt-get install -y zip && \
    # Clean up apt cache to reduce image size
    rm -rf /var/lib/apt/lists/*

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
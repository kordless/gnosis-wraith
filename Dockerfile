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
    apt-get install -y zip nvidia-cuda-toolkit nvidia-cuda-dev && \
    # Clean up apt cache to reduce image size
    rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# Create extension zip file
RUN mkdir -p /app/webwraith/server/static/downloads && \
    if [ -d "/app/webwraith/extension" ]; then \
      cd /app/webwraith && \
      zip -r /app/webwraith/server/static/downloads/wraith-extension.zip extension; \
    fi

# Volume for persistent storage
VOLUME /data

# Define environment variables
ENV WRAITH_STORAGE_PATH=/data
ENV QUART_APP=webwraith.app:app
ENV QUART_ENV=production

# Expose the port
EXPOSE 5678

# Command to run using Hypercorn
CMD ["hypercorn", "--bind", "0.0.0.0:5678", "webwraith.server.app:app"]
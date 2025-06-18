# Dockerfile Build Optimization Plan

## Current Issues
1. Installing packages one by one (no caching between builds)
2. Requirements installed after code copy (invalidates cache on code changes)
3. Large unnecessary dependencies (CUDA, PyTorch, EasyOCR)

## Optimized Dockerfile Structure

```dockerfile
# Use the official Playwright Python image 
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Accept extension version as build argument
ARG EXTENSION_VERSION=1.4.1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    wget \
    zip \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Upgrade pip first (separate layer)
RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy only requirements first (better caching)
COPY requirements.txt .

# Install Python dependencies (this layer caches if requirements don't change)
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy application code (changes frequently, so do this last)
COPY . .

# Build extension
RUN mkdir -p /app/web/static/downloads && \
    if [ -d "/app/gnosis_wraith/extension" ]; then \
        cd /app/gnosis_wraith && \
        zip -r /app/web/static/downloads/gnosis-wraith-extension.zip extension; \
    fi

# Volume for persistent storage
VOLUME /data

# Environment variables
ENV GNOSIS_WRAITH_STORAGE_PATH=/data
ENV QUART_APP=app:app
ENV QUART_ENV=production
ENV PYTHONPATH=/app:${PYTHONPATH:-}

# Expose port
EXPOSE 5678

# Run with Hypercorn
CMD ["hypercorn", "--bind", "0.0.0.0:5678", "app:app"]
```

## Quick Fixes for Current Build

1. **Use Docker BuildKit** (faster builds):
```powershell
$env:DOCKER_BUILDKIT=1
docker build -t gnosis-wraith .
```

2. **Build with more CPUs**:
```powershell
docker build --cpu-quota=400000 -t gnosis-wraith .
```

3. **Use a faster mirror** (add to Dockerfile):
```dockerfile
# Use faster pip index
ENV PIP_INDEX_URL=https://pypi.org/simple
```

## Immediate Actions

1. **Remove from Dockerfile**:
   - All CUDA installation steps
   - PyTorch installation
   - EasyOCR pre-download

2. **Update requirements.txt**:
   - Remove easyocr
   - Remove numpy (if not needed elsewhere)
   - Check for other large unused packages

3. **Use multi-stage build** (if needed):
```dockerfile
# Build stage
FROM python:3.10 as builder
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Final stage
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*.whl
```

## Expected Results
- Build time: 10+ minutes → 2-3 minutes
- Image size: Several GB → Under 1GB
- Better caching between builds

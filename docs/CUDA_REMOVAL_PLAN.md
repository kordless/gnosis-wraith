# CUDA Removal Plan

## Why CUDA is in the Project
- CUDA was added to support GPU acceleration for EasyOCR
- PyTorch (used by EasyOCR) was installed with CUDA support
- This significantly increases Docker image size and build time

## Files to Edit

### 1. **Dockerfile**
Remove these sections:

```dockerfile
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
```

Also remove:
```dockerfile
# Install PyTorch with CUDA 12.3 support
RUN pip install --no-cache-dir torch==2.2.0 torchvision==0.17.0 torchaudio==2.2.0 --index-url https://download.pytorch.org/whl/cu121
```

Since PyTorch is only needed for EasyOCR, you can remove it entirely.

## Benefits of Removing CUDA

1. **Smaller Docker image** - Reduces by several GB
2. **Faster builds** - No CUDA repository downloads
3. **Simpler deployment** - No GPU dependencies
4. **Lower memory usage** - CUDA libraries use significant memory
5. **Works on any Cloud Run instance** - No need for GPU instances

## Complete OCR/CUDA Removal

1. Remove EasyOCR from requirements.txt
2. Remove CUDA from Dockerfile
3. Remove PyTorch installation
4. Remove OCR parameters from API
5. Remove any OCR-related code

This will make your Gnosis Wraith service much lighter and easier to deploy!

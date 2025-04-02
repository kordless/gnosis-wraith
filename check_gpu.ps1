# Check if NVIDIA drivers are installed
Write-Host "Checking for NVIDIA drivers..." -ForegroundColor Cyan
try {
    $nvidiaSmiOutput = nvidia-smi
    Write-Host "NVIDIA drivers found:" -ForegroundColor Green
    Write-Host $nvidiaSmiOutput -ForegroundColor Gray
} catch {
    Write-Host "ERROR: NVIDIA drivers not found or nvidia-smi not in PATH" -ForegroundColor Red
    Write-Host "Please install the latest NVIDIA drivers from: https://www.nvidia.com/Download/index.aspx" -ForegroundColor Yellow
    exit 1
}

# Check if Docker Desktop is installed
Write-Host "`nChecking for Docker Desktop..." -ForegroundColor Cyan
try {
    $dockerVersion = docker --version
    Write-Host "Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Docker not found or not in PATH" -ForegroundColor Red
    Write-Host "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    exit 1
}

# Verify Docker GPU support
Write-Host "`nChecking Docker GPU support..." -ForegroundColor Cyan
try {
    $gpuInfo = docker run --rm --gpus all nvidia/cuda:11.0.3-base-ubuntu20.04 nvidia-smi
    Write-Host "Docker GPU support is working:" -ForegroundColor Green
    Write-Host $gpuInfo -ForegroundColor Gray
} catch {
    Write-Host "ERROR: Docker GPU support is not configured properly" -ForegroundColor Red
    Write-Host "Please ensure that:" -ForegroundColor Yellow
    Write-Host "1. 'Use GPU acceleration' is enabled in Docker Desktop Settings > Resources > GPU" -ForegroundColor Yellow
    Write-Host "2. You have restarted Docker Desktop after enabling GPU support" -ForegroundColor Yellow
    exit 1
}

Write-Host "`nAll checks passed! Your system is ready to use GPU acceleration with Docker." -ForegroundColor Green
Write-Host "You can now build and run your Gnosis Wraith container with:" -ForegroundColor Cyan
Write-Host "docker-compose up -d --build" -ForegroundColor White
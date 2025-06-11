# DevOps Refactor Plan for Gnosis Wraith

## Current Issues

### 1. Redis Connection Problem (Local Development Only)
- **Issue**: Gnosis Wraith container cannot connect to Redis container
- **Root Cause**: Using `localhost:6379` which doesn't work across containers
- **Note**: Redis should ONLY be used for local development, NOT cloud deployment

### 2. Manual Container Management
- Need to manually start containers in correct order
- No automated startup sequence
- No environment-based configuration

### 3. Local vs Cloud Configuration
- App needs to detect environment and use appropriate storage backend
- Redis for local development task queue
- File-based or Cloud Tasks for production

## Phase 1: Docker Compose Setup

### docker-compose.yml (Base Configuration)
```yaml
version: '3.8'

services:
  wraith:
    build: .
    container_name: gnosis-wraith
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      - ./storage:/app/storage
      - ./logs:/app/logs
```

### docker-compose.dev.yml (Local Development Overrides)
```yaml
version: '3.8'

services:
  redis:
    image: redis:alpine
    container_name: gnosis-redis-dev
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  wraith:
    depends_on:
      redis:
        condition: service_healthy
    environment:
      - ENVIRONMENT=development
      - REDIS_URL=redis://redis:6379
      - DEBUG=true
      - RELOAD=true
    volumes:
      - ./core:/app/core
      - ./web:/app/web
      - ./ai:/app/ai
    command: python -m uvicorn app:app --reload --host 0.0.0.0 --port 5678

volumes:
  redis-data:
```

### docker-compose.prod.yml (Production Overrides)
```yaml
version: '3.8'

services:
  wraith:
    environment:
      - ENVIRONMENT=production
      - USE_CLOUD_TASKS=true
      - REDIS_URL=  # Empty - no Redis in production
      - DEBUG=false
      - WORKERS=4
    command: python -m uvicorn app:app --host 0.0.0.0 --port 5678 --workers 4
```

## Phase 2: Environment-Aware Configuration

### Update core/config.py
```python
import os
from typing import Optional

class Config:
    # Environment detection
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    IS_DEVELOPMENT = ENVIRONMENT == 'development'
    IS_PRODUCTION = ENVIRONMENT == 'production'
    
    # Redis configuration (development only)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379') if IS_DEVELOPMENT else None
    USE_REDIS = bool(REDIS_URL) and IS_DEVELOPMENT
    
    # Cloud configuration (production only)
    USE_CLOUD_TASKS = os.getenv('USE_CLOUD_TASKS', 'false').lower() == 'true'
    GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT', '')
    
    # Storage configuration
    STORAGE_PATH = os.getenv('STORAGE_PATH', './storage')
    
    # Application settings
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG' if IS_DEVELOPMENT else 'INFO')
    WORKERS = int(os.getenv('WORKERS', '1' if IS_DEVELOPMENT else '4'))
    
    @classmethod
    def get_task_queue_backend(cls) -> str:
        """Determine which task queue backend to use"""
        if cls.IS_DEVELOPMENT and cls.USE_REDIS:
            return 'redis'
        elif cls.IS_PRODUCTION and cls.USE_CLOUD_TASKS:
            return 'cloud_tasks'
        else:
            return 'filesystem'  # Default fallback
```

### Update core/task_manager.py
```python
from core.config import Config

class TaskManager:
    def __init__(self):
        self.backend = Config.get_task_queue_backend()
        
        if self.backend == 'redis' and Config.IS_DEVELOPMENT:
            # Only initialize Redis for local development
            self._init_redis_client()
        elif self.backend == 'cloud_tasks':
            # Initialize Cloud Tasks for production
            self._init_cloud_tasks()
        else:
            # Use filesystem-based queue as fallback
            self._init_filesystem_queue()
    
    async def _init_redis_client(self):
        """Initialize Redis connection for development only"""
        if not Config.IS_DEVELOPMENT:
            raise RuntimeError("Redis should not be used in production!")
        
        try:
            import redis.asyncio as redis
            self._redis_client = redis.from_url(Config.REDIS_URL)
            logger.info("Using Redis for task queue (development mode)")
        except Exception as e:
            logger.warning(f"Redis connection failed, falling back to filesystem: {e}")
            self._init_filesystem_queue()
```

## Phase 3: Usage Commands

### Development
```bash
# Start development environment with Redis
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# View logs
docker-compose logs -f

# Rebuild after code changes
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

### Production
```bash
# Start production environment (no Redis)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Or with explicit environment
ENVIRONMENT=production docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Phase 4: Migration Scripts

### start.sh
```bash
#!/bin/bash
# Unified startup script

ENV=${1:-dev}

if [ "$ENV" == "dev" ] || [ "$ENV" == "development" ]; then
    echo "Starting development environment with Redis..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
elif [ "$ENV" == "prod" ] || [ "$ENV" == "production" ]; then
    echo "Starting production environment (no Redis)..."
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
else
    echo "Usage: ./start.sh [dev|prod]"
    exit 1
fi

# Show running containers
docker-compose ps
```

### rebuild.ps1 (Updated)
```powershell
param(
    [Parameter()]
    [ValidateSet("dev", "prod", "development", "production")]
    [string]$Environment = "dev",
    
    [switch]$NoCache = $false
)

# Map environment aliases
$env = switch ($Environment) {
    "development" { "dev" }
    "production" { "prod" }
    default { $Environment }
}

Write-Host "Rebuilding Gnosis Wraith for $env environment..." -ForegroundColor Green

# Stop existing containers
docker-compose down

# Build with appropriate compose files
$composeFiles = @("docker-compose.yml", "docker-compose.$env.yml")
$buildArgs = @("build")
if ($NoCache) {
    $buildArgs += "--no-cache"
}

docker-compose -f $composeFiles[0] -f $composeFiles[1] $buildArgs

# Start containers
docker-compose -f $composeFiles[0] -f $composeFiles[1] up -d

# Show status
docker-compose ps
```

## Phase 5: Immediate Migration Steps

1. **Create docker-compose files**:
   ```bash
   # Create the three compose files as shown above
   touch docker-compose.yml docker-compose.dev.yml docker-compose.prod.yml
   ```

2. **Update task_manager.py** to handle missing Redis gracefully:
   ```python
   # Add at the top of _process_local_tasks method
   if not hasattr(self, '_redis_client') or not Config.IS_DEVELOPMENT:
       logger.debug("Skipping Redis tasks (not in development mode)")
       return
   ```

3. **Create .env.example**:
   ```env
   # Development
   ENVIRONMENT=development
   REDIS_URL=redis://redis:6379
   DEBUG=true
   
   # Production (no Redis)
   # ENVIRONMENT=production
   # USE_CLOUD_TASKS=true
   # GOOGLE_CLOUD_PROJECT=your-project-id
   ```

4. **Test the setup**:
   ```bash
   # Development (with Redis)
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
   
   # Check Redis is only running in dev
   docker-compose ps
   
   # Production (no Redis)
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   docker-compose ps  # Should show only wraith container
   ```

## Key Principles

1. **Redis is development-only** - Never use Redis in production/cloud
2. **Environment-based configuration** - App detects environment and uses appropriate backends
3. **Graceful fallbacks** - If Redis fails in dev, fall back to filesystem
4. **Clear separation** - Development and production configs are clearly separated
5. **Easy commands** - Simple commands for different environments

## Benefits

- ✅ No more manual container management
- ✅ Redis only runs in development
- ✅ Production uses cloud-native solutions
- ✅ Easy to switch between environments
- ✅ Proper health checks and dependencies
- ✅ Hot reload in development
- ✅ Optimized for both local and cloud deployment

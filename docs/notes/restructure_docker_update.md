# Gnosis Wraith Restructuring - Docker Update Requirements

## Phase 1.5: Docker Configuration Updates

Since the app requires Docker deployment for development, these configs MUST be updated before rebuild.ps1 will work.

### Critical Docker Files to Update:

#### 1. Dockerfile
```dockerfile
# Old paths
COPY server/ /app/server/
COPY gnosis_wraith/server/ /app/gnosis_wraith/server/

# New paths
COPY core/ /app/core/
COPY web/ /app/web/
COPY ai/ /app/ai/

# Update WORKDIR if needed
WORKDIR /app

# Update any RUN commands that reference /server/
```

#### 2. docker-compose.yml
```yaml
volumes:
  # Old
  - ./server:/app/server
  - ./gnosis_wraith/server:/app/gnosis_wraith/server
  
  # New
  - ./core:/app/core
  - ./web:/app/web
  - ./ai:/app/ai
```

#### 3. docker-compose.dev.yml
Same volume updates as above

#### 4. rebuild.ps1
Update any paths that reference the old structure:
- File watchers looking at server/*
- Copy commands
- Build context paths

### Order of Operations:
1. Update Docker config files FIRST
2. Then fix Python imports
3. Then test with rebuild.ps1

### Testing:
```powershell
# After updating Docker configs
./rebuild.ps1

# Should successfully:
# - Build Docker image with new paths
# - Start container
# - Mount correct volumes
```

## Note: Without these Docker updates, rebuild.ps1 will fail!

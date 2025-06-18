# Local Storage Fix Plan - Getting Ready for Full Deployment

## Current Storage Issues

### Problem Analysis
1. **Reports disappearing**: Container uses internal `/data` volume, reports are lost between container restarts
2. **No host mounting**: Current docker-compose uses Docker volume (`wraith-data`) instead of host directory
3. **Path confusion**: Multiple storage paths configured but not properly mounted
4. **One report only**: Likely due to filename collisions or storage not persisting

### Current Setup
```yaml
# docker-compose.yml
volumes:
  - wraith-data:/data  # Docker volume (not host directory!)
  - ./host-files:/host-files  # Only for extension files

# Dockerfile
ENV GNOSIS_WRAITH_STORAGE_PATH=/data
VOLUME /data  # Creates anonymous volume
```

## Phase 1: Immediate Fix - Host Directory Mounting

### 1.1 Create Local Storage Structure
```bash
# Create directories on host
mkdir -p ./storage/reports
mkdir -p ./storage/screenshots
mkdir -p ./storage/system
mkdir -p ./storage/logs
```

### 1.2 Update docker-compose.yml
```yaml
services:
  wraith:
    volumes:
      - ./storage:/data  # Mount host directory instead of Docker volume
      - ./host-files:/host-files
    environment:
      - GNOSIS_WRAITH_STORAGE_PATH=/data
```

### 1.3 Update docker-compose.dev.yml 
```yaml
services:
  web:
    volumes:
      - ./storage:/data  # Consistent with production
      - ./storage:/app/storage  # Legacy path support
      - ./local_datastore:/app/local_datastore
```

## Phase 2: Storage Path Standardization

### 2.1 Fix Path Constants in core/config.py
```python
# Standardize on /data as the root storage path
STORAGE_PATH = os.environ.get('GNOSIS_WRAITH_STORAGE_PATH', '/data')
REPORTS_DIR = os.path.join(STORAGE_PATH, 'reports')
SCREENSHOTS_DIR = os.path.join(STORAGE_PATH, 'screenshots')
SYSTEM_DIR = os.path.join(STORAGE_PATH, 'system')
LOGS_DIR = os.path.join(STORAGE_PATH, 'logs')
```

### 2.2 Create Docker entrypoint script
```bash
#!/bin/bash
# entrypoint.sh - Ensure directories exist
mkdir -p /data/reports /data/screenshots /data/system /data/logs
exec "$@"
```

## Phase 3: Fix Filename Collisions

### 3.1 Update Report Naming
Current issue: Multiple reports might be overwriting each other
```python
# In core/reports.py or filename_utils.py
def generate_report_filename(url, title=None):
    # Add timestamp to prevent collisions
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    domain = extract_domain(url)
    if title:
        # Include timestamp: domain_hash_timestamp.md
        return f"{domain}_{hash}_{timestamp}.md"
    else:
        # Simple: domain_timestamp.md
        return f"{domain}_{timestamp}.md"
```

## Phase 4: Quick Migration Steps

### For Existing Users
1. **Backup current data** (if any exists in Docker volume):
   ```bash
   docker cp wraith-service:/data ./storage_backup
   ```

2. **Stop containers**:
   ```bash
   docker-compose down
   ```

3. **Update docker-compose.yml** with host mount

4. **Restart with new config**:
   ```bash
   docker-compose up -d
   ```

## Phase 5: Testing & Verification

### 5.1 Test Persistence
```bash
# 1. Create a test crawl
curl -X POST http://localhost:5678/api/crawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# 2. Check files exist
ls -la ./storage/reports/
ls -la ./storage/screenshots/

# 3. Restart container
docker-compose restart

# 4. Verify files still exist
ls -la ./storage/reports/
```

### 5.2 Test Multiple Reports
```bash
# Run multiple crawls
for i in {1..5}; do
  curl -X POST http://localhost:5678/api/crawl \
    -d "{\"url\": \"https://example.com/page$i\"}"
  sleep 2
done

# Verify all reports exist
ls -la ./storage/reports/ | wc -l  # Should show 5+ files
```

## Phase 6: Prepare for Full Deployment Plan

### 6.1 Storage Structure for Multi-User
```
storage/
├── anonymous/           # Unauthenticated users
│   ├── reports/
│   └── screenshots/
├── users/              # Authenticated users
│   ├── [user_hash]/
│   │   ├── reports/
│   │   └── screenshots/
└── system/             # System-wide data
    ├── cache/
    └── logs/
```

### 6.2 Environment Variables
```bash
# .env.local
STORAGE_PATH=./storage
ENABLE_USER_BUCKETING=false  # Start simple
RUNNING_IN_CLOUD=false

# .env.production
STORAGE_PATH=/data
ENABLE_USER_BUCKETING=true
RUNNING_IN_CLOUD=true
```

## Immediate Action Items

1. **Update docker-compose.yml** - Change volume mount to `./storage:/data`
2. **Create storage directories** - Run `mkdir -p ./storage/{reports,screenshots,system,logs}`
3. **Test with multiple crawls** - Verify reports aren't overwriting
4. **Document for users** - Add to README about local storage

## Benefits of This Approach

- **Immediate fix**: Reports persist between container restarts
- **User-friendly**: Can browse reports directly in `./storage/reports/`
- **Backup-friendly**: Easy to backup/restore the storage directory
- **Migration-ready**: Structure supports future user bucketing
- **Development-friendly**: Can inspect files without entering container

## Next Steps After This Fix

Once storage is working locally:
1. Implement user bucketing (from deployment plan)
2. Add auth system integration
3. Test cloud storage (GCS) integration
4. Deploy with full multi-user support

This incremental approach gets local users working immediately while preparing for the full deployment architecture.

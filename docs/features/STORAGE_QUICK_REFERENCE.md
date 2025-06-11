# Storage Service Quick Reference

## At a Glance

**Purpose**: Unified storage abstraction with user isolation for local and cloud deployment.

## Key Concepts

- **User Hash**: 12-character SHA-256 hash for user identification
- **Bucketing**: Reports organized by user hash
- **Abstraction**: Same API for local filesystem and Google Cloud Storage

## Quick Start

```python
# Import the service
from server.storage_service_v2 import UserAwareStorageService

# Initialize with user context
storage = UserAwareStorageService(user_hash='a1b2c3d4e5f6')

# Save a report
report_path = await storage.save_report(
    content="# My Report\nContent here...",
    filename="my_report_20250604",
    format="md"
)

# List user's reports
reports = await storage.list_reports()

# Get download URL
url = storage.get_report_url("my_report_20250604.md")
```

## Route Integration

```python
from server.middleware import with_user_storage

@app.route('/api/my-endpoint')
@with_user_storage
async def my_endpoint(storage_service):
    # storage_service is automatically injected with user context
    reports = await storage_service.list_reports()
    return jsonify(reports)
```

## User Hash Generation

```python
# For authenticated users
user_hash = UserAwareStorageService.generate_user_hash(user_id="12345")

# For anonymous users (from request)
user_hash = UserAwareStorageService.generate_user_hash(
    request_headers=dict(request.headers)
)
```

## Storage Structure

```
Local:                          Cloud (GCS):
storage/                        gs://bucket/
└── users/                      └── users/
    ├── a1b2c3d4e5f6/              ├── a1b2c3d4e5f6/
    │   ├── reports/               │   ├── reports/
    │   └── screenshots/           │   └── screenshots/
    └── system/                    └── system/
```

## Environment Variables

| Variable | Local Dev | Production |
|----------|-----------|------------|
| `RUNNING_IN_CLOUD` | `false` | `true` |
| `STORAGE_PATH` | `./storage` | - |
| `GCS_BUCKET_NAME` | - | `gnosis-wraith-storage` |
| `ENABLE_USER_BUCKETING` | `true` | `true` |

## Common Operations

### Save Report
```python
path = await storage.save_report(content, filename, format='md')
```

### Get Report
```python
content = await storage.get_report('report_name.md')
```

### List Reports
```python
reports = await storage.list_reports(format='md')  # Optional filter
```

### Delete Report
```python
success = await storage.delete_report('report_name.md')
```

### Get Stats
```python
stats = await storage.get_user_storage_stats()
# Returns: {files: 10, total_size: 1048576, last_modified: ...}
```

## Admin Operations

```python
# List all users
storage_admin = UserAwareStorageService(user_hash='admin')
users = await storage_admin.list_all_users()

# Access specific user's data
user_storage = UserAwareStorageService(user_hash='target_user_hash')
user_reports = await user_storage.list_reports()
```

## Testing

```bash
# Run storage tests
python test_storage_service.py

# Test with cloud mode
RUNNING_IN_CLOUD=true python test_storage_service.py
```

## Migration

```bash
# Migrate existing reports to user buckets
python scripts/migrate_to_user_buckets.py

# Verify migration
python scripts/verify_migration.py
```

## Debugging

```python
# Enable debug logging
import logging
logging.getLogger('storage_service').setLevel(logging.DEBUG)

# Check storage configuration
from server.storage_service_v2 import get_storage_info
info = get_storage_info()
print(info)  # {'environment': 'local', 'reports_dir': '...', ...}
```

## Error Handling

```python
try:
    report = await storage.get_report('missing.md')
except FileNotFoundError:
    # Handle missing report
    pass
except PermissionError:
    # Handle permission issues
    pass
except Exception as e:
    # Handle other errors
    logger.error(f"Storage error: {e}")
```

## Best Practices

1. **Always use middleware** for user context in routes
2. **Never hardcode paths** - use storage service methods
3. **Handle errors gracefully** - reports might not exist
4. **Set retention policies** for anonymous users
5. **Monitor storage usage** - implement quotas

## Common Issues

| Issue | Solution |
|-------|----------|
| Reports not isolated | Check middleware is applied |
| Permission errors | Verify directory permissions |
| GCS auth fails | Run `gcloud auth application-default login` |
| User hash changes | Ensure consistent headers/session |

## Links

- [Full Implementation Guide](./STORAGE_IMPLEMENTATION_GUIDE.md)
- [Storage Abstraction Plan](../notes/STORAGE_ABSTRACTION_PLAN.md)
- [Migration Scripts](../scripts/)
- [Test Suite](../tests/test_storage_service.py)

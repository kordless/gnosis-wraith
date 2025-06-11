# User Storage System Guide

## Overview

The Gnosis Wraith user storage system provides isolated storage spaces for each user, ensuring privacy and data separation in multi-user environments.

## Directory Structure

```
storage/
├── users/
│   ├── anonymous/          # Shared space for unauthenticated users
│   │   ├── reports/       # Anonymous user reports
│   │   └── screenshots/   # Anonymous user screenshots
│   │
│   └── [user_hash_12]/    # Authenticated user directories
│       ├── reports/       # User-specific reports
│       ├── screenshots/   # User-specific screenshots
│       └── config/        # User-specific settings (future)
│
└── system/                # System-wide data
    └── migration_v1_completed.txt
```

## User Identification

- **Anonymous Users**: All unauthenticated users share the `anonymous` directory
- **Authenticated Users**: Each user gets a unique directory based on SHA256(email)[:12]

## Migration

When upgrading from the old flat storage structure, run the migration script:

```bash
python migrate_to_user_storage.py
```

This will move all existing reports and screenshots to the `anonymous` user directory.

## Environment Variables

- `ENABLE_USER_PARTITIONING=true` - Enable user-specific storage (default: false)
- `GNOSIS_WRAITH_STORAGE_PATH=/data` - Base storage path

## Implementation Details

### Reports

Reports are saved to user-specific directories:
- Anonymous: `/data/users/anonymous/reports/`
- Authenticated: `/data/users/[hash]/reports/`

### Screenshots

Screenshots follow the same pattern:
- Anonymous: `/data/users/anonymous/screenshots/`
- Authenticated: `/data/users/[hash]/screenshots/`

### API Changes

All API endpoints now automatically use the current user's context from the session:

```python
# Reports are automatically saved to user directory
markdown_path = await save_markdown_report(title, crawl_results)

# Screenshots are automatically saved to user directory
screenshot_path = await browser_control.screenshot(path)
```

### URL Structure

Screenshot URLs now include the user hash for proper routing:
- Anonymous: `/screenshots/anonymous/filename.png`
- Authenticated: `/screenshots/[user_hash]/filename.png`

## Security

- Users cannot access other users' files
- The system verifies user hash matches session on screenshot requests
- Directory traversal attacks are prevented by sanitizing filenames

## Backwards Compatibility

- Legacy routes are maintained for existing links
- Migration script preserves all existing data
- System falls back to shared storage if partitioning is disabled

## Troubleshooting

### Reports Not Showing

1. Check if `ENABLE_USER_PARTITIONING=true` is set
2. Verify user is logged in (check session)
3. Check if migration has been run

### Screenshots Not Loading

1. Verify the screenshot URL includes the user hash
2. Check if user has permission to access the file
3. Ensure the file exists in the user's screenshot directory

### Migration Issues

1. Ensure storage directory has write permissions
2. Check if there's enough disk space
3. Review migration logs for specific errors

## Future Enhancements

- User quotas and limits
- Shared reports between users
- Organization-level storage
- Cloud storage backend support
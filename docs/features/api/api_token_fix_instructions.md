# API Token UI Fix - Auth Blueprint Registration

## Problem Fixed
The auth routes were not being registered with the Flask/Quart app, causing 404 errors when trying to access `/auth/token/check` and `/auth/token/regenerate`.

## Changes Made

### 1. Updated `web/routes/__init__.py`:
- Added import for auth blueprint
- Added registration of auth blueprint in `register_blueprints()` function
- Added auth to logging output

### 2. UI Already Updated:
- ProfileSettingsModal has full token management UI
- Token display with blur effect for security
- Generate/regenerate functionality
- Show/hide toggle
- Copy to clipboard

## Required Action
**You need to restart the Docker container for the auth blueprint to be registered:**

```bash
# Option 1: Using rebuild script
./rebuild.ps1

# Option 2: Using docker-compose
docker-compose down
docker-compose up -d

# Option 3: Just restart the container
docker restart gnosis-wraith
```

## Testing
After restart:
1. Login to the application
2. Click the profile icon in the top right
3. You should see the API Token section
4. Click "Generate API Token" to create your first token
5. Use the show/hide toggle to view the token
6. Copy button will copy the full token to clipboard

## API Token Usage
Once generated, use the token in API calls:
```
Authorization: Bearer YOUR_API_TOKEN
```

The backend endpoints at `/auth/token/check` and `/auth/token/regenerate` are already implemented and will work once the auth blueprint is registered.
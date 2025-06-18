# Cloud Run Environment Variables for Gnosis Wraith

Copy and paste these into the Cloud Run environment variables section:

## Required Variables

```
RUNNING_IN_CLOUD=true
GCS_BUCKET_NAME=gnosis-wraith-storage
SECRET_KEY=your-secure-secret-key-here-change-this
APP_DOMAIN=your-service-name.run.app
```

## Optional Branding Variables

```
BRAND=Gnosis Wraith
BRAND_FAVICON=/static/images/favicon.ico
BRAND_COLOR=#6c63ff
BRAND_SERVICE=Gnosis Wraith
BRAND_SERVICE_URL=https://gnosis-wraith.com
BRAND_GITHUB_URL=https://github.com/your-username/gnosis-wraith
ENVIRONMENT=production
ENABLE_DEV_ENDPOINTS=false
```

## Storage Configuration

```
STORAGE_PATH=/data
GNOSIS_WRAITH_STORAGE_PATH=/data
```

## Complete .env format for bulk paste:

```
RUNNING_IN_CLOUD=true
GCS_BUCKET_NAME=gnosis-wraith-storage
SECRET_KEY=your-secure-secret-key-here-change-this
APP_DOMAIN=your-service-name.run.app
BRAND=Gnosis Wraith
BRAND_FAVICON=/static/images/favicon.ico
BRAND_COLOR=#6c63ff
BRAND_SERVICE=Gnosis Wraith
BRAND_SERVICE_URL=https://gnosis-wraith.com
BRAND_GITHUB_URL=https://github.com/your-username/gnosis-wraith
ENVIRONMENT=production
ENABLE_DEV_ENDPOINTS=false
STORAGE_PATH=/data
GNOSIS_WRAITH_STORAGE_PATH=/data
```

## Important Notes:

1. **SECRET_KEY**: Generate a secure key using:
   - Python: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
   - Or online generator (use a reputable one)

2. **GCS_BUCKET_NAME**: 
   - Must be globally unique
   - Use format: `gnosis-wraith-yourname-prod`
   - Will be created automatically if doesn't exist

3. **APP_DOMAIN**: 
   - Will be provided by Cloud Run after deployment
   - Update this after first deployment

4. The storage service will automatically detect it's running in cloud and use GCS instead of local storage.

5. Make sure your Cloud Run service account has the necessary permissions for GCS bucket operations.

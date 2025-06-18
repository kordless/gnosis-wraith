# Cloud Run Deployment Guide for Gnosis Wraith

## Storage Configuration

The project uses a dual storage system that automatically switches between local and cloud storage based on environment:

### Storage Architecture
- **Local Development**: Files stored in `storage/` directory
- **Cloud Run**: Files stored in Google Cloud Storage (GCS)
- **NDB Models**: Local JSON files or Google Datastore (automatic)

## Required Environment Variables for Cloud Run

### Core Configuration
```bash
# Essential - tells the app it's running in cloud
RUNNING_IN_CLOUD=true

# GCS Bucket for file storage
GCS_BUCKET_NAME=your-gnosis-wraith-storage-bucket

# App configuration
SECRET_KEY=your-secure-secret-key-here
APP_DOMAIN=your-app-domain.run.app

# Branding (optional)
BRAND=Gnosis Wraith
BRAND_SERVICE_URL=https://your-domain.com
```

### Storage Service Configuration
The storage service (`core/storage_service.py`) automatically:
- Detects cloud environment via `RUNNING_IN_CLOUD`
- Creates GCS bucket if it doesn't exist
- Handles user-partitioned storage with hash bucketing
- Provides signed URLs for file access

## Deploy via Cloud Console

1. **Build and push Docker image**:
```bash
# Build the image
docker build -t gcr.io/YOUR_PROJECT_ID/gnosis-wraith:latest .

# Push to Container Registry
docker push gcr.io/YOUR_PROJECT_ID/gnosis-wraith:latest
```

2. **Create Cloud Run service**:
```bash
gcloud run deploy gnosis-wraith \
  --image gcr.io/YOUR_PROJECT_ID/gnosis-wraith:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --port 5678 \
  --set-env-vars "RUNNING_IN_CLOUD=true,GCS_BUCKET_NAME=your-bucket-name,SECRET_KEY=your-secret-key"
```

## Deploy via CLI with All Variables

For a complete deployment with all environment variables:

```bash
gcloud run deploy gnosis-wraith \
  --image gcr.io/YOUR_PROJECT_ID/gnosis-wraith:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --port 5678 \
  --set-env-vars "RUNNING_IN_CLOUD=true" \
  --set-env-vars "GCS_BUCKET_NAME=gnosis-wraith-storage-prod" \
  --set-env-vars "SECRET_KEY=$(openssl rand -base64 32)" \
  --set-env-vars "APP_DOMAIN=gnosis-wraith-xxxxx-uc.a.run.app" \
  --set-env-vars "BRAND=Gnosis Wraith" \
  --set-env-vars "BRAND_SERVICE_URL=https://gnosis-wraith.com" \
  --set-env-vars "BRAND_GITHUB_URL=https://github.com/your-org/gnosis-wraith" \
  --set-env-vars "ENVIRONMENT=production" \
  --set-env-vars "ENABLE_DEV_ENDPOINTS=false"
```

## GCS Bucket Setup

Create and configure the GCS bucket:

```bash
# Create bucket
gsutil mb -p YOUR_PROJECT_ID -c STANDARD -l us-central1 gs://gnosis-wraith-storage-prod/

# Set CORS policy (create cors.json first)
gsutil cors set cors.json gs://gnosis-wraith-storage-prod/

# Grant Cloud Run service account access
gsutil iam ch serviceAccount:YOUR_SERVICE_ACCOUNT@developer.gserviceaccount.com:objectAdmin gs://gnosis-wraith-storage-prod/
```

### CORS Configuration (cors.json)
```json
[
  {
    "origin": ["*"],
    "method": ["GET", "HEAD", "PUT", "POST", "DELETE"],
    "responseHeader": ["*"],
    "maxAgeSeconds": 3600
  }
]
```

## Service Account Permissions

The Cloud Run service account needs:
- `storage.buckets.create`
- `storage.objects.create`
- `storage.objects.delete`
- `storage.objects.get`
- `storage.objects.list`
- `datastore.entities.create` (if using Datastore)
- `datastore.entities.get`
- `datastore.entities.list`
- `datastore.entities.update`
- `datastore.entities.delete`

## Authentication Considerations

The app uses session-based authentication. For production:

1. Set a strong `SECRET_KEY`
2. Consider implementing OAuth2 for production
3. The auth system stores user data in Datastore (automatic in cloud mode)

## Monitoring

Enable Cloud Logging to monitor the application:
- Storage operations are logged with user hash
- File operations include full paths
- Errors are logged with stack traces

## Testing Cloud Storage Locally

To test cloud storage locally:

```bash
# Set up credentials
export GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json

# Set environment variables
export RUNNING_IN_CLOUD=true
export GCS_BUCKET_NAME=test-bucket-name

# Run the app
python app.py
```

## Important Notes

1. The storage service automatically handles the transition between local and cloud storage
2. User files are partitioned using SHA-256 hash of email (first 12 chars)
3. Anonymous users get a consistent hash
4. File URLs are signed with 24-hour expiry by default
5. The app creates the GCS bucket if it doesn't exist (requires permission)

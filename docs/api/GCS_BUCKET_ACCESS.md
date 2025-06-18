# GCS Bucket Access for Cloud Run

## Default Behavior

By default, Cloud Run services use the **Compute Engine default service account**:
- Format: `PROJECT-NUMBER-compute@developer.gserviceaccount.com`
- This account has the **Editor** role by default, which includes GCS access

## Checking Access

1. **Find your Cloud Run service account:**
   ```bash
   gcloud run services describe gnosis-wraith --region=us-central1 --format="value(spec.template.spec.serviceAccountName)"
   ```

2. **Check bucket IAM permissions:**
   ```bash
   gsutil iam get gs://your-bucket-name
   ```

## Granting Access (if needed)

If your Cloud Run service can't access the bucket, grant permissions:

### Option 1: Grant to Default Service Account
```bash
# Get your project number
PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)")

# Grant Storage Admin role to the default service account
gsutil iam ch serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com:roles/storage.admin gs://your-bucket-name
```

### Option 2: Use a Custom Service Account (Recommended for production)
```bash
# Create a service account
gcloud iam service-accounts create gnosis-wraith-sa \
    --display-name="Gnosis Wraith Service Account"

# Grant necessary permissions
gsutil iam ch serviceAccount:gnosis-wraith-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com:roles/storage.objectAdmin gs://your-bucket-name

# Deploy Cloud Run with custom service account
gcloud run deploy gnosis-wraith \
    --service-account=gnosis-wraith-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --image=gcr.io/YOUR_PROJECT_ID/gnosis-wraith:latest
```

## Required Permissions

The storage service needs these permissions on the bucket:
- `storage.buckets.get`
- `storage.objects.create`
- `storage.objects.delete`
- `storage.objects.get`
- `storage.objects.list`

## Automatic Bucket Creation

The code in `storage_service.py` tries to create the bucket if it doesn't exist:

```python
try:
    bucket = self._gcs_client.get_bucket(self._bucket_name)
except Exception:
    bucket = self._gcs_client.create_bucket(self._bucket_name)
```

For this to work, the service account needs `storage.buckets.create` permission (included in Storage Admin role).

## Testing Access

After deployment, check Cloud Run logs for any GCS errors:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=gnosis-wraith" --limit=50
```

## Quick Check Command

Run this to verify everything is set up:
```bash
# Check if default service account has access
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)")
gsutil iam get gs://your-bucket-name | grep ${PROJECT_NUMBER}-compute@developer.gserviceaccount.com
```

If you see the service account listed with appropriate roles, Cloud Run should be able to access the bucket!

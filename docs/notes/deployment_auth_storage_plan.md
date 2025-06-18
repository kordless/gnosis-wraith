# Gnosis Wraith Deployment Plan - Auth & Storage Ready

## Current Status
We've implemented storage abstraction and auth models, but need to wire everything together for deployment. This plan gets us from current state to deployable with auth enabled.

## Phase 1: Complete Auth Wiring

### 1.1 Enable Flask-Login in app.py
```python
# Add to app.py after app initialization
from flask_login import LoginManager
from core.models.user import User

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_uid(user_id)
```

### 1.2 Fix Auth Blueprint Registration
Make sure auth blueprint is registered in `app.py`:
```python
from web.routes import register_blueprints
register_blueprints(app)  # This should include auth
```

### 1.3 Update Protected Routes
Add `@login_required` decorator to sensitive endpoints:
```python
# In web/routes/pages.py
from flask_login import login_required

@pages.route('/reports')
@login_required
async def reports():
    # Existing code
```

## Phase 2: Storage with User Context

### 2.1 Update EnhancedStorageService
Add user bucketing to `core/enhanced_storage_service.py`:
```python
from flask_login import current_user
import hashlib

def _get_user_hash(self) -> str:
    """Get current user's storage hash"""
    try:
        if hasattr(current_user, 'email') and current_user.is_authenticated:
            return hashlib.sha256(current_user.email.encode()).hexdigest()[:12]
    except:
        pass
    return 'anonymous'
```

### 2.2 Update Save Methods
Modify save_report to use user buckets:
```python
async def save_report(self, content: str, filename: str, format: str = 'md') -> str:
    user_hash = self._get_user_hash()
    
    if is_running_in_cloud():
        # GCS path with user bucket
        return await self.save_file(content, f'users/{user_hash}/reports', f'{filename}.{format}')
    else:
        # Local path with user bucket
        user_reports_dir = os.path.join(self._reports_dir, 'users', user_hash)
        os.makedirs(user_reports_dir, exist_ok=True)
        # ... rest of logic
```

## Phase 3: Environment Configuration

### 3.1 Development (.env)
```bash
# Auth Settings
USE_LOCAL_DATASTORE=true
LOCAL_DATASTORE_PATH=./local_datastore
DEV=True
SECRET_KEY=your-dev-secret-key-here
APP_DOMAIN=localhost:5678

# Email (SendGrid)
SENDGRID_API_KEY=SG.xxxxx  # Get from SendGrid dashboard
FROM_EMAIL=noreply@gnosis.ai

# SMS (Twilio) - Optional
TWILIO_ACCOUNT_SID=ACxxxxx  # Get from Twilio console
TWILIO_AUTH_TOKEN=xxxxx
TWILIO_NUMBER=+1234567890

# Storage
RUNNING_IN_CLOUD=false
STORAGE_PATH=./storage
ENABLE_USER_BUCKETING=true
```

### 3.2 Production (Google Cloud Run)
```bash
# Create secrets
gcloud secrets create sendgrid-api-key --data-file=<(echo $SENDGRID_API_KEY)
gcloud secrets create secret-key --data-file=<(echo $SECRET_KEY)
gcloud secrets create anthropic-api-key --data-file=<(echo $ANTHROPIC_API_KEY)

# Create GCS bucket
gsutil mb gs://gnosis-wraith-prod
gsutil iam ch allUsers:objectViewer gs://gnosis-wraith-prod  # For public screenshots

# Deploy with secrets
gcloud run deploy gnosis-wraith \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "RUNNING_IN_CLOUD=true,GCS_BUCKET_NAME=gnosis-wraith-prod,ENABLE_USER_BUCKETING=true" \
  --set-secrets "ANTHROPIC_API_KEY=anthropic-api-key:latest,SENDGRID_API_KEY=sendgrid-api-key:latest,SECRET_KEY=secret-key:latest"
```

## Phase 4: Docker Updates

### 4.1 Update requirements.txt
Add missing dependencies:
```
flask-login==0.6.3
google-cloud-storage==2.10.0
sendgrid==6.11.0
twilio==8.11.0
aiofiles==23.2.1
```

### 4.2 Update docker-compose.yml
Add environment variables:
```yaml
services:
  web:
    environment:
      - USE_LOCAL_DATASTORE=true
      - LOCAL_DATASTORE_PATH=/app/local_datastore
      - SECRET_KEY=${SECRET_KEY}
      - SENDGRID_API_KEY=${SENDGRID_API_KEY}
    volumes:
      - ./local_datastore:/app/local_datastore
      - ./storage:/app/storage
```

## Phase 5: Testing Auth Flow

### 5.1 Local Testing
```bash
# 1. Start the app
docker-compose up --build

# 2. Test login flow
curl http://localhost:5678/auth/login
# Should see login page

# 3. Submit email
curl -X POST http://localhost:5678/auth/login \
  -d "email=test@example.com"
# In DEV mode, token prints to console

# 4. Submit token
curl -X POST http://localhost:5678/auth/token \
  -d "token=123456"
# Should redirect to main app
```

### 5.2 Production Testing
- Visit https://your-app.run.app/auth/login
- Enter email
- Check email for token (or SMS if configured)
- Enter token
- Verify redirect to authenticated app

## Phase 6: Quick Start Commands

### Local Development with Auth
```bash
# Clone and setup
git clone https://github.com/kordless/gnosis.git
cd gnosis/gnosis-wraith
cp .env.example .env
# Edit .env with your keys

# Run with Docker
docker-compose up --build

# Access at http://localhost:5678
```

### Deploy to Google Cloud Run
```bash
# One-time setup
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Deploy script
cat > deploy.sh << 'EOF'
#!/bin/bash
echo "Deploying Gnosis Wraith to Cloud Run..."

# Build and push
gcloud builds submit --tag gcr.io/$PROJECT_ID/gnosis-wraith

# Deploy
gcloud run deploy gnosis-wraith \
  --image gcr.io/$PROJECT_ID/gnosis-wraith \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "RUNNING_IN_CLOUD=true,GCS_BUCKET_NAME=gnosis-wraith-prod" \
  --set-secrets "ANTHROPIC_API_KEY=anthropic-api-key:latest"

echo "Deployment complete!"
EOF

chmod +x deploy.sh
./deploy.sh
```

## Phase 7: Post-Deployment Checklist

- [ ] Auth flow works (login/logout)
- [ ] Reports save to user buckets
- [ ] Screenshots accessible via public URLs
- [ ] API endpoints require authentication
- [ ] Storage isolation verified (users can't see each other's data)
- [ ] Email sending works (SendGrid configured)
- [ ] Session persistence works
- [ ] HTTPS enforced on production

## Known Issues to Address

1. **Quart vs Flask**: Auth routes use Flask but app uses Quart
   - Solution: Convert auth routes to async Quart style

2. **Session Storage**: Local uses filesystem, cloud needs Redis/Firestore
   - Solution: Add session backend configuration

3. **Rate Limiting**: No rate limiting on auth endpoints
   - Solution: Add rate limiting middleware

4. **CORS**: May need CORS headers for API usage
   - Solution: Add flask-cors with proper origins

## Next Steps After Deployment

1. **Monitoring**
   - Set up Cloud Logging
   - Add error reporting
   - Monitor auth failures

2. **Scaling**
   - Configure Cloud Run autoscaling
   - Set up Cloud CDN for static assets
   - Add caching layer

3. **Security**
   - Enable Cloud Armor
   - Set up SSL certificates
   - Add CSP headers

## Support Resources

- SendGrid Dashboard: https://app.sendgrid.com
- Twilio Console: https://console.twilio.com
- Google Cloud Console: https://console.cloud.google.com
- Cloud Run Docs: https://cloud.google.com/run/docs

---

*Note: This plan assumes you have Google Cloud SDK installed and a GCP project created. Adjust bucket names and regions as needed for your setup.*

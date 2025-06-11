# 🔧 Repair Plan for Gnosis Wraith Import Errors

## Current Issues Identified

### 1. Primary Import Error
- **Error**: `No module named 'server.job_manager'`
- **Cause**: Phase 2 restructuring wasn't completed for all files
- **Impact**: Application fails to start properly

### 2. Template Path Issues
- **Problem**: Auth routes looking for templates in wrong location
- **Fixed**: Changed `pages/*.html` to `auth/*.html` in auth.py
- **Remaining**: Missing template files:
  - `auth/verify.html` (phone verification)
  - `auth/tfa.html` (2FA form)
  - `auth/phone.html` (phone setup)

### 3. API Response Issue
- **Symptom**: Crawl returning HTML error pages instead of JSON
- **Cause**: Authentication requirement on `/api/crawl` endpoint
- **User Experience**: "Unexpected token '<', "<!DOCTYPE "... is not valid JSON"

## Files That Need Import Updates

The restructuring moved directories:
- `/server/` → `/core/` (processing engine)
- `/gnosis_wraith/server/routes/` → `/web/routes/`
- `/gnosis_wraith/server/static/` → `/web/static/`
- `/gnosis_wraith/server/templates/` → `/web/templates/`

### Search Patterns to Find Bad Imports

```bash
# Find all files still using old imports
grep -r "from server\." --include="*.py" .
grep -r "import server\." --include="*.py" .
grep -r "from gnosis_wraith\.server" --include="*.py" .
```

### Import Replacement Patterns

1. `from server.` → `from core.`
2. `import server.` → `import core.`
3. `from server.routes` → `from web.routes`
4. `from gnosis_wraith.server.` → Update based on new structure

## Recommended Actions

### 1. Complete Phase 2 Import Fixes (HIGHEST PRIORITY)
- Run the search patterns above to find all remaining old imports
- Update all imports according to the restructuring:
  ```python
  # Old
  from server.job_manager import JobManager
  from server.storage_service import StorageService
  from server.config import STORAGE_PATH
  
  # New
  from core.job_manager import JobManager
  from core.storage_service import StorageService
  from core.config import STORAGE_PATH
  ```

### 2. Create Missing Auth Templates
Either:
- **Option A**: Create minimal templates in `/web/templates/auth/`:
  - `verify.html` - Phone verification form
  - `tfa.html` - Two-factor authentication form
  - `phone.html` - Phone number setup form
  
- **Option B**: Modify auth flow to skip these steps temporarily

### 3. Fix API Authentication Issue
The `/api/crawl` endpoint has `@login_required` decorator but the UI might not be authenticated:
- Check if session cookies are being sent
- Verify authentication flow is working
- Consider adding debug logging to see why authentication is failing

## Quick Fix for Immediate Relief

To get the app running quickly:

1. **Find the bad import**:
   ```bash
   grep -r "server.job_manager" --include="*.py" .
   ```

2. **Update it to**:
   ```python
   from core.job_manager import JobManager
   ```

3. **Restart the container**:
   ```powershell
   docker restart gnosis-wraith
   ```

## Expected Outcomes After Fix

1. ✅ Application starts without import errors
2. ✅ Job system initializes properly
3. ✅ API endpoints return JSON responses
4. ✅ Crawling functionality works again

## Reference Documents

- `notes/restructure_phase2_fix_imports.md` - Original import fix plan
- `notes/claude_code_phase2.md` - What Claude Code was working on
- `notes/restructure_phase3_auth_storage.md` - Auth implementation details

## Notes for Claude Code

The restructuring was a major change that touched every file. It appears that while the files were moved correctly (Phase 1), not all imports were updated (Phase 2). This is a common issue with large refactoring operations. A systematic search and replace using the patterns above should resolve the issues.
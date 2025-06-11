# Debugging Stage 3 Rework - Import Issues

## Current Error
```
ModuleNotFoundError: No module named 'gnosis_wraith.server'
```

## Root Cause
The restructuring moved files but there are still references to the old structure:
- Old: `gnosis_wraith.server.*`
- New: `web.*` and `core.*`

## Files That Need Import Updates

### 1. Python Files Still Using Old Imports
Need to search for and update:
- `from gnosis_wraith.server` → `from web` or `from core`
- `import gnosis_wraith.server` → `import web` or `import core`

### 2. Likely Problem Areas
- `__init__.py` files may have old imports
- Route files in `/web/routes/`
- Core processing files in `/core/`
- The main `app.py` seems OK but double-check
- Any config files that reference module paths

### 3. Docker/Deployment Issues
- Dockerfile may have PYTHONPATH issues
- Need to ensure `/app` is in PYTHONPATH
- Check if hypercorn is looking in the right place

## Search Strategy
```bash
# Find all files with old imports
grep -r "gnosis_wraith.server" --include="*.py"
grep -r "from server" --include="*.py"
```

## Common Import Patterns to Fix

### Old Pattern 1: Absolute imports
```python
from gnosis_wraith.server.routes import api
from gnosis_wraith.server.lib.util import some_function
```

### New Pattern 1: Update to new structure
```python
from web.routes import api
from core.lib.util import some_function
```

### Old Pattern 2: Relative imports in moved files
```python
from .lib.util import function  # When file was in server/
```

### New Pattern 2: Update relative paths
```python
from ..lib.util import function  # If file moved to server/subfolder/
```

## Files to Check First
1. `/web/routes/__init__.py` - Likely has blueprint imports
2. `/web/routes/api.py` - May import from core
3. `/web/routes/auth.py` - May import from core
4. `/core/__init__.py` - May have initialization imports
5. Any file that imports models, storage, or utilities

## Quick Fix Checklist
- [ ] Run grep to find all `gnosis_wraith.server` references
- [ ] Update all imports to use `web` or `core`
- [ ] Check relative imports in moved files
- [ ] Verify `__init__.py` files are correct
- [ ] Ensure PYTHONPATH includes project root
- [ ] Test imports with `python -c "import core"` etc.

## Docker Specific
The error is happening in hypercorn trying to load the app, so also check:
- How is hypercorn being called? 
- Is it looking for `app:app` in the right place?
- Does Docker have the correct WORKDIR?

## Next Steps
1. Search for all old import patterns
2. Update them systematically
3. Pay special attention to __init__.py files
4. Test imports before rebuilding Docker

## For Claude Code
The error `ModuleNotFoundError: No module named 'gnosis_wraith.server'` means something is still trying to import the old module structure.

### Priority Search Commands:
```bash
# Find all Python files with old imports
grep -r "gnosis_wraith.server" . --include="*.py"
grep -r "from gnosis_wraith" . --include="*.py"
grep -r "import gnosis_wraith" . --include="*.py"
```

### Also Check:
- Any .yaml or .yml config files that might reference module paths
- The Dockerfile's CMD or ENTRYPOINT
- Environment variables that set module paths
- setup.py if it exists

The error is happening when hypercorn tries to load the app, so the import chain starts from wherever hypercorn is pointed to.


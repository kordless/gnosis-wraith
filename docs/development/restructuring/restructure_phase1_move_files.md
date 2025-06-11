# Gnosis Wraith Restructuring Plan - Phase 1: Directory Movement

## Overview
This document outlines Phase 1 of restructuring Gnosis Wraith to clarify the directory organization.

## Current Structure Problem
- `/server/` contains core processing libraries but is named like a web server
- Auth files were created in wrong location: `gnosis_wraith/server/`
- Confusion about where different components belong

## Phase 1: Move Directories (File Movement Only)

### Step 1: Create New Directory Structure
```bash
mkdir core
mkdir web
mkdir web/routes
mkdir web/templates
mkdir web/static
```

### Step 2: Move Core Processing Files
Move from `/server/` to `/core/`:
- browser.py
- crawler.py
- markdown_generation.py
- storage_service.py
- enhanced_storage_service.py
- reports.py
- reports_v2_example.py
- job_manager.py
- job_routes.py
- job_system.py
- task_handlers.py
- task_manager.py
- filename_utils.py
- initializers.py
- config.py

### Step 3: Move Web Components
Move from `/server/routes/` to `/web/routes/`:
- __init__.py
- api.py
- pages.py
- auth.py (already exists)

Move from `/server/templates/` to `/web/templates/`:
- (entire templates directory)

Move from `/server/static/` to `/web/static/`:
- (entire static directory)

### Step 4: Move Misplaced Auth Files
Move from `/gnosis_wraith/server/` to correct locations:
- models/ → /core/models/
- lib/ndb_local.py → /core/lib/
- templates/auth/ → /web/templates/auth/

Delete:
- /gnosis_wraith/server/storage/ (functionality goes into enhanced_storage_service.py)

## Expected Breaks After Phase 1
All imports will break! This is expected. Examples:
- `from server.crawler import crawl_url` → needs to be `from core.crawler import crawl_url`
- `from server.routes import register_blueprints` → needs to be `from web.routes import register_blueprints`
- Template paths will be wrong
- Static file paths will be wrong

## DO NOT FIX IMPORTS YET!
Just move the files. We'll fix imports in Phase 2.

## Commands for Moving (Windows PowerShell)
```powershell
# Create directories
New-Item -ItemType Directory -Force -Path core, web, web\routes, web\templates, web\static

# Move core files
Move-Item server\*.py -Destination core\ -Exclude __init__.py

# Move routes
Move-Item server\routes\* -Destination web\routes\

# Move templates
Move-Item server\templates -Destination web\ -Force

# Move static
Move-Item server\static -Destination web\ -Force

# Move misplaced auth files
Move-Item gnosis_wraith\server\models -Destination core\ -Force
Move-Item gnosis_wraith\server\lib\ndb_local.py -Destination core\lib\
Move-Item gnosis_wraith\server\templates\auth -Destination web\templates\ -Force

# Clean up
Remove-Item gnosis_wraith\server -Recurse -Force
```

## Verification Checklist
- [ ] /core/ directory created with all processing files
- [ ] /web/ directory created with routes, templates, static
- [ ] /server/ directory is now empty (can be deleted)
- [ ] /gnosis_wraith/server/ is deleted
- [ ] All files accounted for

## Next: See Phase 2 document for fixing imports

# Gnosis Wraith Restructuring Plan - Phase 2: Fix Imports and Paths

## Overview
This document outlines Phase 2 - fixing all the broken imports and paths after moving directories.

## Phase 2: Fix All Import Statements

### Step 1: Update app.py
```python
# Old imports
from server.config import logger, STORAGE_PATH
from server.crawler import extract_urls, crawl_url
from server.reports import save_markdown_report
from server.initializers import init_job_system

# New imports
from core.config import logger, STORAGE_PATH
from core.crawler import extract_urls, crawl_url
from core.reports import save_markdown_report
from core.initializers import init_job_system

# Blueprint imports
from web.routes import register_blueprints

# Template folder
app = Quart(__name__, 
           static_folder='web/static', 
           template_folder='web/templates')
```

### Step 2: Update Core Module Imports
In all files under `/core/`:
```python
# Examples of changes needed:
# In crawler.py
from core.browser import BrowserControl  # was from server.browser
from core.storage_service import StorageService  # was from server.storage_service

# In enhanced_storage_service.py
from core.storage_service import StorageService  # was from .storage_service
```

### Step 3: Update Route Imports
In all files under `/web/routes/`:
```python
# In api.py, pages.py
from core.crawler import crawl_url  # was from server.crawler
from core.reports import generate_markdown_report  # was from server.reports
from core.storage_service import StorageService  # was from server.storage_service

# In auth.py
from core.models.user import User  # was from SlothAI.web.models
from core.lib.util import random_string, email_user, sms_user  # was from SlothAI.lib.util
```

### Step 4: Update Config Paths
In `/core/config.py`:
```python
# Old paths
STORAGE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'storage')

# New paths (go up one more level since we're in /core now)
STORAGE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'storage')
```

### Step 5: Fix Template References
In route files that render templates:
```python
# No change needed! Template paths are relative to template_folder
return await render_template('index.html')  # Still works
return await render_template('auth/login.html')  # Still works
```

### Step 6: Fix Static File References
In HTML templates:
```html
<!-- These should still work as they're URL paths, not file paths -->
<link rel="stylesheet" href="/static/css/style.css">
<script src="/static/js/main.js"></script>
```

### Step 7: Update Any Relative Imports
```python
# In files that use relative imports
from .storage_service import StorageService  # if in same directory
from ..models.user import User  # if going up one directory
```

## Import Search and Replace Patterns

Use these regex patterns in your IDE:

1. `from server\.` → `from core.`
2. `from server\.routes` → `from web.routes`
3. `import server\.` → `import core.`
4. `'gnosis_wraith/server/static'` → `'web/static'`
5. `'gnosis_wraith/server/templates'` → `'web/templates'`

## Testing After Phase 2

1. **Test imports**: `python -c "from core.crawler import crawl_url"`
2. **Test app startup**: `python app.py`
3. **Test routes**: Access http://localhost:5678
4. **Test static files**: Check if CSS/JS loads
5. **Test templates**: Check if pages render

## Common Issues and Fixes

1. **ModuleNotFoundError**: Check PYTHONPATH includes project root
2. **Template not found**: Verify template_folder path in app.py
3. **Static files 404**: Verify static_folder path in app.py
4. **Circular imports**: May need to reorganize some imports

## Next: See Phase 3 document for auth integration

# Claude Quick Start Guide for Gnosis Wraith

Claude, this document is specifically for you. The user is experienced with both this project and with Claude sessions. They've started hundreds of sessions like this and want to skip the typical exploration phase.

## Project Location & Structure

You are working in: `C:\Users\kord\Code\gnosis\gnosis-wraith\`

Key directories:
- `/gnosis_wraith/extension/` - Browser extension (primary focus area)
- `/gnosis_wraith/server/` - Backend server code
- `/gnosis_wraith/server/routes/` - API endpoints
  - `pages.py` - Routes for web pages
  - `api.py` - API endpoints for extension and clients
- `/gnosis_wraith/server/templates/` - HTML templates
  - Templates use Jinja2 templating engine
  - Error pages have specific styling with `error_type` parameter
  - Template version backups in `.filename_versions` directories
- `/gnosis_wraith/server/static/` - CSS, JS, images

## Current Status & Priority Tasks

The project has undergone a recent restructuring to improve the UI and navigation system:

### New Navigation Structure
- `/wraith` - Main crawling page (renamed from index)
- `/code` - Code examples page (moved from a tab on index)
- `/reports` - Reports listing and viewing

### Template System Notes
- Templates use Jinja2 with some limitations:
  - No `range(x, y) | random` filters in templates - use static values
  - No `bin` filter - binary conversions must be done server-side
  - Template changes require server restart to take effect
  - Browser caching can mask template updates - use incognito window for testing
- Error templates have special error types:
  - `error_type="not-found"` - Red ghost theme
  - `error_type="void-state"` - Purple elite-speak theme
  
### Docker Environment
- The application runs in Docker container `gnosis-wraith`
- Server logs can be checked with `docker_logs` when debugging
- `docker_rebuild` may be necessary after significant changes

The browser extension has been fixed but may need additional enhancements:

### Extension Issues
1. **Screenshot functionality** - Recently fixed, but may need testing
2. **DOM capture** - Improved reliability, but may need further testing
3. **Version consistency** - Consistently updated to version 1.2.1 across all files
4. **UI styling** - Improved UI layout with reorganized control buttons and interactive nav tabs

### Implementation Status

#### ✅ Completed
- Basic browser extension structure
- Server API endpoints for receiving extension data
- DOM content extraction system
- Report generation from captured data
- Job-based async processing system (implemented May 2025)
- Dynamic module generation framework (architecture designed)
- Navigation restructuring with sliding tabs
- Code examples page with improved organization
- UI layout enhancements with interactive positioning
- Consistent version numbering (1.2.1) across all components

#### 🔄 In Progress
- Extension UI enhancements
- Better error handling and user feedback
- Integration with Claude MCP for direct content extraction

#### ❌ Not Started
- Voice command integration (planned in UI revamp)
- Full terminal integration for power users
- Custom voice command training
- Advanced speech features

## Common Tasks & Commands

When working on this project, these are common operations:

```
# Exploring files
file_explorer - To navigate the file system
file_explorer with read_file=true - To view file contents

# Editing files
file_apply_diff - To apply changes to files using diff format
file_writer - To create new files or make major changes

# Testing and Debugging
docker_rebuild - To rebuild and test Docker containers
docker_logs container_name=gnosis-wraith - To check the server logs (only when instructed)

# Template Versioning
- Template file changes are automatically backed up to .filename_versions directories
- Each backup is timestamped with version numbers
- If a template is causing errors, looking at previous versions may help

# Common UI/UX Conventions
- Use Font Awesome icons (6.4.0) for UI elements
- Elite speak text style for system errors (R3P0RT, ERR0R, etc.)
- Error messages prefer terminal/coding style formatting

# Don't do unnecessarily:
- Don't run evolve_status at the start of each session - it's unnecessary
- Don't change directories with file_explorer (..) - just use the full paths
- Don't read all available markdown files - refer to specific ones when needed
- Don't check container logs unless specifically requested
```

## User Working Style

The user prefers:
1. Direct, concise responses
2. Minimal exploration of files unless specifically requested
3. Focus on solving the immediate task at hand
4. Assume the user knows the project well - avoid explaining project concepts
5. When making code changes, focus on the technical solution, not explaining basic programming concepts

## Next Session Focus

The immediate focus will be on continuing the UI restructuring and improvements:
1. Further refinements to the navigation system
2. Enhancing the wraith page (formerly index page)
3. Improving the reports page with better filtering and organization
4. Completing the Claude MCP integration for direct content extraction

Claude, the user is ready to begin work immediately and will direct you to specific tasks. There's no need to explore the entire codebase proactively or read all documentation files.

Remember that your role is to assist with technical solutions as directed, not to comprehensively understand the entire system before starting work.

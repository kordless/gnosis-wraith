# Gnosis Navigation Implementation Plan for Claude Code

## Overview
We're implementing a unified navigation system across all Gnosis services (Wraith, Forge, Alaya) with a terminal-first aesthetic. This plan starts with the manifesto page as `/about` and outlines future navigation work.

## Phase 1: Manifesto Page Implementation (Current)

### 1. Route Setup
```python
# In web/routes/pages.py, add:
@pages.route('/about')
@pages.route('/manifesto')
async def manifesto():
    """Serve the Gnosis manifesto page"""
    return await render_template('about.html')
```

### 2. Files to Create/Update
- ✅ Created: `web/templates/about.html` - The manifesto page with terminal styling
- TODO: Update `web/routes/pages.py` to add the route
- TODO: Update any existing navigation links to point to `/about` or `/manifesto`

### 3. Styling Approach
- Terminal green-on-black aesthetic
- JetBrains Mono font
- Box drawing characters for dividers
- Typewriter effect on page load
- No traditional web elements (no cards, no rounded corners)

## Phase 2: Global Navigation Component (Future)

### What We'll Build Next:
1. **Unified Navigation Bar**
   - Consistent across Wraith, Forge, and Alaya
   - Shows current service context
   - Terminal-style bracket notation for links

2. **Service Switcher**
   - Terminal command style: `$ gnosis --service`
   - Keyboard shortcut support (Ctrl+K)
   - Smooth transitions between services

3. **Terminal Status Bar**
   - Replace traditional footers
   - Show real-time system stats
   - Connection status, memory usage, version

### Files We'll Need to Create:
```
web/static/js/
├── gnosis-nav.js          # Global navigation component
├── terminal-status.js      # Status bar component
└── service-switcher.js     # Service switching logic

web/static/css/
└── gnosis-terminal.css     # Shared terminal styles
```

## Phase 3: Integration Points (Future)

### Pages to Update:
1. **Wraith** (`/wraith`, `/`)
   - Current crawler interface
   - Add global nav and status bar
   - Remove duplicate "About" section

2. **Forge** (`/forge`)
   - Add global nav and status bar
   - Remove duplicate "About" section
   - Integrate service switcher

3. **Alaya** (`/alaya`)
   - Create if doesn't exist
   - Use same navigation pattern

### Shared Pages (accessible from any service):
- `/manifesto` (alias for `/about`)
- `/docs`
- `/docs/api`
- `/docs/mcp`
- `/pricing`

## Implementation Notes for Claude Code

### Current Task:
1. Add the route for `/about` and `/manifesto` in `pages.py`
2. Test the manifesto page renders correctly
3. Update any existing "About" links to point to the new page

### Future Considerations:
- Navigation should work without JavaScript (progressive enhancement)
- Status bar data should come from backend (real memory usage, version, etc.)
- Service switcher needs to maintain current page context
- All transitions should feel "terminal-like" (no fade, use ASCII progress bars)

### Design Principles to Maintain:
1. **No traditional web cruft** - No footers with columns of links
2. **Terminal aesthetic throughout** - Green text, monospace fonts, ASCII art
3. **Service context visible** - User always knows which service they're in
4. **Quick access to philosophy** - Manifesto prominent in navigation
5. **Developer-friendly** - GitHub, docs, API always one click away

### What NOT to Change Yet:
- Don't modify the existing Wraith navigation yet
- Don't remove the old about sections yet
- Don't change the authentication flow
- Keep all existing functionality intact

## Success Criteria
- [ ] Manifesto page accessible at `/about` and `/manifesto`
- [ ] Terminal aesthetic matches the design
- [ ] Typewriter effect works on page load
- [ ] All links in navigation are functional
- [ ] GitHub link points to `github.com/kordless/gnosis`

This gives us a working manifesto page while planning for the larger navigation overhaul. The terminal aesthetic will eventually unify all Gnosis services into a cohesive platform.

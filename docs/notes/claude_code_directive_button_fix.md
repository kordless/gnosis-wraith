# Claude Code Directive: Button Group Positioning Fix

## Issue Identified
Claude Code placed the button groups (language selection, options) **under the tab line** instead of **above the tab line** as specified in the redesign plan.

## Current (Incorrect) Layout
```
[Navigation]
[Tab Line: 🕷️ Crawler | 🔨 Forge | 📦 Vault | ℹ️ About]
[Button Groups] ← WRONG POSITION
[Content Area]
```

## Required (Correct) Layout
```
[Navigation]
[Button Groups] ← CORRECT POSITION (like index.html)
[Tab Line: 🕷️ Crawler | 🔨 Forge | 📦 Vault | ℹ️ About]
[Content Area]
```

## Reference Implementation
**Study `index.html`** for the correct button group positioning pattern. The controls should be:
- **Above the tab navigation**
- **Top-right aligned**
- **Independent of tab switching** (always visible)

## Correction Required
**File**: `gnosis_wraith/server/templates/forge.html`

**Action**: Move button groups from below tabs to above tabs, matching the index.html pattern exactly.

**Key Point**: Button groups should be **persistent** and **above the tab line**, not part of the tab content that shifts when users navigate between tabs.

This ensures the language and options controls remain consistently accessible regardless of which tab is active, matching the main crawler interface design pattern.
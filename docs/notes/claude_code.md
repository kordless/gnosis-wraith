# Claude Code Task: Phase 1 - Remove Custom Token Management from Forge

## Project Context
You're working on **Gnosis Wraith**, a web crawling service. The project has two main interfaces:
1. **Main Crawler** (`index.html`) - Has professional token management system
2. **Forge** (`forge.html`) - Has custom, basic token management that needs to be replaced

## Your Mission: Phase 1 - Clean Removal
Remove the existing custom token management code from the Forge interface to prepare for implementing the unified system.

## Target File
`gnosis_wraith/server/templates/forge.html`

## What to Remove
Look for and **completely remove** this section (approximately lines 400-500):

```javascript
{/* LLM Controls and Logout - Same row as tabs, same styling as crawler */}
{authStatus === 'authorized' && (
  <div className="flex items-center space-x-4 text-xs text-gray-400">
    {/* Current provider selector */}
    {/* Current token input modal system */}
    {/* Current logout button */}
  </div>
)}
```

## Specific Code Patterns to Find and Remove

### 1. LLM Provider Selection UI
Look for code containing:
- Provider dropdown/selector
- "anthropic", "openai", "gemini" options
- Provider state management

### 2. Token Input Modal System
Look for code containing:
- Token input fields
- Modal state (`isTokenModalOpen`, `setIsTokenModalOpen`)
- Token validation logic
- "Enter API Token" or similar text

### 3. Custom Authentication UI
Look for code containing:
- Custom authentication buttons
- Token status displays
- Logout functionality embedded in the token section

### 4. Related State Variables
Remove any useState declarations for:
- `llmProvider` or similar
- `isTokenModalOpen` or similar  
- `apiToken` or similar
- Any other token-related state that's duplicating main app functionality

## What NOT to Remove
- Keep the main authentication system (access code authentication)
- Keep the code generation functionality
- Keep the language selection UI
- Keep all other Forge features

## Success Criteria
After your changes:
1. ✅ Forge still loads without JavaScript errors
2. ✅ Access code authentication still works
3. ✅ Code generation UI is still functional (even if not connected to LLM yet)
4. ✅ No duplicate token management UI elements remain
5. ✅ Clean removal with no orphaned variables or functions

## Expected Result
The Forge should have a **clean, simplified interface** without the custom token management, ready for Phase 2 where we'll add the unified token management components.

## File Location
The file is located at: `gnosis_wraith/server/templates/forge.html`

This is a **precision removal task** - clean out the old system without breaking anything else.
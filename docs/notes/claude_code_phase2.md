# Claude Code Task: Phase 2 - Implement Unified Token Management in Forge

## Previous Phase Completed
✅ **Phase 1**: Removed custom token management UI from `forge.html`
- Cleaned out duplicate provider selection dropdowns
- Removed custom token input modals
- Eliminated redundant authentication state
- Forge now has clean interface ready for unified system

## Current State Analysis
The **main crawler** (`index.html`) implements a sophisticated token management system with these components:

### How index.html Implements Token Management

**1. Component Imports** (in `<head>` section):
```html
<script src="/static/js/components/auth-component.js" type="text/babel"></script>
<script src="/static/js/components/token-status-button.js" type="text/babel"></script>
<script src="/static/js/components/token-manager-modal.js" type="text/babel"></script>
<script src="/static/js/components/logout-modal.js" type="text/babel"></script>
```

**2. TokenStatusButton Usage** (color-coded brain icon):
```javascript
<TokenStatusButton 
  onTokenModalOpen={() => setIsTokenModalOpen(true)}
  size="md"
/>
```

**3. TokenManagerModal Integration**:
```javascript
<TokenManagerModal 
  isOpen={isTokenModalOpen}
  onClose={() => setIsTokenModalOpen(false)}
  onTokenUpdated={(provider, token) => {
    console.log(`Token updated for ${provider}:`, token ? 'SET' : 'CLEARED');
  }}
/>
```

## Your Mission: Phase 2 - Add Unified Components

### Target File
`gnosis_wraith/server/templates/forge.html`

### Step 1: Add Component Imports
Add these script imports to the `<head>` section of `forge.html` (after existing utility scripts):

```html
<!-- Token Management Components -->
<script src="/static/js/components/auth-component.js" type="text/babel"></script>
<script src="/static/js/components/token-status-button.js" type="text/babel"></script>
<script src="/static/js/components/token-manager-modal.js" type="text/babel"></script>
<script src="/static/js/components/logout-modal.js" type="text/babel"></script>
```

### Step 2: Add Modal State
In the React component, add state for the token modal:

```javascript
const [isTokenModalOpen, setIsTokenModalOpen] = useState(false);
```

### Step 3: Replace Token UI Section
Find where the old token management was removed and add this new unified UI:

```javascript
{authStatus === 'authorized' && (
  <div className="flex items-center space-x-4 text-xs text-gray-400">
    {/* Token Status Button (color-coded brain icon) */}
    <TokenStatusButton 
      onTokenModalOpen={() => setIsTokenModalOpen(true)}
      size="md"
    />
    
    {/* Provider Display (read-only) */}
    <div className="flex items-center space-x-1 bg-gray-900 p-1 rounded">
      <span className="px-2 py-1 text-xs">
        {localStorage.getItem('gnosis_wraith_llm_provider') || 'anthropic'}
      </span>
    </div>
    
    {/* Logout Button */}
    <LogoutButton 
      onLogout={handleLogout}
      size="sm"
    />
  </div>
)}
```

### Step 4: Add Modal at Component Root
Add the TokenManagerModal at the root level of the React component (same level as other modals):

```javascript
<TokenManagerModal 
  isOpen={isTokenModalOpen}
  onClose={() => setIsTokenModalOpen(false)}
  onTokenUpdated={(provider, token) => {
    console.log(`Forge token updated for ${provider}:`, token ? 'SET' : 'CLEARED');
    // Token is automatically saved to cookies by the modal
  }}
/>
```

## Why We Need This Modal Now
The **TokenManagerModal** provides:

1. **Multi-provider support**: Anthropic, OpenAI, Gemini selection
2. **Secure token storage**: Encrypted cookies with 90-day expiration
3. **Visual feedback**: Color-coded status (red=no token, yellow=invalid, green=valid)
4. **Professional UI**: Consistent with main crawler interface
5. **Shared state**: Tokens work across both crawler and forge
6. **Error handling**: Validation and clear error messages

## Expected Behavior After Implementation
- **Brain icon** shows current token status with color coding
- **Click brain icon** opens professional token management modal
- **Provider display** shows current LLM provider (anthropic/openai/gemini)
- **Logout button** clears authentication and returns to access code screen
- **Token persistence** works across browser sessions via cookies

## Success Criteria
1. ✅ Forge loads without JavaScript errors
2. ✅ Brain icon appears and shows correct color status
3. ✅ Clicking brain icon opens token management modal
4. ✅ Modal allows provider selection and token input
5. ✅ Tokens are shared between crawler and forge interfaces
6. ✅ UI matches main crawler styling and behavior

## Files to Examine for Reference
- `gnosis_wraith/server/templates/index.html` - See how components are integrated
- `gnosis_wraith/server/static/js/components/token-manager-modal.js` - The modal component
- `gnosis_wraith/server/static/js/components/token-status-button.js` - The brain icon component

This phase brings the Forge up to the same professional token management standard as the main crawler interface.
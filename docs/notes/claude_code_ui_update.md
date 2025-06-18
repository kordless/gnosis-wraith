# UI Update Plan: Index.html Navigation Redesign

## Overview
This document outlines the plan to update the index.html navigation to match the forge.html design pattern, moving from a version display to a user-centric navigation with profile settings.

## Current State Analysis

### forge.html Navigation
- Logout button positioned in the top navigation bar
- "Authenticated User" text displayed (needs to be removed we'll show a user profile button that opens a modal later)
- TokenStatusButton (brain icon or other llm icons) for LLM configuration
- Clean, user-focused interface

### index.html Navigation
- VERSION 3.2.7 link in top-right corner
- No visible authentication controls in header
- LLM configuration accessed separately (below)
- Authentication handled in main content area

## Proposed Changes

### 1. Top Navigation Bar Restructure

#### Remove
- Version number display from header

#### Add
- Authentication controls to top-right corner:
  - **Logged Out State**: "Login" button
  - **Logged In State**: 
    - TokenStatusButton (brain icon)
    - Profile icon (replaces direct logout)

### 2. Profile Settings Modal

Create a new modal component accessed via profile icon that contains:
- User information display
- API Token management interface
- link to LLM configurationss modal
- Logout button
- Future user settings/preferences

Please preserve the existing layout of all tabs and containers on the page.

### 3. Component Architecture

```
Header Navigation Structure:
├── Left Side
│   ├── "GNOSIS WRAITH" title (leave in current style)
│   └── System status indicator (same)
└── Right Side
    ├── Not Authenticated
    │   └── Login Button
    └── Authenticated
        ├── TokenStatusButton (brain icon)
        ├── "Authenticated User" text
        └── ProfileIcon → ProfileSettingsModal
```

## Implementation Steps

### Step 1: Create ProfileSettingsModal Component

**File**: `/static/js/components/profile-settings-modal.js`

**Features**:
- Modal overlay consistent with TokenManagerModal styling
- User information section
- API token display with copy/regenerate functions
- Logout button with confirmation
- LLM button to show llm modal (hide this one)
- Extensible design for future settings

**Key Functions**:
```javascript
- handleLogout() - Manages logout process
- copyApiToken() - Copies token to clipboard
- Modal animations and escape key handling
```

### Step 2: Update Main Application (gnosis.js)

**Changes Required**:
- Add `isProfileModalOpen` state
- Import ProfileSettingsModal component
- Move logout logic from inline to modal
- Restructure header JSX for new layout

**Code Structure**:
```javascript
// New state
const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);

// Header restructure
<header>
  <div className="flex justify-between items-center">
    <div>Title + Status</div>
    <div>Auth Controls</div>
  </div>
</header>
```

### Step 3: Create Profile Icon Component

**Options**:
1. Integrate into existing component structure
2. Create standalone `profile-icon.js` component

**Features**:
- User avatar or default icon (fa-user-circle)
- Hover effects
- Click handler to open modal
- Visual feedback for active state

### Step 4: Update Navigation Header Structure

**Tasks**:
- Remove version link code
- Add conditional rendering based on `authStatus`
- Integrate TokenStatusButton in header
- Add ProfileIcon component
- Ensure responsive design

### Step 5: Styling and Polish

**CSS Updates**:
- Consistent spacing with forge.html
- Proper alignment of navigation elements
- Responsive breakpoints for mobile
- Smooth transitions and hover states

## Files to Create/Modify

### New Files
1. **profile-settings-modal.js**
   - Full modal component with user settings
   - Consistent with existing modal patterns

2. **profile-icon.js** (optional)
   - Small component for profile button
   - Can be integrated into gnosis.js instead

### Modified Files
1. **gnosis.js**
   - Update header structure
   - Add profile modal state and handlers
   - Reorganize authentication UI

2. **index.html**
   - Add script tags for new components
   - Ensure proper load order

3. **gnosis.css** (if needed)
   - Additional styling for new components
   - Ensure consistency across modals

## Benefits

1. **Consistency**: Unified navigation pattern across forge.html and index.html
2. **Improved UX**: Settings grouped logically in modal
3. **Cleaner Interface**: Less clutter in main navigation
4. **Extensibility**: Easy to add features to profile settings
5. **Modern Design**: Follows current UI patterns

## Testing Checklist

- [ ] Login/logout flow works correctly
- [ ] Profile modal opens/closes properly
- [ ] API token management functions
- [ ] Responsive design on mobile
- [ ] Keyboard navigation (Esc to close)
- [ ] Visual consistency with forge.html
- [ ] No regression in existing features

## Future Enhancements

- User avatar upload
- Theme preferences
- Notification settings
- Activity history
- Account management features

## Notes for Implementation

- Maintain existing authentication flow logic
- Ensure TokenManagerModal continues to work
- Keep consistent styling with dark theme
- Test thoroughly on different screen sizes
- Consider accessibility (ARIA labels, keyboard nav)
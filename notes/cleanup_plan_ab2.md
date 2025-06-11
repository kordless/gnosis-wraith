# Cleanup Plan: Modular Full-Height Display Component

## Current State Analysis

### Forge Code Display
- Currently has a fixed height with overflow scrolling
- Nice border and header styling
- Copy/Download buttons in header
- Syntax-highlighted code content

### Similar Components Needing Same Pattern
1. **Logs Display** - Shows crawl logs with auto-scroll
2. **Reports Cards** - Shows report cards in scrollable container
3. **Code Display** - Current forge implementation

## Design Goals

1. **Full Height Layout**
   - Display area should use all available vertical space
   - Top panel (nav, controls) remains fixed
   - Content area fills remaining height
   - Scrolling contained within content area only

2. **Modular Component**
   - Reusable across different pages
   - Configurable header content
   - Flexible content rendering
   - Consistent styling

## Implementation Plan

### Phase 1: Create Modular Display Component

**File**: `/static/js/components/full-height-display.js`

```javascript
const FullHeightDisplay = ({
    title,              // Header title
    icon,              // Optional header icon
    iconColor,         // Icon color class
    headerActions,     // React element for header buttons
    children,          // Content to display
    className = '',    // Additional CSS classes
    contentRef,        // Optional ref for content area
    headerClassName = '', // Header styling
    bodyClassName = ''    // Body styling
}) => {
    // Component implementation
};
```

### Phase 2: Update Forge to Use New Component

**Changes to `forge.html`**:
1. Import new component
2. Replace ForgeCodeDisplay with FullHeightDisplay
3. Adjust page layout for full-height design

### Phase 3: Create Display Variants

**Additional Components**:
1. `LogsDisplay` - Wraps FullHeightDisplay for logs
2. `ReportsDisplay` - Wraps FullHeightDisplay for reports
3. `CodeDisplay` - Enhanced code display with syntax highlighting

### Phase 4: Update Other Pages

1. **Crawler page** (`index.html/wraith.html`)
   - Update logs display to use new component
   
2. **Reports page** (`reports.html`)
   - Update report cards display

## CSS Layout Strategy

```css
/* Full height container */
.full-height-container {
    display: flex;
    flex-direction: column;
    height: 100vh;
    overflow: hidden;
}

/* Fixed header area */
.fixed-header {
    flex-shrink: 0;
    /* Contains nav, controls, etc */
}

/* Flexible content area */
.flex-content {
    flex: 1;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}

/* Display component fills available space */
.full-height-display {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.display-body {
    flex: 1;
    overflow-y: auto;
}
```

## Component Structure

```
FullHeightDisplay
├── Header (fixed)
│   ├── Title + Icon
│   └── Actions (Copy, Download, etc)
└── Body (scrollable)
    └── Content (children)
```

## Benefits

1. **Consistency** - Same display pattern across all pages
2. **Maintainability** - Single component to update
3. **Flexibility** - Easy to add new display types
4. **Performance** - Better scroll performance with contained areas
5. **UX** - Maximum content visibility on all screen sizes

## Migration Path

1. Create component without breaking existing functionality
2. Test on Forge page first
3. Gradually migrate other pages
4. Remove old display code once migration complete

## Success Criteria

- [ ] Full-height display uses all available vertical space
- [ ] Scrolling is smooth and contained to content area
- [ ] Component works on Forge, Crawler, and Reports pages
- [ ] No visual regressions from current functionality
- [ ] Code is DRY - no duplicate display logic
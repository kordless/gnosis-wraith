# UI Development Notes - Gnosis Wraith

This document provides technical notes and code snippets for UI components in the Gnosis Wraith project. These notes are intended for developers working on the UI to understand key implementation details.

## Navigation System

### Tab Sliding Implementation

The navigation system uses a combination of CSS and JavaScript to create a smooth sliding tab interface. The active tab is highlighted with a slider element that moves underneath the tabs.

```javascript
// Basic implementation
const slider = document.getElementById('main-nav-slider');
const activeItem = navTabs.querySelector('.nav-item.active');
if (activeItem && slider) {
  slider.style.width = `${activeItem.offsetWidth}px`;
  slider.style.left = `${activeItem.offsetLeft}px`;
}
```

### Navigation Position Animation

The nav tabs now include a subtle position shift based on which tab is being hovered. The entire tab group moves slightly to keep the hovered item centered in the user's focus:

```javascript
// Movement on hover
item.addEventListener('mouseenter', function() {
  if (window.innerWidth > 768) {
    // Move the slider
    slider.style.width = `${this.offsetWidth}px`;
    slider.style.left = `${this.offsetLeft}px`;
    
    // Move the entire nav group based on which item is hovered
    let moveDirection = 0;
    if (item.dataset.page === 'crawl') {
      // If hovering crawl, move 25px to the left
      moveDirection = -25;
    } else if (item.dataset.page === 'reports') {
      // If hovering reports, move 25px to the right
      moveDirection = 25;
    }
    
    // Apply the movement with a smooth transition
    mainNav.style.transition = 'left 0.8s ease';
    mainNav.style.left = `${originalNavPosition + moveDirection}px`;
  }
});
```

## Control Button Positioning

Control buttons (terminal, settings, power) are positioned in the top right corner of the header. The layout uses absolute positioning to ensure consistent placement:

```html
<!-- Control Buttons Group (fixed position top right) -->
<div class="control-buttons" style="display: flex; align-items: center; position: absolute; right: 10px; top: 12px;">
  <a href="{{ url_for('pages.terminal') }}" class="terminal-button" title="Terminal (Alt+T)" style="margin-right: 8px; display: none; width: 34px; height: 34px;">
    <i class="fas fa-terminal" style="color: #999; font-size: 15px;"></i>
  </a>
  
  <a href="{{ url_for('pages.settings') }}" class="settings-button" title="Settings" style="margin-right: 8px; display: none; width: 34px; height: 34px;">
    <i class="fas fa-cog" style="font-size: 15px;"></i>
  </a>
  
  <div class="power-button" id="power-button" title="Power Login/Logout (Alt+P)">
    <i class="fas fa-power-off power-icon"></i>
    <div class="power-indicator"></div>
  </div>
</div>
```

## Login State Management

The UI simulates a login/logout functionality using localStorage to persist state between page loads:

```javascript
// Check for saved login state
try {
  const savedState = localStorage.getItem('logged_in_state');
  if (savedState === 'true') {
    // Restore previous logged-in state
    logged_in_state = true;
    const powerIcon = powerButton.querySelector('.power-icon');
    const powerIndicator = powerButton.querySelector('.power-indicator');
    
    powerIcon.style.color = 'white';
    powerIndicator.style.animation = 'none';
    powerIndicator.style.backgroundColor = '#48bb78';
    powerIndicator.style.boxShadow = '0 0 8px #48bb78';
    
    // Show the settings and terminal buttons
    document.querySelectorAll('.terminal-button, .settings-button').forEach(el => {
      if (el) el.style.display = 'flex';
    });
  }
} catch (e) {
  console.log("Error checking login state", e);
}
```

## Notification System

Notifications appear in the top-right corner but are positioned below the control buttons to avoid overlap:

```javascript
feedbackDiv.style.position = 'fixed';
feedbackDiv.style.top = '70px'; // Below the control buttons
feedbackDiv.style.right = '20px';
feedbackDiv.style.padding = '10px 20px';
feedbackDiv.style.background = '#e74c3c'; // Red for error, #2ecc71 for success
feedbackDiv.style.color = 'white';
feedbackDiv.style.borderRadius = '4px';
feedbackDiv.style.zIndex = '9999';
```

## CSS Variables and Theming

The UI uses CSS variables for consistent styling:

```css
:root {
  --primary-color: #6c63ff;
  --primary-dark: #5a52d5;
  --text-color: #2d3748;
  --light-bg: #f7fafc;
  --border-color: #e2e8f0;
  --success-color: #48bb78;
  --error-color: #f56565;
}
```

## Mobile Responsiveness

The navigation system includes some basic mobile responsiveness adjustments:

```css
@media (max-width: 768px) {
  .main-nav {
    margin-right: 10px;
  }
  
  .nav-tabs {
    padding: 3px;
  }
  
  .nav-tabs .nav-item {
    padding: 6px 12px;
    font-size: 12px;
  }
}
```

## Key UI Components

1. **Tab Navigation**: Sliding tabs with highlight indicators
2. **Control Buttons**: Terminal, settings, and power buttons
3. **Power Indicator**: Visual status indicator with animation
4. **Feedback Messages**: Notification system for user feedback
5. **Ghost Emoji**: Flying ghost animation activated by clicking or Ctrl+G

## Future Development Notes

For future UI development, consider:

1. **Theme System**: Implement full light/dark theme toggle using CSS variables
2. **Animation Library**: Consider implementing a small animation library for consistent effects
3. **Component Structure**: Move toward a more modular component structure
4. **Accessibility**: Improve keyboard navigation and screen reader support
5. **Touch Support**: Enhance mobile support with touch-specific interactions
6. **Settings Storage**: Implement user preferences storage in localStorage

## Known Issues

- Mobile view needs further optimization
- Some animations may cause performance issues on older devices
- Login state is simulated and not connected to a real authentication system
- Navigation tabs position relies on JavaScript and may have positioning glitches in some browsers

# UI Enhancement Log for Gnosis Wraith

This document tracks UI enhancements and improvements made to the Gnosis Wraith web interface and browser extension.

## Recent Changes (May 17, 2025)

### Navigation System Enhancements

#### Code Page UI Improvements
- **Fixed Header Control Button Positioning**:
  - Moved control buttons (terminal, settings, power) to the top right corner
  - Reduced button size from 40px to 34px for a more compact appearance
  - Reduced icon size from 18px to 15px for better proportions
  - Adjusted spacing between buttons to 8px for better visual grouping

- **Navigation Tab Improvements**:
  - Reduced tab height by adjusting padding from 8px 18px to 6px 16px
  - Decreased font size from 14px to 13px
  - Changed border-radius from 22px to 20px
  - Adjusted slider height and positioning for the new tab size
  - Reduced container padding from 5px to 4px

- **Interactive Navigation Movement**:
  - Implemented a subtle hover-based positioning system for the navigation bar
  - Nav tabs now move slightly left when hovering over "Crawl" tab
  - Nav tabs move slightly right when hovering over "Reports" tab
  - Movement is subtle (25px in either direction) with a smooth 0.8s transition
  - Creates an interactive, responsive feel without being distracting

- **Fixed Template Error**:
  - Resolved issue with `current_user.is_authenticated` reference in code_examples.html
  - Implemented a JavaScript-based login state management system
  - Terminal and settings buttons now properly toggle visibility based on login state
  - Notifications appear below the control buttons (70px from top) to avoid overlap

### Version Consistency

- **Unified Version Numbers**:
  - Updated all components to consistently use version 1.2.1
  - Fixed manifest.json version number
  - Updated rebuild.ps1 script to maintain version 1.2.1 consistently
  - Removed version overrides that previously forced 1.1.1/1.1.2

### Error Handling

- Fixed the server error when accessing the /code page
- Updated notification positioning to avoid UI conflicts
- Improved error feedback visual styling

## Future UI Enhancements (Planned)

- Implement full responsive design for mobile devices
- Add dark/light theme toggle
- Create more visual feedback during processing operations
- Add animation transitions between pages
- Implement drag-and-drop file upload interface
- Develop a more comprehensive terminal interface
- Add user preferences storage to remember settings between sessions

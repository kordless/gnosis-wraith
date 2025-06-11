# Gnosis Wraith UI Revamp Notes

## Design Vision: Google-Inspired AI Interface

The Gnosis Wraith UI revamp aims to transform the interface into a clean, engaging experience inspired by Google's simplicity but enhanced with modern AI capabilities and interactive elements.

## Core UI Components

### 1. Speech Integration

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│                       🎙️ "Crawl TechCrunch"                         │
│                                                                     │
│                       🎙️ "Screenshot CNN"                           │
│                                                                     │
│                       🎙️ "Analyze product reviews"                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

- Web Speech API integration (SpeechRecognition and SpeechSynthesis)
- Voice command pattern recognition for common tasks
- Audible confirmation of actions ("Crawling TechCrunch...")
- Supports natural language commands with AI interpretation
- Microphone button accessible from any view for quick commands
- Voice feedback for accessibility (can be toggled in settings)
- Multi-language voice recognition support

### 2. Simplified Header & Navigation

```
┌─────────────────────────────────────────────────────────────────────┐
│ Gnosis Wraith 👻                                      [Login] [Menu] │
└─────────────────────────────────────────────────────────────────────┘
```

- Minimalist header with logo and ghost emoji
- Clean authentication buttons (Login/Logout)
- Hidden menu for accessing Reports, Settings, and Documentation

### 2. Central Search Experience

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│                      🔍 Gnosis Wraith 👻                            │
│                                                                     │
│     ┌─────────────────────────────────────────────────────┐        │
│     │ 👻 Enter URL or describe what to crawl...      🎤 ⚡ │        │
│     └─────────────────────────────────────────────────────┘        │
│                                                                     │
│     Press Ctrl+Y for Hacker News or try "analyze product reviews"   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

- Central positioning for the search box
- Large, friendly ghost logo above the search
- Voice input and "Feeling Lucky" buttons
- "Training" text for natural language prompts

### 3. Interactive Control Cards

```
┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐
│ 📸 Screenshot     │   │ 👁️ OCR Extraction  │   │ 📄 Content Process│
│ Capture visual    │   │ Extract text from  │   │ ┌─────────────────┐
│ snapshots         │   │ images             │   │ │Enh│Basic│Raw HTML│
│          [Toggle] │   │          [Toggle]  │   │ └─────────────────┘
└───────────────────┘   └───────────────────┘   └───────────────────┘

┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐
│ 🔍 JavaScript     │   │ 📊 AI Analysis     │   │ 🔒 Security Level │
│ Enable for        │   │ Generate insights  │   │ ┌─────────────────┐
│ dynamic content   │   │ from content       │   │ │Low │Med │High   │
│          [Toggle] │   │          [Toggle]  │   │ └─────────────────┘
└───────────────────┘   └───────────────────┘   └───────────────────┘
```

- Card-based controls with consistent design
- Mix of toggle switches and button groups
- Visual icons for each setting
- Simple explanatory text
- Hover animations and feedback

### 4. Collapsible Advanced Options

```
┌─────────────────────────────────────────────────────────────────────┐
│ Custom Report Title                                          [▼]    │
├─────────────────────────────────────────────────────────────────────┤
│ [                                                              ]    │
└─────────────────────────────────────────────────────────────────────┘
```

- Expandable sections for less-used features
- Clean animations for expanding/collapsing
- Maintain accessibility while reducing visual noise

### 5. Distinctive Action Button

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│                 ┌─────────────────────────────┐                     │
│                 │   👻 Unleash the Wraith     │                     │
│                 └─────────────────────────────┘                     │
│                                                                     │
│           Gnosis Wraith - Making the invisible web visible          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

- Bold, distinctive action button
- Animated ghost icon (subtle pulse effect)
- Google-inspired tagline below the button

### 6. In-Browser Terminal

```
┌─────────────────────────────────────────────────────────────────────┐
│ > Terminal                                                 [_][□][×]│
├─────────────────────────────────────────────────────────────────────┤
│ gnosis@wraith:~$ █                                                  │
│                                                                     │
│                                                                     │
│                                                                     │
│                                                                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

- Collapsible terminal panel accessible via icon in main interface
- Supports shell commands for power users
- Executes server-side commands or local simulated shell
- Syntax highlighting and command history
- Draggable and resizable window

## Post-Authentication Experience

After login, the interface transforms to show:

1. **Personalized Welcome**
   - "Welcome back, [username]"
   - Quick stats on recent crawls/captures

2. **Recent Activity**
   - Cards showing recent crawls with thumbnails
   - Ability to continue where left off

3. **Suggested Crawls**
   - AI-generated suggestions based on user history
   - Trending topics or sites

4. **Terminal Access**
   - Direct access to shell commands
   - Support for batch operations

## Color Scheme & Typography

- **Primary Color**: Ghost Purple (#6c63ff)
- **Secondary Accents**: Electric Blue (#58c7f3), Ethereal Green (#53f3c3)
- **Background**: Clean white/dark mode with subtle ghost patterns
- **Typography**: Google Sans or similar for headings, Open Sans for body text

## Animation & Interaction Guidelines

1. **Subtle Feedback**
   - Gentle hover states (slight elevation changes)
   - Soft color transitions (200-300ms)

2. **Interactive Elements**
   - Toggle switches slide smoothly
   - Radio buttons have subtle "pop" effect

3. **Loading States**
   - Ghost-themed loading animations
   - Progress indicators that maintain the playful theme

4. **Terminal Animations**
   - Realistic cursor blink
   - Command execution animations
   - Text scrolling effects

## Mobile Adaptations

- Stack control cards vertically on smaller screens
- Maintain large search box experience
- Collapsible terminal becomes full-screen modal
- Bottom navigation bar replaces header menu

## Implementation Notes

### HTML Structure

```html
<header class="ghost-header">
  <!-- Logo and navigation -->
</header>

<main class="ghost-container">
  <div class="ghost-search-container">
    <!-- Search box and voice controls -->
  </div>
  
  <div class="ghost-controls">
    <!-- Control cards in grid layout -->
  </div>
  
  <div class="ghost-advanced-options">
    <!-- Collapsible sections -->
  </div>
  
  <div class="ghost-action">
    <!-- Main action button -->
  </div>
</main>

<div class="ghost-terminal" id="terminal">
  <!-- Terminal implementation -->
</div>

<footer class="ghost-footer">
  <!-- Footer content -->
</footer>
```

### Terminal Implementation Approach

The terminal should be implemented using:

1. **xterm.js** for terminal emulation
2. **Socket.IO** for real-time communication with backend
3. **node-pty** on the server for terminal process management

### Speech Integration Technical Details

The speech recognition system should be implemented using:

1. **Web Speech API** as the foundation:
   ```javascript
   const recognition = new webkitSpeechRecognition();
   recognition.continuous = false;
   recognition.interimResults = true;
   recognition.lang = 'en-US';
   ```

2. **Command Processing Pipeline**:
   ```javascript
   // Process recognized speech
   recognition.onresult = (event) => {
     const speechResult = event.results[0][0].transcript.toLowerCase();
     console.log('Speech recognized:', speechResult);
     
     // Command patterns
     if (speechResult.includes('crawl') || speechResult.includes('analyze')) {
       const url = extractUrlFromSpeech(speechResult);
       if (url) {
         // Set URL in search box
         document.getElementById('url').value = url;
         
         // Provide voice feedback
         speak(`Crawling ${url}`);
         
         // Execute crawl
         document.getElementById('crawl-btn').click();
       }
     }
     // More command patterns...
   };
   ```

3. **Voice Feedback System**:
   ```javascript
   function speak(text) {
     // Check if user has enabled voice feedback
     if (!userPreferences.voiceFeedback) return;
     
     const utterance = new SpeechSynthesisUtterance(text);
     utterance.voice = selectVoice(userPreferences.voiceType);
     utterance.rate = userPreferences.speechRate;
     utterance.pitch = userPreferences.speechPitch;
     
     window.speechSynthesis.speak(utterance);
   }
   ```

4. **Voice Command Training UI**:
   - Interface for users to teach the system custom commands
   - Machine learning to improve recognition accuracy over time
   - Stored command preferences in user profile

Example terminal initialization code:

```javascript
// Terminal initialization
const term = new Terminal({
  cursorBlink: true,
  theme: {
    background: '#1a1a1a',
    foreground: '#f8f8f8',
    cursor: '#6c63ff'
  }
});

// Connect to backend socket
const socket = io.connect('/terminal');

// Handle input
term.onData(data => {
  socket.emit('terminal:input', data);
});

// Handle output
socket.on('terminal:output', data => {
  term.write(data);
});

// Initialize
term.open(document.getElementById('terminal-container'));
socket.emit('terminal:init');
```

## Next Steps & Timeline

1. **Prototype Phase** (2 weeks)
   - Implement basic HTML/CSS for the new interface
   - Create interactive elements with JavaScript
   - Test responsive behavior
   - **Voice command prototype** with basic recognition

2. **Terminal Integration** (2 weeks)
   - Set up xterm.js with basic command handling
   - Implement server-side terminal process management
   - Create command history and auto-completion
   - **Voice-to-terminal command** support

3. **Speech Integration** (2 weeks)
   - Complete Web Speech API implementation
   - Build command processing pipeline
   - Create voice feedback system
   - Develop multi-language support
   - Implement accessibility features

4. **Post-Authentication Features** (1 week)
   - Build recent activity cards
   - Implement suggestion algorithm
   - Create personalized dashboard
   - **Voice profile settings** for customization

5. **Testing & Refinement** (1 week)
   - Conduct usability testing
   - Optimize for performance
   - Test speech recognition accuracy
   - Final design adjustments

## Advanced Speech Features

### 1. Voice Command Customization

Users will be able to create custom voice commands with a simple training interface:

```
┌─────────────────────────────────────────────────────────────────────┐
│ Custom Voice Command                                                │
├─────────────────────────────────────────────────────────────────────┤
│ When I say: [Activate night crawler]                                │
│                                                                     │
│ Gnosis should: [X] Execute command: crawl $1 with javascript=true   │
│                [ ] Navigate to page: ___________________________    │
│                [ ] Execute terminal command: ___________________    │
│                                                                     │
│ Sample phrases to train recognition:                                │
│ [Activate night crawler on TechCrunch] → crawl techcrunch.com       │
│ [Activate night crawler on BBC] → crawl bbc.com                     │
│ [+ Add more examples]                                               │
└─────────────────────────────────────────────────────────────────────┘
```

### 2. Voice-Activated Terminal Commands

The terminal will support direct voice input with commands like:

- "Terminal list directories"
- "Terminal search files for keyword analytics"
- "Terminal run crawler with depth three"

These voice commands will be executed in the terminal with visual feedback showing both the translated command and its execution.

### 3. Voice Biometrics (Future Enhancement)

For enhanced security, voice biometric authentication will be implemented as an optional feature:

- Voice print enrollment during account setup
- Passphrase-based authentication ("Wraith, unlock my dashboard")
- Continuous voice verification for sensitive operations

## Final Vision

The revamped Gnosis Wraith UI will transform the application from a functional tool into an engaging, delightful experience that feels like a modern take on classic Google with advanced speech capabilities. The interface will be approachable for new users while providing the power and flexibility that technical users need through speech commands and terminal integration.

By combining the simplicity of a search-centric interface with voice interaction, AI intelligence, and command-line operations, Gnosis Wraith will offer a unique blend of user-friendly design and technical sophistication. The speech integration will make the application truly hands-free and accessible to a broader audience, while also enhancing productivity for power users.

The vision is to create an interface that feels almost prescient - understanding user intent through minimal input, whether typed, spoken, or commanded through the terminal - making the invisible web truly visible through multiple interaction modalities.

# Gnosis Platform Landing Page Implementation Plan

## Vision: Terminal-Style SaaS Landing That Gets People Hooked

### Core Concept
A landing page that feels like discovering a powerful terminal tool, but guides users into the platform naturally. Think "What if the Matrix's terminal had a friendly onboarding flow?"

## Page Structure

### 1. **Hero Section: Live Terminal Demo**
```
┌─────────────────────────────────────────────────────────────┐
│ $ gnosis --help                                             │
│                                                             │
│ GNOSIS PLATFORM v4.2.0                                      │
│ The Intelligence Layer for the AI Internet                  │
│                                                             │
│ SERVICES:                                                   │
│   wraith    Extract intelligence from any website           │
│   forge     Transform content into living services          │
│   alaya     Store and search your knowledge graph           │
│                                                             │
│ $ gnosis wraith crawl https://news.ycombinator.com         │
│ [LIVE DEMO RUNS HERE - REAL CRAWL]                         │
│                                                             │
│ > Want to try it yourself? [Get Started] [Watch Demo]      │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Auto-typing terminal commands
- REAL live demo (crawl HN or a safe demo site)
- Results stream in real-time
- "Wow" moment in first 5 seconds

### 2. **Interactive Service Selector**
```javascript
// Three terminal windows side by side
const ServiceShowcase = () => {
  const [activeService, setActiveService] = useState('wraith');
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <TerminalWindow 
        title="WRAITH" 
        active={activeService === 'wraith'}
        onClick={() => setActiveService('wraith')}
      >
        {/* Mini demo of crawling */}
      </TerminalWindow>
      
      <TerminalWindow 
        title="FORGE" 
        active={activeService === 'forge'}
        onClick={() => setActiveService('forge')}
      >
        {/* Mini demo of transformation */}
      </TerminalWindow>
      
      <TerminalWindow 
        title="ALAYA" 
        active={activeService === 'alaya'}
        onClick={() => setActiveService('alaya')}
      >
        {/* Mini demo of search */}
      </TerminalWindow>
    </div>
  );
};
```

### 3. **Quick Start Options**

#### A. **Instant Terminal Access** (No signup)
```
┌─────────────────────────────────────────────────────────────┐
│ TRY NOW - NO SIGNUP REQUIRED                                │
│                                                             │
│ [Open Web Terminal]  [Install CLI]  [MCP for Cursor]       │
│                                                             │
│ Or scan QR code from your phone:                           │
│ [QR CODE]                                                   │
└─────────────────────────────────────────────────────────────┘
```

#### B. **Power User Fast Track**
```bash
# For developers - one command setup
curl -sSL https://get.gnosis.ai | sh

# For Cursor users
npx @gnosis/setup-mcp

# For enterprises
docker run -d gnosis/platform
```

### 4. **Social Proof Terminal**
```
┌─────────────────────────────────────────────────────────────┐
│ $ gnosis stats --global                                     │
│                                                             │
│ PLATFORM METRICS (LIVE):                                    │
│ ├─ Pages Crawled Today: 1,247,832                          │
│ ├─ Active Developers: 12,483                               │
│ ├─ Services Generated: 3,921                               │
│ └─ API Calls/Second: 847                                   │
│                                                             │
│ RECENT ACTIVITY:                                           │
│ [09:32:14] User transformed CNN → API in 12 seconds        │
│ [09:32:09] Enterprise crawled 50k pages for analysis       │
│ [09:32:01] Developer deployed custom news aggregator       │
└─────────────────────────────────────────────────────────────┘
```

## Technical Implementation

### 1. **Landing Page Route Structure**
```
/                    → New landing page
/wraith              → Current Wraith interface (after auth)
/forge               → Forge interface
/alaya               → Alaya interface
/try                 → Instant demo terminal (no auth)
/quickstart          → Interactive onboarding
```

### 2. **Progressive Disclosure Flow**
```
Landing → Try Demo → Create Account → Choose Plan → Access Full Platform
   ↓
Can skip to "Try Demo" anytime via:
- QR code
- Direct link
- CLI install
```

### 3. **Authentication Strategy**
- **Landing page**: No auth required
- **Try page**: Limited demo, no auth
- **Full platform**: Email/passwordless auth
- **API/CLI**: Token-based

### 4. **Component Architecture**
```javascript
// New components needed
<TerminalHero />          // Animated hero demo
<ServiceSelector />       // Interactive service cards
<LiveMetrics />          // Real-time stats
<QuickStartTerminal />   // Embedded terminal
<PricingTerminal />      // Pricing in terminal style
```

## Styling Guidelines

### Terminal Aesthetic Rules
1. **Colors**: 
   - Background: `#0a0a0a` (darker than current)
   - Primary text: `#00ff00` (classic terminal green)
   - Accent: `#00ffff` (cyan for links/CTAs)
   - Error: `#ff0040` (hot pink/red)

2. **Typography**:
   - Everything in monospace
   - ASCII art for section dividers
   - Blinking cursor on inputs

3. **Animations**:
   - Text types out character by character
   - Subtle scan line effect
   - Command execution feedback

4. **Interactive Elements**:
   - All buttons look like `[BUTTON TEXT]`
   - Hover shows `> [BUTTON TEXT]`
   - Active shows `>>[BUTTON TEXT]<<`

## Conversion Optimization

### 1. **Multiple Entry Points**
- "Try without signup" → Terminal demo
- "I'm a developer" → CLI quickstart  
- "I use Cursor" → MCP install
- "I need enterprise" → Contact form

### 2. **Reduce Time to Magic**
- Live demo starts automatically
- First "wow" within 5 seconds
- Can start using within 30 seconds

### 3. **QR Code Strategy**
```
Mobile users scan QR → 
Opens mobile-optimized terminal →
Can control desktop demo from phone →
Magic moment: "I'm controlling a server from my phone!"
```

## Implementation Phases

### Phase 1: Core Landing (Week 1)
- [ ] Create `/` route handler
- [ ] Build TerminalHero component
- [ ] Implement auto-typing animation
- [ ] Add basic service selector

### Phase 2: Live Demo (Week 2)
- [ ] Safe demo environment
- [ ] Rate-limited public API
- [ ] WebSocket for live updates
- [ ] Demo content strategy

### Phase 3: Onboarding (Week 3)
- [ ] Quick start terminal
- [ ] CLI installer
- [ ] MCP setup flow
- [ ] Mobile QR experience

### Phase 4: Polish (Week 4)
- [ ] Analytics integration
- [ ] A/B testing setup
- [ ] Performance optimization
- [ ] SEO enhancements

## Success Metrics

1. **Time to First Action**: Target <30 seconds
2. **Demo Completion Rate**: Target >60%
3. **Signup Conversion**: Target >15%
4. **CLI Install Rate**: Target >30% of developers

## Example Landing Page Flow

```
User lands on page →
Sees terminal auto-typing cool commands →
"Whoa, what is this?" →
Clicks service that interests them →
Sees live demo →
"I want this!" →
Chooses quickest path:
  - Web terminal (instant)
  - CLI install (developers)
  - MCP setup (Cursor users)
  - Create account (full access)
```

## Key Differentiators

1. **Not a static landing page** - It's a live demo
2. **Multiple ways in** - Web, CLI, MCP, QR
3. **Feels like discovering a secret tool** - Terminal aesthetic
4. **Immediate value** - Can use before signing up
5. **Developer-first** - But accessible to others

This approach makes Gnosis feel like a powerful developer tool while still being accessible as a SaaS platform. The terminal aesthetic sets expectations (powerful, technical) while the smooth onboarding removes friction.
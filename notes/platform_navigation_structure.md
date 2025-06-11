# Gnosis Platform Navigation & Page Structure

## Current Issues
- "About" duplicated across Wraith and Forge
- No unified navigation
- Traditional footer menus don't fit terminal aesthetic
- Need manifesto page
- GitHub link should point to github.com/kordless/gnosis

## Proposed Structure

### Global Header (Consistent Across All Services)
```
GNOSIS [WRAITH|FORGE|ALAYA]                    [Docs] [Manifesto] [GitHub] [Sign In]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Service Switcher (Terminal Style)
```
$ gnosis --service
> wraith    # Web intelligence & indexing
  forge     # Transform & generate
  alaya     # Knowledge storage
```

## Page URLs & Content

### 1. Landing Pages
```
/                     → Main Gnosis landing (intelligent memory pitch)
/wraith               → Wraith interface (current crawler)
/forge                → Forge interface 
/alaya                → Alaya interface
```

### 2. Information Architecture
```
/manifesto            → Why we built this, philosophy, privacy pledge
/docs                 → Technical documentation
/docs/api             → API reference
/docs/mcp             → MCP setup guide
/docs/self-host       → Docker/local setup
/pricing              → Tiers and licensing
```

### 3. Auth Flow
```
/auth/login           → Email entry
/auth/token           → Token verification
/auth/logout          → Logout confirmation
```

## No Traditional Footer - Terminal Status Bar Instead

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Main Content Area]                                                         │
│                                                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
[GNOSIS v4.2.0] [Status: Connected] [Memory: 2.4GB] [Docs] [API] [Status Page]
```

## Manifesto Page Content Structure

```
/manifesto

THE GNOSIS MANIFESTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Why We Built This

AI has a memory problem. Every conversation starts from zero.
Every document gets forgotten. Every insight vanishes.

We built Gnosis to give AI persistent memory.

## Our Beliefs

1. YOUR DATA IS YOURS
   - We never train on your content
   - Run our code locally to verify
   - Privacy by design, not by policy

2. INTELLIGENCE OVER VOLUME
   - Not about crawling everything
   - About understanding what matters
   - Quality of index beats quantity

3. OPEN BY DEFAULT
   - Source available at github.com/kordless/gnosis
   - Run anywhere: cloud or local
   - No vendor lock-in

## Our Promise

Personal use will always be free.
Your data will never train our models.
The code you run locally is what we run in production.

## The Vision

A world where AI truly augments human intelligence
by remembering what we've learned together.

---
Built with ❤️ and 🧠 by humans who got tired of copy-pasting
```

## Navigation Component (React)

```javascript
const GnosisNav = ({ currentService }) => {
  return (
    <nav className="gnosis-nav bg-black text-green-400 p-4">
      <div className="flex justify-between items-center">
        {/* Left: Logo + Service */}
        <div className="flex items-center space-x-4">
          <Link to="/" className="text-xl font-bold">
            GNOSIS
          </Link>
          {currentService && (
            <>
              <span className="text-gray-500">/</span>
              <span className="text-yellow-400">{currentService.toUpperCase()}</span>
            </>
          )}
        </div>
        
        {/* Right: Quick Links */}
        <div className="flex items-center space-x-6">
          <Link to="/docs" className="hover:text-green-300">
            [Docs]
          </Link>
          <Link to="/manifesto" className="hover:text-green-300">
            [Manifesto]
          </Link>
          <a 
            href="https://github.com/kordless/gnosis" 
            target="_blank"
            className="hover:text-green-300"
          >
            [<i className="fab fa-github"></i>]
          </a>
          {isAuthenticated ? (
            <Link to="/dashboard" className="hover:text-green-300">
              [Dashboard]
            </Link>
          ) : (
            <Link to="/auth/login" className="hover:text-green-300">
              [Sign In]
            </Link>
          )}
        </div>
      </div>
      
      {/* Service Switcher (only on service pages) */}
      {currentService && (
        <ServiceSwitcher current={currentService} />
      )}
    </nav>
  );
};
```

## URL Strategy

### Primary Domains
```
gnosis.ai             → Landing page
wraith.gnosis.ai      → Wraith service (or gnosis.ai/wraith)
forge.gnosis.ai       → Forge service (or gnosis.ai/forge)
alaya.gnosis.ai       → Alaya service (or gnosis.ai/alaya)
```

### Shared Pages (Accessible from any service)
```
*/manifesto           → Same content everywhere
*/docs                → Same docs everywhere
*/pricing             → Same pricing everywhere
```

## Terminal-Style Page Transitions

Instead of traditional page loads:
```
$ gnosis navigate manifesto
> Loading manifesto...
> ████████████████████ 100%
> Displaying content.
```

## Implementation Priority

1. **Fix GitHub link** → Point to github.com/kordless/gnosis
2. **Create unified nav component** → Use across all services
3. **Build manifesto page** → Core philosophy and beliefs
4. **Remove duplicate "About" pages** → Consolidate into manifesto
5. **Add terminal status bar** → Replace traditional footer

## Key Design Principles

1. **No traditional web cruft** - No footer with columns of links
2. **Terminal aesthetic throughout** - Navigation feels like commands
3. **Service context visible** - Always know which service you're in
4. **Quick access to philosophy** - Manifesto prominent, not hidden
5. **Developer-friendly** - GitHub, docs, API always one click away

This creates a cohesive experience across all Gnosis services while maintaining the terminal aesthetic and avoiding traditional web patterns that don't fit.
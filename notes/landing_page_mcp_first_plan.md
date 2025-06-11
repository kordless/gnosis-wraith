# Gnosis Landing Page - MCP-First Implementation Plan

## Core Value Prop: "MCP Server for Your AI IDE in 30 Seconds"

### Hero Section: Get Started FAST

```
GNOSIS WRAITH
AI-Powered Web Intelligence for Your IDE

[Copy MCP Config]  [Sign In (30s)]  [Run Locally]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### The Three Paths (In Priority Order)

## 1. MCP Quick Setup (PRIMARY CTA)

```json
{
  "mcpServers": {
    "gnosis": {
      "command": "npx",
      "args": ["@gnosis/wraith-mcp"],
      "env": {
        "GNOSIS_API_KEY": "Get free key in 30 seconds →"
      }
    }
  }
}

[Copy to Clipboard]

Works with: Cursor | Windsurf | Cline | Claude Desktop
```

**Below the code block:**
```
✓ Paste this in your IDE's config
✓ Sign in to get your API key (email only, 30 seconds)
✓ Start using Gnosis tools in your chat

[Get API Key →]
```

## 2. Cloud Sign In (30 Second Flow)

```
┌─────────────────────────────────────────────────┐
│ QUICK SIGN IN                                   │
│                                                 │
│ Email: [___________________________]           │
│                                                 │
│ [Send Magic Link]                               │
│                                                 │
│ ☐ Enable Gnosis Secure SMS™ (optional)         │
│   Two-factor auth for enterprise users         │
│                                                 │
│ › No password required                          │
│ › Check email for login link                   │
│ › Get API key instantly                        │
└─────────────────────────────────────────────────┘
```

## 3. Run Locally (For Developers)

```bash
# Option A: Docker (Recommended)
docker run -d -p 5678:5678 gnosis/wraith

# Option B: Python
pip install gnosis-wraith
gnosis-wraith serve

# Option C: From Source
git clone https://github.com/gnosis/wraith
cd wraith && ./start.sh

[View Full Docs →] (/docs)
```

## Simplified Page Structure

### Above the Fold
```
GNOSIS WRAITH                                [Sign In]
AI Web Intelligence MCP Server

Turn any website into queryable data.
Built for Cursor, Windsurf, and Claude.

[Get MCP Config]  [Sign In (30s)]  [Docs]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### What You Can Do (Simple Examples)
```
In your IDE chat:
│
├─ "Crawl competitor's pricing page"
├─ "Extract all job listings from this site"  
├─ "Monitor these 5 URLs for changes"
└─ "Turn this documentation into an API"

Real examples from our users →
```

### MCP Installation Steps (Visual)
```
Step 1: Copy Config          Step 2: Get API Key         Step 3: Use in IDE
┌─────────────────┐         ┌──────────────────┐        ┌─────────────────┐
│ {               │         │ Email:           │        │ > Find React    │
│   "mcpServers": │   →     │ [_____________]  │   →    │   examples from │
│     ...         │         │                  │        │   Vercel's site │
│ }               │         │ [Send Link]      │        │                 │
└─────────────────┘         └──────────────────┘        └─────────────────┘
     ↓                             ↓                            ↓
  Copy JSON                   Check Email                  Gnosis crawls
```

### Pricing (Simple Terminal Style)
```
FREE TIER                 PRO                    ENTERPRISE
$0/month                  $29/month              Contact Us
─────────────            ─────────────          ─────────────
100 crawls/day           10,000 crawls/day      Unlimited
Basic support            Priority support        Dedicated support
MCP + Web UI             Everything in Free +    Everything in Pro +
                         API access              Secure SMS™
                         Custom domains          On-premise option
                         Advanced search         SLA guarantees

[Start Free]             [Start Free Trial]     [Talk to Sales]
```

## Implementation Details

### 1. Route Structure
```
/                → Landing page (this plan)
/auth/login      → 30-second email auth
/auth/token      → Token entry page
/dashboard       → Post-login dashboard with API key
/docs            → Full documentation
/pricing         → Detailed pricing
```

### 2. Landing Page Components

```javascript
// Main components needed
<MCPCodeBlock />        // Copy-able MCP config
<QuickSignIn />         // Email-only form
<LocalSetup />          // Docker/pip commands
<ExampleCarousel />     // Rotating examples
<PricingCards />        // Three-tier pricing
```

### 3. Auth Flow Optimization
```
1. User enters email
2. System sends magic link
3. User clicks link → logged in
4. Dashboard shows API key prominently
5. One-click copy API key
6. Optional: Enable SMS 2FA
```

### 4. MCP Config Generator
```javascript
const MCPConfigGenerator = ({ apiKey }) => {
  const config = {
    mcpServers: {
      gnosis: {
        command: "npx",
        args: ["@gnosis/wraith-mcp"],
        env: {
          GNOSIS_API_KEY: apiKey || "YOUR_API_KEY_HERE"
        }
      }
    }
  };
  
  return (
    <div className="bg-gray-900 p-4 rounded">
      <pre className="text-green-400">
        {JSON.stringify(config, null, 2)}
      </pre>
      <button onClick={copyToClipboard}>
        [Copy Config]
      </button>
    </div>
  );
};
```

## Key Messages

1. **"MCP Server in 30 Seconds"** - Speed is the differentiator
2. **"No Password Required"** - Passwordless is modern
3. **"Works with Your IDE"** - Cursor/Windsurf/Cline ready
4. **"Free to Start"** - Remove friction

## Success Metrics

- **Time to API Key**: <60 seconds from landing
- **MCP Config Copies**: Track clipboard usage
- **Free Tier Signups**: Target 40% of visitors
- **MCP Install Success**: Track first API call

## Visual Design

- Keep current terminal aesthetic
- Green on black for familiarity  
- Monospace throughout
- Minimal, focused on code/config
- Interactive elements obvious

This approach prioritizes getting developers using Gnosis through their IDE as fast as possible, with the MCP config as the primary CTA.
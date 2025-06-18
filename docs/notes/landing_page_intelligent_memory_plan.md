# Gnosis Landing Page - Intelligent Memory for AI Conversations

## Core Value Prop: "Give Your AI Perfect Memory"

### Hero Section: The Problem & Solution

```
GNOSIS
Your AI's Extended Memory

Stop losing context. Stop retraining threads.
Index documents, URLs, and images once - discuss forever.

[Get MCP Config]  [Sign In (30s)]  [Run Locally]

Works with: Claude Desktop | Cursor | Windsurf | Cline
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Our Privacy Pledge (Prominent Section)

```
┌─────────────────────────────────────────────────┐
│ 🔒 YOUR DATA STAYS YOURS                       │
│                                                 │
│ We will NEVER:                                  │
│ ❌ Train models on your data                    │
│ ❌ Share your documents with others             │
│ ❌ Use your content for our growth              │
│                                                 │
│ Proof? Run our exact code locally:             │
│                                                 │
│ docker run -d gnosis/memory                     │
│                                                 │
│ Same code. Your infrastructure.                │
│ Zero trust required.                            │
│                                                 │
│ * Corporate use requires license - see terms   │
└─────────────────────────────────────────────────┘
```

## The Real Problem We Solve

```
WITHOUT GNOSIS                    WITH GNOSIS
─────────────────                 ─────────────────
"Read this 50-page PDF"           "What did the PDF say about X?"
*AI forgets after 5 messages*     *AI remembers everything*

"Check these 10 URLs"             "Compare all those sites"
*Context window explodes*         *Instant perfect recall*

"Remember this for later"         "What did we discuss last month?"
*Start new thread, lose it all*   *Seamless continuation*
```

## MCP Quick Setup (Primary CTA)

```json
{
  "mcpServers": {
    "gnosis": {
      "command": "npx",
      "args": ["@gnosis/memory-mcp"],
      "env": {
        "GNOSIS_API_KEY": "Get free key in 30 seconds →"
      }
    }
  }
}

[Copy to Clipboard]
```

**What You Can Do:**
```
│ "Save this documentation for our project"
│ "Index my competitor's entire website"  
│ "Remember these meeting notes"
│ "Store these architecture diagrams"
└─→ Then discuss them in ANY future conversation
```

## Choose Your Deployment

```
CLOUD (EASY)                     SELF-HOSTED (PRIVATE)
━━━━━━━━━━━━                     ━━━━━━━━━━━━━━━━━━━━
✓ Zero setup                     ✓ Complete data control
✓ Always updated                 ✓ Air-gapped option
✓ 30-second start                ✓ Your infrastructure
✓ We handle scale                ✓ Audit everything

[Start Cloud Free]               [View Docker Docs]

                LICENSE NOTE
    Personal use: Free forever (both options)
    Corporate use: License required
    [View License Terms]
```

## Three Tiers of Intelligence (Not Crawl Limits)

```
BASIC MEMORY              EXTENDED MEMORY         PERFECT MEMORY
Free                      $29/month               $99/month
─────────────            ─────────────           ─────────────
100 MB storage           10 GB storage           Unlimited storage
Basic indexing           Smart indexing          Semantic indexing
Text & URLs              + Images & PDFs         + Any file type
Single workspace         5 workspaces            Unlimited workspaces
                         Version history         Full audit trail
                         API access              Priority processing

[Start Free]             [Start Free Trial]      [Contact Sales]
```

## How It Works (Visual)

```
Step 1: Save Anything        Step 2: It's Indexed       Step 3: Discuss Anytime
┌─────────────────┐         ┌──────────────────┐        ┌─────────────────┐
│ "Index this PDF"│         │ ▓▓▓▓▓▓▓▓░░ 90%  │        │ "What did the   │
│ "Save this URL" │   →     │ Creating smart   │   →    │  PDF say about  │
│ "Store image"   │         │ memory index...  │        │  deployment?"   │
└─────────────────┘         └──────────────────┘        └─────────────────┘
     ↓                             ↓                            ↓
  One command               Intelligent parsing          Perfect recall
```

## Trust Through Transparency

```
WHY DOCKER MATTERS
────────────────────────────────────────────────
We're not asking you to trust us with your data.
We're giving you the code to run it yourself.

$ docker run -d -p 5678:5678 gnosis/memory
$ # Your data never leaves your servers

This isn't a "lite" version. It's the EXACT same
code we run in production. Because your privacy
matters more than our convenience.

Corporate? You'll need a license. Fair is fair.
Personal use? Free forever. That's a promise.
```

## Use Cases That Resonate

### For Developers
```
"I indexed our entire codebase docs. Now Claude can answer 
questions about our internal APIs without me copy-pasting."
- Senior Dev at Stripe
```

### For Researchers  
```
"50 research papers indexed. My AI assistant knows more
about my field than I do now."
- PhD Candidate, MIT
```

### For Business Users
```
"All our SOPs and policies indexed. New employees get
AI assistance that actually knows our procedures."
- Operations Manager
```

## Simple Sign In Flow

```
┌─────────────────────────────────────────────────┐
│ Create Your Memory Bank                         │
│                                                 │
│ Email: [___________________________]           │
│                                                 │
│ [Send Magic Link]                               │
│                                                 │
│ ☐ Enable Gnosis Secure SMS™ (recommended)      │
│                                                 │
│ No password. No complexity.                     │
│ Check email → Click link → Start indexing.      │
└─────────────────────────────────────────────────┘
```

## What Makes Gnosis Different

```
❌ NOT ANOTHER CRAWLER
We don't scrape the web. We create intelligent indexes
of YOUR documents for YOUR AI conversations.

✓ PERSISTENT MEMORY
Your AI remembers everything across all conversations

✓ INTELLIGENT INDEXING  
Not just storage - semantic understanding of content

✓ INSTANT RECALL
No retraining. No context stuffing. Just memory.

✓ PRIVACY FIRST
Your data is yours. Run it locally to prove it.
```

## Developer-Friendly Integration

```bash
# Cloud API
curl -X POST https://api.gnosis.ai/index \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"url": "https://docs.yoursite.com"}'

# Or Self-Hosted
curl -X POST http://localhost:5678/index \
  -H "Authorization: Bearer LOCAL_KEY" \
  -d '{"url": "https://internal-docs.local"}'

# Python SDK (works with both)
from gnosis import Memory
memory = Memory(
    api_key="YOUR_KEY",
    endpoint="https://api.gnosis.ai"  # or http://localhost:5678
)
memory.index("https://important-docs.com")
```

## The Pitch in One Line

**"Gnosis gives your AI perfect memory of everything you've ever shown it - on our cloud or yours."**

## Implementation Notes

### Landing Page Focus
1. **Privacy Pledge**: Front and center, not buried in terms
2. **Docker Option**: Equal prominence with cloud
3. **License Clarity**: Personal free, corporate pays
4. **Trust Building**: Same code, your choice where to run it

### Key Differentiators
- Not about crawl count but intelligence
- Not web scraping but document indexing
- Not temporary context but permanent memory
- Not vendor lock-in but portable deployment
- Works across all AI tools (Claude Desktop emphasized)

### Messaging
- "Extended Memory for AI"
- "Never Lose Context Again"
- "Index Once, Discuss Forever"
- "Your AI's Second Brain"
- "Your Data, Your Servers, Your Choice"

This positions Gnosis as both powerful AND trustworthy - essential for anyone seriously using AI tools while caring about data privacy.
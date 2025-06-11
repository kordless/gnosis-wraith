# MCP Easy Setup Plan for Hosted Gnosis Wraith

## Executive Summary

This document outlines a comprehensive plan to make MCP (Model Context Protocol) server setup extremely easy for hosted Gnosis Wraith users. The goal is to reduce setup friction from 20+ steps to a single command, enabling users to integrate Wraith's powerful web crawling and analysis capabilities directly into their AI-powered IDEs (Cursor, Windsurf, Cline) within seconds.

## Problem Statement

Current MCP server setup requires:
- Installing Python/Node dependencies
- Manually editing JSON config files
- Finding correct file paths
- Managing API keys
- Restarting IDEs
- Debugging connection issues

This complexity prevents adoption and frustrates users who just want to use Wraith's capabilities in their IDE.

## Proposed Solution: Three-Tier Approach

### Tier 1: Cloud-Hosted MCP Gateway (Recommended)

**Architecture:**
```
User's IDE <-> NPM Client <-> MCP Gateway <-> Wraith API
```

**Benefits:**
- No local Wraith installation needed
- Always up-to-date
- Centralized auth and rate limiting
- Usage analytics
- Works behind corporate firewalls

**Implementation:**

1. **NPM Package: `@gnosis/wraith-mcp`**
   ```javascript
   // Lightweight client that connects to cloud gateway
   // Auto-handles auth, reconnection, and protocol translation
   npm install -g @gnosis/wraith-mcp
   ```

2. **MCP Gateway Service: `mcp.wraith.nuts.services`**
   - WebSocket server handling MCP protocol
   - Translates MCP calls to Wraith API calls
   - Handles authentication via API keys
   - Provides real-time streaming for long operations
   - Multi-tenant with usage tracking

3. **One-Command Setup:**
   ```bash
   npx @gnosis/setup-wraith-mcp
   ```
   
   This command:
   - Opens browser for OAuth login
   - Generates API key
   - Detects installed IDEs
   - Writes configuration
   - Tests connection
   - Shows success confirmation

### Tier 2: Local Docker Container

For users who prefer self-hosting or have compliance requirements:

**Docker Compose Configuration:**
```yaml
version: '3.8'
services:
  wraith-mcp:
    image: gnosis/wraith-mcp:latest
    environment:
      - WRAITH_API_URL=${WRAITH_URL:-https://wraith.nuts.services}
      - WRAITH_API_KEY=${WRAITH_API_KEY}
    ports:
      - "3456:3456"
    restart: unless-stopped
```

**Setup Command:**
```bash
curl -sSL https://get.wraith.dev/docker | bash
```

### Tier 3: Direct API Integration

For advanced users who want direct integration:

**Simple Python Script:**
```python
# wraith-mcp-local.py
pip install gnosis-wraith-mcp
wraith-mcp serve --api-key YOUR_KEY
```

## Detailed Implementation Plan

### Phase 1: NPM Package Development (Week 1-2)

**Package Structure:**
```
@gnosis/wraith-mcp/
├── src/
│   ├── client.ts         # MCP client implementation
│   ├── auth.ts          # Authentication handling
│   ├── tools/           # Tool definitions
│   │   ├── crawl.ts     # Web crawling tool
│   │   ├── analyze.ts   # Content analysis tool
│   │   └── monitor.ts   # Site monitoring tool
│   └── setup.ts         # Auto-configuration wizard
├── bin/
│   ├── wraith-mcp       # Main executable
│   └── setup-wraith     # Setup wizard
└── package.json
```

**Key Features:**
- Auto-reconnection with exponential backoff
- Credential caching in system keychain
- IDE detection (Cursor, VSCode, Windsurf, Cline)
- Progress reporting for long operations
- Error handling with helpful messages

### Phase 2: Web Dashboard Integration (Week 2-3)

**Dashboard Features at `wraith.nuts.services/developers`:**

1. **Quick Start Page:**
   - Big "Setup IDE Integration" button
   - Animated GIF showing the process
   - Copy button for setup command
   - IDE-specific instructions

2. **API Key Management:**
   - Generate multiple keys with labels
   - Set permissions per key
   - Usage statistics
   - Rate limit configuration

3. **Configuration Generator:**
   ```javascript
   // Interactive config builder
   const config = generateConfig({
     ide: 'cursor',
     tools: ['crawl', 'analyze', 'monitor'],
     apiKey: user.keys.primary,
     advanced: showAdvancedOptions
   });
   ```

4. **Live Testing Interface:**
   - Test MCP connection from browser
   - See real-time logs
   - Debug connection issues
   - Example commands to try

### Phase 3: Setup Wizard Development (Week 3-4)

**Interactive CLI Wizard:**
```
$ npx @gnosis/setup-wraith-mcp

🔮 Gnosis Wraith MCP Setup Wizard

✓ Checking system requirements...
✓ Found IDEs: Cursor, VSCode

? Which IDE would you like to configure? (Use arrow keys)
❯ Cursor
  VSCode
  All

? How would you like to authenticate?
❯ Login with browser (recommended)
  Use existing API key
  Create new account

🌐 Opening browser for authentication...
✓ Authentication successful!

✓ Installing MCP client...
✓ Configuring Cursor...
✓ Testing connection...

🎉 Setup complete! Restart Cursor to use Wraith tools.

Try these commands in Cursor chat:
- "Crawl https://example.com with Wraith"
- "Analyze the content structure of my competitor's site"
- "Monitor these 5 URLs for changes"
```

### Phase 4: Cloud Gateway Development (Week 4-6)

**Gateway Architecture:**

```typescript
// MCP Gateway Server
class WraithMCPGateway {
  // WebSocket handling for persistent connections
  handleConnection(ws: WebSocket, apiKey: string) {
    // Validate API key
    // Setup bidirectional proxy to Wraith API
    // Handle streaming responses
    // Track usage metrics
  }

  // Tool implementations
  async crawl(params: CrawlParams): Promise<CrawlResult> {
    // Rate limiting
    // Parameter validation  
    // Call Wraith API
    // Stream results back
  }
}
```

**Infrastructure Requirements:**
- WebSocket server (Node.js/Deno)
- Redis for session management
- CloudFlare for DDoS protection
- Prometheus for metrics
- Auto-scaling based on connections

### Phase 5: IDE Extensions (Week 6-8)

**Cursor/VSCode Extension:**
- One-click setup from extension marketplace
- Visual tool palette
- Inline result previews
- Context menu integration ("Crawl this URL with Wraith")

## User Experience Flow

### First-Time Setup (Target: Under 60 seconds)

1. **User visits wraith.nuts.services**
2. **Clicks "Setup IDE Integration"**
3. **Copies command:** `npx @gnosis/setup-wraith-mcp`
4. **Runs command in terminal**
5. **Browser opens for auth** (auto-closes after success)
6. **Setup completes automatically**
7. **User restarts IDE**
8. **Wraith tools available immediately**

### Daily Usage

```
User: "Crawl my competitor's pricing page"
Cursor: [Uses Wraith MCP tool automatically]
Result: Full markdown + screenshots delivered inline
```

## Security Considerations

1. **API Key Security:**
   - Keys stored in system keychain
   - Never logged or exposed
   - Scoped permissions
   - Automatic rotation available

2. **Network Security:**
   - All traffic over HTTPS/WSS
   - Certificate pinning for enterprise
   - IP allowlisting optional

3. **Data Privacy:**
   - No crawled content stored on gateway
   - Usage metrics anonymized
   - GDPR compliant
   - SOC2 certification planned

## Metrics for Success

1. **Setup Completion Rate:** Target >90%
2. **Time to First Successful Call:** Target <2 minutes
3. **Daily Active Tools Usage:** Target 50% of registered users
4. **Setup Errors:** Target <5%
5. **User Satisfaction:** Target >4.5/5 stars

## Rollout Plan

### Beta Phase (Week 8-10)
- 50 invited users
- Discord channel for feedback
- Daily updates based on issues
- Video tutorials created

### General Availability (Week 10+)
- Public launch
- Documentation site
- YouTube demos
- Partner with AI IDE communities

## Alternative Approaches Considered

1. **Browser Extension:** Rejected due to security restrictions
2. **Desktop App:** Rejected as too heavy for simple integration  
3. **Direct Binary:** Rejected due to platform differences
4. **OAuth-Only:** Rejected as some users prefer API keys

## Cost Analysis

**Development Costs:**
- 8 weeks of development: $40,000
- Infrastructure setup: $5,000
- Documentation/tutorials: $5,000
- **Total:** $50,000

**Ongoing Costs (Monthly):**
- Gateway hosting: $500-2000 (scales with usage)
- NPM hosting: Free
- Support: 10 hours/week
- **Total:** $2,500-4,500/month

**Revenue Potential:**
- Increased conversion due to easy setup
- Upsell opportunity for premium features
- Enterprise MCP gateway licensing

## Technical Specifications

### MCP Protocol Implementation

```typescript
interface MCPTool {
  name: string;
  description: string;
  inputSchema: JSONSchema;
  handler: (params: any) => Promise<any>;
}

class WraithMCPTools {
  tools: MCPTool[] = [
    {
      name: "wraith_crawl",
      description: "Crawl a website and extract content",
      inputSchema: {
        type: "object",
        properties: {
          url: { type: "string", description: "URL to crawl" },
          options: {
            type: "object",
            properties: {
              screenshot: { type: "boolean" },
              javascript: { type: "boolean" },
              markdown: { type: "string", enum: ["basic", "enhanced"] }
            }
          }
        },
        required: ["url"]
      },
      handler: async (params) => {
        return await this.wraithAPI.crawl(params);
      }
    },
    // ... more tools
  ];
}
```

### Configuration File Format

```json
{
  "mcpServers": {
    "wraith": {
      "command": "npx",
      "args": ["@gnosis/wraith-mcp", "serve"],
      "env": {
        "WRAITH_API_KEY": "${WRAITH_API_KEY}",
        "WRAITH_ENDPOINT": "wss://mcp.wraith.nuts.services",
        "WRAITH_LOG_LEVEL": "info"
      }
    }
  }
}
```

## Success Stories (Projected)

> "I was skeptical about IDE integration, but Wraith's setup was literally one command. Now I crawl competitor sites without leaving Cursor." - Beta User

> "The MCP gateway means I don't need to install anything locally. Perfect for our security-conscious enterprise." - Enterprise Customer

> "Setup took 45 seconds. My mind was blown when I could just say 'analyze this site' and get instant results." - Indie Developer

## Conclusion

By implementing this three-tier approach with a focus on the cloud-hosted MCP gateway, we can reduce setup friction to near zero while providing a robust, scalable solution for IDE integration. The key is meeting users where they are - whether they want a simple cloud solution, self-hosted option, or direct integration.

The one-command setup (`npx @gnosis/setup-wraith-mcp`) will become the gold standard for MCP server installation, driving adoption and making Wraith's powerful capabilities accessible to every developer using AI-powered IDEs.

## Appendix: Quick Implementation Checklist

- [ ] Create @gnosis/wraith-mcp NPM package
- [ ] Build MCP gateway infrastructure  
- [ ] Develop setup wizard CLI
- [ ] Add dashboard integration pages
- [ ] Write comprehensive documentation
- [ ] Create video tutorials
- [ ] Beta test with 50 users
- [ ] Launch publicly
- [ ] Monitor metrics and iterate

---

*Document Version: 1.0*  
*Last Updated: June 6, 2025*  
*Author: Gnosis Wraith Team*
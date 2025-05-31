# Claude Desktop API Access Report

## Summary
Claude Desktop stores conversation history locally but lacks an official API for programmatic access. While built-in export features exist, developers seeking to integrate with chat history must use unofficial methods.

## Official Methods
- **Built-in Export**: Users can export all data via Settings → Privacy → Export data
- **Data Format**: Provides complete conversation history delivered via email

## Unofficial API Options
- **Unofficial Claude API** (github.com/st1vms/unofficial-claude-api):
  - Python library for Claude.ai interaction
  - Features: chat creation, message history retrieval, chat deletion
  - Requires Firefox with geckodriver for session authentication
  - Supports proxy configurations and file attachments

- **Claude Export Script** (github.com/ryanschiang/claude-export):
  - Browser-based export to Markdown, JSON, or PNG
  - Works locally without server dependencies
  - Limited to manual execution

- **MCP Server Implementation** (github.com/mlobo2012/Claude_Desktop_API_USE_VIA_MCP):
  - Integration between Claude Desktop and API
  - Provides conversation management features
  - Requires additional setup and API key

## Limitations
- All unofficial methods lack official support
- May break with Claude updates
- Session handling can be complex
- Rate limits apply to free accounts

## Recommendation
For developers needing programmatic access to Claude chat history, the unofficial Claude API library offers the most comprehensive solution, though requires technical setup. For simple exports, the official export feature remains most reliable.

*Note: This information is current as of May 2025 and subject to change with Claude updates.*
# AI Tools Directory

This directory contains modular tools that can be used with different AI providers (Anthropic, OpenAI, Ollama, etc.).

## Structure
- Each tool module (e.g., `calculate.py`) contains related tools using `@mcp.tool()` decorators
- Tools are loaded dynamically based on query requirements  
- Provider-agnostic design allows same tools to work with different AI services

## Usage
Tools are selected and loaded based on the type of query being processed.

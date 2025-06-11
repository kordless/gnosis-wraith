# Gnosis Wraith LLM Agentic API Implementation Plan

## Overview
This plan outlines the implementation of advanced LLM-powered endpoints for Gnosis Wraith v2 API, focusing on:
1. JavaScript injection generation and execution
2. Self-writing code examples for response formatting
3. Markdown cleanup and optimization
4. OCR with image-to-LLM processing
5. Agentic workflow with tool chaining

## Current State
- ✅ Basic v2 endpoints implemented: `/md`, `/screenshot`, `/pdf`, `/html`, `/batch`
- ✅ Authentication system with API tokens
- ✅ Basic LLM integration in `/api/suggest` endpoint
- ✅ Toolbag system for chaining tools
- ⚠️ Missing: JavaScript execution, agentic workflows, OCR-to-LLM, markdown cleanup

## Implementation Tasks for Claude Code

### 1. JavaScript Injection Endpoint (`/api/v2/execute
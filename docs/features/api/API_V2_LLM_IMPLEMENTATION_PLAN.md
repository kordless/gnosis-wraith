# API v2 LLM Features Implementation Plan

## Core LLM-Powered Features to Implement

### 1. JavaScript Injection System (`/api/v2/inject`)

**Purpose**: Generate and execute JavaScript based on natural language requests

**Request Structure**:
```json
{
  "url": "https://example.com",
  "request": "Extract all email addresses from the page",
  "llm_provider": "anthropic",
  "llm_token": "sk-...",
  "execute_immediately": true,
  "return_code": false
}
```

**Workflow**:
1. LLM analyzes the request and generates appropriate JavaScript
2. JavaScript is validated for safety
3. Code is injected and executed on the target page
4. Results are extracted and returned

**Implementation Notes**:
- Use the existing `ai/code_generator.py` as a base
- Add JavaScript-specific prompts and validation
- Integrate with browser automation for execution
- Safety checks to prevent malicious code

### 2. Content Processing Suggestions (`/api/v2/suggest`)

**Purpose**: Generate code snippets for processing extracted content

**Request Structure**:
```json
{
  "content": "// extracted markdown or HTML",
  "goal": "Create a table of all product prices",
  "output_format": "python|javascript|jq",
  "llm_provider": "anthropic",
  "llm_token": "sk-..."
}
```

**Workflow**:
1. Analyze the content structure
2. Generate appropriate processing code
3. Optionally execute and show results
4. Return code with explanations

**Implementation Notes**:
- Self-writing examples based on actual content
- Multiple output format support
- Include common patterns library

### 3. Markdown Cleanup (`/api/v2/clean`)

**Purpose**: Use LLM to clean and optimize messy markdown

**Request Structure**:
```json
{
  "markdown": "// messy markdown content",
  "goals": ["remove_ads", "fix_formatting", "simplify_structure"],
  "preserve": ["links", "images"],
  "llm_provider": "anthropic",
  "llm_token": "sk-..."
}
```

**Workflow**:
1. Analyze markdown structure and issues
2. Apply intelligent cleanup rules
3. Preserve important content
4. Return optimized markdown

**Implementation Notes**:
- Handle large documents by chunking
- Preserve semantic structure
- Option for aggressive vs conservative cleaning

### 4. OCR to LLM Pipeline (`/api/v2/vision`)

**Purpose**: Extract text from images and analyze with LLM

**Request Structure**:
```json
{
  "url": "https://example.com",
  "image_selector": "img.product-image",
  "analysis_prompt": "Extract product details from these images",
  "llm_provider": "anthropic|openai",
  "llm_token": "sk-...",
  "vision_model": "claude-3-opus-20240229"
}
```

**Workflow**:
1. Extract images from webpage
2. Send to vision-capable LLM
3. Process responses
4. Aggregate results

**Implementation Notes**:
- Support for Claude Vision and GPT-4V
- Batch processing for multiple images
- Fallback to traditional OCR if needed

### 5. Agentic Workflow Engine (`/api/v2/workflow`)

**Purpose**: Execute multi-step workflows with decision points

**Request Structure**:
```json
{
  "url": "https://example.com",
  "workflow": {
    "steps": [
      {
        "tool": "extract_content",
        "params": {"format": "markdown"}
      },
      {
        "tool": "analyze_content", 
        "params": {"prompt": "Is this a product page?"},
        "decision": {
          "if_true": "extract_product_details",
          "if_false": "summarize_content"
        }
      }
    ]
  },
  "llm_provider": "anthropic",
  "llm_token": "sk-..."
}
```

**Workflow**:
1. Parse workflow definition
2. Execute steps sequentially
3. Make decisions based on LLM analysis
4. Return complete execution trace

**Implementation Notes**:
- Built on existing toolbag system
- Support conditional branching
- Error handling and recovery
- Progress tracking for long workflows

## Implementation Priority

### Phase 1: Core JavaScript Injection
1. `/api/v2/execute` - Direct JavaScript execution
2. `/api/v2/inject` - LLM-generated JavaScript
3. Safety validation system

### Phase 2: Content Processing
1. `/api/v2/suggest` - Code generation for content
2. `/api/v2/clean` - Markdown cleanup
3. `/api/v2/analyze` - General content analysis

### Phase 3: Vision and OCR
1. `/api/v2/ocr` - Basic OCR extraction
2. `/api/v2/vision` - LLM vision analysis
3. Integration with content pipeline

### Phase 4: Workflow Automation
1. `/api/v2/workflow` - Workflow engine
2. `/api/v2/chain` - Simple tool chaining
3. Decision tree support

## Technical Requirements

### LLM Integration
- Support for Anthropic Claude (primary)
- Support for OpenAI GPT-4 (secondary)
- Local model fallback options
- Token usage tracking

### Safety and Security
- JavaScript sandbox for execution
- Code validation before injection
- Rate limiting per API token
- Audit logging for all operations

### Performance
- Async/await for all operations
- Streaming for large responses
- Caching for repeated operations
- Batch processing optimization

## File Structure for Implementation

```
gnosis-wraith/
├── ai/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── javascript_agent.py
│   │   ├── content_agent.py
│   │   ├── vision_agent.py
│   │   └── workflow_agent.py
│   ├── prompts/
│   │   ├── javascript_injection.py
│   │   ├── content_processing.py
│   │   └── markdown_cleanup.py
│   └── validators/
│       ├── javascript_validator.py
│       └── safety_checker.py
├── core/
│   ├── javascript_executor.py
│   ├── workflow_engine.py
│   └── vision_processor.py
└── web/
    └── routes/
        └── api_v2_llm.py  # New endpoints
```

## Next Steps for Claude Code

1. Read existing code structure:
   - `ai/code_generator.py`
   - `ai/toolbag.py`
   - `web/routes/api_v2.py`

2. Implement `/api/v2/execute` endpoint first
3. Add `/api/v2/inject` with LLM integration
4. Create safety validation system
5. Test with real-world examples
6. Iterate based on results

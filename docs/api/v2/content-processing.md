# AI-Powered Content Processing

Transform and analyze web content using advanced AI models from multiple providers.

## 🧠 Content Analysis

### POST `/api/v2/analyze`

Analyze content to extract entities, sentiment, themes, and insights.

#### Request

```json
{
  "content": "Apple Inc. announced record quarterly revenue of $123.9 billion, up 2 percent year over year. CEO Tim Cook attributed the growth to strong iPhone 15 sales and expanding services revenue. The company also revealed plans to invest heavily in AI research, competing directly with Microsoft and Google in the enterprise AI market.",
  "analysis_type": "comprehensive",
  "llm_provider": "anthropic",
  "llm_token": "sk-ant-...",
  "options": {
    "include_confidence_scores": true,
    "language": "en"
  }
}
```

#### Response

```json
{
  "success": true,
  "analysis": {
    "entities": [
      {
        "text": "Apple Inc.",
        "type": "ORGANIZATION",
        "confidence": 0.99,
        "metadata": {
          "wikipedia_url": "https://en.wikipedia.org/wiki/Apple_Inc.",
          "industry": "Technology"
        }
      },
      {
        "text": "Tim Cook",
        "type": "PERSON",
        "role": "CEO",
        "confidence": 0.98
      },
      {
        "text": "$123.9 billion",
        "type": "MONEY",
        "normalized": 123900000000,
        "currency": "USD",
        "confidence": 0.99
      }
    ],
    "sentiment": {
      "overall": "positive",
      "score": 0.82,
      "aspects": {
        "financial_performance": "very_positive",
        "competitive_position": "positive",
        "future_outlook": "positive"
      }
    },
    "key_themes": [
      {
        "theme": "Financial Growth",
        "relevance": 0.9,
        "keywords": ["revenue", "growth", "sales"]
      },
      {
        "theme": "AI Competition",
        "relevance": 0.7,
        "keywords": ["AI research", "competing", "enterprise AI"]
      }
    ],
    "summary": "Apple reported strong quarterly results with 2% revenue growth driven by iPhone 15 and services, while announcing strategic AI investments to compete with tech giants.",
    "classification": {
      "primary": "Business/Finance",
      "secondary": ["Technology", "Artificial Intelligence"],
      "confidence": 0.91
    }
  },
  "metadata": {
    "words": 72,
    "sentences": 3,
    "language": "en",
    "readability_score": 12.5
  }
}
```

### Analysis Types

#### Entity Extraction
```json
{
  "analysis_type": "entities",
  "options": {
    "entity_types": ["PERSON", "ORGANIZATION", "LOCATION", "DATE", "MONEY"],
    "include_metadata": true
  }
}
```

#### Sentiment Analysis
```json
{
  "analysis_type": "sentiment",
  "options": {
    "granularity": "sentence",  // Options: document, sentence, aspect
    "aspects": ["product", "service", "price", "customer_service"]
  }
}
```

#### Topic Modeling
```json
{
  "analysis_type": "topics",
  "options": {
    "num_topics": 5,
    "include_keywords": true,
    "min_topic_probability": 0.1
  }
}
```

## 🧹 Markdown Cleaning

### POST `/api/v2/clean`

Clean and optimize markdown content using AI.

#### Request

```json
{
  "content": "# Welcome!!!!! 🎉🎉🎉\n\n\nThis is    a poorly formatted document...\n\n\n\n## Click here!! ➡️➡️ [LINK](http://example.com)\n\n* item one\n+ item two\n- item three\n\nVisit our website at http://example.com or https://example.com!!!",
  "llm_provider": "openai",
  "llm_token": "sk-...",
  "options": {
    "remove_emojis": true,
    "fix_formatting": true,
    "standardize_links": true,
    "remove_excessive_punctuation": true,
    "preserve_meaning": true
  }
}
```

#### Response

```json
{
  "success": true,
  "cleaned_content": "# Welcome\n\nThis is a poorly formatted document.\n\n## Link\n\n[Visit our website](http://example.com)\n\n- item one\n- item two\n- item three\n\nVisit our website at [example.com](http://example.com).",
  "changes_made": [
    "Removed excessive exclamation marks",
    "Removed emojis",
    "Normalized whitespace",
    "Standardized list markers",
    "Converted URLs to markdown links",
    "Fixed heading capitalization"
  ],
  "statistics": {
    "original_length": 198,
    "cleaned_length": 147,
    "reduction_percent": 25.8
  }
}
```

### Cleaning Options

```json
{
  "options": {
    // Formatting
    "fix_formatting": true,
    "normalize_whitespace": true,
    "fix_line_breaks": true,
    
    // Content
    "remove_emojis": false,
    "remove_excessive_punctuation": true,
    "fix_capitalization": true,
    
    // Links
    "standardize_links": true,
    "remove_broken_links": false,
    "convert_to_markdown_links": true,
    
    // Structure
    "fix_heading_hierarchy": true,
    "standardize_lists": true,
    "format_code_blocks": true,
    
    // Preservation
    "preserve_meaning": true,
    "preserve_code": true,
    "preserve_quotes": true
  }
}
```

## 📝 Content Summarization

### POST `/api/v2/summarize`

Create intelligent summaries in various styles and lengths.

#### Request

```json
{
  "content": "Long article about quantum computing breakthroughs...",
  "summary_type": "executive",
  "summary_length": "medium",
  "llm_provider": "anthropic",
  "llm_token": "sk-ant-...",
  "options": {
    "preserve_key_points": true,
    "include_quotes": false,
    "style": "professional"
  }
}
```

#### Response

```json
{
  "success": true,
  "summary": "Researchers at MIT have achieved a significant breakthrough in quantum error correction, reducing error rates by 90% through a novel qubit design. This advancement brings practical quantum computing applications in cryptography and drug discovery closer to reality, with commercial deployment expected within 5 years.",
  "metadata": {
    "original_words": 2456,
    "summary_words": 52,
    "compression_ratio": 47.2,
    "key_points": [
      "90% reduction in quantum error rates",
      "Novel qubit design from MIT",
      "Applications in cryptography and drug discovery",
      "Commercial deployment within 5 years"
    ],
    "readability_score": 14.2
  }
}
```

### Summary Types

#### Executive Summary
```json
{
  "summary_type": "executive",
  "options": {
    "focus": ["business_impact", "key_decisions", "recommendations"],
    "tone": "formal"
  }
}
```

#### Technical Summary
```json
{
  "summary_type": "technical",
  "options": {
    "preserve_technical_terms": true,
    "include_specifications": true,
    "detail_level": "high"
  }
}
```

#### Bullet Points
```json
{
  "summary_type": "bullets",
  "options": {
    "max_bullets": 7,
    "style": "concise",
    "prioritize": "importance"
  }
}
```

#### Abstract
```json
{
  "summary_type": "abstract",
  "options": {
    "structure": ["objective", "methods", "results", "conclusion"],
    "max_words": 250
  }
}
```

### Summary Lengths

- **`brief`** - 1-2 sentences (20-50 words)
- **`short`** - 1 paragraph (50-100 words)
- **`medium`** - 2-3 paragraphs (100-250 words)
- **`long`** - 4-5 paragraphs (250-500 words)
- **`detailed`** - Comprehensive summary (500+ words)

## 🔍 Structured Data Extraction

### POST `/api/v2/extract`

Extract structured data from content using AI with schema validation.

#### Request

```json
{
  "content": "Product Review: The new iPhone 15 Pro Max is priced at $1,199 and features a titanium design. Battery life improved by 25% compared to the previous model. Available in 4 colors: Natural Titanium, Blue Titanium, White Titanium, and Black Titanium. The A17 Pro chip provides 20% better performance.",
  "schema": {
    "type": "object",
    "properties": {
      "product_name": {"type": "string"},
      "price": {"type": "number"},
      "currency": {"type": "string"},
      "features": {
        "type": "array",
        "items": {"type": "string"}
      },
      "improvements": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "aspect": {"type": "string"},
            "improvement": {"type": "string"},
            "percentage": {"type": "number"}
          }
        }
      },
      "colors": {
        "type": "array",
        "items": {"type": "string"}
      }
    }
  },
  "llm_provider": "openai",
  "llm_token": "sk-..."
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "product_name": "iPhone 15 Pro Max",
    "price": 1199,
    "currency": "USD",
    "features": [
      "Titanium design",
      "A17 Pro chip"
    ],
    "improvements": [
      {
        "aspect": "Battery life",
        "improvement": "increase",
        "percentage": 25
      },
      {
        "aspect": "Performance",
        "improvement": "better",
        "percentage": 20
      }
    ],
    "colors": [
      "Natural Titanium",
      "Blue Titanium",
      "White Titanium",
      "Black Titanium"
    ]
  },
  "confidence": 0.95,
  "extraction_method": "schema_based"
}
```

### Common Extraction Schemas

#### Contact Information
```json
{
  "schema": {
    "type": "object",
    "properties": {
      "name": {"type": "string"},
      "email": {"type": "string", "format": "email"},
      "phone": {"type": "string"},
      "address": {
        "type": "object",
        "properties": {
          "street": {"type": "string"},
          "city": {"type": "string"},
          "state": {"type": "string"},
          "zip": {"type": "string"}
        }
      }
    }
  }
}
```

#### Event Details
```json
{
  "schema": {
    "type": "object",
    "properties": {
      "event_name": {"type": "string"},
      "date": {"type": "string", "format": "date"},
      "time": {"type": "string", "format": "time"},
      "location": {"type": "string"},
      "description": {"type": "string"},
      "speakers": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "name": {"type": "string"},
            "title": {"type": "string"},
            "topic": {"type": "string"}
          }
        }
      }
    }
  }
}
```

## 🌍 Multi-Language Support

All content processing endpoints support multiple languages:

```json
{
  "content": "Texto en español para analizar...",
  "options": {
    "language": "es",  // ISO 639-1 code
    "output_language": "en"  // Translate results to English
  }
}
```

Supported languages:
- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- Chinese (zh)
- Japanese (ja)
- Korean (ko)
- Russian (ru)

## 🔧 Provider Configuration

### Anthropic (Claude)
```json
{
  "llm_provider": "anthropic",
  "llm_token": "sk-ant-...",
  "options": {
    "model": "claude-3-opus-20240229",
    "temperature": 0.3,
    "max_tokens": 4096
  }
}
```

### OpenAI (GPT)
```json
{
  "llm_provider": "openai",
  "llm_token": "sk-...",
  "options": {
    "model": "gpt-4-turbo-preview",
    "temperature": 0.3,
    "top_p": 0.9
  }
}
```

### Google (Gemini)
```json
{
  "llm_provider": "gemini",
  "llm_token": "AIza...",
  "options": {
    "model": "gemini-pro",
    "temperature": 0.3,
    "safety_settings": "BLOCK_MEDIUM_AND_ABOVE"
  }
}
```

### Local Models (Ollama)
```json
{
  "llm_provider": "ollama",
  "llm_token": "optional",
  "options": {
    "model": "llama2",
    "temperature": 0.3,
    "ollama_base_url": "http://localhost:11434"
  }
}
```

## 📊 Batch Processing

Process multiple pieces of content in one request:

```json
{
  "contents": [
    {
      "id": "doc1",
      "content": "First document..."
    },
    {
      "id": "doc2", 
      "content": "Second document..."
    }
  ],
  "analysis_type": "comprehensive",
  "llm_provider": "anthropic",
  "llm_token": "sk-ant-...",
  "options": {
    "parallel_processing": true,
    "max_concurrent": 3
  }
}
```

## 💰 Cost Optimization

### Token Usage

All responses include token usage information:

```json
{
  "success": true,
  "data": {...},
  "usage": {
    "prompt_tokens": 1234,
    "completion_tokens": 567,
    "total_tokens": 1801,
    "estimated_cost": 0.054  // in USD
  }
}
```

### Optimization Tips

1. **Cache Results** - Reuse analysis for identical content
2. **Batch Requests** - Process multiple items together
3. **Choose Appropriate Models** - Use smaller models for simple tasks
4. **Limit Output Length** - Set max_tokens appropriately
5. **Use Streaming** - For large responses, enable streaming

## 🚨 Error Handling

### Common Errors

```json
{
  "success": false,
  "error": {
    "code": "LLM_RATE_LIMIT",
    "message": "Rate limit exceeded for provider",
    "details": {
      "provider": "openai",
      "reset_in_seconds": 45,
      "suggestion": "Wait before retrying or use a different provider"
    }
  }
}
```

### Error Codes

- `INVALID_LLM_TOKEN` - Authentication failed
- `LLM_RATE_LIMIT` - Provider rate limit hit  
- `CONTENT_TOO_LONG` - Content exceeds limits
- `INVALID_SCHEMA` - Schema validation failed
- `UNSUPPORTED_LANGUAGE` - Language not supported
- `PROVIDER_ERROR` - LLM provider error
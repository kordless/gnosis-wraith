# AI-Directed Crawl Implementation Plan

## Overview
Implement an intelligent crawling system that uses AI to dynamically decide what to crawl based on user objectives, making Wraith the first truly agentic web scraping platform.

## API Endpoints

### 1. Start AI-Directed Crawl
```
POST /v2/crawl/intelligent
```

**Request:**
```json
{
  "start_url": "https://example.com",
  "objective": "Find all technical documentation about their API, including authentication, rate limits, and code examples",
  "config": {
    "max_pages": 100,
    "max_domains": 5,
    "time_limit_minutes": 30,
    "formats": ["markdown", "structured_data"]
  },
  "ai_config": {
    "model": "gpt-4",  // optional, defaults to built-in
    "temperature": 0.3,
    "exploration_strategy": "best_first", // or "depth_first", "breadth_first"
    "decision_criteria": {
      "relevance_threshold": 0.7,
      "explore_external_domains": true,
      "generate_urls": true,
      "follow_patterns": true
    },
    "extraction_config": {
      "dynamic_schema": true,  // AI adapts schema based on findings
      "extract_on_navigate": false  // Only extract when relevant
    }
  },
  "webhook": {
    "url": "https://your-server.com/webhook",
    "events": ["decision.made", "objective.progress", "job.complete"]
  }
}
```

**Response:**
```json
{
  "job_id": "ai_crawl_abc123",
  "status": "running",
  "objective_understanding": {
    "interpreted_as": "Technical API documentation search",
    "key_targets": ["authentication", "rate limits", "code examples"],
    "estimated_pages": "10-50"
  }
}
```

### 2. Get AI Crawl Status
```
GET /v2/jobs/{job_id}
```

**Response (Running):**
```json
{
  "job_id": "ai_crawl_abc123",
  "status": "running",
  "progress": {
    "pages_analyzed": 15,
    "pages_scraped": 8,
    "pages_skipped": 7,
    "objective_completion": 0.65,
    "time_elapsed_seconds": 120
  },
  "current_focus": "Exploring /docs subdirectory",
  "ai_insights": {
    "discovered_patterns": [
      "API docs located under /developers and /docs",
      "Authentication info in /security section",
      "Code examples use .md files with ```code blocks"
    ],
    "url_patterns_found": [
      "/api/v*/",
      "/developers/*/docs",
      "/reference/*"
    ],
    "objective_alignment": {
      "authentication": 0.8,
      "rate_limits": 0.4,
      "code_examples": 0.7
    }
  },
  "data": [
    {
      "url": "https://example.com/developers/auth",
      "markdown": "# Authentication\n\n...",
      "ai_relevance_score": 0.95,
      "extracted_data": {
        "auth_methods": ["Bearer Token", "API Key"],
        "endpoints": ["/oauth/token", "/api/auth"]
      }
    }
  ],
  "decision_log": [
    {
      "timestamp": "2024-06-11T10:30:15Z",
      "url": "https://example.com/about",
      "decision": "skip",
      "reasoning": "About page unlikely to contain API documentation",
      "confidence": 0.9
    },
    {
      "timestamp": "2024-06-11T10:30:18Z", 
      "url": "https://example.com/developers",
      "decision": "explore_deeply",
      "reasoning": "Developers section highly likely to contain API docs",
      "confidence": 0.95,
      "child_urls_identified": 12
    }
  ]
}
```

**Response (Complete):**
```json
{
  "job_id": "ai_crawl_abc123", 
  "status": "done",
  "summary": {
    "objective": "Find all technical documentation about their API",
    "objective_completion": 0.92,
    "total_pages_analyzed": 45,
    "total_pages_scraped": 23,
    "domains_explored": 2,
    "duration_seconds": 300
  },
  "key_findings": {
    "authentication": {
      "found": true,
      "urls": ["https://example.com/developers/auth"],
      "methods": ["Bearer Token", "API Key", "OAuth2"]
    },
    "rate_limits": {
      "found": true,
      "urls": ["https://example.com/api/limits"],
      "limits": {"default": "1000/hour", "authenticated": "5000/hour"}
    },
    "code_examples": {
      "found": true,
      "count": 47,
      "languages": ["Python", "JavaScript", "Go", "Ruby"]
    }
  },
  "ai_generated_report": "Based on my crawl, here's what I found about their API:\n\n1. **Authentication**: They support three methods...\n2. **Rate Limits**: Default is 1000 requests/hour...\n3. **Code Examples**: Comprehensive examples in 4 languages...",
  "suggested_next_actions": [
    "Explore their GitHub repos for additional examples",
    "Check their status page for API reliability info",
    "Review their pricing page for tier-based limits"
  ],
  "data": [...all scraped pages...]
}
```

### 3. Real-time Decision Stream
```
GET /v2/jobs/{job_id}/decisions
Accept: text/event-stream
```

**Response (SSE):**
```
event: decision
data: {"url": "https://example.com/api", "action": "crawl", "reasoning": "API root likely contains overview"}

event: discovery
data: {"type": "pattern", "pattern": "/api/v{version}/{resource}", "confidence": 0.85}

event: objective_progress
data: {"completion": 0.45, "found": {"auth": true, "rate_limits": false}}

event: url_generated
data: {"url": "https://example.com/api/authentication", "reasoning": "Common API doc pattern"}
```

## Implementation Architecture

### Components

1. **AI Decision Engine**
   - Relevance scoring using embeddings
   - URL pattern recognition
   - Objective completion tracking
   - Dynamic strategy adjustment

2. **URL Generation Module**
   - Pattern-based URL synthesis
   - Common documentation path knowledge
   - Domain-specific heuristics

3. **Extraction Adapter**
   - Dynamic schema generation
   - Context-aware extraction
   - Progressive refinement

4. **Decision Logger**
   - All decisions recorded with reasoning
   - Exportable for analysis
   - Learning feedback loop

### AI Decision Flow

```python
class AIDirectedCrawler:
    async def make_crawl_decision(self, url: str, context: CrawlContext) -> Decision:
        # 1. Check if URL matches discovered patterns
        pattern_score = self.pattern_matcher.score(url)
        
        # 2. Calculate semantic relevance to objective
        relevance_score = await self.calculate_relevance(
            url, 
            context.objective,
            context.discovered_content
        )
        
        # 3. Consider crawl budget and priorities
        priority = self.prioritizer.calculate(
            url,
            context.pages_remaining,
            context.objective_completion
        )
        
        # 4. Make decision with reasoning
        if relevance_score > self.threshold:
            return Decision(
                action="crawl",
                priority=priority,
                reasoning=f"High relevance ({relevance_score:.2f}) to objective",
                extract_config=self.generate_extraction_schema(url, context)
            )
        else:
            return Decision(
                action="skip",
                reasoning=f"Low relevance ({relevance_score:.2f}) to objective"
            )
    
    async def generate_urls(self, context: CrawlContext) -> List[str]:
        # Use patterns and AI to hypothesize new URLs
        prompts = self.build_url_generation_prompt(context)
        suggested_urls = await self.llm.generate(prompts)
        return self.validate_urls(suggested_urls)
```

### Objective Completion Scoring

```python
class ObjectiveScorer:
    def calculate_completion(self, objective: str, findings: dict) -> float:
        # Break down objective into components
        components = self.parse_objective(objective)
        
        # Score each component
        scores = {}
        for component in components:
            scores[component] = self.score_component(
                component,
                findings.get(component, {})
            )
        
        # Weighted average based on importance
        return self.weighted_average(scores)
```

## Database Schema

```sql
-- AI Crawl Jobs
CREATE TABLE ai_crawl_jobs (
    id UUID PRIMARY KEY,
    objective TEXT NOT NULL,
    start_url TEXT NOT NULL,
    config JSONB NOT NULL,
    ai_config JSONB NOT NULL,
    status VARCHAR(20) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    objective_completion FLOAT,
    ai_summary TEXT
);

-- Decision Log
CREATE TABLE crawl_decisions (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES ai_crawl_jobs(id),
    url TEXT NOT NULL,
    decision VARCHAR(20) NOT NULL,
    reasoning TEXT NOT NULL,
    confidence FLOAT NOT NULL,
    relevance_score FLOAT,
    created_at TIMESTAMP NOT NULL
);

-- Pattern Discovery
CREATE TABLE discovered_patterns (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES ai_crawl_jobs(id),
    pattern TEXT NOT NULL,
    pattern_type VARCHAR(50),
    confidence FLOAT,
    example_urls TEXT[]
);
```

## Python SDK Integration

```python
# Simple API
result = client.crawl_intelligent(
    "https://example.com",
    objective="Find all pricing information including enterprise plans"
)

# Advanced with callbacks
async def on_decision(decision):
    print(f"AI decided to {decision.action} {decision.url}: {decision.reasoning}")

async def on_discovery(discovery):
    print(f"AI discovered: {discovery.insight}")

result = await client.crawl_intelligent(
    "https://example.com",
    objective="Research their machine learning capabilities",
    config={
        "max_pages": 200,
        "exploration_strategy": "best_first"
    },
    callbacks={
        "on_decision": on_decision,
        "on_discovery": on_discovery
    }
)

# Access decision history
for decision in result.decision_log:
    print(f"{decision.url}: {decision.action} ({decision.confidence:.2f})")
```

## Pricing Considerations

Since this uses AI heavily:
- Base crawl cost + AI decision cost per page analyzed
- Possible tiers:
  - Basic: Simple relevance scoring
  - Pro: Full reasoning + URL generation
  - Enterprise: Custom models + learning

## Success Metrics

1. **Objective completion rate** - How well we meet user goals
2. **Efficiency ratio** - Pages scraped vs analyzed
3. **Discovery rate** - New relevant pages found via AI
4. **Time to objective** - How fast we find what users want
5. **User satisfaction** - Did AI find what human would miss?

## Competitive Advantages

1. **First true AI-directed crawler** - Not just extraction, but navigation
2. **Objective-based** - Users describe goals, not paths
3. **Transparent AI** - See exactly why decisions were made
4. **Adaptive** - Learns patterns during crawl
5. **Efficient** - Wastes no time on irrelevant content

This positions Wraith as the most intelligent web scraping platform available.
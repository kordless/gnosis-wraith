# Phase 5: Agentic System Architecture

## Overview
Transform the Gnosis ecosystem into an agentic platform where LLMs orchestrate services through APIs, creating self-evolving web services from any URL.

## Vision: "Website Xeroxing with Intelligence"
Point Gnosis at any website → It creates a smart API version that evolves beyond the original. Crawled content becomes the foundation for generated services, not just static archives.

## Core Architecture

### 1. Job System as Execution Engine (from Phase 4)
```
Phase 4 Task Queue → Agentic Execution Layer
- Storage-first pattern for all operations
- Cloud Run Jobs for scalable processing
- Job chaining for complex workflows
- Progress tracking and fault tolerance
```

### 2. MCP Tools → API Pattern
```
Current (Local MCP):
- file_diff_write(file_path="local/file.py", diff_text="...")
- Direct filesystem access

Future (API-based):
- wraith_api.crawl(url="https://example.com")
- forge_api.transform(image_url="...", operations=["resize:800x600"])
- alaya_api.store(domain="example_com", content=processed_data)
```

### 3. Forge as Synthetic API Factory
```
forge.nuts.services/
├── forge/api/              # Meta-API for creating new APIs
│   ├── create              # Generate new API from description
│   ├── evolve              # Modify existing API
│   └── deploy              # Deploy to subdomain
├── [generated-service]/    # Auto-generated services
│   ├── index.html         # UI artifact
│   └── api/               # Generated endpoints
│       ├── search         # Search crawled docs
│       ├── data           # Serve processed content
│       └── sync           # Refresh from source
```

## Implementation Components

### 1. Agentic Coordinator
```python
# core/agent_coordinator.py
class AgentCoordinator:
    def __init__(self):
        self.job_runner = JobRunner()
        self.llm_client = LLMClient()
        self.service_registry = ServiceRegistry()
    
    async def process_intent(self, user_request: str):
        # LLM determines required services
        plan = await self.llm_client.create_plan(user_request)
        
        # Execute plan using job system
        for step in plan.steps:
            job_id = await self.job_runner.trigger(step)
            await self.monitor_job(job_id)
    
    async def create_service_from_url(self, url: str):
        # Crawl → Analyze → Synthesize → Deploy
        crawl_job = await self.trigger_crawl(url)
        analysis = await self.analyze_content(crawl_job.result)
        api_code = await self.generate_api(analysis)
        service_url = await self.deploy_service(api_code)
        return service_url
```

### 2. Service Evolution Engine
```python
# core/service_evolution.py
class ServiceEvolution:
    async def evolve_service(self, service_id: str, feedback: dict):
        # Load current service definition
        service = await self.load_service(service_id)
        
        # Generate improvements
        improvements = await self.llm_client.suggest_improvements(
            service.code,
            feedback
        )
        
        # Apply changes through Forge
        updated_code = await forge_api.transform_code(
            service.code,
            improvements
        )
        
        # Deploy new version
        await self.deploy_version(service_id, updated_code)
```

### 3. Dynamic Endpoint Generation
```python
# forge/endpoint_generator.py
class EndpointGenerator:
    def generate_from_content(self, crawled_data: dict) -> dict:
        """Generate API endpoints based on crawled content structure"""
        
        endpoints = {}
        
        # Analyze content patterns
        if self.has_search_functionality(crawled_data):
            endpoints['/search'] = self.generate_search_endpoint()
        
        if self.has_dynamic_data(crawled_data):
            endpoints['/refresh'] = self.generate_refresh_endpoint()
            
        if self.has_forms(crawled_data):
            endpoints['/submit'] = self.generate_form_handler()
        
        return endpoints
```

## Service Lifecycle

### 1. Creation Flow
```
User: "Create an API from https://analytics-dashboard.com"
         ↓
1. Wraith crawls site, captures structure and content
2. Agent analyzes: dashboards, charts, data sources
3. Forge generates: 
   - /api/metrics - serves extracted metrics
   - /api/charts - generates chart data
   - /api/refresh - re-crawls for updates
4. Deploy to: forge.nuts.services/analytics-dashboard/
5. Evolution begins: monitors usage, adapts endpoints
```

### 2. Evolution Examples
```
Original Site: Static documentation
Generated API v1: Basic search endpoint
Generated API v2: Adds categorization from usage patterns
Generated API v3: Adds related content suggestions
Generated API v4: Adds version comparison features
```

## Integration with Existing Phases

### Phase 4 Task Queue Integration
- Each service operation becomes a job
- Complex workflows use job chaining
- Background evolution runs as scheduled jobs

### Storage Architecture (Alaya)
```
storage/
├── services/
│   ├── [service_id]/
│   │   ├── definition.json    # Service configuration
│   │   ├── code/             # Generated API code
│   │   ├── content/          # Crawled/processed data
│   │   └── evolution/        # Version history
```

### MCP Tool Migration
```python
# Current MCP tool
@mcp.tool()
def crawl_website(url: str):
    # Direct crawl
    return crawler.crawl(url)

# Future API-based MCP tool
@mcp.tool()
def crawl_website(url: str):
    # API call
    return wraith_api.crawl(url)
```

## Code Synthesis Integration

### 1. MCP Tool Generation
```python
async def generate_mcp_tool(service_url: str):
    # Analyze service API
    api_spec = await fetch_api_spec(service_url)
    
    # Generate MCP tool code
    tool_code = await llm_client.generate_code(
        template="mcp_tool",
        api_spec=api_spec
    )
    
    # Deploy to Claude Desktop
    await deploy_mcp_tool(tool_code)
```

### 2. UI Artifact → Backend Service
```python
async def artifact_to_service(artifact_code: str):
    # Extract API requirements from UI code
    requirements = analyze_ui_requirements(artifact_code)
    
    # Generate matching backend
    backend_code = await generate_backend(requirements)
    
    # Deploy together
    service_url = await deploy_full_service(
        frontend=artifact_code,
        backend=backend_code
    )
```

## Example: Complete Service Generation

### Input
```
User: "Create a service that monitors Hacker News for AI topics"
```

### Process
```python
# 1. Agent creates plan
plan = {
    "steps": [
        {"action": "crawl", "url": "https://news.ycombinator.com"},
        {"action": "analyze", "focus": "AI-related content"},
        {"action": "generate_api", "endpoints": ["search", "trending", "alerts"]},
        {"action": "generate_ui", "type": "dashboard"},
        {"action": "deploy", "subdomain": "hn-ai-monitor"}
    ]
}

# 2. Execute through job system
jobs = []
for step in plan.steps:
    job = await job_runner.trigger_job(step)
    jobs.append(job)
    await job.wait_complete()

# 3. Result: Live service
service_url = "https://forge.nuts.services/hn-ai-monitor/"
api_url = "https://forge.nuts.services/hn-ai-monitor/api/"
```

### Generated Service
```
forge.nuts.services/hn-ai-monitor/
├── index.html              # React dashboard showing AI topics
├── api/
│   ├── trending           # GET - trending AI topics
│   ├── search            # POST - search HN for AI content
│   ├── alerts            # WebSocket - real-time AI post alerts
│   └── refresh           # POST - trigger fresh crawl
```

## Migration Path

### Step 1: API Wrappers for Existing Tools
- Wrap current functionality in REST APIs
- Maintain backward compatibility
- Test with simple use cases

### Step 2: LLM Orchestration Layer
- Build agent coordinator
- Create planning capabilities
- Test with controlled workflows

### Step 3: Service Generation
- Implement basic endpoint generation
- Test with simple sites
- Iterate on quality

### Step 4: Evolution Engine
- Add feedback collection
- Implement improvement generation
- Deploy incremental updates

## Success Metrics

1. **Service Generation Speed**: < 5 minutes from URL to live API
2. **API Quality**: Generated endpoints work 90%+ of the time
3. **Evolution Effectiveness**: Services improve with usage
4. **Developer Adoption**: MCP tools prefer APIs over local access

## Future Enhancements

1. **Multi-Agent Collaboration**: Multiple LLMs working on different aspects
2. **Cross-Service Integration**: Services discovering and using each other
3. **Semantic Service Mesh**: Services understanding their relationships
4. **Autonomous Improvement**: Services evolving without human intervention

## Next Steps

1. [ ] Build API wrappers for Wraith, Forge, and Alaya
2. [ ] Create agent coordinator with basic planning
3. [ ] Implement simple service generation from URL
4. [ ] Add evolution tracking and improvement system
5. [ ] Deploy first auto-generated service as proof of concept
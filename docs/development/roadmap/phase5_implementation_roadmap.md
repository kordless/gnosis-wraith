# Phase 5 Implementation Roadmap: Agentic System

## Quick Reference Architecture
```
User Request → Agent Coordinator → Job Queue → Service APIs → Results
                      ↓
                 LLM Planning
                      ↓
              [Wraith, Forge, Alaya]
```

## Stage 1: API Wrapper Layer (Week 1-2)

### 1.1 Wraith API Wrapper
```python
# web/routes/wraith_api.py
from quart import Blueprint, request, jsonify
from core.job_runner import job_runner

wraith_api = Blueprint('wraith_api', __name__, url_prefix='/api/v1/wraith')

@wraith_api.route('/crawl', methods=['POST'])
async def crawl_endpoint():
    """Public API endpoint for crawling"""
    data = await request.json
    
    # Create job instead of direct crawl
    job_id = await job_runner.trigger_job({
        "type": "crawl",
        "params": {
            "url": data.get('url'),
            "screenshot": data.get('screenshot', 'top'),
            "markdown": data.get('markdown', 'enhanced')
        }
    })
    
    return jsonify({
        "job_id": job_id,
        "status_url": f"/api/v1/jobs/{job_id}",
        "estimated_time": "10-30 seconds"
    })
```

### 1.2 Forge API Wrapper
```python
# web/routes/forge_api.py
@forge_api.route('/transform', methods=['POST'])
async def transform_endpoint():
    """Transform media through Forge FFmpeg container"""
    data = await request.json
    
    job_id = await job_runner.trigger_job({
        "type": "forge_transform",
        "params": {
            "input_url": data.get('input_url'),
            "operations": data.get('operations', []),
            "output_format": data.get('format', 'png')
        }
    })
    
    return jsonify({"job_id": job_id})
```

### 1.3 Alaya Storage API
```python
# web/routes/alaya_api.py
@alaya_api.route('/store', methods=['POST'])
async def store_endpoint():
    """Store content in Alaya with organization"""
    data = await request.json
    
    result = await storage_service.store({
        "domain": data.get('domain'),
        "content_type": data.get('type'),
        "content": data.get('content'),
        "metadata": data.get('metadata', {})
    })
    
    return jsonify(result)
```

## Stage 2: Agent Coordinator (Week 3-4)

### 2.1 Basic Coordinator
```python
# core/agent/coordinator.py
class AgentCoordinator:
    def __init__(self):
        self.planner = TaskPlanner()
        self.executor = TaskExecutor()
        self.monitor = TaskMonitor()
    
    async def handle_request(self, user_input: str) -> dict:
        # 1. Parse intent
        intent = await self.parse_intent(user_input)
        
        # 2. Create execution plan
        plan = await self.planner.create_plan(intent)
        
        # 3. Execute plan
        results = []
        for task in plan.tasks:
            result = await self.executor.execute(task)
            results.append(result)
            
        return {"plan": plan, "results": results}
```

### 2.2 LLM Integration
```python
# core/agent/llm_planner.py
class LLMPlanner:
    async def create_plan(self, user_input: str) -> ExecutionPlan:
        prompt = f"""
        User request: {user_input}
        
        Available services:
        - wraith: Web crawling and screenshot capture
        - forge: Media transformation and processing
        - alaya: Content storage and retrieval
        
        Create an execution plan using these services.
        Return as JSON with steps array.
        """
        
        response = await self.llm_client.complete(prompt)
        return ExecutionPlan.from_json(response)
```

## Stage 3: Service Generation MVP (Week 5-6)

### 3.1 Simple Service Generator
```python
# forge/generators/api_generator.py
class APIGenerator:
    async def generate_from_crawl(self, crawl_data: dict) -> str:
        """Generate API code from crawled content"""
        
        # Analyze content structure
        analysis = self.analyze_content(crawl_data)
        
        # Generate endpoint code
        code = await self.llm_client.generate_code(
            template="fastapi_service",
            endpoints=analysis.suggested_endpoints,
            data_structure=analysis.data_structure
        )
        
        return code
```

### 3.2 Service Deployment
```python
# forge/deployer.py
class ServiceDeployer:
    async def deploy_service(self, service_code: str, config: dict):
        # 1. Create service directory
        service_path = self.create_service_directory(config['name'])
        
        # 2. Write service files
        self.write_service_files(service_path, service_code)
        
        # 3. Create Dockerfile
        self.create_dockerfile(service_path)
        
        # 4. Deploy to Cloud Run
        service_url = await self.deploy_to_cloud_run(service_path)
        
        return service_url
```

## Stage 4: Evolution System (Week 7-8)

### 4.1 Feedback Collection
```python
# core/evolution/feedback.py
class FeedbackCollector:
    async def collect_metrics(self, service_id: str):
        return {
            "usage_count": await self.get_usage_count(service_id),
            "error_rate": await self.get_error_rate(service_id),
            "response_times": await self.get_response_times(service_id),
            "user_feedback": await self.get_user_feedback(service_id)
        }
```

### 4.2 Evolution Engine
```python
# core/evolution/engine.py
class EvolutionEngine:
    async def evolve_service(self, service_id: str):
        # 1. Collect feedback
        feedback = await self.feedback_collector.collect(service_id)
        
        # 2. Analyze improvements needed
        improvements = await self.analyze_improvements(feedback)
        
        # 3. Generate updated code
        new_code = await self.generate_improvements(
            current_code=await self.load_service_code(service_id),
            improvements=improvements
        )
        
        # 4. Deploy new version
        await self.deploy_version(service_id, new_code)
```

## Concrete First Implementation: URL Monitor Service

### Step 1: Create the crawler job
```bash
curl -X POST http://localhost:5678/api/v1/agent/create-service \
  -H "Content-Type: application/json" \
  -d '{
    "request": "Monitor https://news.ycombinator.com for AI posts",
    "type": "monitor"
  }'
```

### Step 2: Agent creates plan
```json
{
  "plan": {
    "tasks": [
      {"service": "wraith", "action": "crawl", "params": {"url": "https://news.ycombinator.com"}},
      {"service": "agent", "action": "analyze_content", "params": {"focus": "AI-related"}},
      {"service": "forge", "action": "generate_api", "params": {"endpoints": ["trending", "search"]}},
      {"service": "forge", "action": "deploy", "params": {"name": "hn-ai-monitor"}}
    ]
  }
}
```

### Step 3: Generated service structure
```
services/hn-ai-monitor/
├── app.py              # FastAPI application
├── requirements.txt    # Dependencies
├── Dockerfile         # Container config
├── data/
│   └── crawled/       # Stored HN data
└── config.json        # Service metadata
```

### Step 4: Generated API code (simplified)
```python
# services/hn-ai-monitor/app.py
from fastapi import FastAPI
from datetime import datetime

app = FastAPI(title="HN AI Monitor")

@app.get("/api/trending")
async def get_trending_ai_posts():
    """Return trending AI-related posts"""
    # Implementation generated by LLM
    pass

@app.get("/api/search")
async def search_ai_posts(query: str):
    """Search for AI-related posts"""
    # Implementation generated by LLM
    pass

@app.post("/api/refresh")
async def refresh_data():
    """Trigger fresh crawl of HN"""
    # Calls back to Wraith API
    pass
```

## Testing Strategy

### 1. Unit Tests for Each Component
```python
# tests/test_agent_coordinator.py
async def test_simple_crawl_request():
    coordinator = AgentCoordinator()
    result = await coordinator.handle_request("crawl https://example.com")
    assert result['plan']['tasks'][0]['service'] == 'wraith'
```

### 2. Integration Tests
```python
# tests/test_service_generation.py
async def test_generate_simple_api():
    # Crawl a site
    crawl_data = await wraith_api.crawl("https://example.com")
    
    # Generate API
    api_code = await api_generator.generate_from_crawl(crawl_data)
    
    # Verify code structure
    assert "FastAPI" in api_code
    assert "@app.get" in api_code
```

### 3. End-to-End Tests
```python
# tests/test_full_flow.py
async def test_create_service_from_url():
    # Request service creation
    response = await agent_api.create_service(
        "Create API for https://example.com"
    )
    
    # Wait for completion
    service_url = await wait_for_service(response['job_id'])
    
    # Test the generated service
    api_response = await requests.get(f"{service_url}/api/test")
    assert api_response.status_code == 200
```

## Configuration & Environment

### Required Environment Variables
```bash
# .env
GOOGLE_CLOUD_PROJECT=gnosis-wraith
CLOUD_RUN_REGION=us-central1
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-opus-20240229
STORAGE_BUCKET=gnosis-wraith-storage
JOB_QUEUE_TOPIC=wraith-jobs
```

### Docker Compose for Local Development
```yaml
# docker-compose.yml
version: '3.8'
services:
  wraith:
    build: .
    ports:
      - "5678:5678"
    environment:
      - ENVIRONMENT=development
      
  forge-ffmpeg:
    image: gnosis-forge-ffmpeg
    ports:
      - "6789:8000"
      
  agent-coordinator:
    build: ./agent
    ports:
      - "5679:5679"
    depends_on:
      - wraith
      - forge-ffmpeg
```

## Monitoring & Observability

### 1. Service Health Endpoints
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "wraith": await check_wraith_health(),
            "forge": await check_forge_health(),
            "alaya": await check_alaya_health()
        }
    }
```

### 2. Metrics Collection
```python
# core/metrics.py
class MetricsCollector:
    def track_service_creation(self, service_id: str, duration: float):
        self.metrics.record("service.created", {
            "service_id": service_id,
            "duration_seconds": duration
        })
```

## Next Immediate Actions

1. **This Week**: 
   - [ ] Create `/api/v1/wraith/crawl` endpoint
   - [ ] Update MCP wraith_crawler tool to use API
   - [ ] Test with simple crawl → store flow

2. **Next Week**:
   - [ ] Build basic agent coordinator
   - [ ] Create LLM planning prompt
   - [ ] Test plan generation for simple requests

3. **Week 3**:
   - [ ] Generate first simple API from crawled content
   - [ ] Deploy to local Docker
   - [ ] Create monitoring dashboard

This roadmap provides concrete steps to transform the Phase 4 job queue into the Phase 5 agentic system, with clear milestones and testable outcomes.
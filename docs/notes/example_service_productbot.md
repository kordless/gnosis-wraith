# ProductBot.ai - B2B Product Intelligence API Service

## Overview
A B2B API service that analyzes companies' products and provides revenue optimization recommendations by combining:
- Customer's product/company URL analysis
- Insights from 50+ pre-indexed product research sites
- Company signals and market intelligence
- Custom collections for industry-specific analysis

## Architecture

### 1. Core API Design
```
productbot.ai/
├── /api/v1/
│   ├── /analyze                 # Main analysis endpoint
│   ├── /collections             # Manage custom collections
│   ├── /reports                 # Access generated reports
│   ├── /signals                 # Company signals API
│   └── /index                   # Access to pre-crawled data
├── /prototype/                   # Forge UI for testing
└── /docs/                       # API documentation
```

### 2. Main Analysis Workflow

```python
# api/v1/analyze.py
from fastapi import FastAPI, APIKey, BackgroundTasks
from core.agent import ProductAnalysisAgent

app = FastAPI(title="ProductBot.ai API")
agent = ProductAnalysisAgent()

@app.post("/api/v1/analyze")
async def analyze_product(
    request: AnalysisRequest,
    api_key: str = Depends(verify_api_key),
    background_tasks: BackgroundTasks
):
    """
    Main endpoint - accepts customer URL and returns product recommendations
    """
    # 1. Validate API key and check rate limits
    customer = await get_customer_by_api_key(api_key)
    await check_rate_limit(customer.id)
    
    # 2. Create analysis job
    job = await create_analysis_job({
        "customer_id": customer.id,
        "target_url": request.product_url,
        "collections": request.collections or ["default"],
        "analysis_depth": request.depth or "standard",
        "include_competitors": request.include_competitors,
        "market_segment": request.market_segment
    })
    
    # 3. Execute analysis in background
    background_tasks.add_task(
        execute_product_analysis,
        job_id=job.id,
        customer=customer
    )
    
    # 4. Return job info for polling
    return {
        "job_id": job.id,
        "status_url": f"/api/v1/reports/{job.id}/status",
        "estimated_time": "2-5 minutes",
        "webhook_url": request.webhook_url  # Optional callback
    }

async def execute_product_analysis(job_id: str, customer: Customer):
    """Background task that orchestrates the analysis"""
    
    # 1. Crawl customer's product page
    customer_data = await agent.crawl_customer_product(job.target_url)
    
    # 2. Extract product features and positioning
    product_profile = await agent.analyze_product_profile(customer_data)
    
    # 3. Search pre-indexed knowledge base
    market_insights = await agent.search_product_intelligence({
        "product_type": product_profile.category,
        "features": product_profile.features,
        "price_range": product_profile.pricing,
        "collections": job.collections
    })
    
    # 4. Analyze competitor landscape
    if job.include_competitors:
        competitors = await agent.analyze_competitors(product_profile)
    
    # 5. Generate recommendations
    recommendations = await agent.generate_recommendations({
        "product": product_profile,
        "market": market_insights,
        "competitors": competitors,
        "customer_signals": await get_company_signals(customer_data.company)
    })
    
    # 6. Create report
    report = await create_report({
        "job_id": job_id,
        "recommendations": recommendations,
        "confidence_scores": recommendations.confidence,
        "data_sources": recommendations.sources
    })
    
    # 7. Notify customer
    if job.webhook_url:
        await notify_webhook(job.webhook_url, report)
```

### 3. Collections Management API

```python
@app.post("/api/v1/collections")
async def create_collection(
    request: CreateCollectionRequest,
    api_key: str = Depends(verify_api_key)
):
    """Create custom collection of product research sources"""
    
    collection = await create_customer_collection({
        "name": request.name,
        "description": request.description,
        "sources": request.sources,  # URLs to crawl/monitor
        "keywords": request.keywords,
        "update_frequency": request.update_frequency or "weekly"
    })
    
    # Trigger initial crawl of collection sources
    await agent.index_collection(collection.id)
    
    return {
        "collection_id": collection.id,
        "name": collection.name,
        "source_count": len(collection.sources),
        "status": "indexing"
    }

@app.get("/api/v1/collections")
async def list_collections(api_key: str = Depends(verify_api_key)):
    """List customer's collections"""
    customer = await get_customer_by_api_key(api_key)
    collections = await get_customer_collections(customer.id)
    
    return {
        "collections": [
            {
                "id": c.id,
                "name": c.name,
                "source_count": len(c.sources),
                "last_updated": c.last_updated,
                "document_count": c.document_count
            }
            for c in collections
        ]
    }

@app.put("/api/v1/collections/{collection_id}/sources")
async def update_collection_sources(
    collection_id: str,
    request: UpdateSourcesRequest,
    api_key: str = Depends(verify_api_key)
):
    """Add/remove sources from a collection"""
    
    collection = await get_collection(collection_id)
    await verify_collection_ownership(collection, api_key)
    
    if request.add_sources:
        await add_sources_to_collection(collection_id, request.add_sources)
    
    if request.remove_sources:
        await remove_sources_from_collection(collection_id, request.remove_sources)
    
    # Re-index if needed
    if request.reindex:
        await agent.index_collection(collection_id)
    
    return {"status": "updated", "collection_id": collection_id}
```

### 4. Pre-Indexed Knowledge Base

```python
# core/knowledge_base.py
class ProductKnowledgeBase:
    """Manages the 50+ pre-crawled product research sites"""
    
    def __init__(self):
        self.sources = {
            # Product research sites
            "gartner": {
                "url": "https://www.gartner.com",
                "type": "analyst_reports",
                "crawl_frequency": "daily",
                "sections": ["magic_quadrant", "peer_insights", "research"]
            },
            "g2crowd": {
                "url": "https://www.g2.com",
                "type": "user_reviews",
                "crawl_frequency": "daily",
                "sections": ["reviews", "comparisons", "categories"]
            },
            "producthunt": {
                "url": "https://www.producthunt.com",
                "type": "new_products",
                "crawl_frequency": "hourly",
                "sections": ["trending", "collections", "discussions"]
            },
            "capterra": {
                "url": "https://www.capterra.com",
                "type": "software_reviews",
                "crawl_frequency": "daily"
            },
            # Industry-specific sources
            "techcrunch": {
                "url": "https://techcrunch.com",
                "type": "tech_news",
                "sections": ["startups", "venture", "products"]
            },
            # ... 45+ more sources
        }
    
    async def search(self, query: dict) -> list:
        """Search across all indexed content"""
        results = []
        
        # Use vector search for semantic matching
        embeddings = await generate_embeddings(query)
        
        # Search each source's indexed content
        for source_id, source_config in self.sources.items():
            matches = await vector_search(
                index=f"productbot_{source_id}",
                embeddings=embeddings,
                filters=query.get("filters", {})
            )
            results.extend(matches)
        
        # Rank by relevance and recency
        return self.rank_results(results, query)
```

### 5. Prototype UI in Forge

```javascript
// prototype/index.html - Built with Forge UI
const ProductBotPrototype = () => {
    const [productUrl, setProductUrl] = useState('');
    const [selectedCollections, setSelectedCollections] = useState(['default']);
    const [analysis, setAnalysis] = useState(null);
    const [collections, setCollections] = useState([]);
    
    useEffect(() => {
        // Load user's collections
        loadCollections();
    }, []);
    
    const runAnalysis = async () => {
        const response = await fetch('/api/v1/analyze', {
            method: 'POST',
            headers: {
                'X-API-Key': apiKey,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                product_url: productUrl,
                collections: selectedCollections,
                include_competitors: true,
                analysis_depth: 'comprehensive'
            })
        });
        
        const job = await response.json();
        pollForResults(job.job_id);
    };
    
    return (
        <div className="productbot-prototype">
            <h1>ProductBot.ai Prototype</h1>
            
            <div className="input-section">
                <input
                    type="url"
                    placeholder="Enter your product URL"
                    value={productUrl}
                    onChange={(e) => setProductUrl(e.target.value)}
                />
                
                <div className="collections-selector">
                    <h3>Select Knowledge Collections</h3>
                    {collections.map(collection => (
                        <label key={collection.id}>
                            <input
                                type="checkbox"
                                checked={selectedCollections.includes(collection.id)}
                                onChange={(e) => toggleCollection(collection.id)}
                            />
                            {collection.name} ({collection.document_count} sources)
                        </label>
                    ))}
                </div>
                
                <button onClick={runAnalysis}>
                    Analyze Product
                </button>
            </div>
            
            {analysis && (
                <div className="results">
                    <RevenueRecommendations data={analysis.recommendations} />
                    <CompetitorAnalysis data={analysis.competitors} />
                    <MarketInsights data={analysis.market_insights} />
                </div>
            )}
        </div>
    );
};
```

### 6. Report Generation

```python
# core/report_generator.py
class ProductReportGenerator:
    async def generate_report(self, analysis_data: dict) -> Report:
        """Generate comprehensive product strategy report"""
        
        report = {
            "executive_summary": await self.generate_summary(analysis_data),
            "revenue_opportunities": await self.identify_revenue_opportunities(analysis_data),
            "feature_recommendations": await self.recommend_features(analysis_data),
            "pricing_insights": await self.analyze_pricing(analysis_data),
            "competitive_positioning": await self.position_analysis(analysis_data),
            "implementation_roadmap": await self.create_roadmap(analysis_data),
            "confidence_metrics": self.calculate_confidence(analysis_data)
        }
        
        # Generate multiple formats
        formats = {
            "json": report,
            "pdf": await self.generate_pdf(report),
            "markdown": await self.generate_markdown(report),
            "presentation": await self.generate_slides(report)
        }
        
        return Report(
            id=generate_id(),
            data=report,
            formats=formats,
            created_at=datetime.now()
        )
```

### 7. API Response Examples

```json
// POST /api/v1/analyze response
{
    "job_id": "job_abc123",
    "status_url": "/api/v1/reports/job_abc123/status",
    "estimated_time": "2-5 minutes"
}

// GET /api/v1/reports/{job_id} response
{
    "report_id": "rpt_xyz789",
    "status": "completed",
    "product_url": "https://example.com/product",
    "recommendations": {
        "revenue_impact": {
            "potential_increase": "15-25%",
            "confidence": 0.82,
            "timeframe": "6-12 months"
        },
        "top_recommendations": [
            {
                "title": "Add usage-based pricing tier",
                "impact": "high",
                "effort": "medium",
                "rationale": "87% of successful competitors offer this",
                "examples": ["competitor_a", "competitor_b"],
                "implementation_guide": "..."
            },
            {
                "title": "Integrate with Slack and Teams",
                "impact": "high",
                "effort": "low",
                "rationale": "Missing table stakes feature",
                "market_data": "92% of enterprise customers require"
            }
        ],
        "market_insights": {
            "growth_rate": "23% YoY",
            "tam": "$2.3B",
            "competitive_landscape": "fragmented",
            "emerging_trends": ["ai_integration", "vertical_solutions"]
        }
    },
    "data_sources": [
        "50 product research sites",
        "247 competitor products analyzed",
        "1,832 user reviews processed",
        "15 analyst reports"
    ],
    "formats_available": ["json", "pdf", "markdown", "presentation"]
}
```

### 8. Pricing Model

```python
# Tiered API pricing
PRICING_TIERS = {
    "starter": {
        "monthly_price": 499,
        "analyses_per_month": 10,
        "collections": 1,
        "sources_per_collection": 10,
        "rate_limit": "10/hour"
    },
    "growth": {
        "monthly_price": 1499,
        "analyses_per_month": 50,
        "collections": 5,
        "sources_per_collection": 50,
        "rate_limit": "100/hour",
        "features": ["competitor_analysis", "custom_reports"]
    },
    "enterprise": {
        "monthly_price": "custom",
        "analyses_per_month": "unlimited",
        "collections": "unlimited",
        "sources_per_collection": "unlimited",
        "rate_limit": "custom",
        "features": ["white_label", "dedicated_crawlers", "sla"]
    }
}
```

### 9. Integration Examples

```python
# Customer integration example
import requests

class ProductBotClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://productbot.ai/api/v1"
    
    def analyze_product(self, product_url, collections=None):
        response = requests.post(
            f"{self.base_url}/analyze",
            headers={"X-API-Key": self.api_key},
            json={
                "product_url": product_url,
                "collections": collections or ["default"],
                "include_competitors": True
            }
        )
        
        job = response.json()
        return self.wait_for_report(job["job_id"])
    
    def create_collection(self, name, sources):
        """Create custom collection for industry-specific analysis"""
        response = requests.post(
            f"{self.base_url}/collections",
            headers={"X-API-Key": self.api_key},
            json={
                "name": name,
                "sources": sources,
                "update_frequency": "daily"
            }
        )
        return response.json()

# Usage
client = ProductBotClient("api_key_123")
report = client.analyze_product("https://myapp.com")
print(f"Revenue opportunity: {report['recommendations']['revenue_impact']}")
```

This shows how ProductBot.ai leverages the Phase 5 architecture to create a sophisticated B2B API service that:
- Uses Wraith for intelligent crawling
- Maintains a knowledge base of 50+ product sites
- Allows custom collections for industry-specific insights
- Provides actionable revenue recommendations
- Offers both API and prototype UI access
- Scales through the job queue system
- Evolves its recommendations based on market changes
# Real-World Examples

Practical examples demonstrating common use cases for the Gnosis Wraith API v2.

## 📰 News Aggregation

### Scraping Multiple News Sites

```python
import asyncio
import aiohttp
from datetime import datetime

async def aggregate_news(token):
    base_url = "http://localhost:5678/api/v2"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    news_sites = [
        {"url": "https://news.ycombinator.com", "selector": ".titleline"},
        {"url": "https://www.reddit.com/r/technology", "selector": ".Post"},
        {"url": "https://techcrunch.com", "selector": "article"}
    ]
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        
        for site in news_sites:
            # Extract headlines using JavaScript
            payload = {
                "url": site["url"],
                "javascript": f"""
                    const headlines = Array.from(document.querySelectorAll('{site["selector"]}')).slice(0, 10).map(el => {{
                        const link = el.querySelector('a');
                        return {{
                            title: link?.textContent?.trim(),
                            url: link?.href,
                            source: '{site["url"]}'
                        }};
                    }});
                    JSON.stringify(headlines);
                """,
                "take_screenshot": True,
                "extract_markdown": True
            }
            
            task = session.post(f"{base_url}/execute", headers=headers, json=payload)
            tasks.append(task)
        
        # Gather all results
        responses = await asyncio.gather(*tasks)
        
        all_headlines = []
        for response in responses:
            data = await response.json()
            if data["success"]:
                headlines = data["result"]
                all_headlines.extend(headlines)
        
        # Analyze trends using AI
        analysis_payload = {
            "content": "\n".join([h["title"] for h in all_headlines]),
            "analysis_type": "topics",
            "llm_provider": "anthropic",
            "llm_token": "your-anthropic-key",
            "options": {
                "num_topics": 5,
                "include_keywords": True
            }
        }
        
        async with session.post(f"{base_url}/analyze", headers=headers, json=analysis_payload) as resp:
            analysis = await resp.json()
        
        return {
            "headlines": all_headlines,
            "trending_topics": analysis["analysis"]["topics"],
            "timestamp": datetime.now().isoformat()
        }

# Usage
result = asyncio.run(aggregate_news("your-api-token"))
print(f"Found {len(result['headlines'])} headlines")
print(f"Top trend: {result['trending_topics'][0]['theme']}")
```

## 🛒 E-commerce Price Monitoring

### Track Product Prices Across Sites

```python
import requests
import json
from typing import List, Dict

class PriceMonitor:
    def __init__(self, api_token: str, base_url: str = "http://localhost:5678/api/v2"):
        self.token = api_token
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def monitor_product(self, product_urls: List[Dict[str, str]]) -> Dict:
        """Monitor prices for a product across multiple sites"""
        
        results = []
        
        for product in product_urls:
            # Generate extraction code using AI
            inject_payload = {
                "url": product["url"],
                "request": f"Extract the price, availability, and shipping info for the {product['name']}",
                "llm_provider": "openai",
                "llm_token": "your-openai-key",
                "take_screenshot": True
            }
            
            response = requests.post(
                f"{self.base_url}/inject",
                headers=self.headers,
                json=inject_payload
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    result = data["result"]
                    results.append({
                        "store": product["store"],
                        "product": product["name"],
                        "data": result,
                        "screenshot": data.get("screenshot"),
                        "timestamp": data.get("timestamp")
                    })
        
        # Analyze price differences
        if results:
            prices = [r["data"].get("price", 0) for r in results if r["data"].get("price")]
            if prices:
                analysis = {
                    "lowest_price": min(prices),
                    "highest_price": max(prices),
                    "average_price": sum(prices) / len(prices),
                    "price_range": max(prices) - min(prices),
                    "best_deal": min(results, key=lambda x: x["data"].get("price", float('inf')))
                }
                
                return {
                    "products": results,
                    "analysis": analysis
                }
        
        return {"products": results, "analysis": None}

# Usage
monitor = PriceMonitor("your-api-token")

products = [
    {
        "store": "Amazon",
        "name": "iPhone 15 Pro",
        "url": "https://www.amazon.com/dp/B0C123456"
    },
    {
        "store": "Best Buy", 
        "name": "iPhone 15 Pro",
        "url": "https://www.bestbuy.com/site/iphone-15-pro/1234567.p"
    }
]

result = monitor.monitor_product(products)
print(f"Best price: ${result['analysis']['lowest_price']} at {result['analysis']['best_deal']['store']}")
```

## 🔬 Research Paper Analysis

### Extract and Summarize Academic Content

```python
import requests
from typing import List
import time

def analyze_research_papers(paper_urls: List[str], api_token: str):
    """Extract and analyze research papers"""
    
    base_url = "http://localhost:5678/api/v2"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    papers_data = []
    
    # First, crawl all papers
    for url in paper_urls:
        # Extract paper content
        scrape_response = requests.post(
            f"{base_url}/scrape",
            headers=headers,
            json={
                "url": url,
                "formats": ["markdown", "text"],
                "options": {
                    "wait_for": 3000,
                    "include_links": True
                }
            }
        )
        
        if scrape_response.status_code == 200:
            data = scrape_response.json()
            if data["success"]:
                papers_data.append({
                    "url": url,
                    "content": data["data"]["markdown"],
                    "metadata": data["data"]["metadata"]
                })
    
    # Analyze each paper
    analyzed_papers = []
    
    for paper in papers_data:
        # Extract structured information
        extract_response = requests.post(
            f"{base_url}/extract",
            headers=headers,
            json={
                "content": paper["content"],
                "schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "authors": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "abstract": {"type": "string"},
                        "methodology": {"type": "string"},
                        "key_findings": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "citations_count": {"type": "number"},
                        "publication_date": {"type": "string"},
                        "keywords": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "llm_provider": "anthropic",
                "llm_token": "your-anthropic-key"
            }
        )
        
        if extract_response.status_code == 200:
            extract_data = extract_response.json()
            
            # Generate summary
            summary_response = requests.post(
                f"{base_url}/summarize",
                headers=headers,
                json={
                    "content": paper["content"],
                    "summary_type": "abstract",
                    "summary_length": "medium",
                    "llm_provider": "anthropic",
                    "llm_token": "your-anthropic-key",
                    "options": {
                        "style": "academic",
                        "preserve_technical_terms": True
                    }
                }
            )
            
            summary_data = summary_response.json()
            
            analyzed_papers.append({
                "url": paper["url"],
                "extracted_data": extract_data.get("data", {}),
                "summary": summary_data.get("summary", ""),
                "metadata": paper["metadata"]
            })
        
        # Rate limiting
        time.sleep(1)
    
    # Cross-paper analysis
    all_findings = []
    for paper in analyzed_papers:
        findings = paper["extracted_data"].get("key_findings", [])
        all_findings.extend(findings)
    
    if all_findings:
        # Find common themes
        theme_analysis = requests.post(
            f"{base_url}/analyze",
            headers=headers,
            json={
                "content": "\n".join(all_findings),
                "analysis_type": "topics",
                "llm_provider": "anthropic",
                "llm_token": "your-anthropic-key",
                "options": {
                    "num_topics": 5
                }
            }
        )
        
        themes = theme_analysis.json().get("analysis", {}).get("topics", [])
    else:
        themes = []
    
    return {
        "papers": analyzed_papers,
        "common_themes": themes,
        "total_papers": len(analyzed_papers)
    }

# Usage
papers = [
    "https://arxiv.org/abs/2401.12345",
    "https://arxiv.org/abs/2401.67890"
]

results = analyze_research_papers(papers, "your-api-token")
print(f"Analyzed {results['total_papers']} papers")
print(f"Common theme: {results['common_themes'][0]['theme']}")
```

## 📊 Social Media Analytics

### Monitor Brand Mentions

```python
import requests
from datetime import datetime, timedelta
import json

class SocialMediaMonitor:
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = "http://localhost:5678/api/v2"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def search_mentions(self, brand: str, platforms: List[str]) -> Dict:
        """Search for brand mentions across platforms"""
        
        mentions = []
        
        for platform in platforms:
            # Search for mentions
            search_query = f"{brand} site:{platform}.com"
            
            search_response = requests.post(
                f"{self.base_url}/search",
                headers=self.headers,
                json={
                    "query": search_query,
                    "limit": 20,
                    "scrape_options": {
                        "formats": ["markdown"],
                        "timeout": 15000
                    }
                }
            )
            
            if search_response.status_code == 200:
                results = search_response.json()
                
                # Analyze sentiment for each result
                for result in results.get("data", []):
                    sentiment_response = requests.post(
                        f"{self.base_url}/analyze",
                        headers=self.headers,
                        json={
                            "content": result["markdown"],
                            "analysis_type": "sentiment",
                            "llm_provider": "openai",
                            "llm_token": "your-openai-key",
                            "options": {
                                "aspects": ["brand_perception", "product_quality", "customer_service"]
                            }
                        }
                    )
                    
                    if sentiment_response.status_code == 200:
                        sentiment_data = sentiment_response.json()
                        
                        mentions.append({
                            "platform": platform,
                            "url": result["url"],
                            "title": result["title"],
                            "content_preview": result["markdown"][:200] + "...",
                            "sentiment": sentiment_data["analysis"]["sentiment"],
                            "timestamp": datetime.now().isoformat()
                        })
        
        # Aggregate sentiment
        sentiment_scores = [m["sentiment"]["score"] for m in mentions]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        
        positive_mentions = len([s for s in sentiment_scores if s > 0.6])
        negative_mentions = len([s for s in sentiment_scores if s < -0.6])
        neutral_mentions = len(mentions) - positive_mentions - negative_mentions
        
        return {
            "brand": brand,
            "mentions": mentions,
            "analytics": {
                "total_mentions": len(mentions),
                "average_sentiment": avg_sentiment,
                "sentiment_breakdown": {
                    "positive": positive_mentions,
                    "neutral": neutral_mentions,
                    "negative": negative_mentions
                },
                "platforms_covered": list(set(m["platform"] for m in mentions))
            }
        }
    
    def track_competitor_activity(self, competitors: List[str]) -> Dict:
        """Track competitor activities and announcements"""
        
        competitor_data = {}
        
        for competitor in competitors:
            # Check their website for updates
            scrape_response = requests.post(
                f"{self.base_url}/scrape",
                headers=self.headers,
                json={
                    "url": f"https://{competitor}.com/news",
                    "formats": ["markdown"],
                    "options": {
                        "wait_for": 3000
                    }
                }
            )
            
            if scrape_response.status_code == 200:
                content = scrape_response.json()["data"]["markdown"]
                
                # Extract recent announcements
                extract_response = requests.post(
                    f"{self.base_url}/extract",
                    headers=self.headers,
                    json={
                        "content": content,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "recent_announcements": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "title": {"type": "string"},
                                            "date": {"type": "string"},
                                            "summary": {"type": "string"},
                                            "category": {"type": "string"}
                                        }
                                    }
                                },
                                "key_metrics": {
                                    "type": "object",
                                    "properties": {
                                        "revenue": {"type": "string"},
                                        "growth": {"type": "string"},
                                        "employees": {"type": "number"}
                                    }
                                }
                            }
                        },
                        "llm_provider": "anthropic",
                        "llm_token": "your-anthropic-key"
                    }
                )
                
                if extract_response.status_code == 200:
                    competitor_data[competitor] = extract_response.json()["data"]
        
        return competitor_data

# Usage
monitor = SocialMediaMonitor("your-api-token")

# Monitor brand mentions
brand_mentions = monitor.search_mentions(
    brand="YourBrand",
    platforms=["twitter", "reddit", "linkedin"]
)

print(f"Found {brand_mentions['analytics']['total_mentions']} mentions")
print(f"Average sentiment: {brand_mentions['analytics']['average_sentiment']:.2f}")

# Track competitors
competitor_updates = monitor.track_competitor_activity(
    competitors=["competitor1", "competitor2"]
)
```

## 🏢 Company Research

### Comprehensive Company Analysis

```python
import requests
from typing import Dict, List
import json

def research_company(company_name: str, company_domain: str, api_token: str) -> Dict:
    """Perform comprehensive company research"""
    
    base_url = "http://localhost:5678/api/v2"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    research_data = {}
    
    # 1. Crawl company website
    crawl_response = requests.post(
        f"{base_url}/crawl",
        headers=headers,
        json={
            "url": f"https://{company_domain}",
            "limit": 50,
            "depth": 2,
            "formats": ["markdown"],
            "options": {
                "include_patterns": ["/about*", "/team*", "/careers*", "/products*"],
                "concurrent_requests": 3
            }
        }
    )
    
    if crawl_response.status_code == 200:
        job_id = crawl_response.json()["job_id"]
        
        # Wait for crawl to complete
        import time
        while True:
            status_response = requests.get(
                f"{base_url}/jobs/{job_id}",
                headers=headers
            )
            
            status_data = status_response.json()
            if status_data["status"] == "done":
                crawled_pages = status_data["data"]
                break
            elif status_data["status"] == "error":
                print("Crawl failed:", status_data["error"])
                break
            
            time.sleep(2)
        
        # 2. Extract company information from all pages
        all_content = "\n\n".join([page["markdown"] for page in crawled_pages])
        
        extract_response = requests.post(
            f"{base_url}/extract",
            headers=headers,
            json={
                "content": all_content[:50000],  # Limit content size
                "schema": {
                    "type": "object",
                    "properties": {
                        "company_info": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "founded": {"type": "string"},
                                "headquarters": {"type": "string"},
                                "industry": {"type": "string"},
                                "size": {"type": "string"},
                                "mission": {"type": "string"},
                                "values": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            }
                        },
                        "leadership": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "position": {"type": "string"},
                                    "bio": {"type": "string"}
                                }
                            }
                        },
                        "products_services": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "description": {"type": "string"},
                                    "category": {"type": "string"}
                                }
                            }
                        },
                        "recent_news": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "date": {"type": "string"},
                                    "summary": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "llm_provider": "anthropic",
                "llm_token": "your-anthropic-key"
            }
        )
        
        if extract_response.status_code == 200:
            research_data["company_data"] = extract_response.json()["data"]
    
    # 3. Search for recent news and mentions
    news_search = requests.post(
        f"{base_url}/search",
        headers=headers,
        json={
            "query": f'"{company_name}" news announcement',
            "limit": 10,
            "scrape_options": {
                "formats": ["markdown"],
                "timeout": 10000
            }
        }
    )
    
    if news_search.status_code == 200:
        news_results = news_search.json()["data"]
        
        # Analyze news sentiment
        news_content = "\n".join([n["markdown"] for n in news_results[:5]])
        
        sentiment_response = requests.post(
            f"{base_url}/analyze",
            headers=headers,
            json={
                "content": news_content,
                "analysis_type": "sentiment",
                "llm_provider": "openai",
                "llm_token": "your-openai-key"
            }
        )
        
        if sentiment_response.status_code == 200:
            research_data["news_sentiment"] = sentiment_response.json()["analysis"]
    
    # 4. Generate executive summary
    summary_response = requests.post(
        f"{base_url}/summarize",
        headers=headers,
        json={
            "content": json.dumps(research_data),
            "summary_type": "executive",
            "summary_length": "medium",
            "llm_provider": "anthropic",
            "llm_token": "your-anthropic-key",
            "options": {
                "focus": ["key_insights", "competitive_position", "recent_developments"],
                "style": "professional"
            }
        }
    )
    
    if summary_response.status_code == 200:
        research_data["executive_summary"] = summary_response.json()["summary"]
    
    return research_data

# Usage
company_research = research_company(
    company_name="Example Corp",
    company_domain="example.com",
    api_token="your-api-token"
)

print("Executive Summary:")
print(company_research.get("executive_summary", "No summary available"))
```

## 🎯 SEO Analysis

### Analyze Website SEO Performance

```python
import requests
from urllib.parse import urlparse

def analyze_website_seo(url: str, api_token: str) -> Dict:
    """Comprehensive SEO analysis of a website"""
    
    base_url = "http://localhost:5678/api/v2"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    domain = urlparse(url).netloc
    
    # 1. Analyze homepage
    homepage_response = requests.post(
        f"{base_url}/scrape",
        headers=headers,
        json={
            "url": url,
            "formats": ["html", "markdown", "links"],
            "options": {
                "include_metadata": True
            }
        }
    )
    
    homepage_data = homepage_response.json()["data"]
    
    # 2. Extract SEO elements using JavaScript
    seo_extract = requests.post(
        f"{base_url}/execute",
        headers=headers,
        json={
            "url": url,
            "javascript": """
                const seoData = {
                    title: document.title,
                    meta_description: document.querySelector('meta[name="description"]')?.content,
                    meta_keywords: document.querySelector('meta[name="keywords"]')?.content,
                    h1_tags: Array.from(document.querySelectorAll('h1')).map(h => h.textContent.trim()),
                    h2_tags: Array.from(document.querySelectorAll('h2')).map(h => h.textContent.trim()),
                    images: Array.from(document.querySelectorAll('img')).map(img => ({
                        src: img.src,
                        alt: img.alt,
                        title: img.title
                    })),
                    internal_links: Array.from(document.querySelectorAll('a[href^="/"], a[href*="' + window.location.hostname + '"]')).length,
                    external_links: Array.from(document.querySelectorAll('a[href^="http"]:not([href*="' + window.location.hostname + '"])')).length,
                    schema_markup: Array.from(document.querySelectorAll('script[type="application/ld+json"]')).map(s => JSON.parse(s.textContent))
                };
                JSON.stringify(seoData);
            """
        }
    )
    
    seo_elements = seo_extract.json()["result"]
    
    # 3. Analyze content quality
    content_analysis = requests.post(
        f"{base_url}/analyze",
        headers=headers,
        json={
            "content": homepage_data["markdown"],
            "analysis_type": "comprehensive",
            "llm_provider": "openai",
            "llm_token": "your-openai-key"
        }
    )
    
    # 4. Check site performance
    performance_check = requests.post(
        f"{base_url}/execute",
        headers=headers,
        json={
            "url": url,
            "javascript": """
                const perfData = performance.getEntriesByType('navigation')[0];
                JSON.stringify({
                    load_time: perfData.loadEventEnd - perfData.fetchStart,
                    dom_ready: perfData.domContentLoadedEventEnd - perfData.fetchStart,
                    first_paint: performance.getEntriesByName('first-paint')[0]?.startTime,
                    resources: performance.getEntriesByType('resource').length
                });
            """
        }
    )
    
    # 5. Generate SEO recommendations
    seo_report = {
        "url": url,
        "domain": domain,
        "seo_elements": seo_elements,
        "content_analysis": content_analysis.json()["analysis"],
        "performance": performance_check.json()["result"],
        "issues": [],
        "recommendations": []
    }
    
    # Check for common SEO issues
    if not seo_elements.get("meta_description"):
        seo_report["issues"].append("Missing meta description")
        seo_report["recommendations"].append("Add a compelling meta description under 160 characters")
    
    if len(seo_elements.get("h1_tags", [])) != 1:
        seo_report["issues"].append(f"Found {len(seo_elements.get('h1_tags', []))} H1 tags (should be exactly 1)")
    
    images_without_alt = [img for img in seo_elements.get("images", []) if not img.get("alt")]
    if images_without_alt:
        seo_report["issues"].append(f"{len(images_without_alt)} images missing alt text")
    
    # Generate AI-powered recommendations
    recommendations_response = requests.post(
        f"{base_url}/analyze",
        headers=headers,
        json={
            "content": json.dumps(seo_report),
            "analysis_type": "custom",
            "llm_provider": "anthropic",
            "llm_token": "your-anthropic-key",
            "options": {
                "prompt": "Based on this SEO analysis, provide 5 specific, actionable recommendations to improve search engine rankings."
            }
        }
    )
    
    if recommendations_response.status_code == 200:
        seo_report["ai_recommendations"] = recommendations_response.json()["analysis"]
    
    return seo_report

# Usage
seo_analysis = analyze_website_seo("https://example.com", "your-api-token")

print(f"SEO Issues Found: {len(seo_analysis['issues'])}")
for issue in seo_analysis['issues']:
    print(f"- {issue}")

print("\nRecommendations:")
for rec in seo_analysis['recommendations']:
    print(f"- {rec}")
```

## 🔄 Workflow Automation

### Multi-Step Data Pipeline

```python
import requests
from typing import List, Dict
import asyncio
import aiohttp

class DataPipeline:
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = "http://localhost:5678/api/v2"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    async def process_urls(self, urls: List[str], workflow: Dict) -> List[Dict]:
        """Process multiple URLs through a defined workflow"""
        
        async with aiohttp.ClientSession() as session:
            results = []
            
            for url in urls:
                result = {"url": url, "steps": {}}
                
                # Step 1: Scrape content
                if "scrape" in workflow:
                    async with session.post(
                        f"{self.base_url}/scrape",
                        headers=self.headers,
                        json={
                            "url": url,
                            "formats": workflow["scrape"]["formats"],
                            "options": workflow["scrape"].get("options", {})
                        }
                    ) as response:
                        data = await response.json()
                        result["steps"]["scrape"] = data["data"]
                
                # Step 2: Execute JavaScript
                if "execute" in workflow:
                    async with session.post(
                        f"{self.base_url}/execute",
                        headers=self.headers,
                        json={
                            "url": url,
                            "javascript": workflow["execute"]["code"],
                            "take_screenshot": workflow["execute"].get("screenshot", False)
                        }
                    ) as response:
                        data = await response.json()
                        result["steps"]["execute"] = data["result"]
                
                # Step 3: Clean content
                if "clean" in workflow and result["steps"].get("scrape"):
                    async with session.post(
                        f"{self.base_url}/clean",
                        headers=self.headers,
                        json={
                            "content": result["steps"]["scrape"]["markdown"],
                            "llm_provider": workflow["clean"]["provider"],
                            "llm_token": workflow["clean"]["token"],
                            "options": workflow["clean"].get("options", {})
                        }
                    ) as response:
                        data = await response.json()
                        result["steps"]["clean"] = data["cleaned_content"]
                
                # Step 4: Extract structured data
                if "extract" in workflow:
                    content = result["steps"].get("clean", result["steps"].get("scrape", {}).get("markdown", ""))
                    async with session.post(
                        f"{self.base_url}/extract",
                        headers=self.headers,
                        json={
                            "content": content,
                            "schema": workflow["extract"]["schema"],
                            "llm_provider": workflow["extract"]["provider"],
                            "llm_token": workflow["extract"]["token"]
                        }
                    ) as response:
                        data = await response.json()
                        result["steps"]["extract"] = data["data"]
                
                # Step 5: Analyze
                if "analyze" in workflow:
                    content = result["steps"].get("clean", result["steps"].get("scrape", {}).get("markdown", ""))
                    async with session.post(
                        f"{self.base_url}/analyze",
                        headers=self.headers,
                        json={
                            "content": content,
                            "analysis_type": workflow["analyze"]["type"],
                            "llm_provider": workflow["analyze"]["provider"],
                            "llm_token": workflow["analyze"]["token"]
                        }
                    ) as response:
                        data = await response.json()
                        result["steps"]["analyze"] = data["analysis"]
                
                results.append(result)
            
            return results

# Usage
pipeline = DataPipeline("your-api-token")

# Define workflow
workflow = {
    "scrape": {
        "formats": ["markdown", "screenshot"],
        "options": {"wait_for": 2000}
    },
    "execute": {
        "code": "document.querySelectorAll('.price').length",
        "screenshot": True
    },
    "clean": {
        "provider": "openai",
        "token": "your-openai-key",
        "options": {
            "remove_ads": True,
            "fix_formatting": True
        }
    },
    "extract": {
        "provider": "anthropic",
        "token": "your-anthropic-key",
        "schema": {
            "type": "object",
            "properties": {
                "products": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "price": {"type": "number"},
                            "availability": {"type": "string"}
                        }
                    }
                }
            }
        }
    },
    "analyze": {
        "type": "sentiment",
        "provider": "openai",
        "token": "your-openai-key"
    }
}

# Process URLs
urls = [
    "https://example-shop1.com/products",
    "https://example-shop2.com/catalog"
]

results = asyncio.run(pipeline.process_urls(urls, workflow))

# Aggregate results
all_products = []
for result in results:
    if "extract" in result["steps"]:
        products = result["steps"]["extract"].get("products", [])
        all_products.extend(products)

print(f"Found {len(all_products)} total products")
```

## 💡 Tips and Best Practices

### Rate Limiting and Retries

```python
import time
from typing import Callable, Any
import requests

def with_retry(func: Callable, max_retries: int = 3, delay: float = 1.0) -> Any:
    """Decorator for automatic retries with exponential backoff"""
    
    def wrapper(*args, **kwargs):
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = delay * (2 ** attempt)
                    print(f"Request failed, retrying in {wait_time}s...")
                    time.sleep(wait_time)
        
        raise last_exception
    
    return wrapper

# Usage
@with_retry
def scrape_with_retry(url: str, token: str):
    response = requests.post(
        "http://localhost:5678/api/v2/scrape",
        headers={"Authorization": f"Bearer {token}"},
        json={"url": url, "formats": ["markdown"]},
        timeout=30
    )
    response.raise_for_status()
    return response.json()
```

### Caching Results

```python
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Optional

class APICache:
    def __init__(self, cache_dir: str = "./cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_key(self, endpoint: str, params: Dict) -> str:
        """Generate cache key from endpoint and parameters"""
        cache_data = f"{endpoint}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(cache_data.encode()).hexdigest()
    
    def get(self, endpoint: str, params: Dict, max_age: timedelta = timedelta(hours=1)) -> Optional[Dict]:
        """Get cached result if available and not expired"""
        cache_key = self._get_cache_key(endpoint, params)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cached = json.load(f)
            
            cached_time = datetime.fromisoformat(cached["timestamp"])
            if datetime.now() - cached_time < max_age:
                return cached["data"]
        
        return None
    
    def set(self, endpoint: str, params: Dict, data: Dict):
        """Cache the result"""
        cache_key = self._get_cache_key(endpoint, params)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        with open(cache_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "data": data
            }, f)

# Usage
cache = APICache()

def cached_scrape(url: str, token: str) -> Dict:
    params = {"url": url, "formats": ["markdown"]}
    
    # Check cache
    cached_result = cache.get("/v2/scrape", params)
    if cached_result:
        print("Using cached result")
        return cached_result
    
    # Make API call
    response = requests.post(
        "http://localhost:5678/api/v2/scrape",
        headers={"Authorization": f"Bearer {token}"},
        json=params
    )
    
    result = response.json()
    
    # Cache the result
    if result["success"]:
        cache.set("/v2/scrape", params, result)
    
    return result
```
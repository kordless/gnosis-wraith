# Example Service: news.nuts.services - The Onion-Style Article Generator

## Overview
A perfect example of the Phase 5 agentic system in action - takes any URL, generates satirical articles, and evolves them as new information arrives.

## Service Architecture

### 1. User Flow
```
User visits news.nuts.services
    ↓
Enters URL (e.g., "https://techcrunch.com/2025/06/04/ai-startup-raises-funding")
    ↓
System crawls article → Analyzes content → Generates satire → Creates shareable page
    ↓
Article lives at: news.nuts.services/articles/[article-id]
    ↓
Auto-updates as related news emerges
```

### 2. Authentication Strategy (Cross-Service)

#### Option A: Unified Auth Service (Recommended)
```
auth.nuts.services/
├── /login              # Single sign-on for all *.nuts.services
├── /api/verify         # JWT verification endpoint
├── /api/user           # User profile/preferences
└── /api/tokens         # Service-specific API tokens

Each service (news, forge, etc.) validates tokens against auth.nuts.services
```

#### Option B: Federated Auth
```python
# core/auth/federated.py
class NutsServicesAuth:
    """Shared auth across all Gnosis services"""
    
    def __init__(self):
        self.auth_domain = "auth.nuts.services"
        self.jwt_secret = os.getenv("NUTS_JWT_SECRET")
    
    async def verify_token(self, token: str) -> dict:
        # Verify JWT signed by auth.nuts.services
        return jwt.decode(token, self.jwt_secret)
    
    async def get_user_services(self, user_id: str) -> list:
        # Return which services user has access to
        return ["news", "forge", "wraith"]  # etc
```

### 3. news.nuts.services Implementation

#### Frontend (React Artifact)
```javascript
// news.nuts.services/index.html
const NewsNutsApp = () => {
    const [url, setUrl] = useState('');
    const [article, setArticle] = useState(null);
    const [loading, setLoading] = useState(false);
    
    const generateArticle = async () => {
        setLoading(true);
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url })
        });
        
        const data = await response.json();
        // Redirect to article page
        window.location.href = `/articles/${data.article_id}`;
    };
    
    return (
        <div className="satire-generator">
            <h1>News Nuts 🥜</h1>
            <p>Turn any news into satire, Onion-style</p>
            <input 
                type="url" 
                placeholder="Paste a news article URL"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
            />
            <button onClick={generateArticle}>
                Generate Satirical Take
            </button>
        </div>
    );
};
```

#### Backend API
```python
# services/news/app.py
from fastapi import FastAPI, Depends
from core.auth import verify_user
from core.agent import AgentCoordinator

app = FastAPI(title="News Nuts API")
agent = AgentCoordinator()

@app.post("/api/generate")
async def generate_satire(request: GenerateRequest, user=Depends(verify_user)):
    # 1. Crawl the source article
    crawl_job = await agent.execute_task({
        "service": "wraith",
        "action": "crawl",
        "params": {"url": request.url}
    })
    
    # 2. Extract key facts
    facts = await agent.analyze_content(crawl_job.result)
    
    # 3. Generate satirical article
    satire = await agent.generate_satire({
        "facts": facts,
        "style": "the_onion",
        "tone": request.tone or "absurdist"
    })
    
    # 4. Create article record
    article = await create_article({
        "source_url": request.url,
        "title": satire.title,
        "content": satire.content,
        "author": f"NewsNuts AI ({user.username})",
        "user_id": user.id
    })
    
    # 5. Set up monitoring for updates
    await agent.create_monitor({
        "article_id": article.id,
        "source_url": request.url,
        "update_frequency": "hourly"
    })
    
    return {"article_id": article.id, "url": f"/articles/{article.id}"}

@app.get("/articles/{article_id}")
async def get_article(article_id: str):
    article = await load_article(article_id)
    return render_template("article.html", article=article)

@app.post("/api/articles/{article_id}/evolve")
async def evolve_article(article_id: str, update: UpdateInfo):
    """Called by monitoring system when new related news appears"""
    
    article = await load_article(article_id)
    
    # Generate update/addition to article
    evolution = await agent.evolve_satire({
        "original": article.content,
        "new_info": update.new_information,
        "style": "add_update_section"
    })
    
    # Append evolution to article
    article.content += f"\n\n[Update {datetime.now()}]\n{evolution}"
    article.evolution_count += 1
    await save_article(article)
    
    # Notify subscribers
    await notify_subscribers(article_id, "Article updated with new developments!")
```

### 4. Article Evolution System

```python
# core/evolution/news_monitor.py
class NewsMonitor:
    """Monitors for related news and triggers article updates"""
    
    async def check_for_updates(self, article: Article):
        # 1. Search for related news
        related = await self.search_related_news(
            keywords=article.extracted_keywords,
            since=article.last_updated
        )
        
        # 2. Filter for significant updates
        significant = self.filter_significant(related)
        
        # 3. Trigger evolution if needed
        if significant:
            await self.trigger_evolution(article.id, significant)
    
    async def search_related_news(self, keywords: list, since: datetime):
        # Use news APIs or crawl news sites
        results = []
        
        # Check major news sources
        for source in ["techcrunch", "reuters", "ap"]:
            matches = await wraith_api.search_site(
                site=source,
                keywords=keywords,
                since=since
            )
            results.extend(matches)
        
        return results
```

### 5. Shareable Article Page

```python
# templates/article.html (Jinja2)
<!DOCTYPE html>
<html>
<head>
    <title>{{ article.title }} - News Nuts</title>
    <meta property="og:title" content="{{ article.title }}">
    <meta property="og:description" content="{{ article.excerpt }}">
    <meta property="og:image" content="{{ article.hero_image }}">
    <meta name="twitter:card" content="summary_large_image">
</head>
<body>
    <article class="onion-style">
        <header>
            <h1>{{ article.title }}</h1>
            <p class="byline">By {{ article.author }} | {{ article.created_at }}</p>
            {% if article.evolution_count > 0 %}
            <p class="evolution-badge">
                🔄 Updated {{ article.evolution_count }} times
            </p>
            {% endif %}
        </header>
        
        <div class="content">
            {{ article.content | markdown }}
        </div>
        
        <footer>
            <p class="source">
                Satirizing: <a href="{{ article.source_url }}">Original Article</a>
            </p>
            <div class="share-buttons">
                <button onclick="shareTwitter()">Share on Twitter</button>
                <button onclick="copyLink()">Copy Link</button>
            </div>
            
            {% if user.is_authenticated %}
            <div class="subscribe">
                <button onclick="subscribeToUpdates()">
                    🔔 Notify me of updates
                </button>
            </div>
            {% endif %}
        </footer>
    </article>
    
    <script>
        // Real-time updates via WebSocket
        const ws = new WebSocket('wss://news.nuts.services/ws/articles/{{ article.id }}');
        ws.onmessage = (event) => {
            const update = JSON.parse(event.data);
            if (update.type === 'article_evolved') {
                showUpdateNotification();
            }
        };
    </script>
</body>
</html>
```

### 6. Storage Structure (Alaya)

```
storage/
├── services/
│   └── news/
│       ├── articles/
│       │   └── [article_id]/
│       │       ├── metadata.json
│       │       ├── content.md
│       │       ├── evolution_history.json
│       │       └── metrics.json
│       ├── users/
│       │   └── [user_hash]/
│       │       ├── articles.json
│       │       └── preferences.json
│       └── monitoring/
│           └── active_monitors.json
```

## Cross-Service Integration

### 1. With Other nuts.services
```python
# Example: Auto-generate memes for articles
async def generate_meme_for_article(article_id: str):
    article = await load_article(article_id)
    
    # Call forge.nuts.services to create meme
    meme_url = await forge_api.generate_meme({
        "headline": article.title,
        "style": "drake_format"
    })
    
    article.meme_url = meme_url
    await save_article(article)
```

### 2. With Authentication Service
```python
# Middleware for all routes
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Check if route requires auth
    if requires_auth(request.url.path):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        
        # Verify with auth.nuts.services
        user = await verify_token_with_auth_service(token)
        if not user:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        
        request.state.user = user
    
    return await call_next(request)
```

## Deployment Configuration

```yaml
# k8s/news-service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: news-nuts
  namespace: gnosis-services
spec:
  template:
    spec:
      containers:
      - image: gcr.io/gnosis-project/news-nuts:latest
        ports:
        - containerPort: 8080
        env:
        - name: AUTH_SERVICE_URL
          value: "https://auth.nuts.services"
        - name: WRAITH_API_URL
          value: "https://api.nuts.services/wraith"
        - name: STORAGE_BUCKET
          value: "gnosis-news-storage"
```

## Revenue Model Options

1. **Freemium**: 
   - Free: 5 articles/month
   - Pro: Unlimited + priority evolution updates
   
2. **API Access**: 
   - Developers can use news.nuts.services/api for their apps
   
3. **Custom Satire Styles**: 
   - Train on specific satirical voices/publications

This shows how news.nuts.services fits perfectly into the Phase 5 architecture - it's a self-contained service that uses the agent coordinator to orchestrate other services (Wraith for crawling, LLMs for generation, Alaya for storage) while maintaining its own identity and purpose.
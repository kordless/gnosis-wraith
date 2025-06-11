# DevOps Refactor: Wraith for Claude Code Love CD

## Overview

This refactor plan transforms Gnosis Wraith into a Docker Compose-based system with proper environment separation, including a development-only queue monitor page that triggers processing via JavaScript polling.

## Key Principles

1. **Redis is development-only** - Never deployed to production/cloud
2. **Browser-based queue processor** - JavaScript page polls queue endpoint while open
3. **No server-side cron** - Processing only happens when developer has monitor page open
4. **Claude Code friendly** - Easy to use with Claude Code CD workflows

## The Queue Monitor Page

### Concept
- Development-only page at `/dev/queue-monitor`
- Uses JavaScript `setInterval()` to poll processing endpoint
- Only processes queue while page is open in browser
- Shows real-time queue status and processing results
- Similar to Cloud Run Jobs but manual/on-demand

### How It Works
```javascript
// When page loads, start polling
let pollInterval;
window.addEventListener('load', () => {
    // Poll every 5 seconds while page is open
    pollInterval = setInterval(async () => {
        const response = await fetch('/api/process-queue');
        updateQueueStatus(response);
    }, 5000);
});

// Stop polling when page closes
window.addEventListener('beforeunload', () => {
    clearInterval(pollInterval);
});
```

## Phase 1: Docker Compose Setup

### docker-compose.yml (Base Configuration)
```yaml
version: '3.8'

services:
  wraith:
    build: .
    container_name: gnosis-wraith
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      - ./storage:/app/storage
      - ./logs:/app/logs
    networks:
      - gnosis-network

networks:
  gnosis-network:
    driver: bridge
```

### docker-compose.dev.yml (Development Overrides)
```yaml
version: '3.8'

services:
  redis:
    image: redis:alpine
    container_name: gnosis-redis-dev
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - gnosis-network

  wraith:
    depends_on:
      redis:
        condition: service_healthy
    environment:
      - ENVIRONMENT=development
      - REDIS_URL=redis://redis:6379
      - DEBUG=true
      - RELOAD=true
      - ENABLE_DEV_ENDPOINTS=true
    volumes:
      - ./core:/app/core
      - ./web:/app/web
      - ./ai:/app/ai
      - ./app.py:/app/app.py
    command: python -m uvicorn app:app --reload --host 0.0.0.0 --port 5678

volumes:
  redis-data:
```

### docker-compose.prod.yml (Production Overrides)
```yaml
version: '3.8'

services:
  wraith:
    environment:
      - ENVIRONMENT=production
      - USE_CLOUD_TASKS=true
      - REDIS_URL=  # Empty - no Redis in production
      - DEBUG=false
      - WORKERS=4
      - ENABLE_DEV_ENDPOINTS=false  # Disable dev endpoints
    command: python -m uvicorn app:app --host 0.0.0.0 --port 5678 --workers 4
```

## Phase 2: Queue Monitor Implementation

### web/routes/dev.py (Development Routes)
```python
from quart import Blueprint, render_template, jsonify, request
from core.config import Config
from core.task_manager import TaskManager
import functools

dev_bp = Blueprint('dev', __name__, url_prefix='/dev')

def dev_only(f):
    """Decorator to ensure endpoint only works in development"""
    @functools.wraps(f)
    async def decorated_function(*args, **kwargs):
        if not Config.IS_DEVELOPMENT:
            return jsonify({"error": "Not available in production"}), 404
        return await f(*args, **kwargs)
    return decorated_function

@dev_bp.route('/queue-monitor')
@dev_only
async def queue_monitor():
    """Development queue monitor page"""
    return await render_template('dev/queue_monitor.html')

@dev_bp.route('/api/queue-status')
@dev_only
async def queue_status():
    """Get current queue status"""
    task_manager = TaskManager()
    status = await task_manager.get_queue_status()
    return jsonify(status)

@dev_bp.route('/api/process-queue', methods=['POST'])
@dev_only
async def process_queue():
    """Process one batch of queue items"""
    task_manager = TaskManager()
    results = await task_manager.process_batch(limit=5)
    return jsonify({
        "processed": len(results),
        "results": results,
        "timestamp": datetime.now().isoformat()
    })
```

### web/templates/dev/queue_monitor.html
```html
<!DOCTYPE html>
<html>
<head>
    <title>Queue Monitor - Development Only</title>
    <style>
        body {
            font-family: 'Monaco', 'Consolas', monospace;
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 20px;
        }
        .monitor {
            background: #252526;
            border: 1px solid #464647;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .status {
            display: grid;
            grid-template-columns: 200px 1fr;
            gap: 10px;
            margin-bottom: 20px;
        }
        .status-label {
            color: #9cdcfe;
        }
        .status-value {
            color: #ce9178;
        }
        .log {
            background: #1e1e1e;
            border: 1px solid #464647;
            border-radius: 4px;
            padding: 10px;
            height: 400px;
            overflow-y: auto;
            font-size: 12px;
        }
        .log-entry {
            margin-bottom: 5px;
            padding: 5px;
            border-left: 3px solid #007acc;
        }
        .log-entry.error {
            border-left-color: #f44747;
        }
        .log-entry.success {
            border-left-color: #89d185;
        }
        .controls {
            margin-bottom: 20px;
        }
        button {
            background: #0e639c;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 10px;
        }
        button:hover {
            background: #1177bb;
        }
        button:disabled {
            background: #464647;
            cursor: not-allowed;
        }
        .indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 5px;
        }
        .indicator.active {
            background: #89d185;
            animation: pulse 1s infinite;
        }
        .indicator.inactive {
            background: #f44747;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
    </style>
</head>
<body>
    <h1>🔄 Queue Monitor (Development Only)</h1>
    
    <div class="monitor">
        <h2>
            <span id="polling-indicator" class="indicator inactive"></span>
            Polling Status
        </h2>
        <div class="controls">
            <button id="start-btn" onclick="startPolling()">Start Polling</button>
            <button id="stop-btn" onclick="stopPolling()" disabled>Stop Polling</button>
            <button onclick="processOnce()">Process Once</button>
            <label>
                Interval: 
                <select id="interval-select" onchange="updateInterval()">
                    <option value="1000">1 second</option>
                    <option value="5000" selected>5 seconds</option>
                    <option value="10000">10 seconds</option>
                    <option value="30000">30 seconds</option>
                </select>
            </label>
        </div>
        
        <div class="status">
            <div class="status-label">Queue Size:</div>
            <div class="status-value" id="queue-size">-</div>
            
            <div class="status-label">Processed Total:</div>
            <div class="status-value" id="processed-total">0</div>
            
            <div class="status-label">Last Poll:</div>
            <div class="status-value" id="last-poll">Never</div>
            
            <div class="status-label">Next Poll:</div>
            <div class="status-value" id="next-poll">Not scheduled</div>
        </div>
    </div>
    
    <div class="monitor">
        <h2>📋 Processing Log</h2>
        <div id="log" class="log"></div>
    </div>

    <script>
        let pollInterval = null;
        let pollIntervalMs = 5000;
        let processedTotal = 0;
        let nextPollTimeout = null;
        
        function addLogEntry(message, type = 'info') {
            const log = document.getElementById('log');
            const entry = document.createElement('div');
            entry.className = `log-entry ${type}`;
            entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
            log.insertBefore(entry, log.firstChild);
            
            // Keep only last 100 entries
            while (log.children.length > 100) {
                log.removeChild(log.lastChild);
            }
        }
        
        async function updateQueueStatus() {
            try {
                const response = await fetch('/dev/api/queue-status');
                const data = await response.json();
                document.getElementById('queue-size').textContent = data.queue_size || 0;
            } catch (error) {
                addLogEntry(`Failed to get queue status: ${error.message}`, 'error');
            }
        }
        
        async function processQueue() {
            document.getElementById('last-poll').textContent = new Date().toLocaleTimeString();
            
            try {
                const response = await fetch('/dev/api/process-queue', {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.processed > 0) {
                    processedTotal += data.processed;
                    document.getElementById('processed-total').textContent = processedTotal;
                    addLogEntry(`Processed ${data.processed} items`, 'success');
                    
                    // Log individual results
                    data.results.forEach(result => {
                        addLogEntry(`  ↳ ${result.task_id}: ${result.status}`, 
                                   result.status === 'success' ? 'success' : 'error');
                    });
                } else {
                    addLogEntry('No items to process', 'info');
                }
                
                await updateQueueStatus();
                
            } catch (error) {
                addLogEntry(`Processing error: ${error.message}`, 'error');
            }
            
            // Update next poll time
            if (pollInterval) {
                const nextTime = new Date(Date.now() + pollIntervalMs);
                document.getElementById('next-poll').textContent = nextTime.toLocaleTimeString();
            }
        }
        
        function startPolling() {
            if (pollInterval) return;
            
            document.getElementById('start-btn').disabled = true;
            document.getElementById('stop-btn').disabled = false;
            document.getElementById('polling-indicator').className = 'indicator active';
            
            addLogEntry('Started polling', 'success');
            
            // Process immediately
            processQueue();
            
            // Then set interval
            pollInterval = setInterval(processQueue, pollIntervalMs);
        }
        
        function stopPolling() {
            if (!pollInterval) return;
            
            clearInterval(pollInterval);
            pollInterval = null;
            
            document.getElementById('start-btn').disabled = false;
            document.getElementById('stop-btn').disabled = true;
            document.getElementById('polling-indicator').className = 'indicator inactive';
            document.getElementById('next-poll').textContent = 'Not scheduled';
            
            addLogEntry('Stopped polling', 'error');
        }
        
        async function processOnce() {
            addLogEntry('Manual process triggered', 'info');
            await processQueue();
        }
        
        function updateInterval() {
            pollIntervalMs = parseInt(document.getElementById('interval-select').value);
            
            if (pollInterval) {
                stopPolling();
                startPolling();
                addLogEntry(`Interval changed to ${pollIntervalMs/1000} seconds`, 'info');
            }
        }
        
        // Initial status update
        updateQueueStatus();
        addLogEntry('Queue monitor loaded', 'info');
        
        // Stop polling on page unload
        window.addEventListener('beforeunload', () => {
            if (pollInterval) {
                clearInterval(pollInterval);
            }
        });
    </script>
</body>
</html>
```

## Phase 3: Configuration Updates

### core/config.py
```python
import os

class Config:
    # Environment detection
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    IS_DEVELOPMENT = ENVIRONMENT == 'development'
    IS_PRODUCTION = ENVIRONMENT == 'production'
    
    # Development features
    ENABLE_DEV_ENDPOINTS = os.getenv('ENABLE_DEV_ENDPOINTS', 'false').lower() == 'true'
    
    # Redis configuration (development only)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379') if IS_DEVELOPMENT else None
    USE_REDIS = bool(REDIS_URL) and IS_DEVELOPMENT
    
    # Queue processing
    QUEUE_BATCH_SIZE = int(os.getenv('QUEUE_BATCH_SIZE', '5'))
    QUEUE_TIMEOUT = int(os.getenv('QUEUE_TIMEOUT', '30'))
```

### app.py Updates
```python
from web.routes import auth, api, pages, terminal
from web.routes.dev import dev_bp
from core.config import Config

async def create_app():
    app = Quart(__name__)
    
    # Register blueprints
    app.register_blueprint(auth.auth_bp)
    app.register_blueprint(api.api_bp)
    app.register_blueprint(pages.pages_bp)
    app.register_blueprint(terminal.terminal_bp)
    
    # Register dev blueprint only in development
    if Config.IS_DEVELOPMENT and Config.ENABLE_DEV_ENDPOINTS:
        app.register_blueprint(dev_bp)
        logger.info("Development endpoints enabled at /dev/*")
    
    return app
```

## Phase 4: Quick Start Commands

### Development (with queue monitor)
```bash
# Start with Redis and dev endpoints
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Open queue monitor in browser
open http://localhost:5678/dev/queue-monitor

# View logs
docker-compose logs -f wraith
```

### Production (no dev features)
```bash
# Start production mode
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Helper Scripts

#### start-dev.sh
```bash
#!/bin/bash
echo "Starting Gnosis Wraith in development mode..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

echo "Waiting for services to start..."
sleep 5

echo "Services running:"
docker-compose ps

echo ""
echo "Queue monitor available at: http://localhost:5678/dev/queue-monitor"
echo "Main app available at: http://localhost:5678"
```

#### rebuild-dev.ps1
```powershell
Write-Host "Rebuilding Gnosis Wraith for development..." -ForegroundColor Green

# Stop existing
docker-compose down

# Rebuild
docker-compose -f docker-compose.yml -f docker-compose.dev.yml build --no-cache

# Start
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Open queue monitor
Start-Process "http://localhost:5678/dev/queue-monitor"

Write-Host "Queue monitor opened in browser" -ForegroundColor Green
```

## Benefits

1. **Simple Queue Processing**: Just open the monitor page and it processes
2. **No Background Services**: Processing only happens when you want it
3. **Visual Feedback**: See queue status and processing results in real-time
4. **Development Only**: Automatically disabled in production
5. **Claude Code Friendly**: Easy to use during development iterations

## How It Works

1. Open `/dev/queue-monitor` in your browser during development
2. Click "Start Polling" to begin processing queue
3. Page sends requests to `/dev/api/process-queue` every 5 seconds
4. Each request processes up to 5 queue items
5. See results in real-time in the log
6. Close page or click "Stop Polling" to pause processing

This approach mimics Cloud Run Jobs but with manual control - perfect for development!

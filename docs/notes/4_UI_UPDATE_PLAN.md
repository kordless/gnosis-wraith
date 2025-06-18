# Phase 4: UI Update Plan for Claude Desktop

## Overview
Update the Gnosis Wraith UI to fully support V2 endpoints, MCP tools, and provide optimal experience for Claude Desktop users.

## Timeline: Week 5 (5-7 days)

## 4.1 UI Architecture Updates

### File: `web/static/js/components/v2-api-client.js` (NEW)

Create V2 API client with smart sync/async handling:

```javascript
/**
 * V2 API Client with smart sync/async support
 */
class V2ApiClient {
    constructor() {
        this.baseUrl = '/v2';
        this.activeJobs = new Map();
        this.sessionId = null;
    }

    /**
     * Smart crawl that handles both sync and async responses
     */
    async crawl(url, options = {}) {
        const requestData = {
            url: url,
            javascript: options.javascript || false,
            screenshot: options.screenshot || false,
            full_content: options.fullContent || false,
            depth: options.depth || 0,
            session_id: this.sessionId
        };

        try {
            const response = await fetch(`${this.baseUrl}/crawl`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Version': '2'
                },
                body: JSON.stringify(requestData)
            });

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Crawl failed');
            }

            // Handle async response
            if (data.async && data.job_id) {
                // Store job for tracking
                this.activeJobs.set(data.job_id, {
                    url: url,
                    startTime: Date.now(),
                    estimatedTime: data.estimated_time
                });

                // Return job info for UI to handle
                return {
                    type: 'async',
                    jobId: data.job_id,
                    estimatedTime: data.estimated_time,
                    checkUrl: data.check_url
                };
            }

            // Handle sync response
            if (data.session_id) {
                this.sessionId = data.session_id;
            }

            return {
                type: 'sync',
                data: data,
                sessionId: this.sessionId
            };

        } catch (error) {
            console.error('Crawl error:', error);
            throw error;
        }
    }

    /**
     * Check job status with progress updates
     */
    async checkJobStatus(jobId) {
        try {
            const response = await fetch(`${this.baseUrl}/jobs/${jobId}`);
            const data = await response.json();

            if (data.status === 'completed' && data.result) {
                // Remove from active jobs
                this.activeJobs.delete(jobId);
                
                // Extract session if present
                if (data.result.session_id) {
                    this.sessionId = data.result.session_id;
                }
            }

            return data;
        } catch (error) {
            console.error('Job status error:', error);
            throw error;
        }
    }

    /**
     * Search previous crawls
     */
    async search(query, limit = 10) {
        try {
            const response = await fetch(`${this.baseUrl}/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query, limit })
            });

            return await response.json();
        } catch (error) {
            console.error('Search error:', error);
            throw error;
        }
    }

    /**
     * Execute a workflow
     */
    async executeWorkflow(workflowName, parameters) {
        try {
            const response = await fetch(`${this.baseUrl}/workflows/${workflowName}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(parameters)
            });

            return await response.json();
        } catch (error) {
            console.error('Workflow error:', error);
            throw error;
        }
    }

    /**
     * Get all active jobs
     */
    getActiveJobs() {
        return Array.from(this.activeJobs.entries()).map(([jobId, info]) => ({
            jobId,
            ...info,
            elapsed: Date.now() - info.startTime
        }));
    }
}

// Export for use in other components
window.V2ApiClient = V2ApiClient;
```

### File: `web/static/js/components/crawl-interface-v2.js` (NEW)

Enhanced crawl interface with V2 features:

```javascript
/**
 * Enhanced crawl interface for V2 API
 */
class CrawlInterfaceV2 extends HTMLElement {
    constructor() {
        super();
        this.apiClient = new V2ApiClient();
        this.activeJobs = new Map();
        this.jobCheckIntervals = new Map();
    }

    connectedCallback() {
        this.innerHTML = `
            <div class="crawl-interface-v2">
                <!-- URL Input Section -->
                <div class="url-input-section">
                    <input 
                        type="url" 
                        id="crawl-url" 
                        placeholder="Enter URL to crawl..."
                        class="url-input"
                    />
                    <button id="crawl-btn" class="primary-button">
                        <span class="button-text">Crawl</span>
                        <span class="button-spinner hidden">⏳</span>
                    </button>
                </div>

                <!-- Options Section -->
                <div class="crawl-options">
                    <label class="option-toggle">
                        <input type="checkbox" id="opt-javascript" />
                        <span>Enable JavaScript</span>
                        <span class="option-hint">(slower)</span>
                    </label>
                    
                    <label class="option-toggle">
                        <input type="checkbox" id="opt-screenshot" />
                        <span>Capture Screenshot</span>
                        <span class="option-hint">(slower)</span>
                    </label>
                    
                    <label class="option-toggle">
                        <input type="checkbox" id="opt-full-content" />
                        <span>Extract Full Content</span>
                    </label>
                    
                    <div class="depth-control">
                        <label>Crawl Depth:</label>
                        <input 
                            type="range" 
                            id="opt-depth" 
                            min="0" 
                            max="3" 
                            value="0"
                        />
                        <span id="depth-value">0</span>
                    </div>
                </div>

                <!-- Smart Mode Indicator -->
                <div class="smart-mode-indicator">
                    <span class="indicator-label">Execution Mode:</span>
                    <span id="execution-mode" class="mode-badge">Auto-detect</span>
                    <span id="time-estimate" class="time-estimate"></span>
                </div>

                <!-- Session Info -->
                <div id="session-info" class="session-info hidden">
                    <span>🔗 Session Active</span>
                    <button id="clear-session" class="small-button">Clear</button>
                </div>

                <!-- Active Jobs -->
                <div id="active-jobs" class="active-jobs hidden">
                    <h3>Active Jobs</h3>
                    <div id="jobs-list"></div>
                </div>

                <!-- Results Section -->
                <div id="results-section" class="results-section hidden">
                    <div class="results-header">
                        <h3>Results</h3>
                        <div class="result-actions">
                            <button id="save-result" class="small-button">Save</button>
                            <button id="export-result" class="small-button">Export</button>
                            <button id="analyze-result" class="small-button">Analyze</button>
                        </div>
                    </div>
                    <div id="results-content"></div>
                </div>

                <!-- Quick Actions -->
                <div class="quick-actions">
                    <button id="workflow-analyze" class="workflow-button" data-workflow="analyze_website">
                        🔍 Analyze Website
                    </button>
                    <button id="workflow-monitor" class="workflow-button" data-workflow="monitor_changes">
                        📊 Monitor Changes
                    </button>
                    <button id="workflow-extract" class="workflow-button" data-workflow="extract_data">
                        📤 Extract Data
                    </button>
                </div>
            </div>
        `;

        this.attachEventListeners();
        this.updateExecutionMode();
    }

    attachEventListeners() {
        // Crawl button
        this.querySelector('#crawl-btn').addEventListener('click', () => this.handleCrawl());
        
        // Enter key on URL input
        this.querySelector('#crawl-url').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleCrawl();
        });

        // Options change
        const options = ['#opt-javascript', '#opt-screenshot', '#opt-full-content', '#opt-depth'];
        options.forEach(opt => {
            this.querySelector(opt).addEventListener('change', () => this.updateExecutionMode());
        });

        // Depth slider
        this.querySelector('#opt-depth').addEventListener('input', (e) => {
            this.querySelector('#depth-value').textContent = e.target.value;
            this.updateExecutionMode();
        });

        // Session clear
        this.querySelector('#clear-session').addEventListener('click', () => this.clearSession());

        // Workflow buttons
        this.querySelectorAll('.workflow-button').forEach(btn => {
            btn.addEventListener('click', (e) => this.executeWorkflow(e.target.dataset.workflow));
        });

        // Result actions
        this.querySelector('#analyze-result').addEventListener('click', () => this.analyzeResult());
    }

    async updateExecutionMode() {
        const options = this.getOptions();
        
        // Estimate complexity
        let complexity = 0;
        if (options.javascript) complexity += 2;
        if (options.screenshot) complexity += 1;
        if (options.fullContent) complexity += 0.5;
        if (options.depth > 0) complexity += options.depth * 2;

        const modeEl = this.querySelector('#execution-mode');
        const timeEl = this.querySelector('#time-estimate');

        if (complexity < 3) {
            modeEl.textContent = 'Sync (Fast)';
            modeEl.className = 'mode-badge mode-sync';
            timeEl.textContent = '~1-3 seconds';
        } else {
            modeEl.textContent = 'Async (Background)';
            modeEl.className = 'mode-badge mode-async';
            timeEl.textContent = `~${Math.round(complexity * 2)}-${Math.round(complexity * 3)} seconds`;
        }
    }

    getOptions() {
        return {
            javascript: this.querySelector('#opt-javascript').checked,
            screenshot: this.querySelector('#opt-screenshot').checked,
            fullContent: this.querySelector('#opt-full-content').checked,
            depth: parseInt(this.querySelector('#opt-depth').value)
        };
    }

    async handleCrawl() {
        const url = this.querySelector('#crawl-url').value.trim();
        if (!url) {
            this.showError('Please enter a URL');
            return;
        }

        const button = this.querySelector('#crawl-btn');
        const buttonText = button.querySelector('.button-text');
        const buttonSpinner = button.querySelector('.button-spinner');

        // Update UI
        button.disabled = true;
        buttonText.classList.add('hidden');
        buttonSpinner.classList.remove('hidden');

        try {
            const result = await this.apiClient.crawl(url, this.getOptions());

            if (result.type === 'async') {
                // Handle async job
                this.addActiveJob(result.jobId, url, result.estimatedTime);
                this.showNotification(`Crawl job started. Estimated time: ${result.estimatedTime}s`);
                
                // Start checking job status
                this.startJobStatusCheck(result.jobId);
            } else {
                // Handle sync result
                this.displayResults(result.data);
                this.updateSessionInfo();
            }

        } catch (error) {
            this.showError(error.message);
        } finally {
            button.disabled = false;
            buttonText.classList.remove('hidden');
            buttonSpinner.classList.add('hidden');
        }
    }

    addActiveJob(jobId, url, estimatedTime) {
        this.activeJobs.set(jobId, {
            url,
            startTime: Date.now(),
            estimatedTime
        });

        this.updateActiveJobsDisplay();
    }

    updateActiveJobsDisplay() {
        const jobsSection = this.querySelector('#active-jobs');
        const jobsList = this.querySelector('#jobs-list');

        if (this.activeJobs.size === 0) {
            jobsSection.classList.add('hidden');
            return;
        }

        jobsSection.classList.remove('hidden');
        
        jobsList.innerHTML = Array.from(this.activeJobs.entries()).map(([jobId, info]) => {
            const elapsed = Math.round((Date.now() - info.startTime) / 1000);
            const progress = Math.min(100, (elapsed / info.estimatedTime) * 100);
            
            return `
                <div class="job-item" data-job-id="${jobId}">
                    <div class="job-url">${info.url}</div>
                    <div class="job-progress">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${progress}%"></div>
                        </div>
                        <span class="progress-text">${elapsed}s / ~${info.estimatedTime}s</span>
                    </div>
                    <button class="cancel-job" onclick="this.parentElement.dispatchEvent(new CustomEvent('cancel-job', {detail: '${jobId}'}))">
                        ❌
                    </button>
                </div>
            `;
        }).join('');

        // Add cancel handlers
        jobsList.querySelectorAll('.job-item').forEach(item => {
            item.addEventListener('cancel-job', (e) => this.cancelJob(e.detail));
        });
    }

    async startJobStatusCheck(jobId) {
        const checkInterval = setInterval(async () => {
            try {
                const status = await this.apiClient.checkJobStatus(jobId);

                if (status.status === 'completed') {
                    // Job completed
                    clearInterval(checkInterval);
                    this.jobCheckIntervals.delete(jobId);
                    this.activeJobs.delete(jobId);
                    
                    this.displayResults(status.result);
                    this.updateSessionInfo();
                    this.updateActiveJobsDisplay();
                    
                    this.showNotification('Crawl completed successfully! ✅');
                } else if (status.status === 'failed') {
                    // Job failed
                    clearInterval(checkInterval);
                    this.jobCheckIntervals.delete(jobId);
                    this.activeJobs.delete(jobId);
                    
                    this.showError(`Crawl failed: ${status.error}`);
                    this.updateActiveJobsDisplay();
                }
                
                // Update progress if still running
                if (status.status === 'running' && status.progress) {
                    this.updateJobProgress(jobId, status.progress);
                }

            } catch (error) {
                console.error('Job check error:', error);
            }
        }, 1000); // Check every second

        this.jobCheckIntervals.set(jobId, checkInterval);
    }

    updateJobProgress(jobId, progress) {
        const jobElement = this.querySelector(`[data-job-id="${jobId}"] .progress-fill`);
        if (jobElement) {
            jobElement.style.width = `${progress}%`;
        }
    }

    updateSessionInfo() {
        const sessionInfo = this.querySelector('#session-info');
        
        if (this.apiClient.sessionId) {
            sessionInfo.classList.remove('hidden');
        } else {
            sessionInfo.classList.add('hidden');
        }
    }

    clearSession() {
        this.apiClient.sessionId = null;
        this.updateSessionInfo();
        this.showNotification('Session cleared');
    }

    displayResults(data) {
        const resultsSection = this.querySelector('#results-section');
        const resultsContent = this.querySelector('#results-content');

        resultsSection.classList.remove('hidden');

        // Format results based on data type
        let html = '<div class="result-data">';
        
        if (data.content) {
            html += `
                <div class="result-field">
                    <h4>Content</h4>
                    <div class="content-preview">${this.truncate(data.content, 500)}</div>
                </div>
            `;
        }

        if (data.screenshot) {
            html += `
                <div class="result-field">
                    <h4>Screenshot</h4>
                    <img src="${data.screenshot}" alt="Screenshot" class="result-screenshot" />
                </div>
            `;
        }

        if (data.metadata) {
            html += `
                <div class="result-field">
                    <h4>Metadata</h4>
                    <pre class="metadata-display">${JSON.stringify(data.metadata, null, 2)}</pre>
                </div>
            `;
        }

        html += '</div>';
        resultsContent.innerHTML = html;

        // Store current result for actions
        this.currentResult = data;
    }

    truncate(text, length) {
        if (text.length <= length) return text;
        return text.substring(0, length) + '...';
    }

    async executeWorkflow(workflowName) {
        const url = this.querySelector('#crawl-url').value.trim();
        if (!url) {
            this.showError('Please enter a URL first');
            return;
        }

        try {
            const result = await this.apiClient.executeWorkflow(workflowName, { url });
            
            if (result.success) {
                this.displayWorkflowResults(workflowName, result);
            } else {
                this.showError(result.error);
            }
        } catch (error) {
            this.showError(error.message);
        }
    }

    displayWorkflowResults(workflowName, result) {
        // Create a special display for workflow results
        const resultsContent = this.querySelector('#results-content');
        
        resultsContent.innerHTML = `
            <div class="workflow-results">
                <h3>Workflow: ${workflowName.replace('_', ' ').toUpperCase()}</h3>
                <div class="workflow-steps">
                    ${result.steps_completed ? `<p>✅ Completed ${result.steps_completed} steps</p>` : ''}
                </div>
                <div class="workflow-output">
                    ${this.formatWorkflowOutput(result)}
                </div>
            </div>
        `;

        this.querySelector('#results-section').classList.remove('hidden');
    }

    formatWorkflowOutput(result) {
        let html = '';
        
        if (result.analysis) {
            html += `<div class="output-section">
                <h4>Analysis</h4>
                <p>${result.analysis}</p>
            </div>`;
        }
        
        if (result.structure) {
            html += `<div class="output-section">
                <h4>Site Structure</h4>
                <pre>${result.structure}</pre>
            </div>`;
        }
        
        if (result.key_points) {
            html += `<div class="output-section">
                <h4>Key Points</h4>
                <ul>${result.key_points.split('\n').map(point => `<li>${point}</li>`).join('')}</ul>
            </div>`;
        }
        
        return html;
    }

    showNotification(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => toast.classList.add('show'), 10);
        
        // Remove after delay
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    async analyzeResult() {
        if (!this.currentResult) {
            this.showError('No result to analyze');
            return;
        }

        // This would integrate with AI analysis tools
        this.showNotification('Analysis feature coming soon!');
    }

    disconnectedCallback() {
        // Clean up intervals
        this.jobCheckIntervals.forEach(interval => clearInterval(interval));
    }
}

// Register custom element
customElements.define('crawl-interface-v2', CrawlInterfaceV2);
```

### File: `web/static/css/v2-interface.css` (NEW)

Modern CSS for V2 interface:

```css
/* V2 Interface Styles */
.crawl-interface-v2 {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
}

/* URL Input Section */
.url-input-section {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
}

.url-input {
    flex: 1;
    padding: 12px 16px;
    font-size: 16px;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    transition: border-color 0.3s;
}

.url-input:focus {
    outline: none;
    border-color: #3498db;
}

.primary-button {
    padding: 12px 24px;
    background: #3498db;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.3s;
    position: relative;
    min-width: 120px;
}

.primary-button:hover {
    background: #2980b9;
}

.primary-button:disabled {
    background: #95a5a6;
    cursor: not-allowed;
}

.button-spinner {
    display: inline-block;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Options Section */
.crawl-options {
    background: #f8f9fa;
    padding: 16px;
    border-radius: 8px;
    margin-bottom: 16px;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 12px;
}

.option-toggle {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
}

.option-toggle input[type="checkbox"] {
    width: 18px;
    height: 18px;
    cursor: pointer;
}

.option-hint {
    color: #7f8c8d;
    font-size: 12px;
}

.depth-control {
    display: flex;
    align-items: center;
    gap: 10px;
}

.depth-control input[type="range"] {
    flex: 1;
}

/* Smart Mode Indicator */
.smart-mode-indicator {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
    padding: 12px;
    background: #ecf0f1;
    border-radius: 8px;
}

.mode-badge {
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 14px;
    font-weight: 600;
}

.mode-sync {
    background: #2ecc71;
    color: white;
}

.mode-async {
    background: #e74c3c;
    color: white;
}

.time-estimate {
    color: #7f8c8d;
    font-size: 14px;
}

/* Session Info */
.session-info {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px;
    background: #e8f4f8;
    border-radius: 8px;
    margin-bottom: 16px;
}

.small-button {
    padding: 4px 12px;
    background: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
}

/* Active Jobs */
.active-jobs {
    background: #fff3cd;
    padding: 16px;
    border-radius: 8px;
    margin-bottom: 16px;
}

.active-jobs h3 {
    margin-top: 0;
    color: #856404;
}

.job-item {
    display: grid;
    grid-template-columns: 1fr auto auto;
    align-items: center;
    gap: 12px;
    padding: 12px;
    background: white;
    border-radius: 6px;
    margin-bottom: 8px;
}

.job-url {
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.job-progress {
    display: flex;
    align-items: center;
    gap: 8px;
}

.progress-bar {
    width: 150px;
    height: 8px;
    background: #e0e0e0;
    border-radius: 4px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background: #3498db;
    transition: width 0.3s;
}

.progress-text {
    font-size: 12px;
    color: #7f8c8d;
}

.cancel-job {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 16px;
    padding: 4px;
}

/* Results Section */
.results-section {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 16px;
}

.results-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
}

.result-actions {
    display: flex;
    gap: 8px;
}

.content-preview {
    background: #f8f9fa;
    padding: 12px;
    border-radius: 6px;
    max-height: 200px;
    overflow-y: auto;
    font-family: monospace;
    font-size: 14px;
}

.result-screenshot {
    max-width: 100%;
    border-radius: 6px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.metadata-display {
    background: #f8f9fa;
    padding: 12px;
    border-radius: 6px;
    overflow-x: auto;
    font-size: 12px;
}

/* Quick Actions */
.quick-actions {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 12px;
}

.workflow-button {
    padding: 16px;
    background: white;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    cursor: pointer;
    font-size: 16px;
    font-weight: 500;
    transition: all 0.3s;
    text-align: center;
}

.workflow-button:hover {
    border-color: #3498db;
    background: #f0f8ff;
}

/* Toast Notifications */
.toast {
    position: fixed;
    bottom: 20px;
    right: 20px;
    padding: 16px 24px;
    border-radius: 8px;
    color: white;
    font-weight: 500;
    transform: translateY(100px);
    opacity: 0;
    transition: all 0.3s;
    z-index: 1000;
}

.toast.show {
    transform: translateY(0);
    opacity: 1;
}

.toast-info {
    background: #3498db;
}

.toast-error {
    background: #e74c3c;
}

.toast-success {
    background: #2ecc71;
}

/* Workflow Results */
.workflow-results {
    padding: 16px;
}

.workflow-results h3 {
    margin-top: 0;
    color: #2c3e50;
}

.workflow-steps {
    margin-bottom: 16px;
    color: #27ae60;
}

.output-section {
    margin-bottom: 20px;
    padding: 16px;
    background: #f8f9fa;
    border-radius: 6px;
}

.output-section h4 {
    margin-top: 0;
    color: #34495e;
}

/* Responsive Design */
@media (max-width: 768px) {
    .crawl-interface-v2 {
        padding: 12px;
    }

    .url-input-section {
        flex-direction: column;
    }

    .crawl-options {
        grid-template-columns: 1fr;
    }

    .job-item {
        grid-template-columns: 1fr;
        gap: 8px;
    }

    .job-progress {
        width: 100%;
    }

    .progress-bar {
        width: 100%;
    }
}

/* Dark Mode Support */
@media (prefers-color-scheme: dark) {
    .crawl-interface-v2 {
        color: #ecf0f1;
    }

    .url-input {
        background: #2c3e50;
        border-color: #34495e;
        color: white;
    }

    .crawl-options {
        background: #2c3e50;
    }

    .smart-mode-indicator {
        background: #34495e;
    }

    .results-section {
        background: #2c3e50;
        border-color: #34495e;
    }

    .content-preview,
    .metadata-display {
        background: #34495e;
        color: #ecf0f1;
    }

    .workflow-button {
        background: #2c3e50;
        border-color: #34495e;
        color: #ecf0f1;
    }

    .workflow-button:hover {
        background: #34495e;
        border-color: #3498db;
    }
}

/* Hidden utility */
.hidden {
    display: none !important;
}
```

### File: `web/templates/gnosis_v2.html` (NEW)

Updated main template for V2:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gnosis Wraith V2 - Intelligent Web Crawler</title>
    
    <!-- CSS -->
    <link rel="stylesheet" href="/static/css/v2-interface.css">
    
    <!-- Favicon -->
    <link rel="icon" type="image/svg+xml" href="/static/images/favicon.svg">
</head>
<body>
    <div class="app-container">
        <!-- Header -->
        <header class="app-header">
            <div class="header-content">
                <h1>🌐 Gnosis Wraith <span class="version-badge">V2</span></h1>
                <p class="tagline">Intelligent Web Crawling with AI-Powered Analysis</p>
            </div>
            
            <nav class="header-nav">
                <a href="#" class="nav-link active">Crawl</a>
                <a href="#reports" class="nav-link">Reports</a>
                <a href="#tools" class="nav-link">Tools</a>
                <a href="#api" class="nav-link">API</a>
            </nav>
        </header>

        <!-- Main Content -->
        <main class="app-main">
            <!-- V2 Crawl Interface -->
            <crawl-interface-v2></crawl-interface-v2>
            
            <!-- Features Section -->
            <section class="features-section">
                <h2>V2 Features</h2>
                <div class="features-grid">
                    <div class="feature-card">
                        <span class="feature-icon">⚡</span>
                        <h3>Smart Sync/Async</h3>
                        <p>Automatically chooses the best execution mode based on crawl complexity</p>
                    </div>
                    
                    <div class="feature-card">
                        <span class="feature-icon">🔗</span>
                        <h3>Session Persistence</h3>
                        <p>Maintain browser state between crawls for authenticated pages</p>
                    </div>
                    
                    <div class="feature-card">
                        <span class="feature-icon">🤖</span>
                        <h3>AI-Powered Tools</h3>
                        <p>Chain multiple tools together for complex analysis workflows</p>
                    </div>
                    
                    <div class="feature-card">
                        <span class="feature-icon">📊</span>
                        <h3>Real-time Progress</h3>
                        <p>Track async jobs with live progress updates</p>
                    </div>
                </div>
            </section>
            
            <!-- MCP Tools Section -->
            <section class="tools-section" id="tools">
                <h2>Available MCP Tools</h2>
                <div class="tools-grid">
                    <!-- Web Crawling Tools -->
                    <div class="tool-category">
                        <h3>🌐 Web Crawling</h3>
                        <ul class="tool-list">
                            <li>crawl_webpage_with_smart_execution</li>
                            <li>crawl_website_with_depth_control</li>
                            <li>check_crawl_job_status</li>
                            <li>search_previous_crawl_results</li>
                        </ul>
                    </div>
                    
                    <!-- Content Processing Tools -->
                    <div class="tool-category">
                        <h3>📝 Content Processing</h3>
                        <ul class="tool-list">
                            <li>extract_structured_data_with_schema</li>
                            <li>convert_html_to_clean_markdown</li>
                            <li>analyze_content_sentiment_and_entities</li>
                            <li>summarize_long_text_intelligently</li>
                        </ul>
                    </div>
                    
                    <!-- Analysis Tools -->
                    <div class="tool-category">
                        <h3>🔍 Analysis</h3>
                        <ul class="tool-list">
                            <li>analyze_website_structure</li>
                            <li>extract_key_information_points</li>
                            <li>classify_content_by_topic</li>
                            <li>generate_comprehensive_report</li>
                        </ul>
                    </div>
                </div>
            </section>
        </main>

        <!-- Footer -->
        <footer class="app-footer">
            <p>Gnosis Wraith V2 - Built for Claude Desktop Integration</p>
            <p class="footer-links">
                <a href="/api/v2/docs">API Docs</a> |
                <a href="https://github.com/gnosis-wraith">GitHub</a> |
                <a href="/about">About</a>
            </p>
        </footer>
    </div>

    <!-- JavaScript -->
    <script src="/static/js/components/v2-api-client.js"></script>
    <script src="/static/js/components/crawl-interface-v2.js"></script>
    
    <!-- Initialize -->
    <script>
        // Check for Claude Desktop
        if (window.claude) {
            console.log('Running in Claude Desktop environment');
            document.body.classList.add('claude-desktop');
        }
        
        // Initialize app
        document.addEventListener('DOMContentLoaded', () => {
            console.log('Gnosis Wraith V2 initialized');
        });
    </script>
</body>
</html>
```

## 4.2 Claude Desktop Integration

### File: `claude-desktop-config.json` (NEW)

Configuration for Claude Desktop:

```json
{
    "name": "Gnosis Wraith",
    "version": "2.0.0",
    "description": "Intelligent web crawler with AI-powered analysis",
    "homepage": "http://localhost:5000/v2",
    "features": {
        "tools": true,
        "workflows": true,
        "persistent_sessions": true
    },
    "tools": [
        {
            "name": "crawl_webpage_with_smart_execution",
            "category": "web_crawling",
            "description": "Intelligently crawl webpages with automatic sync/async execution"
        },
        {
            "name": "analyze_website_structure",
            "category": "analysis",
            "description": "Analyze and understand website architecture"
        },
        {
            "name": "extract_structured_data_with_schema",
            "category": "content_processing",
            "description": "Extract data using custom schemas"
        }
    ],
    "workflows": [
        {
            "name": "analyze_website",
            "description": "Complete website analysis workflow",
            "steps": ["crawl", "analyze", "extract", "summarize"]
        },
        {
            "name": "monitor_changes",
            "description": "Monitor websites for changes",
            "steps": ["crawl", "compare", "alert"]
        }
    ],
    "ui_preferences": {
        "theme": "auto",
        "compact_mode": false,
        "show_tool_hints": true
    }
}
```

## 4.3 Testing UI Updates

### File: `tests/test_ui_v2.py`

UI testing suite:

```python
"""
UI tests for V2 interface.
"""

from playwright.sync_api import sync_playwright
import pytest

class TestV2UI:
    """Test V2 UI components."""
    
    @pytest.fixture
    def browser_page(self):
        """Create browser page for testing."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            yield page
            browser.close()
    
    def test_crawl_interface_loads(self, browser_page):
        """Test that V2 interface loads correctly."""
        page = browser_page
        page.goto("http://localhost:5000/v2")
        
        # Check main elements exist
        assert page.query_selector("crawl-interface-v2")
        assert page.query_selector("#crawl-url")
        assert page.query_selector("#crawl-btn")
    
    def test_smart_mode_updates(self, browser_page):
        """Test smart mode indicator updates."""
        page = browser_page
        page.goto("http://localhost:5000/v2")
        
        # Check initial mode
        mode = page.query_selector("#execution-mode")
        assert "Auto-detect" in mode.inner_text()
        
        # Enable JavaScript option
        page.click("#opt-javascript")
        
        # Mode should update
        page.wait_for_timeout(100)
        assert "Async" in mode.inner_text() or "Sync" in mode.inner_text()
    
    def test_job_progress_display(self, browser_page):
        """Test job progress display."""
        page = browser_page
        page.goto("http://localhost:5000/v2")
        
        # Enter URL and enable complex options
        page.fill("#crawl-url", "https://example.com")
        page.click("#opt-javascript")
        page.click("#opt-screenshot")
        
        # Start crawl
        page.click("#crawl-btn")
        
        # Should show active jobs section
        page.wait_for_selector("#active-jobs", state="visible", timeout=5000)
        
        # Check job item exists
        assert page.query_selector(".job-item")
    
    def test_workflow_buttons(self, browser_page):
        """Test workflow quick action buttons."""
        page = browser_page
        page.goto("http://localhost:5000/v2")
        
        # Check workflow buttons exist
        assert page.query_selector("[data-workflow='analyze_website']")
        assert page.query_selector("[data-workflow='monitor_changes']")
        assert page.query_selector("[data-workflow='extract_data']")
        
        # Click analyze workflow
        page.fill("#crawl-url", "https://example.com")
        page.click("[data-workflow='analyze_website']")
        
        # Should trigger workflow
        page.wait_for_selector(".workflow-results", timeout=10000)
```

## Deliverables

1. **V2 API Client** with smart sync/async handling
2. **Enhanced UI Components**:
   - Smart crawl interface
   - Job progress tracking
   - Session management
   - Workflow execution
3. **Modern CSS** with dark mode support
4. **Claude Desktop configuration**
5. **UI test suite** using Playwright

## Success Criteria

- [ ] UI automatically detects sync vs async mode
- [ ] Job progress updates in real-time
- [ ] Session persistence is visible and manageable
- [ ] Workflows execute with single click
- [ ] Claude Desktop integration works seamlessly
- [ ] UI is responsive and works on mobile
- [ ] Dark mode works properly
- [ ] All tests pass

## Implementation Notes

1. **Progressive Enhancement**: UI works without JavaScript but is enhanced with it
2. **Real-time Updates**: Use WebSockets or SSE for job progress if needed
3. **Error Handling**: Clear error messages with actionable solutions
4. **Performance**: Lazy load components as needed
5. **Accessibility**: Follow WCAG guidelines

## Next Steps

After Phase 4 completion:
- Deploy to production
- Create user documentation
- Set up monitoring and analytics
- Gather user feedback for v2.1
/**
 * Gnosis Wraith Main Application
 * This is the main React application that orchestrates all components
 */

// React hooks are globally available from the React import in the HTML
const { useState, useEffect, useRef } = React;

const GnosisWraithInterface = () => {
  // Authentication state - Since we're on /crawl, user is already authenticated via @login_required
  const [authStatus, setAuthStatus] = useState('authorized');
  const [inputValue, setInputValue] = useState('');
  
  // System status state
  const [systemStatus, setSystemStatus] = useState('initializing');
  const [healthCheckInterval, setHealthCheckInterval] = useState(null);
  
  // Logs state
  const [logs, setLogs] = useState([]);
  
  // Crawl statistics
  const [crawlStats, setCrawlStats] = useState({
    total: 0,
    success: 0,
    errors: 0,
    lastUrl: ''
  });
  
  // URL history state
  const [urlHistory, setUrlHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  
  // Settings state
  const [reportFormat, setReportFormat] = useState('md'); // Default to Markdown
  const [forceJavascript, setForceJavascript] = useState(false); // Force JavaScript toggle
  const [screenshotMode, setScreenshotMode] = useState('full'); // Default to full screenshots
  const [markdownQuality, setMarkdownQuality] = useState('enhanced'); // Default to enhanced markdown
  const [customReportName, setCustomReportName] = useState(''); // Custom report name
  const [reportNamesEnabled, setReportNamesEnabled] = useState(true); // Report names toggle
  const [ocrEnabled, setOcrEnabled] = useState(false); // OCR extraction toggle
  
  // References for scrolling and sizing
  const logsEndRef = useRef(null);
  const logContainerRef = useRef(null);
  const rootContainerRef = useRef(null);
  
  // State for recent reports
  const [recentReports, setRecentReports] = useState([]);
  const [loadingRecentReports, setLoadingRecentReports] = useState(false);
  
  // State to track log container visibility
  const [logContainerVisible, setLogContainerVisible] = useState(false);
  
  // State to track user scrolling and auto-scrolling settings
  const [isUserScrolling, setIsUserScrolling] = useState(false);
  const [shouldScrollToBottom, setShouldScrollToBottom] = useState(true);
  
  // Log filter and order state
  const [logFilter, setLogFilter] = useState('');
  const [logFilterMode, setLogFilterMode] = useState('include');
  const [logOrder, setLogOrder] = useState('newest');
  
  // Crawling state for button spinner
  const [isCrawling, setIsCrawling] = useState(false);
  
  // Floating ghost buddy state
  const [ghostVisible, setGhostVisible] = useState(false);
  const [ghostPhase, setGhostPhase] = useState('popping'); // 'popping', 'wiggling', 'shrinking', 'gone'
  
  // Profile modal state
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [isTokenModalOpen, setIsTokenModalOpen] = useState(false);
  
  // Initialize the application
  useEffect(() => {
    // Check if a valid auth code exists in localStorage or cookies
    let storedAuthCode = localStorage.getItem('gnosis_auth_code');
    
    // If not in localStorage, check cookies
    if (!storedAuthCode) {
      storedAuthCode = CookieUtils.getCookie('gnosis_auth_code');
    }
    
    // Removed c0d3z pattern check - authentication now handled differently

    
    // Load URL history from localStorage
    try {
      const storedHistory = localStorage.getItem('gnosis_url_history');
      if (storedHistory) {
        setUrlHistory(JSON.parse(storedHistory));
      }
    } catch (e) {
      console.error('Error loading URL history:', e);
    }
    
    // Load report format preference from localStorage
    try {
      const storedFormat = localStorage.getItem('gnosis_report_format');
      if (storedFormat && ['md', 'html', 'png'].includes(storedFormat)) {
        setReportFormat(storedFormat);
      }
    } catch (e) {
      console.error('Error loading report format preference:', e);
    }
    
    // Load force JavaScript preference from localStorage
    try {
      const storedForceJs = localStorage.getItem('gnosis_force_javascript');
      if (storedForceJs === 'true') {
        setForceJavascript(true);
      }
    } catch (e) {
      console.error('Error loading force JavaScript preference:', e);
    }
    
    // Load screenshot mode preference from localStorage
    try {
      const storedScreenshotMode = localStorage.getItem('gnosis_screenshot_mode');
      if (storedScreenshotMode && ['off', 'top', 'full'].includes(storedScreenshotMode)) {
        setScreenshotMode(storedScreenshotMode);
      }
    } catch (e) {
      console.error('Error loading screenshot mode preference:', e);
    }
    
    // Load markdown quality preference from localStorage
    try {
      const storedMarkdownQuality = localStorage.getItem('gnosis_markdown_quality');
      if (storedMarkdownQuality && ['enhanced', 'basic', 'none'].includes(storedMarkdownQuality)) {
        setMarkdownQuality(storedMarkdownQuality);
      }
    } catch (e) {
      console.error('Error loading markdown quality preference:', e);
    }
    
    // Load report names enabled preference from localStorage
    try {
      const storedReportNamesEnabled = localStorage.getItem('gnosis_report_names_enabled');
      if (storedReportNamesEnabled !== null) {
        setReportNamesEnabled(JSON.parse(storedReportNamesEnabled));
      }
    } catch (e) {
      console.error('Error loading report names enabled preference:', e);
    }
    
    // Load OCR enabled preference from localStorage
    try {
      const storedOcrEnabled = localStorage.getItem('gnosis_ocr_enabled');
      if (storedOcrEnabled !== null) {
        setOcrEnabled(JSON.parse(storedOcrEnabled));
      }
    } catch (e) {
      console.error('Error loading OCR enabled preference:', e);
    }
    
    // Set log container visibility to true by default
    setLogContainerVisible(true);
    
    // Start health checking immediately
    checkServerHealth();
    
    // Set up periodic health checks every 30 seconds
    const interval = setInterval(checkServerHealth, 30000);
    setHealthCheckInterval(interval);
    
    // Simulate system initialization
    setTimeout(() => {
      addLog('System initialization complete');
      addLog('Gnosis Wraith v3.2.7 ready');
      
      // Check localStorage directly instead of relying on authStatus state
      const storedAuthCode = localStorage.getItem('gnosis_auth_code');
      // Removed c0d3z authentication check
      addLog('System ready');

      
      // Load stored crawl stats if they exist
      const storedStats = localStorage.getItem('gnosis_crawl_stats');
      if (storedStats) {
        try {
          const stats = JSON.parse(storedStats);
          // Ensure we have the lastUrl property
          if (!stats.hasOwnProperty('lastUrl')) {
            stats.lastUrl = '';
          }
          setCrawlStats(stats);
          addLog(`Loaded previous session statistics: ${stats.total} crawls`);
        } catch (e) {
          console.error('Error parsing stored crawl stats:', e);
        }
      }
    }, 1500);
    
    // Cleanup interval on unmount
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, []);
  
  // Update local storage when crawl stats change
  useEffect(() => {
    // Skip initial render
    if (crawlStats.total > 0) {
      localStorage.setItem('gnosis_crawl_stats', JSON.stringify(crawlStats));
    }
  }, [crawlStats]);
  
  // Simplified auto-scroll logs to bottom when new logs are added
  useEffect(() => {
    // Only auto-scroll when showing newest first and we're at or near the bottom
    if (logs.length > 0 && 
        logContainerRef && logContainerRef.current && 
        logContainerVisible && 
        logOrder === 'newest' &&
        shouldScrollToBottom &&
        !isUserScrolling) {
      
      const container = logContainerRef.current;
      // Use container.scrollTo instead of scrollIntoView to keep scroll contained
      container.scrollTo({
        top: container.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [logs, logContainerVisible, shouldScrollToBottom, logOrder, isUserScrolling]);
  
  // Handle scroll events in the log container to detect position
  useEffect(() => {
    const handleScroll = (e) => {
      // Stop event propagation to prevent page scrolling
      e.stopPropagation();
      
      const container = e.target;
      if (container === logContainerRef.current) {
        // Calculate if we're near the bottom (within 50px)
        const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 50;
        setShouldScrollToBottom(isNearBottom);
        
        // Detect if user is actively scrolling
        setIsUserScrolling(true);
        
        // Clear the user scrolling flag after a delay
        clearTimeout(window.scrollTimeout);
        window.scrollTimeout = setTimeout(() => {
          setIsUserScrolling(false);
        }, 150);
      }
    };
    
    // Add scroll event listener to the log container only
    const logContainer = logContainerRef.current;
    if (logContainer) {
      logContainer.addEventListener('scroll', handleScroll, { passive: false });
    }
    
    return () => {
      // Clean up event listener and timeout
      if (logContainer) {
        logContainer.removeEventListener('scroll', handleScroll);
      }
      if (window.scrollTimeout) {
        clearTimeout(window.scrollTimeout);
      }
    };
  }, []);
  
  // CRT flicker effect
  useEffect(() => {
    const flickerInterval = setInterval(() => {
      if (Math.random() < 0.1) { // 10% chance every interval
        const crtElement = logContainerRef.current;
        if (crtElement) {
          crtElement.classList.add('active');
          setTimeout(() => {
            crtElement.classList.remove('active');
          }, 100);
        }
      }
    }, 2000);
    
    return () => clearInterval(flickerInterval);
  }, []);
  
  // Simple height calculation that fills available space
  useEffect(() => {
    const calculateHeight = () => {
      if (logContainerRef.current && rootContainerRef.current) {
        const viewportHeight = window.innerHeight;
        const logContainer = logContainerRef.current;
        const logRect = logContainer.getBoundingClientRect();
        
        // Calculate available height from current position to bottom of viewport
        const availableHeight = viewportHeight - logRect.top - 20; // 20px bottom margin
        
        // Set minimum height
        const finalHeight = Math.max(300, availableHeight);
        
        // Apply the height
        logContainer.style.height = `${finalHeight}px`;
        logContainer.style.visibility = 'visible';
        setLogContainerVisible(true);
      }
    };
    
    // Initial calculation
    const timer = setTimeout(calculateHeight, 100);
    
    // Handle window resize
    const handleResize = () => {
      calculateHeight();
    };
    
    window.addEventListener('resize', handleResize);
    
    return () => {
      clearTimeout(timer);
      window.removeEventListener('resize', handleResize);
    };
  }, []); // Run once on mount
  
  // Floating Ghost Buddy Animation System 👻
  useEffect(() => {
    const startGhostCycle = () => {
      // Random delay before ghost appears (5-45 minutes)
      // Weighted towards longer times - using exponential distribution
      const minMinutes = 5;
      const maxMinutes = 45;
      
      // Generate a random number with exponential distribution (favoring higher values)
      const random = Math.random();
      const exponentialRandom = 1 - Math.exp(-2 * random); // Exponential distribution
      const delayMinutes = minMinutes + (maxMinutes - minMinutes) * exponentialRandom;
      const appearDelay = delayMinutes * 60 * 1000; // Convert to milliseconds
      
      console.log(`Ghost will appear in ${Math.round(delayMinutes)} minutes`);
      
      setTimeout(() => {
        // POP! Ghost appears
        setGhostVisible(true);
        setGhostPhase('popping');
        
        // After popping in, start wiggling
        setTimeout(() => {
          setGhostPhase('wiggling');
          
          // Wiggle and grow/shrink for random time (4-8 seconds)
          const wiggleTime = Math.random() * 4000 + 4000;
          
          setTimeout(() => {
            // Start shrinking phase
            setGhostPhase('shrinking');
            
            // After shrinking, POP away
            setTimeout(() => {
              setGhostVisible(false);
              setGhostPhase('gone');
              
              // Wait a bit then start the cycle again
              setTimeout(startGhostCycle, 5000); // Short delay before calculating next appearance
            }, 800); // shrinking animation duration
          }, wiggleTime);
        }, 600); // popping animation duration
      }, appearDelay);
    };
    
    // Start the ghost cycle after component mounts with initial delay of 2-5 minutes
    const initialDelay = (Math.random() * 3 + 2) * 60 * 1000; // 2-5 minutes for first appearance
    const initialTimer = setTimeout(startGhostCycle, initialDelay);
    
    return () => {
      clearTimeout(initialTimer);
    };
  }, []);
  
  // Store URL history in local storage
  const updateUrlHistory = (url) => {
    // Get existing history or initialize empty array
    let history = [];
    try {
      const storedHistory = localStorage.getItem('gnosis_url_history');
      if (storedHistory) {
        history = JSON.parse(storedHistory);
      }
    } catch (e) {
      console.error('Error parsing URL history:', e);
    }
    
    // Add new URL to history if not a duplicate of the most recent
    if (url && url.trim() && (history.length === 0 || history[0] !== url)) {
      history.unshift(url); // Add to beginning
      history = history.slice(0, 10); // Keep only 10 most recent
      localStorage.setItem('gnosis_url_history', JSON.stringify(history));
    }
    
    return history;
  };
  
  // Function to check server health
  const checkServerHealth = async () => {
    const previousStatus = systemStatus;
    
    try {
      const response = await fetch('/health', {
        method: 'HEAD',
        cache: 'no-cache'
      });
      
      if (response.ok) {
        if (systemStatus !== 'online') {
          setSystemStatus('online');
          console.log('🟢 Health Check: Server is ONLINE (HEAD /health returned 200)');
          
          // If we were offline and now we're online, refresh the page
          if (previousStatus === 'offline') {
            addLog('🔄 Server back online - refreshing page in 2 seconds...');
            setTimeout(() => {
              window.location.reload();
            }, 2000);
          }
        }
      } else {
        if (systemStatus !== 'degraded') {
          setSystemStatus('degraded');
          const statusExplanation = getHttpStatusExplanation(response.status);
          console.log(`🟡 Health Check: Server is DEGRADED (HEAD /health returned ${response.status} - ${statusExplanation})`);
          addLog(`Server health check failed: HTTP ${response.status} - ${statusExplanation}`);
        }
      }
    } catch (error) {
      if (systemStatus !== 'offline') {
        setSystemStatus('offline');
        console.log(`🔴 Health Check: Server is OFFLINE (HEAD /health failed - ${error.message})`);
        addLog(`Server health check failed: ${error.message}`);
        addLog('🔍 Monitoring for server recovery...');
      }
    }
  };
  
  // Function to add a log entry
  const addLog = (message) => {
    // Ensure unique IDs even if logs are added in the same millisecond
    const uniqueId = Date.now() + Math.random().toString(36).substr(2, 5);
    
    // Check if the message already contains HTML
    const containsHtml = message.includes('<a') || message.includes('<span') || message.includes('<div');
    
    // If the message doesn't already contain HTML, check for URLs and make them clickable
    let processedMessage = message;
    if (!containsHtml) {
      // Regex to match URLs
      const urlRegex = /(https?:\/\/[^\s<>"']+)/g;
      processedMessage = message.replace(urlRegex, url => {
        // Skip if it's already in an HTML tag or looks like one
        if (url.includes('<') || url.includes('>')) return url;
        return `<a href="${url}" target="_blank" class="text-blue-400 hover:underline break-words">${url}</a>`;
      });
    }
    
    // Generate a formatted timestamp with microseconds in Z time
    const now = new Date();
    const pad = (num, size) => String(num).padStart(size, '0');
    const timestamp = `${now.getUTCFullYear()}-${pad(now.getUTCMonth() + 1, 2)}-${pad(now.getUTCDate(), 2)}T${pad(now.getUTCHours(), 2)}:${pad(now.getUTCMinutes(), 2)}:${pad(now.getUTCSeconds(), 2)}.${pad(now.getUTCMilliseconds(), 3)}Z`;
    
    // Subtle color change based on hour of day - create a gentle color cycle
    const hourFraction = (now.getHours() * 60 + now.getMinutes()) / (24 * 60);
    const hue = Math.floor(hourFraction * 360); // Full color cycle through the day
    const timestampColor = `hsl(${hue}, 85%, 65%)`; // Brighter, more pastel colors
    const timestampBgColor = `hsl(${hue}, 50%, 25%)`; // Lighter background with moderate saturation
    
    // Create an object with isHtml flag if the message contains HTML
    const logEntry = {
      id: uniqueId,
      message: processedMessage,
      timestamp,
      timestampColor,
      timestampBgColor,
      isHtml: containsHtml || processedMessage !== message // True if original contained HTML or we added HTML
    };
    
    setLogs(prevLogs => {
      // Keep only the last 100 logs for performance
      const newLogs = [...prevLogs, logEntry];
      return newLogs.slice(-100);
    });
  };
  
  // Function to update crawl statistics
  const updateCrawlStats = (success = true) => {
    setCrawlStats(prev => ({
      ...prev,
      total: prev.total + 1,
      success: prev.success + (success ? 1 : 0),
      errors: prev.errors + (success ? 0 : 1)
    }));
    
    // Track last error timestamp for factory safety humor
    if (!success) {
      localStorage.setItem('gnosis_last_error_timestamp', Date.now().toString());
    }
    
    // Refresh recent reports when stats change
    // Add a delay to ensure the server has finished writing the report
    setTimeout(() => {
      fetchRecentReports();
    }, 2000); // 2 second delay
  };
  
  // Function to handle authentication
  const handleAuthenticate = () => {
    // Using the AuthenticationComponent's logic
    window.AuthenticationComponent({
      authStatus,
      setAuthStatus,
      inputValue,
      setInputValue,
      addLog
    }).handleAuthenticate();
  };
  
  // Handle logout from CrawlerInput  
  const handleLogout = () => {
    localStorage.removeItem('gnosis_auth_code');
    localStorage.removeItem('authStatus');
    CookieUtils.deleteCookie('gnosis_auth_code');
    setAuthStatus('unauthorized');
    window.location.reload();
  };
  
  // Function to handle search (crawling)
  const handleSearch = async () => {
    if (inputValue.trim()) {
      // Double-check to prevent race conditions
      if (isCrawling) {
        console.warn('Crawl already in progress, ignoring duplicate request');
        return;
      }
      
      setIsCrawling(true); // Start spinner
      
      // Store the query or URL
      let queryUrl = inputValue.trim();
      
      // Add to URL history and update state
      const updatedHistory = updateUrlHistory(queryUrl);
      setUrlHistory(updatedHistory);
      
      // Update last URL in stats
      setCrawlStats(prev => ({
        ...prev,
        lastUrl: queryUrl
      }));
      
      addLog(`Initiating crawl sequence for: ${queryUrl}`);
      
      try {
        // Just a simple logging message without implying conversion
        addLog(`Processing input: ${queryUrl}`);
        
        // Log crawl attempt to server
        try {
          const logData = {
            query: queryUrl,
            auth_code: localStorage.getItem('gnosis_auth_code') || 'none',
            timestamp: new Date().toISOString(),
            event: 'crawl_attempt'
          };
          
          // Send the log to server
          const logResponse = await fetch('/api/log', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(logData)
          });
          
          if (logResponse.ok) {
            addLog(`Event logged: crawl_attempt`);
          }
        } catch (logError) {
          console.error('Error logging to server:', logError);
        }
        
        addLog('Dispatching ethereal agents...');
        
        // Smart URL detection: Skip suggestion API for clean URLs
        let shouldCallSuggestAPI = false;
        let reasonToSkip = '';
        
        // Check if it's a clean URL without additional text
        if (queryUrl.match(/^https?:\/\/[^\s]+$/) && !queryUrl.includes(' ')) {
          // It's a clean URL with no spaces - skip suggestion
          reasonToSkip = 'Clean URL detected - skipping suggestion API';
          shouldCallSuggestAPI = false;
        } else if (!queryUrl.startsWith('http')) {
          // No http/https protocol - might need URL extraction
          reasonToSkip = 'No protocol detected - using suggestion API';
          shouldCallSuggestAPI = true;
        } else if (queryUrl.includes(' ') && queryUrl.match(/https?:\/\/[^\s]+/)) {
          // Has spaces AND contains a URL - likely natural language with URL context
          reasonToSkip = 'Natural language with URL context - using suggestion API';
          shouldCallSuggestAPI = true;
        } else {
          // Default to using suggestion API for other cases
          reasonToSkip = 'Ambiguous input - using suggestion API';
          shouldCallSuggestAPI = true;
        }
        
        addLog(`🧠 ${reasonToSkip}`);
        
        if (shouldCallSuggestAPI) {
          // Call the suggestion API for complex queries
          try {
          // Get the selected provider and corresponding API key from cookies
          const provider = localStorage.getItem('gnosis_wraith_llm_provider') || 'anthropic';
          
          // Get the API key for the selected provider
          let apiKey = '';
          let cookieName = '';
          
          switch(provider) {
            case 'anthropic':
              cookieName = 'gnosis_wraith_llm_token_anthropic';
              break;
            case 'openai':
              cookieName = 'gnosis_wraith_llm_token_openai';
              break;
            case 'gemini':
              cookieName = 'gnosis_wraith_llm_token_gemini';
              break;
            default:
              cookieName = 'gnosis_wraith_llm_token_anthropic';
          }
          
          apiKey = CookieUtils.getCookie(cookieName);
          
          // Log the request before making it
          addLog(`<div class="api-request px-2 py-1 bg-gray-900 rounded border-l-2 border-blue-500 inline-block">
            <span class="text-blue-400 font-mono font-semibold">POST</span>
            <span class="text-gray-400 font-mono">/api/suggest</span>
            <span class="text-yellow-400 font-mono ml-2 px-1.5 py-0.5 bg-yellow-900 bg-opacity-30 rounded">SENDING</span>
          </div>`);
          
          const suggestResponse = await fetch('/api/suggest', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
              query: queryUrl,
              provider: provider,
              api_key: apiKey || null // Send the user's API key if available
            })
          });
          
          // Log the response status immediately after receiving it
          const statusColor = suggestResponse.ok ? 'text-green-400' : 'text-red-400';
          const statusBg = suggestResponse.ok ? 'bg-green-900' : 'bg-red-900';
          addLog(`<div class="api-request px-2 py-1 bg-gray-900 rounded border-l-2 border-blue-500 inline-block">
            <span class="text-blue-400 font-mono font-semibold">POST</span>
            <span class="text-gray-400 font-mono">/api/suggest</span>
            <span class="${statusColor} font-mono ml-2 px-1.5 py-0.5 ${statusBg} bg-opacity-30 rounded">${suggestResponse.status} ${suggestResponse.statusText}</span>
          </div>`);
          
          let retryCount = 0;
          const maxRetries = 2;
          let suggestSuccess = false;
          
          while (retryCount <= maxRetries && !suggestSuccess) {
            try {
              if (retryCount > 0) {
                addLog(`Retrying URL suggestion (attempt ${retryCount + 1})...`);
              }
              
              if (suggestResponse.ok) {
                const suggestResult = await suggestResponse.json();
                
                // Format and display JSON with syntax highlighting and collapsible structure
                const jsonStr = JSON.stringify(suggestResult, null, 2);
                const formattedJson = formatJsonForDisplay(jsonStr);
                
                // Determine styling based on success/error status
                const isError = suggestResult.success === false;
                const borderColor = isError ? 'border-red-500' : 'border-purple-500';
                const bgColor = isError ? 'bg-red-900 bg-opacity-20' : 'bg-gray-900';
                const statusIcon = isError ? '<i class="fas fa-exclamation-triangle text-red-400 mr-1"></i>' : '';
                const statusText = isError ? 'ERROR' : 'SUCCESS';
                const statusColor = isError ? 'text-red-400' : 'text-purple-400';
                
                addLog(`<div class="json-container ${bgColor} rounded p-2 my-1 border-l-2 ${borderColor} break-words">
                  <div class="flex justify-between items-center mb-1">
                    <div class="flex items-center">
                      ${statusIcon}<span class="text-xs ${statusColor} font-semibold mr-2">${statusText}</span>
                      <button class="text-xs text-gray-400 hover:text-gray-300 px-2 py-0.5 bg-gray-800 rounded toggle-json" onclick="event.preventDefault(); toggleJsonVisibility(this); return false;">
                        <i class="fas fa-chevron-down"></i> <span>Collapse</span>
                      </button>
                    </div>
                    <button class="text-xs text-gray-400 hover:text-gray-300 px-2 py-0.5 bg-gray-800 rounded copy-json" onclick="event.preventDefault(); copyJsonToClipboard(this, '${jsonStr.replace(/'/g, "\\'")}'); return false;" title="Copy JSON">
                      <i class="fas fa-copy"></i> <span>Copy</span>
                    </button>
                  </div>
                  <div class="json-content text-xs font-mono">${formattedJson}</div>
                </div>`);

                if (suggestResult.success && suggestResult.suggested_url) {
                  // Read javascript_recommended and settle time from the API response
                  const jsRecommended = suggestResult.javascript_recommended === true;
                  const settleTime = suggestResult.javascript_settle_time_ms || 0;
                  
                  // Store the recommendations for later use in the crawl
                  window.javascriptRecommended = jsRecommended;
                  window.javascriptSettleTime = settleTime;
                  
                  if (jsRecommended) {
                    addLog(`JavaScript recommended for this URL.`);
                    if (settleTime > 0) {
                      addLog(`Recommended settle time: ${settleTime}ms for dynamic content loading.`);
                    }
                  }
                  
                  // Display crawling notes if present
                  if (suggestResult.crawling_notes) {
                    addLog(`📝 Crawling notes: ${suggestResult.crawling_notes}`);
                  }
                  
                  // Function to use URL in crawler input
                  const useUrlInCrawler = (url) => {
                    // Use React state instead of DOM manipulation for more reliable behavior
                    setInputValue(url);
                    setShowHistory(false);
                    
                    // Schedule a focus on the input field after state update
                    setTimeout(() => {
                      const inputField = document.querySelector('input[placeholder="Enter URL or summon phrase..."]');
                      if (inputField) {
                        inputField.focus();
                      }
                    }, 50);
                  };
                  
                  // Make this function accessible in window scope
                  window.useUrlInCrawler = useUrlInCrawler;
                  
                  addLog(`<a href="#" class="text-green-400 hover:text-green-300 hover:underline ml-2" title="Use this URL" onclick="event.preventDefault(); event.stopPropagation(); window.useUrlInCrawler('${suggestResult.suggested_url.replace(/'/g, "\\'")}'); return false;"><i class="fas fa-level-up-alt mr-1"></i>Use this URL</a>`);
                  
                  // Only show the log if the URL actually changed
                  if (suggestResult.suggested_url !== queryUrl) {
                    addLog(`<div class="log-url-info"><span class="text-yellow-400 font-semibold">Translated to URL:</span> <span class="text-green-300">${suggestResult.suggested_url}</span> <a href="#" class="text-green-400 hover:text-green-300 hover:underline ml-2" title="Use this URL" onclick="event.preventDefault(); event.stopPropagation(); window.useUrlInCrawler('${suggestResult.suggested_url.replace(/'/g, "\\'")}'); return false;"><i class="fas fa-level-up-alt mr-1"></i>Use this URL</a></div>`);
                  } else {
                    addLog(`<div class="log-url-info"><span class="text-blue-400 font-semibold">URL confirmed:</span> <span class="text-green-300">${suggestResult.suggested_url}</span> <a href="#" class="text-green-400 hover:text-green-300 hover:underline ml-2" title="Use this URL" onclick="event.preventDefault(); event.stopPropagation(); window.useUrlInCrawler('${suggestResult.suggested_url.replace(/'/g, "\\'")}'); return false;"><i class="fas fa-level-up-alt mr-1"></i>Use this URL</a></div>`);
                  }
                  // Update the query to the suggested URL
                  queryUrl = suggestResult.suggested_url;
                  suggestSuccess = true;
                } else {
                  addLog(`Suggestion API response received but no URL suggested.`);
                  suggestSuccess = true;
                }
              } else {
                if (retryCount === maxRetries) {
                  // Create a visually distinctive error message
                  addLog(`<div class="bg-red-900 bg-opacity-30 border border-red-700 rounded px-3 py-2 my-2">
                    <div class="flex items-center">
                      <span class="text-red-500 mr-2"><i class="fas fa-exclamation-circle"></i></span>
                      <span class="text-red-400 font-semibold">API suggest failed (${suggestResponse.status})</span>
                    </div>
                    <div class="mt-1 text-red-300">
                      The URL suggestion service returned an error. Using original input: ${queryUrl}
                    </div>
                  </div>`);
                }
              }
            } catch (retryError) {
              if (retryCount === maxRetries) {
                // Create a visually distinctive error message for exceptions
                addLog(`<div class="bg-red-900 bg-opacity-30 border border-red-700 rounded px-3 py-2 my-2">
                  <div class="flex items-center">
                    <span class="text-red-500 mr-2"><i class="fas fa-exclamation-circle"></i></span>
                    <span class="text-red-400 font-semibold">API Error</span>
                  </div>
                  <div class="mt-1 text-red-300">
                    Error in suggestion API: ${retryError.message}<br>
                    Using original input: ${queryUrl}
                  </div>
                </div>`);
              }
            }
            
            retryCount++;
            
            // Break if success or if we've reached max retries
            if (suggestSuccess || retryCount > maxRetries) {
              break;
            }
            
            // Wait a short time before retrying
            await new Promise(resolve => setTimeout(resolve, 500));
          }
        } catch (suggestError) {
          // Create a visually distinctive error message for the main try/catch block
          addLog(`<div class="bg-red-900 bg-opacity-30 border border-red-700 rounded px-3 py-2 my-2">
            <div class="flex items-center">
              <span class="text-red-500 mr-2"><i class="fas fa-exclamation-circle"></i></span>
              <span class="text-red-400 font-semibold">API Connection Error</span>
            </div>
            <div class="mt-1 text-red-300">
              Failed to connect to suggestion API: ${suggestError.message}<br>
              Continuing with original input: ${queryUrl}
            </div>
          </div>`);
        }
        } else {
          // Skip suggestion API for clean URLs
          addLog(`⚡ Fast-tracking clean URL - proceeding directly to crawl`);
        }
        
        // Now make the actual crawl request
        addLog(`Crawling URL: ${queryUrl}${window.javascriptRecommended ? ' with JavaScript enabled' : ''}`);
        addLog('Scanning liminal boundaries...');
        
        const crawlResponse = await fetch('/api/crawl', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            url: queryUrl,
            title: reportNamesEnabled ? (customReportName.trim() || null) : null,
            take_screenshot: screenshotMode !== 'off',
            screenshot_mode: screenshotMode, // 'off', 'top', or 'full'
            javascript_enabled: forceJavascript || window.javascriptRecommended === true, // Force JS if enabled, otherwise use API recommendation
            javascript_settle_time: window.javascriptSettleTime || 0, // Use the settle time recommendation
            ocr_extraction: ocrEnabled,
            markdown_extraction: markdownQuality, // 'enhanced', 'basic', or 'none'
            output_format: 'markdown', // Ensure reports are generated
            response_format: 'full' // Get full response including report_path
          })
        });
        
        if (crawlResponse.ok) {
          const crawlResult = await crawlResponse.json();
          if (crawlResult.success) {
            // Log successful crawl
            addLog('Crawl successful.');
            
            if (crawlResult.report_path) {
              // Create correct report path based on the selected format
              let reportPath = '';
              let reportType = '';
              
              if (reportFormat === 'md') {
                // Ensure path starts with /reports/
                reportPath = crawlResult.report_path.startsWith('/reports/') 
                  ? crawlResult.report_path 
                  : `/reports/${crawlResult.report_path.split('/').pop()}`;
                reportType = 'Markdown';
              } else if (reportFormat === 'html') {
                // Ensure HTML path points to /reports/ and has .html extension
                const baseName = crawlResult.report_path.split('/').pop().replace('.md', '.html');
                reportPath = `/reports/${baseName}`;
                reportType = 'HTML';
              } else if (reportFormat === 'png') {
                // Extract screenshot from the first result
                if (crawlResult.results && crawlResult.results[0] && crawlResult.results[0].screenshot) {
                  // Ensure screenshot path starts with /screenshots/
                  const screenshotFile = crawlResult.results[0].screenshot.split('/').pop();
                  reportPath = `/screenshots/${screenshotFile}`;
                  reportType = 'Screenshot';
                } else {
                  // Fallback to markdown report in /reports/
                  reportPath = crawlResult.report_path.startsWith('/reports/') 
                    ? crawlResult.report_path 
                    : `/reports/${crawlResult.report_path.split('/').pop()}`;
                  reportType = 'Markdown';
                  addLog(`Screenshot not available, defaulting to Markdown.`);
                }
              }
              
              addLog(`<span class="text-blue-400 font-semibold">Report generated:</span> <span class="text-gray-300">${crawlResult.report_path}</span>`);
              
              if (reportType === 'HTML') {
                addLog(`<span class="text-teal-400 font-semibold">Materializing HTML report...</span>`);
              }
              
              addLog(`<div class="report-link bg-gray-900 rounded p-2 my-1 border-l-2 border-green-500">
                <div class="flex justify-between items-center">
                  <span class="text-xs text-green-400 font-semibold mr-2">View ${reportType} Report</span>
                  <a href="${reportPath}" target="_blank" class="text-green-300 hover:text-green-200 underline break-words px-2 py-1 bg-gray-800 rounded">
                    <i class="fas fa-external-link-alt text-xs mr-1"></i>Open ${reportType}
                  </a>
                </div>
              </div>`);
            }
            
            // Log success to server and update stats
            try {
              const logData = {
                query: queryUrl, 
                report_path: crawlResult.report_path || 'none',
                html_path: crawlResult.html_path || 'none',
                timestamp: new Date().toISOString(),
                event: 'crawl_success'
              };
              
              await fetch('/api/log', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json'
                },
                body: JSON.stringify(logData)
              });
            } catch (logError) {
              console.error('Error logging success to server:', logError);
            }
            
            // Update crawl stats for success
            updateCrawlStats(true);
            
            // Emit crawl completion event for reports refresh
            window.dispatchEvent(new CustomEvent('crawlComplete', {
              detail: { 
                success: true, 
                reportPath: crawlResult.report_path,
                url: queryUrl 
              }
            }));
          } else {
            addLog(`Crawl error: ${crawlResult.error || 'Unknown error'}`);
            
            // Log error to server
            try {
              const logData = {
                query: queryUrl, 
                error: crawlResult.error || 'Unknown error',
                timestamp: new Date().toISOString(),
                event: 'crawl_error'
              };
              
              await fetch('/api/log', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json'
                },
                body: JSON.stringify(logData)
              });
            } catch (logError) {
              console.error('Error logging error to server:', logError);
            }
            
            // Update crawl stats for error
            updateCrawlStats(false);
          }
        } else {
          addLog(`Server error: ${crawlResponse.status} - ${crawlResponse.statusText}`);
          
          // Log error to server
          try {
            const logData = {
              query: queryUrl, 
              error: `${crawlResponse.status} - ${crawlResponse.statusText}`,
              timestamp: new Date().toISOString(),
              event: 'crawl_error'
            };
            
            await fetch('/api/log', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json'
              },
              body: JSON.stringify(logData)
            });
          } catch (logError) {
            console.error('Error logging error to server:', logError);
          }
          
          // Update crawl stats for error
          updateCrawlStats(false);
        }
      } catch (error) {
        addLog(`Error: ${error.message}`);
        
        // Log error to server
        try {
          const logData = {
            query: queryUrl, 
            error: error.message,
            timestamp: new Date().toISOString(),
            event: 'crawl_error'
          };
          
          await fetch('/api/log', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(logData)
          });
        } catch (logError) {
          console.error('Error logging error to server:', logError);
        }
        
        // Update crawl stats for error
        updateCrawlStats(false);
      } finally {
        // Clear input regardless of success or failure
        setInputValue('');
        setIsCrawling(false); // Stop spinner
      }
    }
  };
  
  // Fetch recent reports when authorized
  useEffect(() => {
    if (authStatus === 'authorized') {
      fetchRecentReports();
    }
  }, [authStatus]);

  // Function to handle log order changes
  const handleLogOrderChange = (newOrder) => {
    setLogOrder(newOrder);
    localStorage.setItem('gnosis_log_order', newOrder);
  };
  
  // Function to fetch recent reports (latest 5)
  const fetchRecentReports = async () => {
    try {
      setLoadingRecentReports(true);
      
      const response = await fetch('/reports?json=true');
      if (response.ok) {
        const data = await response.json();
        // Get only the 5 most recent reports
        const recent = (data.reports || []).slice(0, 5);
        setRecentReports(recent);
        console.log('Recent reports loaded:', recent.length);
      } else {
        console.error(`Failed to fetch recent reports: ${response.status}`);
        setRecentReports([]);
      }
    } catch (error) {
      console.error(`Error fetching recent reports: ${error.message}`);
      setRecentReports([]);
    } finally {
      setLoadingRecentReports(false);
    }
  };
  
  return (
    <div ref={rootContainerRef} className="h-screen bg-gray-900 text-green-400 p-4 font-mono overflow-hidden">
      <div className="w-full mx-auto flex flex-col h-full">
        <header className="mb-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center">
              <h1 className="text-2xl md:text-3xl font-bold">GNOSIS WRAITH</h1>
              {/* Floating Ghost Buddy 👻 */}
              {ghostVisible && (
                <div 
                  className={`ml-2 text-2xl ghost-buddy ${
                    ghostPhase === 'popping' ? 'scale-110' :
                    ghostPhase === 'shrinking' ? 'scale-50 opacity-50' : ''
                  }`}
                  style={{
                    animation: ghostPhase === 'popping' ? 'ghostPop 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55)' :
                              ghostPhase === 'wiggling' ? 'ghostWiggle 2s ease-in-out infinite' : 
                              ghostPhase === 'shrinking' ? 'none' : undefined
                  }}
                  onClick={() => {
                    // Easter egg: clicking ghost makes it wiggle extra!
                    if (ghostPhase === 'wiggling') {
                      const ghost = document.querySelector('.ghost-buddy');
                      if (ghost) {
                        ghost.style.animation = 'ghostWiggle 0.5s ease-in-out 3';
                        setTimeout(() => {
                          ghost.style.animation = 'ghostWiggle 2s ease-in-out infinite';
                        }, 1500);
                      }
                    }
                  }}
                  title="👻 Hey there! Click me while I'm wiggling!"
                >
                  👻
                </div>
              )}
            </div>
            <div className="flex items-center space-x-2">
              {authStatus === 'authorized' ? (
                <div className="flex items-center space-x-2">
                  <TokenStatusButton 
                    onTokenModalOpen={() => setIsTokenModalOpen(true)}
                    size="md"
                  />
                  <button
                    onClick={() => setIsProfileModalOpen(true)}
                    className="w-8 h-8 bg-gray-800 hover:bg-gray-700 border-2 border-gray-600 rounded flex items-center justify-center transition-all duration-200 hover:scale-105 active:scale-95"
                    title="Profile Settings"
                  >
                    <i className="fas fa-user-circle text-gray-400 text-base"></i>
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => document.querySelector('input[type="password"]')?.focus()}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded transition-colors"
                >
                  Login
                </button>
              )}
            </div>
          </div>
          <div className="flex items-center space-x-2 mt-2">
            <div className={`h-3 w-3 rounded-full ${
              systemStatus === 'online' ? 'bg-green-500' : 
              systemStatus === 'degraded' ? 'bg-yellow-500' :
              systemStatus === 'offline' ? 'bg-red-500' : 
              'bg-gray-500'
            }`}></div>
            <span className="text-sm uppercase">System Status: {systemStatus}</span>
            <div className="ml-auto text-xs text-gray-500">
              Press <kbd className="px-1 py-0.5 bg-gray-800 rounded border border-gray-600">Enter</kbd> to crawl
            </div>
          </div>
        </header>

        {/* Crawler input component */}
        <CrawlerInput 
          authStatus={authStatus}
          inputValue={inputValue}
          setInputValue={setInputValue}
          handleAuthenticate={handleAuthenticate}
          handleSearch={handleSearch}
          urlHistory={urlHistory}
          setUrlHistory={setUrlHistory}
          showHistory={showHistory}
          setShowHistory={setShowHistory}
          reportFormat={reportFormat}
          setReportFormat={setReportFormat}
          forceJavascript={forceJavascript}
          setForceJavascript={setForceJavascript}
          screenshotMode={screenshotMode}
          setScreenshotMode={setScreenshotMode}
          markdownQuality={markdownQuality}
          setMarkdownQuality={setMarkdownQuality}
          customReportName={customReportName}
          setCustomReportName={setCustomReportName}
          reportNamesEnabled={reportNamesEnabled}
          setReportNamesEnabled={setReportNamesEnabled}
          ocrEnabled={ocrEnabled}
          setOcrEnabled={setOcrEnabled}
          addLog={addLog}
          isCrawling={isCrawling}
          onLogout={handleLogout}
        />

        {/* Full-width dual tab interface */}
        <div className="flex-grow overflow-hidden" style={{ minHeight: '180px' }}>
          <DualTabInterface
            // Log props
            logs={logs}
            logsEndRef={logsEndRef}
            logContainerRef={logContainerRef}
            logContainerVisible={logContainerVisible}
            logOrder={logOrder}
            onLogOrderChange={handleLogOrderChange}
            logFilter={logFilter}
            setLogFilter={setLogFilter}
            logFilterMode={logFilterMode}
            setLogFilterMode={setLogFilterMode}
            
            // Reports props
            recentReports={recentReports}
            loadingRecentReports={loadingRecentReports}
            crawlStats={crawlStats}
            fetchRecentReports={fetchRecentReports}
          />
        </div>
      </div>
      
      {/* Token Manager Modal */}
      {isTokenModalOpen && (
        <TokenManagerModal
          isOpen={isTokenModalOpen}
          onClose={() => setIsTokenModalOpen(false)}
          onTokenUpdated={(provider, token) => {
            if (token) {
              addLog(`${provider} API token updated successfully`);
            } else {
              addLog(`${provider} API token cleared`);
            }
          }}
        />
      )}
      
      {/* Profile Settings Modal */}
      {isProfileModalOpen && (
        <ProfileSettingsModal
          isOpen={isProfileModalOpen}
          onClose={() => setIsProfileModalOpen(false)}
          apiToken={localStorage.getItem('gnosis_auth_code') || ''}
          userName={window.GNOSIS_CONFIG && window.GNOSIS_CONFIG.user_data && window.GNOSIS_CONFIG.user_data.name ? window.GNOSIS_CONFIG.user_data.name : null}
          onOpenTokenManager={() => {
            setIsProfileModalOpen(false);
            setIsTokenModalOpen(true);
          }}
          onLogout={() => {
            // Logout is handled by the modal itself
            setAuthStatus('unauthorized');
          }}
          onTokenGenerated={() => {
            addLog('API token generated successfully');
          }}
        />
      )}
    </div>
  );
};

// Render the application
ReactDOM.render(
  <GnosisWraithInterface />,
  document.getElementById('root')
);
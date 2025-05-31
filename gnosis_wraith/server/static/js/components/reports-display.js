/**
 * Reports Display Component
 * Handles the reports content (without container - used inside dual tab interface)
 */

const ReportsDisplay = ({
  recentReports,
  loadingRecentReports,
  crawlStats,
  fetchRecentReports,
  searchFilter = '', // External search filter from dual tab interface
  filterMode = 'include' // Filter mode: 'include' or 'exclude'
}) => {
  const [allReports, setAllReports] = React.useState([]);
  const [loadingAllReports, setLoadingAllReports] = React.useState(false);
  const [hasMoreReports, setHasMoreReports] = React.useState(true);
  const [pageOffset, setPageOffset] = React.useState(0);
  const [lastRefresh, setLastRefresh] = React.useState(Date.now());
  const [autoRefresh, setAutoRefresh] = React.useState(true);

  // Load all reports on component mount
  React.useEffect(() => {
    loadAllReports();
  }, []);

  // Auto-refresh polling when tab is active
  React.useEffect(() => {
    if (!autoRefresh) return;

    const pollInterval = setInterval(() => {
      // Only refresh if we're not already loading and the tab is visible
      if (!loadingAllReports && !document.hidden) {
        loadAllReports(0, false); // Refresh from beginning
      }
    }, 10000); // Poll every 10 seconds

    return () => clearInterval(pollInterval);
  }, [loadingAllReports, autoRefresh]);

  // Listen for crawl completion events
  React.useEffect(() => {
    const handleCrawlComplete = (event) => {
      console.log('Crawl completed, refreshing reports...');
      setTimeout(() => {
        loadAllReports(0, false); // Refresh after a short delay
        setLastRefresh(Date.now());
      }, 2000); // 2 second delay to ensure report is saved
    };

    // Listen for custom crawl completion events
    window.addEventListener('crawlComplete', handleCrawlComplete);
    
    return () => window.removeEventListener('crawlComplete', handleCrawlComplete);
  }, []);

  // Function to load all reports with pagination
  const loadAllReports = async (offset = 0, append = false) => {
    try {
      setLoadingAllReports(true);
      
      const response = await fetch(`/reports?json=true&limit=20&offset=${offset}`);
      if (response.ok) {
        const data = await response.json();
        const newReports = data.reports || [];
        
        if (append) {
          setAllReports(prev => [...prev, ...newReports]);
        } else {
          setAllReports(newReports);
        }
        
        // Check if we have more reports
        setHasMoreReports(newReports.length === 20);
        setPageOffset(offset + newReports.length);
      } else {
        console.error(`Failed to fetch reports: ${response.status}`);
      }
    } catch (error) {
      console.error(`Error fetching reports: ${error.message}`);
    } finally {
      setLoadingAllReports(false);
    }
  };

  // Infinite scroll handler
  const handleScroll = (e) => {
    const { scrollTop, scrollHeight, clientHeight } = e.target;
    const threshold = 100; // Load more when 100px from bottom
    
    if (scrollHeight - scrollTop - clientHeight < threshold && hasMoreReports && !loadingAllReports) {
      loadAllReports(pageOffset, true);
    }
  };

  // Filter reports based on search with include/exclude mode
  const filteredReports = searchFilter.trim() 
    ? allReports.filter(report => {
        const searchTerm = searchFilter.toLowerCase();
        const name = (report.name || report.filename || '').toLowerCase();
        const path = (report.path || '').toLowerCase();
        const url = (report.url || '').toLowerCase();
        const matches = name.includes(searchTerm) || path.includes(searchTerm) || url.includes(searchTerm);
        return filterMode === 'include' ? matches : !matches;
      })
    : allReports;

  return (
    <div className="h-full" onScroll={handleScroll}>
      {/* Elegant Dashboard Metrics */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {/* Total Crawls Widget */}
        <div className="bg-gradient-to-br from-blue-900/40 to-blue-800/20 backdrop-blur-sm border border-blue-500/30 rounded-lg p-4 shadow-lg hover:shadow-blue-500/20 transition-all duration-300">
          <div className="flex items-center justify-between mb-3">
            <div className="text-blue-300 text-sm font-medium tracking-wide">TOTAL CRAWLS</div>
            <div className="w-8 h-8 bg-blue-500/20 rounded-full flex items-center justify-center">
              <i className="fas fa-spider text-blue-400 text-sm"></i>
            </div>
          </div>
          <div className="text-2xl font-bold text-blue-100 mb-2 font-mono tracking-tight">
            {crawlStats.total.toLocaleString()}
          </div>
          <div className="relative h-2 bg-blue-900/50 rounded-full overflow-hidden">
            <div 
              className="absolute top-0 left-0 h-full bg-gradient-to-r from-blue-500 to-blue-400 rounded-full transition-all duration-700 ease-out"
              style={{ width: `${Math.min(100, (crawlStats.total / 100) * 100)}%` }}
            ></div>
            <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-r from-transparent via-white/10 to-transparent animate-pulse"></div>
          </div>
        </div>

        {/* Success Rate Widget */}
        <div className="bg-gradient-to-br from-green-900/40 to-green-800/20 backdrop-blur-sm border border-green-500/30 rounded-lg p-4 shadow-lg hover:shadow-green-500/20 transition-all duration-300">
          <div className="flex items-center justify-between mb-3">
            <div className="text-green-300 text-sm font-medium tracking-wide">SUCCESS RATE</div>
            <div className="w-8 h-8 bg-green-500/20 rounded-full flex items-center justify-center">
              <i className="fas fa-check-circle text-green-400 text-sm"></i>
            </div>
          </div>
          <div className="text-2xl font-bold text-green-100 mb-2 font-mono tracking-tight">
            {crawlStats.total > 0 ? Math.round((crawlStats.success / crawlStats.total) * 100) : 0}%
          </div>
          <div className="relative h-2 bg-green-900/50 rounded-full overflow-hidden">
            <div 
              className="absolute top-0 left-0 h-full bg-gradient-to-r from-green-500 to-green-400 rounded-full transition-all duration-700 ease-out"
              style={{ 
                width: `${crawlStats.total > 0 ? Math.round((crawlStats.success / crawlStats.total) * 100) : 0}%` 
              }}
            ></div>
            <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-r from-transparent via-white/10 to-transparent animate-pulse"></div>
          </div>
        </div>

        {/* Reports Count Widget */}
        <div className="bg-gradient-to-br from-purple-900/40 to-purple-800/20 backdrop-blur-sm border border-purple-500/30 rounded-lg p-4 shadow-lg hover:shadow-purple-500/20 transition-all duration-300">
          <div className="flex items-center justify-between mb-3">
            <div className="text-purple-300 text-sm font-medium tracking-wide">REPORTS</div>
            <div className="w-8 h-8 bg-purple-500/20 rounded-full flex items-center justify-center">
              <i className="fas fa-file-alt text-purple-400 text-sm"></i>
            </div>
          </div>
          <div className="text-2xl font-bold text-purple-100 mb-2 font-mono tracking-tight">
            {allReports.length.toLocaleString()}
          </div>
          <div className="relative h-2 bg-purple-900/50 rounded-full overflow-hidden">
            <div 
              className="absolute top-0 left-0 h-full bg-gradient-to-r from-purple-500 to-purple-400 rounded-full transition-all duration-700 ease-out"
              style={{ width: `${Math.min(100, (allReports.length / 50) * 100)}%` }}
            ></div>
            <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-r from-transparent via-white/10 to-transparent animate-pulse"></div>
          </div>
        </div>

        {/* Errors Widget */}
        <div className="bg-gradient-to-br from-red-900/40 to-red-800/20 backdrop-blur-sm border border-red-500/30 rounded-lg p-4 shadow-lg hover:shadow-red-500/20 transition-all duration-300">
          <div className="flex items-center justify-between mb-3">
            <div className="text-red-300 text-sm font-medium tracking-wide">ERRORS</div>
            <div className="w-8 h-8 bg-red-500/20 rounded-full flex items-center justify-center">
              <i className="fas fa-exclamation-triangle text-red-400 text-sm"></i>
            </div>
          </div>
          <div className="text-2xl font-bold text-red-100 mb-2 font-mono tracking-tight">
            {crawlStats.errors.toLocaleString()}
          </div>
          <div className="relative h-2 bg-red-900/50 rounded-full overflow-hidden">
            <div 
              className="absolute top-0 left-0 h-full bg-gradient-to-r from-red-500 to-red-400 rounded-full transition-all duration-700 ease-out"
              style={{ width: `${Math.min(100, (crawlStats.errors / 20) * 100)}%` }}
            ></div>
            <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-r from-transparent via-white/10 to-transparent animate-pulse"></div>
          </div>
        </div>
      </div>

      {/* Auto-refresh Controls */}
      <div className="flex items-center justify-between mb-4 p-3 bg-gray-900/50 border border-gray-700/50 rounded-lg">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <i className="fas fa-sync-alt text-gray-400 text-sm"></i>
            <span className="text-gray-400 text-sm">Last refresh:</span>
            <span className="text-gray-300 text-xs font-mono">
              {new Date(lastRefresh).toLocaleTimeString()}
            </span>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-2 py-1 rounded text-xs transition-colors ${
                autoRefresh 
                  ? 'bg-green-800 text-white' 
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
              title={autoRefresh ? 'Auto-refresh ON (every 10s)' : 'Auto-refresh OFF'}
            >
              <i className={`fas ${autoRefresh ? 'fa-toggle-on' : 'fa-toggle-off'} mr-1`}></i>
              Auto
            </button>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => {
              loadAllReports(0, false);
              setLastRefresh(Date.now());
            }}
            disabled={loadingAllReports}
            className="px-3 py-1 bg-blue-700 hover:bg-blue-600 disabled:bg-gray-700 disabled:opacity-50 text-white rounded text-xs transition-colors"
            title="Refresh reports now"
          >
            <i className={`fas fa-sync-alt mr-1 ${loadingAllReports ? 'fa-spin' : ''}`}></i>
            Refresh
          </button>
          
          <div className="flex items-center space-x-2 text-xs text-gray-500">
            <span>
              {filteredReports.length} report{filteredReports.length !== 1 ? 's' : ''}
            </span>
            {loadingAllReports && (
              <div className="flex items-center text-blue-400">
                <i className="fas fa-sync-alt fa-spin mr-1"></i>
                <span>Updating...</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {loadingAllReports && allReports.length === 0 ? (
        <div className="text-center py-8">
          <div className="text-gray-400">
            <i className="fas fa-spinner fa-spin mr-2"></i>
            Loading reports...
          </div>
        </div>
      ) : filteredReports.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredReports.map((report, index) => (
            <ReportCard key={index} report={report} />
          ))}
        </div>
      ) : (
        <div className="text-center py-8">
          <div className="text-gray-500">
            <i className="fas fa-folder-open text-4xl mb-4"></i>
            <div>No reports found</div>
            {searchFilter && (
              <div className="text-sm mt-2">
                Try adjusting your search filter
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* Loading more indicator */}
      {loadingAllReports && allReports.length > 0 && (
        <div className="text-center py-4">
          <div className="text-gray-400 text-sm">
            <i className="fas fa-spinner fa-spin mr-2"></i>
            Loading more reports...
          </div>
        </div>
      )}
      
      {/* End of results indicator */}
      {!hasMoreReports && filteredReports.length > 0 && (
        <div className="text-center py-4">
          <div className="text-gray-500 text-sm">
            <i className="fas fa-check mr-2"></i>
            All reports loaded
          </div>
        </div>
      )}
    </div>
  );
};

// Report Card Component - Conference Badge Style
const ReportCard = ({ report }) => {
  const [selectedFormat, setSelectedFormat] = React.useState('md');
  const [isFlipped, setIsFlipped] = React.useState(false);
  
  // Generate format options based on available formats from server
  const getFormatOptions = () => {
    const options = [];
    const hasBasePath = !!(report.path || report.name || report.filename);
    const reportFormats = report.formats || {};
    
    // Markdown - check if available from server data
    const hasMarkdown = reportFormats.markdown || hasBasePath;
    options.push({ value: 'md', label: 'Markdown', icon: 'fab fa-markdown', available: hasMarkdown });
    
    // HTML - always available if we have markdown (can be generated on-demand)
    options.push({ value: 'html', label: 'HTML', icon: 'fab fa-html5', available: hasMarkdown });
    
    // JSON - check if available from server data  
    const hasJson = reportFormats.json || hasBasePath;
    options.push({ value: 'json', label: 'JSON', icon: 'fas fa-code', available: hasJson });
    
    // Screenshot - check various sources for availability
    const hasScreenshot = !!(
      report.screenshot || 
      report.has_screenshot || 
      report.screenshot_url ||
      (report.metadata && report.metadata.screenshot) ||
      // If screenshots were enabled during crawling, assume it exists
      (hasBasePath && localStorage.getItem('gnosis_screenshot_mode') !== 'off')
    );
    options.push({ value: 'png', label: 'Screenshot', icon: 'fas fa-camera', available: hasScreenshot });
    
    return options;
  };
  
  const getReportUrl = (format) => {
    if (!report.path && !report.name && !report.filename) return '#';
    
    // Use the base path/name - now we have more reliable data structure
    const basePath = report.path || report.name || report.filename;
    if (!basePath) return '#';
    
    // Check if we have specific format files from the server
    const reportFormats = report.formats || {};
    
    switch (format) {
      case 'html':
        // For HTML, we use the base path and let the server convert from markdown on-demand
        return `/reports/${basePath.replace(/\.(md|json|png)$/, '.html')}`;
      case 'png':
        // For screenshots, use the same logic as the screenshot display
        if (report.screenshot_url) {
          return report.screenshot_url;
        } else if (report.screenshot) {
          // Check if it's already a proper web path
          if (report.screenshot.startsWith('/screenshots/') || report.screenshot.startsWith('http')) {
            return report.screenshot;
          } else if (report.screenshot.startsWith('/')) {
            return report.screenshot;
          } else {
            // Convert file path to web URL
            const filename = report.screenshot.split(/[/\\]/).pop();
            return `/screenshots/${filename}`;
          }
        } else {
          // Try to construct screenshot URL from base name
          const baseFilename = basePath.replace(/\.(md|json|html)$/, '');
          return `/screenshots/${baseFilename}.png`;
        }
      case 'json':
        // Use actual JSON filename if available, otherwise construct from base path
        if (reportFormats.json && reportFormats.json.filename) {
          return `/reports/${reportFormats.json.filename}`;  
        }
        return `/reports/${basePath.replace(/\.(md|html|png)$/, '.json')}`;
      case 'md':
      default:
        // Use actual markdown filename if available, otherwise construct from base path
        if (reportFormats.markdown && reportFormats.markdown.filename) {
          return `/reports/${reportFormats.markdown.filename}`;
        }
        return `/reports/${basePath.replace(/\.(html|json|png)$/, '.md')}`;
    }
  };

  const formatOptions = getFormatOptions();

  return (
    <div className="report-badge-container perspective-1000 h-80">
      <div className={`report-badge-inner relative w-full h-full transition-transform duration-700 preserve-3d ${isFlipped ? 'rotateY-180' : ''}`}>
        
        {/* Front of Badge */}
        <div className="report-badge-front absolute inset-0 w-full h-full backface-hidden bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-600 rounded-lg shadow-lg hover:shadow-xl transition-all duration-300">
          
          {/* Screenshot/Header Image - Made Taller */}
          <div className="badge-header relative h-48 bg-gray-700 rounded-t-lg overflow-hidden">
            {(() => {
              // Enhanced screenshot detection and URL construction
              const reportFormats = report.formats || {};
              
              // Debug logging to help troubleshoot (only log once to reduce noise)
              if (!window.debugLoggedReports) window.debugLoggedReports = new Set();
              const reportKey = `${report.name}-${report.screenshot_url || 'no-screenshot'}`;
              
              if (!window.debugLoggedReports.has(reportKey)) {
                console.log('Report screenshot debug:', {
                  report_screenshot: report.screenshot,
                  report_screenshot_url: report.screenshot_url,
                  report_formats: reportFormats,
                  report_name: report.name || report.filename
                });
                window.debugLoggedReports.add(reportKey);
              }
              
              const hasActualScreenshot = !!(
                report.screenshot_url || 
                report.screenshot ||
                (reportFormats.screenshot && reportFormats.screenshot.filename) ||
                // Also check for hash-based naming pattern used by new system
                (report.name && report.name.includes('.png'))
              );
              
              if (hasActualScreenshot) {
                // Construct screenshot URL with improved logic
                let screenshotUrl = '';
                
                if (report.screenshot_url) {
                  screenshotUrl = report.screenshot_url;
                } else if (report.screenshot) {
                  // Check if it's already a proper web path
                  if (report.screenshot.startsWith('/screenshots/') || report.screenshot.startsWith('http')) {
                    screenshotUrl = report.screenshot;
                  } else if (report.screenshot.startsWith('/')) {
                    // It's already a web path, use as-is
                    screenshotUrl = report.screenshot;
                  } else {
                    // Convert file path to web URL (handle both Unix and Windows paths)
                    const filename = report.screenshot.split(/[/\\]/).pop();
                    screenshotUrl = `/screenshots/${filename}`;
                  }
                } else if (reportFormats.screenshot && reportFormats.screenshot.filename) {
                  screenshotUrl = `/screenshots/${reportFormats.screenshot.filename}`;
                } else if (report.name && report.name.includes('.png')) {
                  // Handle case where screenshot name is in the report name
                  screenshotUrl = `/screenshots/${report.name}`;
                }
                
                if (!window.debugLoggedReports.has(reportKey)) {
                  console.log('Constructed screenshot URL:', screenshotUrl);
                  window.debugLoggedReports.add(reportKey + '-url');
                }
                
                return (
                  <>
                    <img 
                      src={screenshotUrl}
                      alt={`Screenshot of ${report.name || report.filename || 'report'}`}
                      className="w-full h-full object-cover object-top"
                      onLoad={(e) => {
                        console.log('Screenshot loaded successfully:', screenshotUrl);
                        // Show image and hide fallback
                        e.target.style.display = 'block';
                        const fallback = e.target.parentElement.querySelector('.screenshot-fallback');
                        if (fallback) fallback.style.display = 'none';
                      }}
                      onError={(e) => {
                        console.error('Screenshot failed to load:', screenshotUrl);
                        // Hide broken image and show fallback
                        e.target.style.display = 'none';
                        const fallback = e.target.parentElement.querySelector('.screenshot-fallback');
                        if (fallback) fallback.style.display = 'flex';
                      }}
                    />
                    {/* Fallback placeholder - always present but hidden by default */}
                    <div className="screenshot-fallback w-full h-full bg-gradient-to-br from-blue-900/30 to-purple-900/30 items-center justify-center flex" style={{display: 'none'}}>
                      <div className="text-center text-gray-300">
                        <i className="fas fa-image text-3xl mb-2 opacity-50"></i>
                        <div className="text-xs opacity-75">Screenshot Unavailable</div>
                        <div className="text-xs opacity-50 mt-1">({screenshotUrl})</div>
                      </div>
                    </div>
                  </>
                );
              } else {
                // Show modern conference badge style placeholder
                return (
                  <div className="w-full h-full bg-gradient-to-br from-blue-900/30 to-purple-900/30 flex items-center justify-center relative">
                    <div className="text-center text-gray-300">
                      <i className="fas fa-globe-americas text-3xl mb-2 opacity-60"></i>
                      <div className="text-xs opacity-75">Web Content</div>
                    </div>
                    {/* Corner badge design element */}
                    <div className="absolute top-2 right-2 w-6 h-6 bg-green-500/20 rounded-full flex items-center justify-center">
                      <i className="fas fa-check text-green-400 text-xs"></i>
                    </div>
                  </div>
                );
              }
            })()}
            
            {/* Title Overlay - Centered on screenshot */}
            <div className="absolute bottom-3 left-3 right-12 z-10">
              <div className="bg-black/70 backdrop-blur-sm rounded-lg px-3 py-2 border border-white/20">
                <div className="text-sm font-bold text-white leading-tight text-center">
                  {(() => {
                    const reportTitle = report.name || report.filename || 'Untitled Report';
                    
                    // Clean up hash-based filenames (e.g., splunk_com_96352fa9 -> SPLUNK.COM)
                    if (reportTitle.includes('_') && reportTitle.match(/[a-f0-9]{8,}$/)) {
                      const parts = reportTitle.split('_');
                      // Remove last part if it looks like a hash (8+ hex characters)
                      if (parts.length > 1 && parts[parts.length - 1].match(/^[a-f0-9]{8,}$/)) {
                        parts.pop(); // Remove the hash
                      }
                      // Convert to readable domain format
                      const cleanedTitle = parts.join('.').toUpperCase();
                      if (cleanedTitle.length > 45) {
                        return cleanedTitle.substring(0, 42) + '...';
                      }
                      return cleanedTitle;
                    }
                    
                    // Original truncation logic for other titles
                    if (reportTitle.length > 45) {
                      // Split long filename intelligently at underscores or hyphens
                      const parts = reportTitle.split(/[_\-]/);
                      if (parts.length > 1 && reportTitle.length > 55) {
                        // Show first few parts + last part for very long names
                        const firstParts = parts.slice(0, 2).join('_');
                        const lastPart = parts[parts.length - 1];
                        if (firstParts.length + lastPart.length + 3 <= 45) {
                          return `${firstParts}...${lastPart}`;
                        }
                      }
                      // Fallback: simple truncation
                      return reportTitle.substring(0, 42) + '...';
                    }
                    return reportTitle;
                  })()}
                </div>
              </div>
            </div>
            
            {/* Flip button - moved to top-right and made smaller */}
            <button 
              onClick={() => setIsFlipped(!isFlipped)}
              className="absolute top-3 right-3 w-6 h-6 bg-black/30 hover:bg-black/60 rounded-full flex items-center justify-center transition-all duration-200 backdrop-blur-sm border border-white/10 opacity-70 hover:opacity-100"
              title="View format options"
            >
              <i className="fas fa-cog text-white text-xs"></i>
            </button>
          </div>
          
          {/* Badge Content - Adjusted height since title moved to overlay */}
          <div className="badge-content p-4 flex flex-col h-32">>
            
            {/* Conference Badge Details - More space now */}
            <div className="flex-1 space-y-2 text-xs">
              {report.url && (
                <div className="bg-gray-800/50 rounded px-2 py-1">
                  <div className="text-gray-500 text-xs mb-1">Source</div>
                  <div className="text-blue-400 font-mono truncate text-xs">
                    {new URL(report.url).hostname}
                  </div>
                </div>
              )}
              
              <div className="flex justify-between">
                <div className="bg-gray-800/50 rounded px-2 py-1 flex-1 mr-1">
                  <div className="text-gray-500 text-xs">Size</div>
                  <div className="text-white font-mono text-xs">
                    {report.size ? `${Math.round(report.size / 1024)}KB` : 'N/A'}
                  </div>
                </div>
                <div className="bg-gray-800/50 rounded px-2 py-1 flex-1 ml-1">
                  <div className="text-gray-500 text-xs">Created</div>
                  <div className="text-white font-mono text-xs">
                    {report.created_str || 'Unknown'}
                  </div>
                </div>
              </div>
            </div>
            
            {/* Quick Action Button */}
            <div className="mt-auto">
              <a
                href={getReportUrl('md')}
                target="_blank"
                className="block w-full bg-green-600 hover:bg-green-700 text-white text-center py-2 px-4 rounded transition-colors duration-200 text-sm font-medium"
              >
                <i className="fas fa-external-link-alt mr-2"></i>
                {(() => {
                  if (report.url) {
                    try {
                      const domain = new URL(report.url).hostname.replace('www.', '');
                      // Limit domain length to fit on button (about 15 chars max)
                      const truncatedDomain = domain.length > 15 ? domain.substring(0, 12) + '...' : domain;
                      return `Report for ${truncatedDomain}`;
                    } catch (e) {
                      return 'View Report';
                    }
                  }
                  
                  // If no URL, try to extract domain from report title/name
                  const reportTitle = report.name || report.filename || '';
                  if (reportTitle.includes('_') && reportTitle.match(/[a-f0-9]{8,}$/)) {
                    const parts = reportTitle.split('_');
                    // Remove last part if it looks like a hash
                    if (parts.length > 1 && parts[parts.length - 1].match(/^[a-f0-9]{8,}$/)) {
                      parts.pop();
                    }
                    const cleanDomain = parts.join('.').toLowerCase();
                    if (cleanDomain) {
                      const truncated = cleanDomain.length > 15 ? cleanDomain.substring(0, 12) + '...' : cleanDomain;
                      return `Report for ${truncated}`;
                    }
                  }
                  
                  return 'View Report';
                })()}
              </a>
            </div>
          </div>
        </div>
        
        {/* Back of Badge */}
        <div className="report-badge-back absolute inset-0 w-full h-full backface-hidden rotateY-180 bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-600 rounded-lg shadow-lg">
          
          {/* Back Header */}
          <div className="badge-back-header h-12 bg-gray-700/50 rounded-t-lg flex items-center justify-between px-4">
            <div className="text-sm font-semibold text-purple-400">
              <i className="fas fa-cog mr-2"></i>
              Format Options
            </div>
            <button 
              onClick={() => setIsFlipped(!isFlipped)}
              className="w-6 h-6 bg-black/30 hover:bg-black/50 rounded-full flex items-center justify-center transition-colors duration-200"
            >
              <i className="fas fa-times text-white text-xs"></i>
            </button>
          </div>
          
          {/* Back Content */}
          <div className="p-4 h-68">
            
            {/* Format Selector */}
            <div className="mb-4">
              <div className="text-xs text-gray-400 mb-2">Available Formats:</div>
              <div className="grid grid-cols-2 gap-2">
                {formatOptions.map(option => (
                  <button
                    key={option.value}
                    onClick={() => option.available && setSelectedFormat(option.value)}
                    disabled={!option.available}
                    className={`cursor-pointer p-2 rounded border transition-all duration-200 ${
                      !option.available
                        ? 'opacity-50 cursor-not-allowed bg-gray-800 border-gray-700 text-gray-600'
                        : selectedFormat === option.value
                        ? (() => {
                            switch(option.value) {
                              case 'md': return 'bg-blue-800 border-blue-600 text-white';
                              case 'html': return 'bg-orange-800 border-orange-600 text-white';
                              case 'png': return 'bg-green-800 border-green-600 text-white';
                              case 'json': return 'bg-purple-800 border-purple-600 text-white';
                              default: return 'bg-blue-800 border-blue-600 text-white';
                            }
                          })()
                        : 'hover:bg-gray-700 border-gray-600 text-gray-300'
                    }`}
                    title={option.available ? `Select ${option.label} format` : `${option.label} not available`}
                  >
                    <div className="flex items-center justify-center">
                      <i className={`${option.icon} text-sm mr-2`}></i>
                      <span className="text-xs font-medium">{option.label}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
            
            {/* Metadata */}
            <div className="mb-4 text-xs">
              <div className="text-gray-400 mb-2">Report Details:</div>
              <div className="space-y-1 text-gray-300">
                <div>Created: {report.created_str || 'Unknown'}</div>
                {report.url && (
                  <div className="break-all">URL: {report.url}</div>
                )}
                {report.size && (
                  <div>Size: {Math.round(report.size / 1024)}KB</div>
                )}
              </div>
            </div>
            
            {/* Action Buttons */}
            <div className="flex space-x-2 mt-auto">
              <a
                href={getReportUrl(selectedFormat)}
                target="_blank"
                className={`flex-1 text-center py-2 px-3 rounded transition-colors duration-200 text-sm font-medium ${
                  formatOptions.find(o => o.value === selectedFormat)?.available
                    ? (() => {
                        switch(selectedFormat) {
                          case 'md': return 'bg-blue-600 hover:bg-blue-700 text-white';
                          case 'html': return 'bg-orange-600 hover:bg-orange-700 text-white';
                          case 'png': return 'bg-green-600 hover:bg-green-700 text-white';
                          case 'json': return 'bg-purple-600 hover:bg-purple-700 text-white';
                          default: return 'bg-blue-600 hover:bg-blue-700 text-white';
                        }
                      })()
                    : 'bg-gray-700 text-gray-400 cursor-not-allowed'
                }`}
              >
                <i className={`${formatOptions.find(o => o.value === selectedFormat)?.icon || 'fas fa-file'} mr-1`}></i>
                Open {formatOptions.find(o => o.value === selectedFormat)?.label}
              </a>
              
              <button
                onClick={() => setIsFlipped(false)}
                className="flex-1 bg-gray-700 hover:bg-gray-600 text-white text-center py-2 px-3 rounded transition-colors duration-200 text-sm"
              >
                <i className="fas fa-arrow-left mr-1"></i>
                Back to Overview
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Export the component
window.ReportsDisplay = ReportsDisplay;
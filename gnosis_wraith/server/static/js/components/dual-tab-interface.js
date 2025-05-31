/**
 * Dual Tab Interface Component
 * Handles the Reports | Logs tab system with integrated headers
 */

const DualTabInterface = ({
  // Log props
  logs,
  logsEndRef,
  logContainerRef,
  logContainerVisible,
  logOrder,
  onLogOrderChange,
  logFilter,
  setLogFilter,
  logFilterMode,
  setLogFilterMode,
  
  // Reports props
  recentReports,
  loadingRecentReports,
  crawlStats,
  fetchRecentReports
}) => {
  const [activeTab, setActiveTab] = React.useState('logs'); // Default to logs as requested
  const [isTransitioning, setIsTransitioning] = React.useState(false);
  const [reportsSearchFilter, setReportsSearchFilter] = React.useState('');
  const [reportsFilterMode, setReportsFilterMode] = React.useState('include');

  // Load active tab from localStorage on mount
  React.useEffect(() => {
    const savedTab = localStorage.getItem('gnosis_active_tab');
    if (savedTab && ['reports', 'logs'].includes(savedTab)) {
      setActiveTab(savedTab);
    }
  }, []);

  // Handle tab switching with animation
  const handleTabSwitch = (tabName) => {
    if (tabName === activeTab || isTransitioning) return;
    
    setIsTransitioning(true);
    
    // Save tab preference
    localStorage.setItem('gnosis_active_tab', tabName);
    
    // Smooth transition
    setTimeout(() => {
      setActiveTab(tabName);
      setTimeout(() => {
        setIsTransitioning(false);
      }, 150);
    }, 75);
  };

  return (
    <div className="h-full flex flex-col">
      {/* Tab Content with integrated headers */}
      <div className={`flex-grow transition-all duration-200 ${isTransitioning ? 'opacity-50 scale-98' : 'opacity-100 scale-100'}`}>
        {activeTab === 'reports' ? (
          // Reports container with integrated header
          <div className="h-full flex flex-col">
            {/* Reports container with integrated tab header */}
            <div className="flex-grow bg-gray-800 border border-gray-700 rounded-md overflow-auto">
              <div className="px-4 py-2 border-b border-gray-700 bg-gray-900">
                <div className="flex items-center space-x-2">
                  {/* Tabs that swap positions - inactive first, active second */}
                  <button
                    onClick={() => handleTabSwitch('logs')}
                    className="px-3 py-1 text-gray-400 hover:text-gray-200 hover:bg-gray-700 rounded font-medium flex items-center space-x-1 transition-colors text-sm"
                    disabled={isTransitioning}
                  >
                    <i className="fas fa-terminal text-xs"></i>
                    <span>Logs</span>
                  </button>
                  
                  <div className="text-gray-600 text-sm">|</div>
                  
                  <button className="px-3 py-1 bg-blue-600 text-white rounded font-medium flex items-center space-x-1 text-sm">
                    <i className="fas fa-chart-bar text-xs"></i>
                    <span>Reports</span>
                  </button>

                  {/* Search box */}
                  <div className="flex-grow ml-4">
                    <div className="flex items-center space-x-1 bg-gray-900 p-1 rounded">
                      <input
                        type="text"
                        className="flex-grow px-2 py-1 bg-gray-900 border border-gray-700 rounded text-xs text-gray-200 placeholder-gray-500"
                        placeholder="Search reports..."
                        value={reportsSearchFilter}
                        onChange={(e) => setReportsSearchFilter(e.target.value)}
                      />
                      <button
                        onClick={() => setReportsFilterMode(reportsFilterMode === 'include' ? 'exclude' : 'include')}
                        className={`px-1.5 py-1 text-xs rounded transition-colors ${
                          reportsFilterMode === 'include'
                            ? 'bg-blue-600 text-white'
                            : 'bg-red-600 text-white'
                        }`}
                        title={reportsFilterMode === 'include' ? 'Switch to exclude mode' : 'Switch to include mode'}
                      >
                        <i className={`fas ${reportsFilterMode === 'include' ? 'fa-check' : 'fa-times'} mr-0.5`}></i>
                        <span className="text-xs">{reportsFilterMode === 'include' ? 'MATCH' : 'HIDE'}</span>
                      </button>
                      {reportsSearchFilter && (
                        <button 
                          onClick={() => setReportsSearchFilter('')}
                          className="px-1.5 py-1 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded text-xs transition-colors"
                          title="Clear search"
                        >
                          <i className="fas fa-times"></i>
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Reports content */}
              <div className="p-4">
                <ReportsDisplay
                  recentReports={recentReports}
                  loadingRecentReports={loadingRecentReports}
                  crawlStats={crawlStats}
                  fetchRecentReports={fetchRecentReports}
                  searchFilter={reportsSearchFilter}
                  filterMode={reportsFilterMode}
                />
              </div>
            </div>
          </div>
        ) : (
          // Logs container with integrated header (original style)
          <div 
            ref={logContainerRef} 
            className="bg-gray-800 border border-gray-700 rounded-md overflow-auto log-container crt-scanlines crt-flicker h-full"
            style={{ visibility: logContainerVisible ? 'visible' : 'hidden' }}
          >
            <div className="px-4 py-2 border-b border-gray-700 bg-gray-900">
              <div className="flex items-center space-x-2">
                {/* Tabs that swap positions - inactive first, active second */}
                <button
                  onClick={() => handleTabSwitch('reports')}
                  className="px-3 py-1 text-gray-400 hover:text-gray-200 hover:bg-gray-700 rounded font-medium flex items-center space-x-1 transition-colors text-sm"
                  disabled={isTransitioning}
                >
                  <i className="fas fa-chart-bar text-xs"></i>
                  <span>Reports</span>
                </button>
                
                <div className="text-gray-600 text-sm">|</div>
                
                <button className="px-3 py-1 bg-green-600 text-white rounded font-medium flex items-center space-x-1 text-sm">
                  <i className="fas fa-terminal text-xs"></i>
                  <span>Logs</span>
                </button>

                {/* Search and controls */}
                <div className="flex-grow ml-4">
                  <div className="flex items-center space-x-1 bg-gray-900 p-1 rounded">
                    <input 
                      type="text"
                      className="flex-grow px-2 py-1 bg-gray-900 border border-gray-700 rounded text-xs"
                      placeholder="Filter logs..."
                      value={logFilter}
                      onChange={(e) => setLogFilter(e.target.value)}
                    />
                    <button
                      onClick={() => setLogFilterMode(logFilterMode === 'include' ? 'exclude' : 'include')}
                      className={`px-1.5 py-1 text-xs rounded transition-colors ${
                        logFilterMode === 'include'
                          ? 'bg-blue-600 text-white'
                          : 'bg-red-600 text-white'
                      }`}
                      title={logFilterMode === 'include' ? 'Switch to exclude mode' : 'Switch to include mode'}
                    >
                      <i className={`fas ${logFilterMode === 'include' ? 'fa-check' : 'fa-times'} mr-0.5`}></i>
                      <span className="text-xs">{logFilterMode === 'include' ? 'MATCH' : 'HIDE'}</span>
                    </button>
                    {logFilter && (
                      <button
                        onClick={() => setLogFilter('')}
                        className="px-1.5 py-1 text-xs bg-gray-700 hover:bg-gray-600 text-gray-300 rounded transition-colors"
                        title="Clear filter"
                      >
                        <i className="fas fa-times"></i>
                      </button>
                    )}
                    
                    {/* Sort order buttons - compressed */}
                    <div className="flex items-center space-x-0.5 bg-gray-800 p-0.5 rounded">
                      <button
                        onClick={() => onLogOrderChange('newest')}
                        className={`px-1.5 py-1 rounded transition-colors ${
                          logOrder === 'newest' ? 'bg-green-800 text-white' : 'hover:bg-gray-700'
                        }`}
                        title="Show newest logs first"
                      >
                        <i className="fas fa-arrow-down text-xs"></i>
                      </button>
                      <button
                        onClick={() => onLogOrderChange('oldest')}
                        className={`px-1.5 py-1 rounded transition-colors ${
                          logOrder === 'oldest' ? 'bg-green-800 text-white' : 'hover:bg-gray-700'
                        }`}
                        title="Show oldest logs first"
                      >
                        <i className="fas fa-arrow-up text-xs"></i>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Logs content */}
            <div className="p-4">
              {(() => {
                // Filter logs based on filter text and mode
                const filteredLogs = logFilter.trim() ? logs.filter(log => {
                  const message = log.message.toLowerCase();
                  const filter = logFilter.toLowerCase();
                  const matches = message.includes(filter);
                  return logFilterMode === 'include' ? matches : !matches;
                }) : logs;
                
                // Process logs based on order preference
                const processedLogs = logOrder === 'oldest' ? [...filteredLogs] : [...filteredLogs].reverse();
                
                return (
                  <>
                    {processedLogs.map(log => (
                      <div key={log.id} className="mb-2 break-words overflow-wrap-anywhere text-sm">
                        <div className="flex">
                          <div 
                            className="flex-shrink-0 px-2 py-0.5 rounded-md mr-2 font-mono text-xs flex items-center justify-center" 
                            style={{ 
                              color: log.timestampColor || '#9ca3af', 
                              backgroundColor: log.timestampBgColor || 'rgba(31, 41, 55, 0.5)',
                              minHeight: '1.75rem' // Ensure consistent height
                            }}
                          >
                            {log.timestamp}
                          </div>
                          
                          <div className="flex-grow flex items-center"> {/* Message content aligned with timestamp */}
                            {log.isHtml ? (
                              <span dangerouslySetInnerHTML={{ __html: log.message }} className="break-words" />
                            ) : (
                              <span className="break-words overflow-wrap-anywhere">{log.message}</span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                    {processedLogs.length === 0 && (
                      <div className="h-full flex items-center justify-center text-gray-600">
                        Initializing system...
                      </div>
                    )}
                    <div ref={logsEndRef} />
                  </>
                );
              })()}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Export the component
window.DualTabInterface = DualTabInterface;
/**
 * Log Display Component
 * Handles the log output display and scrolling behavior
 */

const LogDisplay = ({
  logs,
  logsEndRef,
  logContainerRef,
  logContainerVisible,
  logOrder,
  onLogOrderChange,
  logFilter,
  setLogFilter,
  logFilterMode,
  setLogFilterMode
}) => {
  // Filter logs based on filter text and mode
  const filteredLogs = logFilter.trim() ? logs.filter(log => {
    const message = log.message.toLowerCase();
    const filter = logFilter.toLowerCase();
    const matches = message.includes(filter);
    return logFilterMode === 'include' ? matches : !matches;
  }) : logs;
  
  // Process logs based on order preference
  const processedLogs = logOrder === 'oldest' ? [...filteredLogs] : [...filteredLogs].reverse();
  
  // Handle filter changes
  const handleFilterChange = (e) => {
    const value = e.target.value;
    setLogFilter(value);
    localStorage.setItem('gnosis_log_filter', value);
  };
  
  const handleFilterModeChange = (mode) => {
    setLogFilterMode(mode);
    localStorage.setItem('gnosis_log_filter_mode', mode);
  };
  
  return (
    <div 
      ref={logContainerRef} 
      className="bg-gray-800 border border-gray-700 rounded-md overflow-auto log-container crt-scanlines crt-flicker"
      style={{ visibility: logContainerVisible ? 'visible' : 'hidden' }}
    >
      <div className="px-4 py-2 border-b border-gray-700 bg-gray-900">
        {/* Single row - Title, Sort Order, and Filter all aligned */}
        <div className="flex justify-between items-center space-x-4">
          <h2 className="text-lg font-semibold text-green-400 flex-shrink-0">Logs</h2>
          
          {/* Filter section - takes up available space */}
          <div className="flex items-center space-x-1 bg-gray-900 p-1 rounded flex-grow">
            <input 
              type="text"
              className="flex-grow px-2 py-1 bg-gray-900 border border-gray-700 rounded text-xs"
              placeholder="Filter logs..."
              value={logFilter}
              onChange={handleFilterChange}
              title="Filter log messages"
            />
            <button
              onClick={() => handleFilterModeChange('include')}
              className={`px-2 py-1 text-xs rounded transition-colors ${
                logFilterMode === 'include'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
              title="Show logs that match filter"
            >
              <i className="fas fa-check mr-1"></i>MATCH
            </button>
            <button
              onClick={() => handleFilterModeChange('exclude')}
              className={`px-2 py-1 text-xs rounded transition-colors ${
                logFilterMode === 'exclude'
                  ? 'bg-red-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
              title="Hide logs that match filter"
            >
              <i className="fas fa-times mr-1"></i>HIDE
            </button>
            {logFilter && (
              <button
                onClick={() => {
                  setLogFilter('');
                  localStorage.removeItem('gnosis_log_filter');
                }}
                className="px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 text-gray-300 rounded transition-colors"
                title="Clear filter"
              >
                <i className="fas fa-times"></i>
              </button>
            )}
          </div>
          
          {/* Sort order with bounding box */}
          <div className="flex items-center space-x-1 bg-gray-900 p-1 rounded flex-shrink-0">
            <label className={`cursor-pointer px-2 py-1 rounded transition-colors ${
              logOrder === 'newest' ? 'bg-green-800 text-white' : 'hover:bg-gray-700'
            }`} title="Show newest logs first">
              <input
                type="radio"
                name="logOrder"
                value="newest"
                checked={logOrder === 'newest'}
                onChange={() => onLogOrderChange('newest')}
                className="sr-only"
              />
              <i className="fas fa-arrow-down"></i>
            </label>
            <label className={`cursor-pointer px-2 py-1 rounded transition-colors ${
              logOrder === 'oldest' ? 'bg-green-800 text-white' : 'hover:bg-gray-700'
            }`} title="Show oldest logs first">
              <input
                type="radio"
                name="logOrder"
                value="oldest"
                checked={logOrder === 'oldest'}
                onChange={() => onLogOrderChange('oldest')}
                className="sr-only"
              />
              <i className="fas fa-arrow-up"></i>
            </label>
          </div>
          
          {/* Log count when filtering */}
          {logFilter && (
            <div className="text-xs text-gray-400 flex-shrink-0">
              {processedLogs.length} of {logs.length}
            </div>
          )}
        </div>
      </div>
      <div className="p-4">
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
      </div>
    </div>
  );
};

// Export the component
window.LogDisplay = LogDisplay;
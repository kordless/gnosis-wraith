/**
 * Recent Crawls Component with Local Storage
 * Displays and manages locally stored crawl history with search functionality
 */

const RecentCrawls = ({
  recentReports,
  loadingRecentReports,
  localCrawlHistory,
  filteredCrawls,
  crawlSearchTerm,
  setCrawlSearchTerm,
  handleCrawlSearch,
  showLocalCrawls,
  setShowLocalCrawls,
  setLocalCrawlHistory,
  setFilteredCrawls
}) => {
  // Initialize local state for toggling between server reports and local history
  const [searchInputVisible, setSearchInputVisible] = useState(false);
  
  // Handle search input change
  const handleSearchChange = (e) => {
    const value = e.target.value;
    setCrawlSearchTerm(value);
    handleCrawlSearch(value);
  };
  
  // Toggle search input visibility
  const toggleSearchInput = () => {
    setSearchInputVisible(!searchInputVisible);
    if (!searchInputVisible) {
      // Focus the search input when it becomes visible
      setTimeout(() => {
        const searchInput = document.getElementById('crawl-search-input');
        if (searchInput) {
          searchInput.focus();
        }
      }, 50);
    }
  };
  
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-md p-4">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-lg">Recent Crawls</h3>
        <div className="flex space-x-1">
          {/* Search toggle button */}
          <button 
            className={`px-2 py-1 text-xs rounded ${searchInputVisible ? 'bg-blue-700 text-white' : 'bg-gray-700 hover:bg-gray-600'}`}
            onClick={toggleSearchInput}
            title="Search crawl history"
          >
            <i className="fas fa-search"></i>
          </button>
          
          {/* Storage toggle button */}
          <button 
            className={`px-2 py-1 text-xs rounded ${showLocalCrawls ? 'bg-green-700 text-white' : 'bg-gray-700 hover:bg-gray-600'}`}
            onClick={() => setShowLocalCrawls(!showLocalCrawls)}
            title={showLocalCrawls ? "Show recent server reports" : "Show local history"}
          >
            <i className={`fas ${showLocalCrawls ? 'fa-database' : 'fa-server'}`}></i>
          </button>
        </div>
      </div>
      
      {/* Search input that appears when search is toggled */}
      {searchInputVisible && (
        <div className="mb-2 transition-all duration-300 ease-in-out">
          <input
            id="crawl-search-input"
            type="text"
            placeholder="Search crawl history..."
            className="w-full px-2 py-1 bg-gray-900 border border-gray-700 rounded text-sm text-white"
            value={crawlSearchTerm}
            onChange={handleSearchChange}
          />
          {crawlSearchTerm && filteredCrawls.length === 0 && (
            <div className="text-xs text-yellow-400 mt-1">No results found</div>
          )}
        </div>
      )}
      
      {/* Status indicator for which source is being displayed */}
      <div className="text-xs text-gray-400 mb-1 flex items-center">
        <span className={`h-2 w-2 rounded-full mr-1 ${showLocalCrawls ? 'bg-green-500' : 'bg-blue-500'}`}></span>
        {showLocalCrawls ? `Showing local history (${filteredCrawls.length}/${localCrawlHistory.length})` : 'Showing server reports'}
      </div>
      
      {/* Display appropriate content based on view mode */}
      {showLocalCrawls ? (
        // Local crawl history view
        <div>
          {filteredCrawls.length > 0 ? (
            <ul className="text-sm space-y-2 max-h-60 overflow-y-auto custom-scrollbar">
              {filteredCrawls.map((crawl, index) => (
                <li key={index} className="border-b border-gray-700 pb-1 last:border-b-0">
                  <a 
                    href={crawl.url} 
                    target="_blank" 
                    className="text-green-300 hover:underline truncate block"
                  >
                    {crawl.title}
                  </a>
                  <div className="flex justify-between items-center">
                    <div className="text-xs text-gray-400">
                      {crawl.created_str}
                    </div>
                    {crawl.screenshot && (
                      <a 
                        href={crawl.screenshot}
                        target="_blank"
                        className="text-xs text-blue-400 hover:underline"
                        title="View screenshot"
                      >
                        <i className="fas fa-image"></i>
                      </a>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          ) : crawlSearchTerm ? (
            <div className="text-gray-500 text-sm py-2">No matching results</div>
          ) : (
            <div className="text-gray-500 text-sm py-2">No local history found</div>
          )}
          
          {/* Clear history button */}
          {localCrawlHistory.length > 0 && (
            <div className="mt-2 flex justify-end">
              <button 
                className="text-xs text-red-400 hover:text-red-300 px-2 py-1 bg-gray-900 hover:bg-gray-800 rounded"
                onClick={() => {
                  // Create confirmation modal
                  const confirmModal = document.createElement('div');
                  confirmModal.className = 'fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50';
                  confirmModal.innerHTML = `
                    <div class="bg-gray-800 border border-red-500 rounded-lg p-6 max-w-md w-full mx-4">
                      <div class="flex items-center mb-4">
                        <i class="fas fa-exclamation-triangle text-red-500 text-xl mr-3"></i>
                        <h3 class="text-lg font-semibold text-red-400">Clear Crawl History</h3>
                      </div>
                      <p class="text-gray-300 mb-6">
                        Are you sure you want to clear all locally stored crawl history? This action cannot be undone.
                      </p>
                      <div class="flex justify-end space-x-3">
                        <button class="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded text-sm transition-colors" id="cancel-clear-history-btn">
                          Cancel
                        </button>
                        <button class="px-4 py-2 bg-red-700 hover:bg-red-600 text-white rounded text-sm transition-colors" id="confirm-clear-history-btn">
                          <i class="fas fa-trash mr-1"></i>Clear History
                        </button>
                      </div>
                    </div>
                  `;
                  document.body.appendChild(confirmModal);
                  
                  // Add event handlers
                  document.getElementById('cancel-clear-history-btn').addEventListener('click', () => {
                    document.body.removeChild(confirmModal);
                  });
                  
                  document.getElementById('confirm-clear-history-btn').addEventListener('click', () => {
                    // Clear local storage
                    localStorage.removeItem('gnosis_crawl_history');
                    
                    // Update state
                    setLocalCrawlHistory([]);
                    setFilteredCrawls([]);
                    
                    document.body.removeChild(confirmModal);
                  });
                  
                  // Close modal when clicking outside
                  confirmModal.addEventListener('click', (e) => {
                    if (e.target === confirmModal) {
                      document.body.removeChild(confirmModal);
                    }
                  });
                }}
              >
                <i className="fas fa-trash-alt mr-1"></i> Clear History
              </button>
            </div>
          )}
        </div>
      ) : (
        // Server reports view (original behavior)
        recentReports.length > 0 ? (
          <ul className="text-sm space-y-2">
            {recentReports.map(report => (
              <li key={report.filename} className="border-b border-gray-700 pb-1 last:border-b-0">
                <a 
                  href={report.filename.startsWith('/') ? report.filename : `/reports/${report.filename}`} 
                  target="_blank" 
                  className="text-green-300 hover:underline truncate block"
                >
                  {report.title}
                </a>
                <div className="text-xs text-gray-400">
                  {report.created_str}
                </div>
              </li>
            ))}
          </ul>
        ) : loadingRecentReports ? (
          <div className="text-center py-2">
            <div className="text-xs text-gray-400">Loading...</div>
          </div>
        ) : (
          <div className="text-gray-500 text-sm">No recent crawls found</div>
        )
      )}
    </div>
  );
};

// Export the component
window.RecentCrawls = RecentCrawls;
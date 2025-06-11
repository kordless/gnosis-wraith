/**
 * Reports Dashboard Component
 * Factory-style safety dashboard with crawl reports and statistics
 */

const ReportsDashboard = ({ 
  crawlStats, 
  recentReports, 
  loadingRecentReports,
  reportFormat,
  setReportFormat,
  onRefreshReports 
}) => {
  const [searchTerm, setSearchTerm] = React.useState('');
  const [sortBy, setSortBy] = React.useState('newest');
  
  // Calculate days since last serious incident (error)
  const daysSinceIncident = React.useMemo(() => {
    // Get a somewhat realistic but fun number
    const baseDate = new Date('2025-01-15'); // App started
    const now = new Date();
    const daysDiff = Math.floor((now - baseDate) / (1000 * 60 * 60 * 24));
    
    // If we have recent errors, reduce the count
    const recentErrorRate = crawlStats.total > 0 ? (crawlStats.errors / crawlStats.total) : 0;
    const adjustment = Math.floor(recentErrorRate * 100);
    
    return Math.max(0, daysSinceIncident - adjustment);
  }, [crawlStats]);
  
  // Calculate success percentage
  const successRate = React.useMemo(() => {
    if (crawlStats.total === 0) return 100;
    return Math.round((crawlStats.success / crawlStats.total) * 100);
  }, [crawlStats]);
  
  // Filter and sort reports
  const filteredReports = React.useMemo(() => {
    let filtered = recentReports.filter(report => 
      report.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      report.filename?.toLowerCase().includes(searchTerm.toLowerCase())
    );
    
    switch (sortBy) {
      case 'oldest':
        return filtered.reverse();
      case 'name':
        return filtered.sort((a, b) => 
          (a.name || a.filename || '').localeCompare(b.name || b.filename || '')
        );
      default: // newest
        return filtered;
    }
  }, [recentReports, searchTerm, sortBy]);
  
  return (
    <div className="reports-dashboard">
      {/* Factory Safety Banner */}
      <div className="safety-banner mb-6 bg-yellow-500 text-black p-4 rounded-lg text-center font-bold text-xl">
        <i className="fas fa-hard-hat mr-2"></i>
        {daysSinceIncident} DAYS SINCE LAST SERIOUS CRAWLING INCIDENT
        <i className="fas fa-hard-hat ml-2"></i>
      </div>
      
      {/* Statistics Dashboard */}
      <div className="dashboard-stats grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="stat-card bg-gray-800 border border-gray-700 rounded-lg p-4 text-center hover:border-green-500 transition-all duration-300">
          <div className="stat-value text-3xl font-bold text-green-400 font-mono">
            {crawlStats.total.toLocaleString()}
          </div>
          <div className="stat-label text-gray-400 text-sm uppercase tracking-wide mt-1">
            Total Crawls
          </div>
        </div>
        
        <div className="stat-card bg-gray-800 border border-gray-700 rounded-lg p-4 text-center hover:border-green-500 transition-all duration-300">
          <div className="stat-value text-3xl font-bold text-green-400 font-mono">
            {successRate}%
          </div>
          <div className="stat-label text-gray-400 text-sm uppercase tracking-wide mt-1">
            Success Rate
          </div>
        </div>
        
        <div className="stat-card bg-gray-800 border border-gray-700 rounded-lg p-4 text-center hover:border-green-500 transition-all duration-300">
          <div className="stat-value text-3xl font-bold text-blue-400 font-mono">
            {recentReports.length}
          </div>
          <div className="stat-label text-gray-400 text-sm uppercase tracking-wide mt-1">
            Reports Generated
          </div>
        </div>
        
        <div className="stat-card bg-gray-800 border border-gray-700 rounded-lg p-4 text-center hover:border-green-500 transition-all duration-300">
          <div className="stat-value text-3xl font-bold text-red-400 font-mono">
            {crawlStats.errors}
          </div>
          <div className="stat-label text-gray-400 text-sm uppercase tracking-wide mt-1">
            Incidents
          </div>
        </div>
      </div>
      
      {/* Controls Row */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
        {/* Search */}
        <div className="flex-1 max-w-md">
          <div className="relative">
            <i className="fas fa-search absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"></i>
            <input
              type="text"
              placeholder="Search reports..."
              className="w-full bg-gray-800 border border-gray-600 rounded-lg pl-10 pr-4 py-2 text-green-400 placeholder-gray-400 focus:border-green-500 focus:outline-none"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>
        
        {/* Sort and Controls */}
        <div className="flex items-center gap-3">
          <select
            className="bg-gray-800 border border-gray-600 rounded px-3 py-2 text-green-400 focus:border-green-500 focus:outline-none"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="newest">Newest First</option>
            <option value="oldest">Oldest First</option>
            <option value="name">Name A-Z</option>
          </select>
          
          <button
            onClick={onRefreshReports}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors duration-200 flex items-center gap-2"
            disabled={loadingRecentReports}
          >
            <i className={`fas fa-sync-alt ${loadingRecentReports ? 'animate-spin' : ''}`}></i>
            Refresh
          </button>
        </div>
      </div>
      
      {/* Reports Grid */}
      <div className="reports-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loadingRecentReports ? (
          <div className="col-span-full text-center py-8">
            <i className="fas fa-spinner fa-spin text-2xl text-green-400 mb-2"></i>
            <div className="text-gray-400">Loading reports...</div>
          </div>
        ) : filteredReports.length > 0 ? (
          filteredReports.map((report, index) => (
            <div key={index} className="report-card bg-gray-800 border border-gray-700 rounded-lg p-4 hover:border-green-500 transition-all duration-300 hover:shadow-lg">
              {/* Report Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h3 className="text-green-400 font-semibold text-sm mb-1 line-clamp-2">
                    {report.name || report.filename || 'Untitled Report'}
                  </h3>
                  <div className="text-xs text-gray-500">
                    {report.created_str || report.timestamp}
                  </div>
                </div>
                
                {/* File Type Badge */}
                <div className="ml-2">
                  <span className="inline-block bg-green-900 text-green-300 text-xs px-2 py-1 rounded">
                    {report.filename?.split('.').pop()?.toUpperCase() || 'MD'}
                  </span>
                </div>
              </div>
              
              {/* Report Content Preview */}
              {report.url && (
                <div className="mb-3">
                  <div className="text-xs text-gray-400 mb-1">Source:</div>
                  <div className="text-xs text-blue-400 font-mono bg-gray-900 p-2 rounded break-all">
                    {report.url}
                  </div>
                </div>
              )}
              
              {/* Format Selector & Actions */}
              <div className="flex items-center justify-between mt-4 pt-3 border-t border-gray-700">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-400">View as:</span>
                  <select className="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-xs text-green-400">
                    <option value="md">Markdown</option>
                    <option value="html">HTML</option>
                    <option value="json">JSON</option>
                  </select>
                </div>
                
                <a
                  href={`/reports/${report.path || report.filename}`}
                  target="_blank"
                  className="inline-flex items-center gap-1 bg-green-600 hover:bg-green-700 text-white text-xs px-3 py-1 rounded transition-colors duration-200"
                >
                  <i className="fas fa-external-link-alt"></i>
                  Open
                </a>
              </div>
            </div>
          ))
        ) : (
          <div className="col-span-full text-center py-12">
            <i className="fas fa-ghost text-4xl text-gray-600 mb-4"></i>
            <div className="text-gray-400 text-lg mb-2">No reports found</div>
            <div className="text-gray-500 text-sm">
              {searchTerm ? 'Try adjusting your search terms' : 'Start crawling to generate reports'}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Make component globally available
window.ReportsDashboard = ReportsDashboard;
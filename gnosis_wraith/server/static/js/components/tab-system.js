/**
 * Tab System Component
 * Handles the Reports | Logs dual tab interface with smooth animations
 */

const TabSystem = ({ 
  crawlStats, 
  recentReports, 
  loadingRecentReports,
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
  reportFormat,
  setReportFormat,
  onRefreshReports 
}) => {
  const [activeTab, setActiveTab] = React.useState('logs'); // Default to Logs
  
  const handleTabClick = (tabName) => {
    if (tabName !== activeTab) {
      setActiveTab(tabName);
      
      // Add a small delay to ensure smooth animation
      if (tabName === 'logs' && logsEndRef.current) {
        setTimeout(() => {
          logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }, 100);
      }
    }
  };
  
  return (
    <div className="tab-system w-full">
      {/* Tab Navigation */}
      <div className="tab-nav flex border-b border-gray-700 mb-6">
        <button
          className={`tab-button px-6 py-3 font-semibold text-lg transition-all duration-300 relative ${
            activeTab === 'reports'
              ? 'text-green-400 border-b-2 border-green-400 bg-gray-800'
              : 'text-gray-400 hover:text-gray-300 hover:bg-gray-800'
          }`}
          onClick={() => handleTabClick('reports')}
        >
          <i className="fas fa-chart-bar mr-2"></i>
          Reports
          {activeTab === 'reports' && (
            <div className="absolute inset-x-0 bottom-0 h-0.5 bg-green-400 animate-pulse"></div>
          )}
        </button>
        
        <div className="mx-2 text-gray-600 text-lg py-3">|</div>
        
        <button
          className={`tab-button px-6 py-3 font-semibold text-lg transition-all duration-300 relative ${
            activeTab === 'logs'
              ? 'text-green-400 border-b-2 border-green-400 bg-gray-800'
              : 'text-gray-400 hover:text-gray-300 hover:bg-gray-800'
          }`}
          onClick={() => handleTabClick('logs')}
        >
          <i className="fas fa-terminal mr-2"></i>
          Logs
          {activeTab === 'logs' && (
            <div className="absolute inset-x-0 bottom-0 h-0.5 bg-green-400 animate-pulse"></div>
          )}
        </button>
      </div>
      
      {/* Tab Content */}
      <div className="tab-content">
        {/* Reports Tab */}
        <div className={`tab-pane ${activeTab === 'reports' ? 'block' : 'hidden'}`}>
          <div className="animate-fadeIn">
            <ReportsDashboard
              crawlStats={crawlStats}
              recentReports={recentReports}
              loadingRecentReports={loadingRecentReports}
              reportFormat={reportFormat}
              setReportFormat={setReportFormat}
              onRefreshReports={onRefreshReports}
            />
          </div>
        </div>
        
        {/* Logs Tab */}
        <div className={`tab-pane ${activeTab === 'logs' ? 'block' : 'hidden'}`}>
          <div className="animate-fadeIn">
            <LogDisplay 
              logs={logs}
              logsEndRef={logsEndRef}
              logContainerRef={logContainerRef}
              logContainerVisible={logContainerVisible}
              logOrder={logOrder}
              onLogOrderChange={onLogOrderChange}
              logFilter={logFilter}
              setLogFilter={setLogFilter}
              logFilterMode={logFilterMode}
              setLogFilterMode={setLogFilterMode}
            />
          </div>
        </div>
      </div>
      
      <style jsx>{`
        .animate-fadeIn {
          animation: fadeIn 0.3s ease-in-out;
        }
        
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .tab-button {
          position: relative;
          border-radius: 8px 8px 0 0;
        }
        
        .tab-button::before {
          content: '';
          position: absolute;
          top: 0;
          left: 50%;
          transform: translateX(-50%);
          width: 0;
          height: 2px;
          background: linear-gradient(90deg, transparent, #10b981, transparent);
          transition: width 0.3s ease;
        }
        
        .tab-button:hover::before {
          width: 80%;
        }
        
        .tab-button.active::before {
          width: 100%;
        }
      `}</style>
    </div>
  );
};

// Make component globally available
window.TabSystem = TabSystem;
/**
 * Crawler Input Component
 * Handles URL input, history, and crawl functionality
 */

const CrawlerInput = ({
  authStatus,
  inputValue,
  setInputValue,
  handleAuthenticate,
  handleSearch,
  urlHistory,
  setUrlHistory,
  showHistory,
  setShowHistory,
  reportFormat,
  setReportFormat,
  forceJavascript,
  setForceJavascript,
  screenshotMode,
  setScreenshotMode,
  markdownQuality,
  setMarkdownQuality,
  customReportName,
  setCustomReportName,
  reportNamesEnabled,
  setReportNamesEnabled,
  ocrEnabled,
  setOcrEnabled,
  addLog,
  isCrawling,
  onLogout // Add logout callback
}) => {
  const { useState, useEffect } = React;
  
  // State for modals and screenshot/OCR settings
  const [showTokenModal, setShowTokenModal] = useState(false);
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  
  // Initialize screenshot mode with smart defaults and occasional re-enabling
  useEffect(() => {
    const savedScreenshotMode = localStorage.getItem('gnosis_screenshot_mode');
    if (!savedScreenshotMode) {
      // First time - default to 'top'
      setScreenshotMode('top');
      localStorage.setItem('gnosis_screenshot_mode', 'top');
      addLog('Screenshot mode initialized to: top');
    } else if (savedScreenshotMode === 'off') {
      // 25% chance to re-enable screenshots on page reload if they were off
      if (Math.random() < 0.25) {
        setScreenshotMode('top');
        localStorage.setItem('gnosis_screenshot_mode', 'top');
        addLog('Screenshots automatically re-enabled (helpful reminder)');
      } else {
        setScreenshotMode(savedScreenshotMode);
      }
    } else {
      setScreenshotMode(savedScreenshotMode);
    }
  }, []);
  
  // Handle screenshot mode change
  const handleScreenshotModeChange = (mode) => {
    setScreenshotMode(mode);
    localStorage.setItem('gnosis_screenshot_mode', mode);
    addLog(`Screenshot mode set to: ${mode}`);
    
    // If turning off screenshots, also turn off OCR
    if (mode === 'off' && ocrEnabled) {
      setOcrEnabled(false);
      localStorage.setItem('gnosis_ocr_enabled', 'false');
      addLog('OCR disabled (screenshots turned off)');
    }
    
    // Dispatch favicon change event
    document.dispatchEvent(new CustomEvent('screenshotModeChanged', {
      detail: { mode: mode }
    }));
  };
  
  // Handle OCR toggle
  const handleOcrToggle = () => {
    // If screenshots are off and user tries to enable OCR, turn on top screenshot mode
    if (!screenshotMode || screenshotMode === 'off') {
      if (!ocrEnabled) {
        // Enable top screenshot mode and OCR
        handleScreenshotModeChange('top');
        setOcrEnabled(true);
        localStorage.setItem('gnosis_ocr_enabled', 'true');
        addLog('Screenshots enabled (top of page) and OCR enabled');
      }
      return;
    }
    
    const newValue = !ocrEnabled;
    setOcrEnabled(newValue);
    localStorage.setItem('gnosis_ocr_enabled', JSON.stringify(newValue));
    addLog(`OCR ${newValue ? 'enabled' : 'disabled'}`);
  };

  // Handle report names toggle
  const handleReportNamesToggle = () => {
    const newValue = !reportNamesEnabled;
    setReportNamesEnabled(newValue);
    localStorage.setItem('gnosis_report_names_enabled', JSON.stringify(newValue));
    
    if (!newValue) {
      // Clear custom report name when disabling
      setCustomReportName('');
      addLog('Report names disabled - will use simple domain-based naming (e.g., splunk_com)');
    } else {
      addLog('Report names enabled - can specify custom report names');
    }
  };

  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault(); // Prevent form submission or other default behavior
      
      if (authStatus !== 'authorized') {
        if (!inputValue.trim()) return; // Don't authenticate with empty input
        handleAuthenticate();
      } else {
        if (isCrawling || !inputValue.trim()) return; // Don't crawl if already crawling or empty input
        handleSearch();
      }
      // Close history dropdown when Enter is pressed
      setShowHistory(false);
    } else if (e.key === 'Escape') {
      // Close history dropdown when Escape is pressed
      setShowHistory(false);
    }
  };

  // Helper function to get button text with spinner
  const getButtonText = () => {
    if (authStatus === 'authorized') {
      return isCrawling ? (
        <>
          <i className="fas fa-spinner fa-spin mr-2"></i>
          Crawling...
        </>
      ) : (
        'Crawl'
      );
    } else {
      return 'Authenticate';
    }
  };

  // Helper function to determine if button should be disabled
  const isButtonDisabled = () => {
    if (authStatus === 'authorized') {
      return isCrawling || !inputValue.trim();
    } else {
      return !inputValue.trim();
    }
  };

  // Handle token update
  const handleTokenUpdated = (provider, token) => {
    if (token) {
      addLog(`${provider} API token updated successfully`);
    } else {
      addLog(`${provider} API token cleared`);
    }
  };

  // Handle logout
  const handleLogout = () => {
    if (onLogout) {
      onLogout();
    }
  };

  // Handle clear all tokens
  const handleClearAllTokens = () => {
    const providers = [
      'gnosis_wraith_llm_token_anthropic',
      'gnosis_wraith_llm_token_openai', 
      'gnosis_wraith_llm_token_gemini'
    ];
    
    providers.forEach(cookieName => {
      CookieUtils.deleteCookie(cookieName);
    });
    
    addLog('All LLM API tokens have been cleared');
  };

  return (
    <>
      <div className="bg-gray-800 border border-gray-700 rounded-md p-4 mb-4">
        <div className="flex mb-2 border-b border-gray-700 justify-between items-center">
          <div className="flex">
            <button 
              className="px-4 py-2 border-b-2 border-green-500 text-green-400">
              <i className="fas fa-spider"></i>
              <span className="ml-2 hidden-below-1084">Crawler</span>
            </button>
            <a 
              href="/forge"
              className="px-4 py-2 text-gray-400 hover:text-purple-400">
              <i className="fas fa-hammer"></i>
              <span className="ml-2 hidden-below-1084">Forge</span>
            </a>
            <a 
              href="/vault" 
              className="px-4 py-2 text-gray-400 hover:text-blue-400">
              <i className="fas fa-archive"></i>
              <span className="ml-2 hidden-below-1084">Vault</span>
            </a>
            <a 
              href="/about"
              className="px-4 py-2 text-gray-400 hover:text-orange-400">
              <i className="fas fa-info-circle"></i>
              <span className="ml-2 hidden-below-1084">About</span>
            </a>
          </div>
          
          {authStatus === 'authorized' && (
            <div className="flex items-center space-x-4 text-xs text-gray-400">
              {/* Brain Token Status Button */}
              <TokenStatusButton 
                onTokenModalOpen={() => setShowTokenModal(true)}
                size="md"
              />

              
              {/* Screenshot Mode Selection */}
              <div className="flex items-center space-x-1 bg-gray-900 p-1 rounded" title="Screenshot capture mode">
                <label className={`cursor-pointer px-2 py-1 rounded transition-colors ${(!screenshotMode || screenshotMode === 'off') ? 'bg-gray-800 text-white' : 'hover:bg-gray-700'}`} title="No screenshots">
                  <input
                    type="radio"
                    name="screenshotMode"
                    value="off"
                    checked={!screenshotMode || screenshotMode === 'off'}
                    onChange={() => handleScreenshotModeChange('off')}
                    className="sr-only"
                  />
                  <i className="fas fa-times"></i>
                </label>
                <label className={`cursor-pointer px-2 py-1 rounded transition-colors ${screenshotMode === 'top' ? 'bg-blue-800 text-white' : 'hover:bg-gray-700'}`} title="Screenshot top of page only">
                  <input
                    type="radio"
                    name="screenshotMode"
                    value="top"
                    checked={screenshotMode === 'top'}
                    onChange={() => handleScreenshotModeChange('top')}
                    className="sr-only"
                  />
                  <i className="fas fa-crop"></i>
                </label>
                <label className={`cursor-pointer px-2 py-1 rounded transition-colors ${screenshotMode === 'full' ? 'bg-green-800 text-white' : 'hover:bg-gray-700'}`} title="Screenshot full page">
                  <input
                    type="radio"
                    name="screenshotMode"
                    value="full"
                    checked={screenshotMode === 'full'}
                    onChange={() => handleScreenshotModeChange('full')}
                    className="sr-only"
                  />
                  <i className="fas fa-expand-arrows-alt"></i>
                </label>
              </div>
              
              {/* OCR Toggle (always visible, disabled when screenshots off) */}
              <div className="flex items-center space-x-1 bg-gray-900 p-1 rounded" title="OCR text extraction from screenshots">
                <label className={`cursor-pointer px-2 py-1 rounded transition-colors ${
                  (!screenshotMode || screenshotMode === 'off') 
                    ? (ocrEnabled ? 'bg-purple-800 text-white opacity-50' : 'opacity-50 hover:bg-gray-700')
                    : (ocrEnabled ? 'bg-purple-800 text-white' : 'hover:bg-gray-700')
                }`} title={
                  (!screenshotMode || screenshotMode === 'off')
                    ? 'OCR disabled - Click to enable screenshots and OCR'
                    : (ocrEnabled ? 'OCR enabled - Extract text from images' : 'OCR disabled')
                }>
                  <input
                    type="checkbox"
                    checked={ocrEnabled}
                    onChange={handleOcrToggle}
                    className="sr-only"
                  />
                  <i className={`fas ${ocrEnabled ? 'fa-eye' : 'fa-eye-slash'}`}></i>
                </label>
              </div>

             
              {/* Report Name Toggle */}
              <div className="flex items-center space-x-1 bg-gray-900 p-1 rounded" title="Enable or disable custom report naming">
                <label className={`cursor-pointer px-2 py-1 rounded transition-colors ${reportNamesEnabled ? 'bg-orange-800 text-white' : 'hover:bg-gray-700'}`} title={reportNamesEnabled ? 'Report names enabled - Can specify custom report names' : 'Report names disabled - Uses simple domain-based naming'}>
                  <input
                    type="checkbox"
                    checked={reportNamesEnabled}
                    onChange={handleReportNamesToggle}
                    className="sr-only"
                  />
                  <i className={`fas ${reportNamesEnabled ? 'fa-tag' : 'fa-hashtag'}`}></i>
                </label>
              </div>

              {/* Markdown Quality Selection */}
              <div className="flex items-center space-x-1 bg-gray-900 p-1 rounded" title="Choose markdown extraction quality level">
                <label className={`cursor-pointer px-2 py-1 rounded ${markdownQuality === 'enhanced' ? 'bg-green-800 text-white' : ''}`} title="Enhanced - AI-powered content extraction with better formatting">
                 <input
                   type="radio"
                   name="markdownQuality"
                   value="enhanced"
                   checked={markdownQuality === 'enhanced'}
                   onChange={() => {
                     setMarkdownQuality('enhanced');
                     localStorage.setItem('gnosis_markdown_quality', 'enhanced');
                   }}
                   className="sr-only"
                 />
                 <i className="fas fa-magic"></i>
                </label>
                <label className={`cursor-pointer px-2 py-1 rounded ${markdownQuality === 'basic' ? 'bg-blue-800 text-white' : ''}`} title="Basic - Standard markdown conversion, faster processing">
                 <input
                   type="radio"
                   name="markdownQuality"
                   value="basic"
                   checked={markdownQuality === 'basic'}
                   onChange={() => {
                     setMarkdownQuality('basic');
                     localStorage.setItem('gnosis_markdown_quality', 'basic');
                   }}
                   className="sr-only"
                 />
                 <i className="fas fa-file-alt"></i>
                </label>
                <label className={`cursor-pointer px-2 py-1 rounded ${markdownQuality === 'none' ? 'bg-gray-800 text-white' : ''}`} title="Raw - Original HTML content without markdown conversion">
                 <input
                   type="radio"
                   name="markdownQuality"
                   value="none"
                   checked={markdownQuality === 'none'}
                   onChange={() => {
                     setMarkdownQuality('none');
                     localStorage.setItem('gnosis_markdown_quality', 'none');
                   }}
                   className="sr-only"
                 />
                 <i className="fas fa-code"></i>
               </label>
             </div>
             
              {/* JavaScript Toggle */}
              <div className="flex items-center space-x-1 bg-gray-900 p-1 rounded" title="Force JavaScript execution during crawling">
                <label className={`cursor-pointer px-2 py-1 rounded transition-colors ${forceJavascript ? 'bg-blue-800 text-white' : 'hover:bg-gray-700'}`} title={forceJavascript ? 'JavaScript enabled - Will execute JS on all pages' : 'JavaScript disabled - Faster crawling, may miss dynamic content'}>
                 <input
                   type="checkbox"
                   checked={forceJavascript}
                   onChange={(e) => {
                     setForceJavascript(e.target.checked);
                     localStorage.setItem('gnosis_force_javascript', e.target.checked.toString());
                     addLog(`JavaScript force ${e.target.checked ? 'enabled' : 'disabled'}`);
                   }}
                   className="sr-only"
                 />
                 <i className={`fas ${forceJavascript ? 'fa-toggle-on' : 'fa-toggle-off'}`}></i>
               </label>
             </div>
             
             {/* Logout Button */}
             <button 
               onClick={() => setShowLogoutModal(true)}
               className="flex items-center space-x-1 bg-gray-900 p-1 rounded hover:bg-gray-700 transition-colors"
               title="Logout"
             >
               <div className="px-2 py-1 text-red-400 hover:text-red-300">
                 <i className="fas fa-sign-out-alt"></i>
               </div>
             </button>
           </div>
         )}
       </div>
       
       <div className="flex flex-col">
         <div className="flex flex-col space-y-2">
           <div className="flex space-x-2">
             <div className="relative flex-grow">
               <input
                 type={authStatus === 'authorized' ? 'text' : 'password'}
                 placeholder={authStatus === 'authorized' ? "Enter URL or summon phrase..." : "Enter authentication key..."}
                 className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded focus:outline-none focus:border-green-500"
                 value={inputValue}
                 onChange={(e) => setInputValue(e.target.value)}
                 onKeyPress={handleKeyPress}
                 onKeyDown={(e) => {
                   if (e.key === 'Escape') {
                     setShowHistory(false);
                   }
                 }}
                 onFocus={() => authStatus === 'authorized' && urlHistory.length > 0 && setShowHistory(true)}
                 onBlur={() => setTimeout(() => setShowHistory(false), 200)}
               />
               {authStatus === 'authorized' && showHistory && urlHistory.length > 0 && (
                 <div className="absolute z-10 w-full mt-1 bg-gray-800 border border-gray-700 rounded shadow-lg">
                   <ul className="max-h-48 overflow-auto">
                     {urlHistory.map((url, index) => (
                       <li 
                         key={index}
                         className="px-3 py-2 text-sm hover:bg-gray-700 cursor-pointer truncate"
                         onClick={() => {
                           setInputValue(url);
                           setShowHistory(false);
                         }}
                       >
                         {url}
                       </li>
                     ))}
                   </ul>
                 </div>
               )}
             </div>
             <button
               className={`px-4 py-2 bg-green-800 hover:bg-green-700 text-white rounded disabled:opacity-50 ${
                 isButtonDisabled() ? 'cursor-not-allowed' : ''
               }`}
               onClick={authStatus === 'authorized' ? handleSearch : handleAuthenticate}
               disabled={isButtonDisabled()}
             >
               {getButtonText()}
             </button>
           </div>
           
           {/* Custom Report Name Field - Only show when authorized and report names enabled */}
           {authStatus === 'authorized' && reportNamesEnabled && (
             <div className="flex items-center space-x-2">
               <label className="text-xs text-gray-400 min-w-max">Report Name:</label>
               <input
                 type="text"
                 placeholder="Optional custom name for report (leave empty for auto-generated)"
                 className="flex-grow px-3 py-1 bg-gray-900 border border-gray-700 rounded focus:outline-none focus:border-blue-500 text-sm"
                 value={customReportName}
                 onChange={(e) => setCustomReportName(e.target.value)}
                 onKeyPress={(e) => {
                   if (e.key === 'Enter') {
                     e.preventDefault();
                     if (authStatus === 'authorized' && !isCrawling && inputValue.trim()) {
                       handleSearch();
                     }
                   }
                 }}
               />
               {customReportName && (
                 <button
                   onClick={() => setCustomReportName('')}
                   className="px-2 py-1 text-gray-400 hover:text-gray-300 text-xs"
                   title="Clear custom name"
                 >
                   ✕
                 </button>
               )}
             </div>
           )}
           
           {/* Report Naming Status - Show when authorized and names disabled */}
           {authStatus === 'authorized' && !reportNamesEnabled && (
             <div className="flex items-center space-x-2 text-xs text-gray-500">
               <i className="fas fa-hashtag"></i>
               <span>Using simple domain-based naming (e.g., splunk_com.md)</span>
             </div>
           )}
         </div>
         
         {authStatus === 'authorized' && urlHistory.length > 0 && (
           <div className="mt-2 flex space-x-1 items-center">
             <span className="text-xs text-gray-500">Recent:</span>
             <div className="flex flex-wrap gap-1">
               {urlHistory.slice(0, 3).map((url, index) => (
                 <button
                   key={index}
                   className="px-2 py-1 text-xs bg-gray-900 hover:bg-gray-700 rounded border border-gray-700"
                   onClick={() => setInputValue(url)}
                   title={url}
                 >
                   {url.length > 30 ? url.substring(0, 30) + '...' : url}
                 </button>
               ))}
               {urlHistory.length > 3 && (
                 <button
                   className="px-2 py-1 text-xs bg-gray-900 hover:bg-gray-700 rounded border border-gray-700"
                   onClick={() => setShowHistory(!showHistory)}
                 >
                   +{urlHistory.length - 3} more
                 </button>
               )}
               <button
                 className="px-2 py-1 text-xs bg-gray-900 hover:bg-gray-700 rounded border border-gray-700 text-red-400"
                 onClick={() => {
                   // Create confirmation modal
                   const confirmModal = document.createElement('div');
                   confirmModal.className = 'fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50';
                   confirmModal.innerHTML = `
                     <div class="bg-gray-800 border border-red-500 rounded-lg p-6 max-w-md w-full mx-4">
                       <div class="flex items-center mb-4">
                         <i class="fas fa-exclamation-triangle text-red-500 text-xl mr-3"></i>
                         <h3 class="text-lg font-semibold text-red-400">Clear Search History</h3>
                       </div>
                       <p class="text-gray-300 mb-6">
                         Are you sure you want to clear all URL search history? This action cannot be undone.
                       </p>
                       <div class="flex justify-end space-x-3">
                         <button class="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded text-sm transition-colors" id="cancel-clear-btn">
                           Cancel
                         </button>
                         <button class="px-4 py-2 bg-red-700 hover:bg-red-600 text-white rounded text-sm transition-colors" id="confirm-clear-btn">
                           <i class="fas fa-trash mr-1"></i>Clear History
                         </button>
                       </div>
                     </div>
                   `;
                   document.body.appendChild(confirmModal);
                   
                   // Add event handlers
                   document.getElementById('cancel-clear-btn').addEventListener('click', () => {
                     document.body.removeChild(confirmModal);
                   });
                   
                   document.getElementById('confirm-clear-btn').addEventListener('click', () => {
                     localStorage.removeItem('gnosis_url_history');
                     setUrlHistory([]);
                     addLog('URL history has been cleared');
                     document.body.removeChild(confirmModal);
                   });
                   
                   // Close modal when clicking outside
                   confirmModal.addEventListener('click', (e) => {
                     if (e.target === confirmModal) {
                       document.body.removeChild(confirmModal);
                     }
                   });
                   
                   // Handle escape key
                   const handleEscape = (e) => {
                     if (e.key === 'Escape') {
                       document.body.removeChild(confirmModal);
                       document.removeEventListener('keydown', handleEscape);
                     }
                   };
                   document.addEventListener('keydown', handleEscape);
                 }}
                 title="Clear URL history"
               >
                 <span className="text-red-400">×</span> Clear
               </button>
             </div>
           </div>
         )}
       </div>
     </div>
     
     {/* Token Manager Modal */}
     <TokenManagerModal 
       isOpen={showTokenModal}
       onClose={() => setShowTokenModal(false)}
       onTokenUpdated={handleTokenUpdated}
     />
     
     {/* Logout Modal */}
     <LogoutModal 
       isOpen={showLogoutModal}
       onClose={() => setShowLogoutModal(false)}
       onConfirm={handleLogout}
       onClearTokens={handleClearAllTokens}
     />
   </>
  );
};

// Export the component
window.CrawlerInput = CrawlerInput;
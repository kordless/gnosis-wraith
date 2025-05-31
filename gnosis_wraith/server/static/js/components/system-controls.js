/**
 * System Controls Component
 * Displays system status, crawl statistics, and control options
 */

const SystemControls = ({
  authStatus,
  setAuthStatus,
  crawlStats,
  setCrawlStats,
  addLog
}) => {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-md p-4">
      <h2 className="text-xl mb-3">System Controls</h2>
      <div className="space-y-2">
        <div className={`${authStatus === 'authorized' ? 'text-green-500' : 'text-yellow-500'}`}>
          Status: {authStatus === 'authorized' ? 'AUTHORIZED' : 'UNAUTHORIZED'}
        </div>
        
        {authStatus === 'authorized' && (
          <>
            <div className="border-t border-gray-700 my-2 pt-2">
              <div className="text-green-400 font-semibold">Crawl Statistics</div>
            </div>

            <div className="grid grid-cols-3 gap-2 text-center text-sm">
              <div className="bg-gray-900 rounded p-1">
                <div className="text-gray-400">Total</div>
                <div className="text-xl">{crawlStats.total}</div>
              </div>
              <div className="bg-gray-900 rounded p-1">
                <div className="text-gray-400">Success</div>
                <div className="text-xl text-green-500">{crawlStats.success}</div>
              </div>
              <div className="bg-gray-900 rounded p-1">
                <div className="text-gray-400">Errors</div>
                <div className="text-xl text-red-500">{crawlStats.errors}</div>
              </div>
            </div>
            
            {crawlStats.lastUrl && (
              <div className="mt-2 text-xs bg-gray-900 rounded p-2 border border-gray-700">
                <div className="text-gray-400 mb-1">Last Crawled:</div>
                <div className="truncate text-green-300" title={crawlStats.lastUrl}>
                  {crawlStats.lastUrl}
                </div>
              </div>
            )}
            
            <button 
              className="w-full mt-2 bg-gray-900 hover:bg-gray-700 text-xs border border-gray-700 rounded p-1"
              onClick={() => {
                if (confirm('Are you sure you want to clear all crawl statistics?')) {
                  setCrawlStats({ total: 0, success: 0, errors: 0 });
                  localStorage.removeItem('gnosis_crawl_stats');
                  addLog('Crawl statistics have been reset');
                }
              }}
            >
              Reset Stats
            </button>
            
            <div className="border-t border-gray-700 my-2 pt-2">
              <div className="text-green-400 font-semibold mb-2">System Uptime</div>
              {(() => {
                const errorRate = crawlStats.total > 0 ? (crawlStats.errors / crawlStats.total) * 100 : 0;
                const successRate = 100 - errorRate;
                const uptimeColor = successRate >= 95 ? 'bg-green-500' : 
                                  successRate >= 80 ? 'bg-yellow-500' : 'bg-red-500';
                
                return (
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span>Success Rate</span>
                      <span>{successRate.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2 mb-2">
                      <div 
                        className={`h-2 rounded-full transition-all duration-300 ${uptimeColor}`}
                        style={{ width: `${successRate}%` }}
                      ></div>
                    </div>
                    <div className="text-xs text-gray-400">
                      {crawlStats.total > 0 ? 
                        `Error Rate: ${errorRate.toFixed(1)}% (${crawlStats.errors}/${crawlStats.total})` :
                        'No crawls recorded yet'
                      }
                    </div>
                  </div>
                );
              })()}
            </div>
            
            <div className="mt-3 border-t border-gray-700 pt-3">
              <div className="text-green-400 font-semibold mb-2">LLM Settings</div>
              
              {/* Provider selection dropdown */}
              <div className="text-xs text-gray-400 mb-1">LLM Provider:</div>
              <div className="mb-2">
                <select 
                  className="w-full px-2 py-1 bg-gray-900 border border-gray-700 rounded text-xs"
                  value={localStorage.getItem('gnosis_wraith_llm_provider') || 'anthropic'}
                  onChange={(e) => {
                    // Save the selected provider
                    localStorage.setItem('gnosis_wraith_llm_provider', e.target.value);
                    addLog(`Provider set to ${e.target.value}`);
                    
                    // Force re-render to update the key input field
                    setCrawlStats({...crawlStats});
                  }}
                >
                  <option value="anthropic">Anthropic (Claude)</option>
                  <option value="openai">OpenAI (GPT)</option>
                  <option value="gemini">Google (Gemini)</option>
                </select>
              </div>
              
              {/* API Key input field that adapts based on selected provider */}
              {(() => {
                // Get current provider
                const provider = localStorage.getItem('gnosis_wraith_llm_provider') || 'anthropic';
                
                // Key name and placeholder based on provider
                let keyName, placeholder, cookieName;
                
                switch(provider) {
                  case 'anthropic':
                    keyName = 'Anthropic API Token';
                    placeholder = 'sk-ant-api...';
                    cookieName = 'gnosis_wraith_llm_token_anthropic';
                    break;
                  case 'openai':
                    keyName = 'OpenAI API Token';
                    placeholder = 'sk-...';
                    cookieName = 'gnosis_wraith_llm_token_openai';
                    break;
                  case 'gemini':
                    keyName = 'Google Gemini API Token';
                    placeholder = 'api_key...';
                    cookieName = 'gnosis_wraith_llm_token_gemini';
                    break;
                  default:
                    keyName = 'API Token';
                    placeholder = 'Enter API token';
                    cookieName = 'gnosis_wraith_llm_token_anthropic';
                }
                
                // Get the current API key from the cookie
                // Verify CookieUtils exists before attempting to use it
                const currentKey = (typeof CookieUtils !== 'undefined') 
                  ? CookieUtils.getCookie(cookieName) 
                  : (() => { console.error('CookieUtils not available'); return ''; })();
                
                return (
                  <>
                    <div className="text-xs text-gray-400 mb-1">{keyName}:</div>
                    <div className="flex space-x-1">
                      <input 
                        type="password"
                        className="flex-grow px-2 py-1 bg-gray-900 border border-gray-700 rounded text-xs cursor-pointer"
                        placeholder={currentKey ? "••••••••••••••••••••" : "Click 'Set' to configure"}
                        value={currentKey ? "••••••••••••••••••••" : ""}
                        readOnly={true}
                        onClick={() => {
                          // Click the Set/Clear button when field is clicked
                          const button = document.querySelector(`button:contains("${currentKey ? 'Clear' : 'Set'}")`);
                          if (button) button.click();
                        }}
                        title="Click 'Set' button to configure API token"
                      />
                      <button
                        className="px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-xs"
                        onClick={() => {
                          // If we have a key, confirm deletion
                          if (currentKey) {
                            // Create an inline modal for confirmation
                            const confirmBox = document.createElement('div');
                            confirmBox.className = 'fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50';
                            confirmBox.innerHTML = `
                              <div class="bg-gray-800 border border-gray-700 rounded-md p-4 max-w-md w-full">
                                <div class="text-green-400 font-semibold mb-2">Confirm</div>
                                <div class="text-white mb-4">Are you sure you want to remove this API key?</div>
                                <div class="flex justify-end space-x-2">
                                  <button class="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded text-sm" id="cancel-btn">Cancel</button>
                                  <button class="px-3 py-1 bg-red-700 hover:bg-red-600 text-white rounded text-sm" id="confirm-btn">Remove</button>
                                </div>
                              </div>
                            `;
                            document.body.appendChild(confirmBox);
                            
                            // Add event handlers
                            document.getElementById('cancel-btn').addEventListener('click', () => {
                              document.body.removeChild(confirmBox);
                            });
                            document.getElementById('confirm-btn').addEventListener('click', () => {
                              if (typeof CookieUtils !== 'undefined') {
                                CookieUtils.deleteCookie(cookieName);
                              } else {
                                console.error('CookieUtils not available - unable to delete cookie');
                              }
                              addLog(`${keyName} removed`);
                              document.body.removeChild(confirmBox);
                              // Force re-render by updating state
                              setCrawlStats({...crawlStats});
                            });
                          } else {
                            // Create an inline modal for entering a new key
                            const inputBox = document.createElement('div');
                            inputBox.className = 'fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50';
                            inputBox.innerHTML = `
                              <div class="bg-gray-800 border border-gray-700 rounded-md p-4 max-w-md w-full">
                                <div class="text-green-400 font-semibold mb-2">Enter ${keyName}</div>
                                <input type="text" id="api-key-input" class="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded mb-4" placeholder="${placeholder}"/>
                                <div class="flex justify-end space-x-2">
                                  <button class="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded text-sm" id="cancel-key-btn">Cancel</button>
                                  <button class="px-3 py-1 bg-green-700 hover:bg-green-600 text-white rounded text-sm" id="save-key-btn">Save</button>
                                </div>
                              </div>
                            `;
                            document.body.appendChild(inputBox);
                            
                            // Focus the input field
                            setTimeout(() => {
                              document.getElementById('api-key-input').focus();
                            }, 100);
                            
                            // Add event handlers
                            document.getElementById('cancel-key-btn').addEventListener('click', () => {
                              document.body.removeChild(inputBox);
                            });
                            document.getElementById('save-key-btn').addEventListener('click', () => {
                              const inputEl = document.getElementById('api-key-input');
                              const newKey = inputEl.value.trim();
                              
                              if (newKey) {
                                if (typeof CookieUtils !== 'undefined') {
                                  CookieUtils.setCookie(cookieName, newKey);
                                } else {
                                  console.error('CookieUtils not available - unable to set cookie');
                                }
                                addLog(`${keyName} saved`);
                                document.body.removeChild(inputBox);
                                // Force re-render by updating state
                                setCrawlStats({...crawlStats});
                              } else {
                                // Highlight input with red border if empty
                                inputEl.classList.add('border-red-500');
                                setTimeout(() => {
                                  inputEl.classList.remove('border-red-500');
                                }, 2000);
                              }
                            });
                            
                            // Handle enter key
                            document.getElementById('api-key-input').addEventListener('keydown', (e) => {
                              if (e.key === 'Enter') {
                                document.getElementById('save-key-btn').click();
                              } else if (e.key === 'Escape') {
                                document.getElementById('cancel-key-btn').click();
                              }
                            });
                          }
                        }}
                      >
                        {currentKey ? 'Clear' : 'Set'}
                      </button>
                    </div>
                  </>
                );
              })()}
              
              {/* Security info */}
              <div className="mt-2 text-xs text-gray-500 italic">
                API tokens are stored locally in cookies with SameSite=Strict
              </div>
            </div>
            
            <button 
              className="w-full mt-3 bg-gray-900 hover:bg-gray-700 text-xs border border-gray-700 rounded p-1"
              onClick={() => {
                // Create a nice modal for logout confirmation
                const logoutModal = document.createElement('div');
                logoutModal.className = 'fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50';
                logoutModal.innerHTML = `
                  <div class="bg-gray-800 border border-red-500 rounded-lg p-6 max-w-md w-full mx-4">
                    <div class="flex items-center mb-4">
                      <i class="fas fa-exclamation-triangle text-red-500 text-xl mr-3"></i>
                      <h3 class="text-lg font-semibold text-red-400">WIPE SYSTEM</h3>
                    </div>
                    <p class="text-gray-300 mb-4">
                      Choose your logout method:
                    </p>
                    <div class="space-y-3 mb-6">
                      <div class="bg-gray-900 border border-gray-700 rounded p-3">
                        <div class="font-semibold text-yellow-400 mb-1">Standard Logout</div>
                        <div class="text-sm text-gray-400">Clear authentication only. Keep LLM tokens and settings.</div>
                      </div>
                      <div class="bg-gray-900 border border-red-700 rounded p-3">
                        <div class="font-semibold text-red-400 mb-1">WIPE ALL DATA</div>
                        <div class="text-sm text-gray-400">Clear authentication AND all stored tokens/cookies.</div>
                      </div>
                    </div>
                    <div class="flex justify-end space-x-3">
                      <button class="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded text-sm transition-colors" id="cancel-logout-btn">
                        Cancel
                      </button>
                      <button class="px-4 py-2 bg-yellow-700 hover:bg-yellow-600 text-white rounded text-sm transition-colors" id="standard-logout-btn">
                        <i class="fas fa-sign-out-alt mr-1"></i>Standard Logout
                      </button>
                      <button class="px-4 py-2 bg-red-700 hover:bg-red-600 text-white rounded text-sm transition-colors" id="wipe-system-btn">
                        <i class="fas fa-trash mr-1"></i>WIPE SYSTEM
                      </button>
                    </div>
                  </div>
                `;
                document.body.appendChild(logoutModal);
                
                // Add event handlers
                document.getElementById('cancel-logout-btn').addEventListener('click', () => {
                  document.body.removeChild(logoutModal);
                });
                
                document.getElementById('standard-logout-btn').addEventListener('click', () => {
                  localStorage.removeItem('gnosis_auth_code');
                  setAuthStatus('unauthorized');
                  addLog('Authentication cleared');
                  addLog('System locked');
                  addLog('Awaiting new authentication...');
                  document.body.removeChild(logoutModal);
                });
                
                document.getElementById('wipe-system-btn').addEventListener('click', () => {
                  // Clear all localStorage
                  localStorage.clear();
                  
                  // Clear all cookies
                  document.cookie.split(";").forEach(function(c) { 
                    document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/"); 
                  });
                  
                  setAuthStatus('unauthorized');
                  addLog('SYSTEM WIPED - All data cleared');
                  addLog('Authentication cleared');
                  addLog('All tokens and cookies removed');
                  addLog('System reset complete');
                  addLog('Awaiting new authentication...');
                  document.body.removeChild(logoutModal);
                });
                
                // Close modal when clicking outside
                logoutModal.addEventListener('click', (e) => {
                  if (e.target === logoutModal) {
                    document.body.removeChild(logoutModal);
                  }
                });
                
                // Handle escape key
                const handleEscape = (e) => {
                  if (e.key === 'Escape') {
                    document.body.removeChild(logoutModal);
                    document.removeEventListener('keydown', handleEscape);
                  }
                };
                document.addEventListener('keydown', handleEscape);
              }}
            >
              Log Out
            </button>
          </>
        )}
      </div>
    </div>
  );
};

// Export the component
window.SystemControls = SystemControls;
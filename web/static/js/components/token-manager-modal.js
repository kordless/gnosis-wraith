/**
 * Token Manager Modal Component
 * Handles provider selection and token input/management
 */

const TokenManagerModal = ({ 
  isOpen, 
  onClose, 
  onTokenUpdated,
  className = "" 
}) => {
  const { useState, useEffect, useRef } = React;
  
  const [currentProvider, setCurrentProvider] = useState('anthropic');
  const [tokenInput, setTokenInput] = useState('');
  const [isVisible, setIsVisible] = useState(false);
  const modalRef = useRef(null);
  const inputRef = useRef(null);
  
  // Provider configurations
  const providers = {
    anthropic: { 
      name: 'Anthropic (Claude)',
      icon: 'fas fa-brain',
      cookieName: 'gnosis_wraith_llm_token_anthropic',
      placeholder: 'sk-ant-api...',
      color: 'orange'
    },
    openai: { 
      name: 'OpenAI (GPT)',
      icon: 'fas fa-robot',
      cookieName: 'gnosis_wraith_llm_token_openai',
      placeholder: 'sk-...',
      color: 'green'
    },
    gemini: { 
      name: 'Google (Gemini)',
      icon: 'fas fa-gem',
      cookieName: 'gnosis_wraith_llm_token_gemini',
      placeholder: 'API_KEY...',
      color: 'blue'
    }
  };
  
  // Initialize provider from localStorage
  useEffect(() => {
    const savedProvider = localStorage.getItem('gnosis_wraith_llm_provider') || 'anthropic';
    setCurrentProvider(savedProvider);
  }, []);
  
  // Handle modal visibility
  useEffect(() => {
    if (isOpen) {
      setIsVisible(true);
      // Focus input after modal animation
      setTimeout(() => {
        if (inputRef.current) {
          inputRef.current.focus();
        }
      }, 150);
    } else {
      setIsVisible(false);
      setTokenInput('');
    }
  }, [isOpen]);
  
  // Handle escape key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);
  
  // Handle click outside modal
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (modalRef.current && !modalRef.current.contains(event.target)) {
        onClose();
      }
    };
    
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);
  
  // Check if current provider has a token
  const hasCurrentToken = () => {
    const cookieName = providers[currentProvider]?.cookieName;
    return cookieName ? !!CookieUtils.getCookie(cookieName) : false;
  };
  
  // Get all providers with tokens
  const getProvidersWithTokens = () => {
    return Object.keys(providers).filter(key => {
      const cookieName = providers[key].cookieName;
      return CookieUtils.getCookie(cookieName);
    });
  };
  
  // Handle provider change
  const handleProviderChange = (newProvider) => {
    setCurrentProvider(newProvider);
    localStorage.setItem('gnosis_wraith_llm_provider', newProvider);
    setTokenInput(''); // Clear input when switching providers
  };
  
  // Handle save token
  const handleSaveToken = () => {
    if (!tokenInput.trim()) {
      // Highlight input with red border if empty
      if (inputRef.current) {
        inputRef.current.classList.add('border-red-500');
        setTimeout(() => {
          inputRef.current.classList.remove('border-red-500');
        }, 2000);
      }
      return;
    }
    
    const cookieName = providers[currentProvider].cookieName;
    CookieUtils.setCookie(cookieName, tokenInput.trim(), 90); // 90 days
    
    // Trigger update callback
    if (onTokenUpdated) {
      onTokenUpdated(currentProvider, tokenInput.trim());
    }
    
    // Close modal
    onClose();
  };
  
  // Handle clear current token
  const handleClearCurrentToken = () => {
    const cookieName = providers[currentProvider].cookieName;
    CookieUtils.deleteCookie(cookieName);
    
    // Trigger update callback
    if (onTokenUpdated) {
      onTokenUpdated(currentProvider, null);
    }
  };
  
  // Handle clear all tokens
  const handleClearAllTokens = () => {
    Object.values(providers).forEach(provider => {
      CookieUtils.deleteCookie(provider.cookieName);
    });
    
    // Trigger update callback for each provider
    if (onTokenUpdated) {
      Object.keys(providers).forEach(key => {
        onTokenUpdated(key, null);
      });
    }
  };
  
  // Handle enter key in input
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSaveToken();
    }
  };
  
  if (!isOpen) return null;
  
  const currentProviderConfig = providers[currentProvider];
  const providersWithTokens = getProvidersWithTokens();
  
  return (
    <div className={`fixed inset-0 z-50 flex items-center justify-center bg-black transition-opacity duration-200 ${isVisible ? 'bg-opacity-75' : 'bg-opacity-0'} ${className}`}>
      <div 
        ref={modalRef}
        className={`bg-gray-800 border-2 border-gray-600 rounded-lg shadow-2xl w-full max-w-md mx-4 p-6 transform transition-all duration-200 ${isVisible ? 'scale-100 opacity-100' : 'scale-95 opacity-0'}`}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-2">
            <i className="fas fa-key text-green-400"></i>
            <h2 className="text-xl font-bold text-green-400">LLM Token Manager</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white w-8 h-8 flex items-center justify-center rounded hover:bg-gray-700"
          >
            <i className="fas fa-times"></i>
          </button>
        </div>
        
        {/* Provider Selection */}
        <div className="mb-6">
          <label className="block text-sm font-semibold text-gray-300 mb-3">
            Select LLM Provider
          </label>
          <div className="grid grid-cols-1 gap-2">
            {Object.entries(providers).map(([key, config]) => (
              <button
                key={key}
                onClick={() => handleProviderChange(key)}
                className={`flex items-center space-x-3 p-3 border-2 transition-all ${currentProvider === key 
                  ? `border-${config.color}-500 bg-${config.color}-900 bg-opacity-20 text-${config.color}-400` 
                  : 'border-gray-600 bg-gray-700 text-gray-300 hover:border-gray-500 hover:bg-gray-650'
                }`}
                style={{ borderRadius: '0.5rem' }}
              >
                <div className="w-8 h-8 flex items-center justify-center border border-gray-500 bg-gray-800" style={{ borderRadius: '0.25rem' }}>
                  <i className={config.icon}></i>
                </div>
                <span className="font-medium flex-grow text-left">{config.name}</span>
                {CookieUtils.getCookie(config.cookieName) && (
                  <i className="fas fa-check text-green-400"></i>
                )}
              </button>
            ))}
          </div>
        </div>
        
        {/* Token Input */}
        <div className="mb-6">
          <label className="block text-sm font-semibold text-gray-300 mb-3">
            {currentProviderConfig.name} API Token
          </label>
          <input
            ref={inputRef}
            type="password"
            value={tokenInput}
            onChange={(e) => setTokenInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={currentProviderConfig.placeholder}
            className="w-full px-4 py-3 rounded-lg border-2 border-gray-600 bg-gray-900 text-gray-800 placeholder-gray-800 focus:border-green-500 focus:outline-none transition-colors duration-200 font-mono text-sm"
            style={{
              color: '#1f2937',
              backgroundColor: '#0f172a'
            }}
          />
          <p className="text-xs text-gray-500 mt-2">
            Token is encrypted and stored securely in browser cookies
          </p>
        </div>
        
        {/* Action Buttons */}
        <div className="flex flex-col space-y-3">
          <div className="flex space-x-3">
            <button
              onClick={handleSaveToken}
              disabled={!tokenInput.trim()}
              className="flex-1 px-4 py-2 bg-green-700 hover:bg-green-600 disabled:bg-gray-700 disabled:text-gray-500 text-white font-semibold rounded-lg transition-colors duration-200 flex items-center justify-center space-x-2"
            >
              <i className="fas fa-save"></i>
              <span>Save Token</span>
            </button>
            {hasCurrentToken() && (
              <button
                onClick={handleClearCurrentToken}
                className="px-4 py-2 bg-yellow-700 hover:bg-yellow-600 text-white font-semibold rounded-lg transition-colors duration-200 flex items-center justify-center space-x-2"
              >
                <i className="fas fa-eraser"></i>
                <span>Clear</span>
              </button>
            )}
          </div>
          {providersWithTokens.length > 0 && (
            <button
              onClick={handleClearAllTokens}
              className="w-full px-4 py-2 bg-red-700 hover:bg-red-600 text-white font-semibold rounded-lg transition-colors duration-200 flex items-center justify-center space-x-2"
            >
              <i className="fas fa-trash-alt"></i>
              <span>Clear All Tokens ({providersWithTokens.length})</span>
            </button>
          )}
        </div>
        
        {/* Footer Help Text */}
        <div className="mt-6 pt-4 border-t border-gray-700">
          <p className="text-xs text-gray-500 text-center">
            Press <kbd className="px-1 py-0.5 bg-gray-700 rounded text-gray-300">Enter</kbd> to save • 
            <kbd className="px-1 py-0.5 bg-gray-700 rounded text-gray-300 ml-1">Esc</kbd> to close
          </p>
        </div>
      </div>
    </div>
  );
};

window.TokenManagerModal = TokenManagerModal;
/**
 * Token Status Icon Component
 * Shows visual indicator for LLM token status with color coding
 * Red: Token set but not working, Yellow: Not set, Green: Working
 */

const TokenStatusIcon = ({ 
  onTokenModalOpen,
  className = "",
  size = "sm" // "sm", "md", "lg"
}) => {
  const { useState, useEffect } = React;
  
  const [tokenStatus, setTokenStatus] = useState('none'); // 'none', 'invalid', 'valid'
  const [currentProvider, setCurrentProvider] = useState('anthropic');
  
  // Provider configurations
  const providers = {
    anthropic: { 
      name: 'Anthropic',
      icon: 'fas fa-brain',
      cookieName: 'gnosis_wraith_llm_token_anthropic' 
    },
    openai: { 
      name: 'OpenAI',
      icon: 'fas fa-robot',
      cookieName: 'gnosis_wraith_llm_token_openai' 
    },
    gemini: { 
      name: 'Google Gemini',
      icon: 'fas fa-gem',
      cookieName: 'gnosis_wraith_llm_token_gemini' 
    }
  };
  
  // Size configurations
  const sizeClasses = {
    sm: 'w-6 h-6 text-sm',
    md: 'w-8 h-8 text-base',
    lg: 'w-10 h-10 text-lg'
  };
  
  // Check token status
  const checkTokenStatus = async () => {
    const provider = localStorage.getItem('gnosis_wraith_llm_provider') || 'anthropic';
    setCurrentProvider(provider);
    
    const cookieName = providers[provider]?.cookieName;
    if (!cookieName) return;
    
    const token = CookieUtils.getCookie(cookieName);
    
    if (!token) {
      setTokenStatus('none');
      return;
    }
    
    // For now, just assume valid if token exists
    // In the future, we could add actual token validation
    setTokenStatus('valid');
    
    // TODO: Add actual token validation by making API calls
    // This would require setting up endpoints to test each provider
  };
  
  // Update status when provider changes
  useEffect(() => {
    checkTokenStatus();
    
    // Listen for storage changes to update status
    const handleStorageChange = () => {
      checkTokenStatus();
    };
    
    window.addEventListener('storage', handleStorageChange);
    
    // Also check periodically
    const interval = setInterval(checkTokenStatus, 5000);
    
    return () => {
      window.removeEventListener('storage', handleStorageChange);
      clearInterval(interval);
    };
  }, []);
  
  // Get status-based styling
  const getStatusStyling = () => {
    switch (tokenStatus) {
      case 'none':
        return {
          bgColor: 'bg-yellow-600 hover:bg-yellow-500',
          textColor: 'text-yellow-900',
          borderColor: 'border-yellow-500',
          showText: true,
          statusText: 'SET'
        };
      case 'invalid':
        return {
          bgColor: 'bg-red-600 hover:bg-red-500',
          textColor: 'text-red-100',
          borderColor: 'border-red-500',
          showText: false,
          statusText: ''
        };
      case 'valid':
        return {
          bgColor: 'bg-green-600 hover:bg-green-500',
          textColor: 'text-green-100',
          borderColor: 'border-green-500',
          showText: false,
          statusText: ''
        };
      default:
        return {
          bgColor: 'bg-gray-600 hover:bg-gray-500',
          textColor: 'text-gray-100',
          borderColor: 'border-gray-500',
          showText: false,
          statusText: ''
        };
    }
  };
  
  const styling = getStatusStyling();
  const providerConfig = providers[currentProvider] || providers.anthropic;
  
  return (
    <div className={`flex items-center space-x-1 ${className}`}>
      <button
        onClick={onTokenModalOpen}
        className={`
          ${sizeClasses[size]} 
          ${styling.bgColor} 
          ${styling.textColor}
          border-2 ${styling.borderColor}
          rounded-full 
          flex items-center justify-center
          transition-all duration-200
          hover:scale-105
          active:scale-95
          shadow-md hover:shadow-lg
        `}
        title={`${providerConfig.name} API Token - ${
          tokenStatus === 'none' ? 'Not Set' : 
          tokenStatus === 'invalid' ? 'Invalid' : 
          'Valid'
        }`}
      >
        <i className={providerConfig.icon}></i>
      </button>
      
      {styling.showText && (
        <span className="text-xs text-yellow-400 font-semibold">
          {styling.statusText}
        </span>
      )}
    </div>
  );
};

window.TokenStatusIcon = TokenStatusIcon;
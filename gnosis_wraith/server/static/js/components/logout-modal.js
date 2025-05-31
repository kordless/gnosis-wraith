/**
 * Logout Modal Component
 * Handles logout with option to clear all tokens
 */

const LogoutModal = ({ 
  isOpen, 
  onClose, 
  onConfirm,
  onClearTokens,
  className = "" 
}) => {
  const { useState, useEffect, useRef } = React;
  
  const [clearTokensChecked, setClearTokensChecked] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const modalRef = useRef(null);
  
  // Handle modal visibility
  useEffect(() => {
    if (isOpen) {
      setIsVisible(true);
    } else {
      setIsVisible(false);
      setClearTokensChecked(false); // Reset checkbox when modal closes
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
  
  // Check if any tokens exist
  const hasTokens = () => {
    const tokenCookies = [
      'gnosis_wraith_llm_token_anthropic',
      'gnosis_wraith_llm_token_openai', 
      'gnosis_wraith_llm_token_gemini'
    ];
    
    return tokenCookies.some(cookieName => CookieUtils.getCookie(cookieName));
  };
  
  // Handle confirm logout
  const handleConfirmLogout = () => {
    if (clearTokensChecked && onClearTokens) {
      onClearTokens();
    }
    
    if (onConfirm) {
      onConfirm();
    }
    
    onClose();
  };
  
  if (!isOpen) return null;
  
  return (
    <div className={`
      fixed inset-0 z-50 flex items-center justify-center
      bg-black transition-opacity duration-200
      ${isVisible ? 'bg-opacity-75' : 'bg-opacity-0'}
      ${className}
    `}>
      <div 
        ref={modalRef}
        className={`
          bg-gray-800 border-2 border-gray-600 rounded-lg shadow-2xl
          w-full max-w-md mx-4 p-6
          transform transition-all duration-200
          ${isVisible ? 'scale-100 opacity-100' : 'scale-95 opacity-0'}
        `}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-2">
            <i className="fas fa-sign-out-alt text-red-400"></i>
            <h2 className="text-xl font-bold text-red-400">Confirm Logout</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white w-8 h-8 flex items-center justify-center rounded hover:bg-gray-700"
          >
            <i className="fas fa-times"></i>
          </button>
        </div>
        
        {/* Content */}
        <div className="mb-6">
          <p className="text-gray-300 mb-4">
            Are you sure you want to log out? This will clear your authentication session.
          </p>
          
          {/* Clear tokens option - only show if tokens exist */}
          {hasTokens() && (
            <div className="bg-yellow-900 bg-opacity-20 border border-yellow-700 rounded-lg p-4 mb-4">
              <label className="flex items-start space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={clearTokensChecked}
                  onChange={(e) => setClearTokensChecked(e.target.checked)}
                  className="mt-1 w-4 h-4 text-yellow-600 bg-gray-700 border-gray-600 rounded focus:ring-yellow-500 focus:ring-2"
                />
                <div>
                  <span className="text-yellow-400 font-semibold block">
                    Also clear all LLM API tokens
                  </span>
                  <span className="text-yellow-300 text-sm">
                    This will remove all saved API tokens for Anthropic, OpenAI, and Google Gemini
                  </span>
                </div>
              </label>
            </div>
          )}
        </div>
        
        {/* Action Buttons */}
        <div className="flex space-x-3">
          <button
            onClick={onClose}
            className="
              flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600
              text-white font-semibold rounded-lg
              transition-colors duration-200
              flex items-center justify-center space-x-2
            "
          >
            <i className="fas fa-arrow-left"></i>
            <span>Cancel</span>
          </button>
          
          <button
            onClick={handleConfirmLogout}
            className="
              flex-1 px-4 py-2 bg-red-700 hover:bg-red-600
              text-white font-semibold rounded-lg
              transition-colors duration-200
              flex items-center justify-center space-x-2
            "
          >
            <i className="fas fa-sign-out-alt"></i>
            <span>Logout</span>
          </button>
        </div>
        
        {/* Footer Help Text */}
        <div className="mt-4 pt-4 border-t border-gray-700">
          <p className="text-xs text-gray-500 text-center">
            Press <kbd className="px-1 py-0.5 bg-gray-700 rounded text-gray-300">Esc</kbd> to cancel
          </p>
        </div>
      </div>
    </div>
  );
};

window.LogoutModal = LogoutModal;
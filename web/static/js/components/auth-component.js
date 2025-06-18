/**
 * Authentication Component
 * Handles user authentication for the Gnosis Wraith system
 */

const AuthenticationComponent = ({ 
  authStatus, 
  setAuthStatus, 
  inputValue, 
  setInputValue, 
  addLog 
}) => {

  const handleAuthenticate = () => {
    if (inputValue.trim()) {
      setAuthStatus('authenticating');
      addLog(`Authentication attempt: ${inputValue.substring(0, 3)}${'*'.repeat(inputValue.length - 3)}`);
      
      // Removed c0d3z pattern validation
      if (inputValue.trim()) {

        setTimeout(() => {
          // Check if this is a different code than what's currently stored
          const currentStoredCode = localStorage.getItem('gnosis_auth_code') || CookieUtils.getCookie('gnosis_auth_code');
          
          if (currentStoredCode && currentStoredCode !== inputValue) {
            // Different code - clear all existing data first
            addLog(`New authentication code detected`);
            addLog(`Clearing previous session data for security`);
            
            // Clear all localStorage except the new auth code we're about to set
            localStorage.clear();
            
            // Clear all cookies
            document.cookie.split(";").forEach(function(c) { 
              document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/"); 
            });
            
            addLog(`Previous session data cleared`);
          }
          
          setAuthStatus('authorized');
          addLog('Authentication successful');
          addLog(`Access code verified: ${inputValue}`);
          addLog('Distributed crawler system online');
          addLog('Memory banks accessible');
          setInputValue('');
          
          // Store the new auth code in both localStorage and cookies
          localStorage.setItem('gnosis_auth_code', inputValue);
          
          // Also store in cookie with 90 day expiration
          CookieUtils.setCookie('gnosis_auth_code', inputValue, 90);
          
          // Log successful auth to server (optional)
          logToServer('authentication', { code: inputValue });
        }, 1000);
      } else if (inputValue.toLowerCase() === 'password') {
        // Legacy password for testing
        setTimeout(() => {
          setAuthStatus('authorized');
          addLog('Legacy authentication successful');
          addLog('Distributed crawler system online');
          addLog('Memory banks accessible');
          addLog('WARNING: Using legacy credentials');
          setInputValue('');
        }, 1000);
      } else {
        // Failed authentication
        setTimeout(() => {
          setAuthStatus('unauthorized');
          addLog('Authentication failed');
          addLog('Access denied: Invalid code format');
          addLog('Invalid authentication code');

          setInputValue('');
        }, 1000);
      }
    }
  };

  // Function to log events to server
  const logToServer = async (eventType, data) => {
    try {
      // Add timestamp to all log entries
      const logData = {
        ...data,
        timestamp: new Date().toISOString(),
        event: eventType
      };
      
      // Log the event to the client console for debugging
      console.log(`Logging to server: ${eventType}`, logData);
      
      // Send the log to server
      const response = await fetch('/api/log', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(logData)
      });
      
      // Only add the log to the UI if the server request was successful
      if (response.ok) {
        addLog(`Event logged: ${eventType}`);
      }
    } catch (error) {
      // Silent fail if logging fails - doesn't affect the user experience
      console.error('Error logging to server:', error);
    }
  };
  
  return null; // This is a logic-only component, no UI rendering
};

// Export the component to be used in other files
window.AuthenticationComponent = AuthenticationComponent;
  // Function to handle logout
  const handleLogout = () => {
    // Clear auth code from both localStorage and cookies
    localStorage.removeItem('gnosis_auth_code');
    if (typeof CookieUtils !== 'undefined') {
      CookieUtils.deleteCookie('gnosis_auth_code');
    }
    
    // Reset auth status
    setAuthStatus('unauthorized');
    setInputValue('');
    
    // Log the logout
    addLog('Authentication session terminated');
    addLog('System logged out successfully');
  };
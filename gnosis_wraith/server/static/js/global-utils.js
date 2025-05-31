/**
 * Global Utilities for Gnosis Wraith
 * Ensures utilities are available globally
 */

// Create global CookieUtils if not already defined
if (typeof window.CookieUtils === 'undefined') {
  window.CookieUtils = {
    // Get cookie value by name
    getCookie(name) {
      const nameEQ = `${name}=`;
      const ca = document.cookie.split(';');
      for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') c = c.substring(1);
        if (c.indexOf(nameEQ) === 0) {
          return c.substring(nameEQ.length, c.length);
        }
      }
      return '';
    },
    
    // Set cookie with expiration
    setCookie(name, value, days = 90) {
      const date = new Date();
      date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
      const expires = `expires=${date.toUTCString()}`;
      document.cookie = `${name}=${value};${expires};path=/;SameSite=Strict`;
    },
    
    // Delete cookie
    deleteCookie(name) {
      document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;`;
    }
  };
}

// Create global ensureUrlProtocol if not already defined
if (typeof window.ensureUrlProtocol === 'undefined') {
  window.ensureUrlProtocol = function(url) {
    if (!url || typeof url !== 'string') return url;
    
    // Trim whitespace
    const trimmed = url.trim();
    
    // Check if URL already has a protocol
    if (/^(https?:\/\/)/i.test(trimmed)) {
      return trimmed; // Already has protocol, return as is
    }
    
    // Check if URL starts with www.
    if (/^www\./i.test(trimmed)) {
      return `https://${trimmed}`; // Add https:// to www.
    }
    
    // Check if it's a domain-like string without protocol
    const domainPattern = /^([a-z0-9][a-z0-9-]*[a-z0-9]?\.)+[a-z0-9][a-z0-9-]*[a-z0-9]?/i;
    if (domainPattern.test(trimmed)) {
      return `https://${trimmed}`; // Add https:// to domain
    }
    
    // Return original if not matching any URL patterns
    return url;
  };
}

// Create global isLikelyUrl if not already defined
if (typeof window.isLikelyUrl === 'undefined') {
  window.isLikelyUrl = function(input) {
    if (!input || typeof input !== 'string') return false;
    
    // Trim the input
    const trimmed = input.trim();
    
    // Check for common URL patterns
    const hasProtocol = /^(https?:\/\/)/i.test(trimmed);
    const hasWww = /^www\./i.test(trimmed);
    const hasDomain = /^([a-z0-9][a-z0-9-]*[a-z0-9]?\.)+[a-z0-9][a-z0-9-]*[a-z0-9]?/i.test(trimmed);
    
    // Look for TLDs (not exhaustive, just common ones)
    const commonTlds = ['.com', '.org', '.net', '.edu', '.gov', '.io', '.co', '.ai', '.app'];
    const hasTld = commonTlds.some(tld => trimmed.includes(tld));
    
    // Special case for IP addresses
    const isIpAddress = /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?(\/.*)?$/i.test(trimmed);
    
    // Return true if this looks like a URL
    return (hasProtocol || hasWww || (hasDomain && hasTld) || isIpAddress);
  };
}

// Add log function for debugging
console.log('Global utilities loaded successfully - v1.0.1');

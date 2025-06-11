/**
 * Gnosis Wraith Utility Functions
 * Contains shared functionality used across the application
 */

// Function to format JSON with syntax highlighting and better word wrapping
function formatJsonForDisplay(jsonString) {
  try {
    // First, parse and re-stringify the JSON to ensure proper format
    const obj = typeof jsonString === 'string' ? JSON.parse(jsonString) : jsonString;
    
    // Replace JSON syntax with HTML spans for syntax highlighting
    return JSON.stringify(obj, null, 2)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/(\"(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*\"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, 
        function (match) {
          let cls = 'text-blue-400'; // Default for numbers
          
          if (/^\"/.test(match)) {
            if (/:$/.test(match)) {
              cls = 'text-purple-400 font-semibold'; // Keys
            } else {
              cls = 'text-green-400'; // Strings
            }
          } else if (/true|false/.test(match)) {
            cls = 'text-yellow-500'; // Booleans
          } else if (/null/.test(match)) {
            cls = 'text-red-400'; // null values
          }
          
          return '<span class="' + cls + '">' + match + '</span>';
        });
  } catch (e) {
    console.error("Error formatting JSON:", e);
    return jsonString; // Return the original string if there's an error
  }
}

// Function to copy JSON to clipboard
function copyJsonToClipboard(button, jsonString) {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(jsonString).then(() => {
        // Success feedback
        const originalText = button.querySelector('span').textContent;
        const originalIcon = button.querySelector('i').className;
        
        button.querySelector('span').textContent = 'Copied!';
        button.querySelector('i').className = 'fas fa-check';
        button.style.backgroundColor = 'rgba(34, 197, 94, 0.3)';
        
        setTimeout(() => {
          button.querySelector('span').textContent = originalText;
          button.querySelector('i').className = originalIcon;
          button.style.backgroundColor = '';
        }, 2000);
      }).catch(err => {
        console.error('Clipboard API failed:', err);
        fallbackCopyToClipboard(jsonString, button);
      });
    } else {
      fallbackCopyToClipboard(jsonString, button);
    }
  } catch (error) {
    console.error('Copy error:', error);
    showCopyFailureMessage(button);
  }
}

// Fallback copy method for unsupported browsers
function fallbackCopyToClipboard(text, button) {
  try {
    // Create textarea element
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    // Execute copy command
    const successful = document.execCommand('copy');
    
    // Clean up
    document.body.removeChild(textArea);
    
    if (successful) {
      // Success feedback
      const originalText = button.querySelector('span').textContent;
      button.querySelector('span').textContent = 'Copied!';
      
      setTimeout(() => {
        button.querySelector('span').textContent = originalText;
      }, 2000);
    } else {
      showCopyFailureMessage(button);
    }
  } catch (err) {
    console.error('Fallback copy failed:', err);
    showCopyFailureMessage(button);
  }
}

// Show error message when copy fails
function showCopyFailureMessage(button) {
  const originalText = button.querySelector('span').textContent;
  button.querySelector('span').textContent = 'Copy failed!';
  button.style.backgroundColor = 'rgba(239, 68, 68, 0.3)';
  
  setTimeout(() => {
    button.querySelector('span').textContent = originalText;
    button.style.backgroundColor = '';
  }, 2000);
}

// Toggle JSON visibility in the logs
function toggleJsonVisibility(button) {
  const jsonContent = button.parentNode.parentNode.nextElementSibling;
  const buttonText = button.querySelector('span');
  const buttonIcon = button.querySelector('i');
  
  if (jsonContent.style.display === 'none') {
    jsonContent.style.display = 'block';
    buttonText.textContent = 'Collapse';
    buttonIcon.className = 'fas fa-chevron-down';
  } else {
    jsonContent.style.display = 'none';
    buttonText.textContent = 'Expand';
    buttonIcon.className = 'fas fa-chevron-right';
  }
}

// Cookie utilities
const CookieUtils = {
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

// HTTP status code explanations
function getHttpStatusExplanation(status) {
  const statusCodes = {
    400: 'Bad Request',
    401: 'Unauthorized', 
    403: 'Forbidden',
    404: 'Not Found (health endpoint missing)',
    405: 'Method Not Allowed',
    408: 'Request Timeout',
    500: 'Internal Server Error',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    504: 'Gateway Timeout'
  };
  
  return statusCodes[status] || `HTTP ${status}`;
}

// URL validation utility
function isLikelyUrl(input) {
  if (!input || typeof input !== 'string') return false;
  
  // Trim the input
  const trimmed = input.trim();
  
  // Check for common URL patterns
  const hasProtocol = /^(https?:\/\/)/i.test(trimmed);
  const hasWww = /^www\./i.test(trimmed);
  
  // Use simpler regex patterns to avoid escaping issues
  const hasDomain = /^([a-z0-9][a-z0-9-]*[a-z0-9]?\.)+[a-z0-9][a-z0-9-]*[a-z0-9]?/i.test(trimmed);
  
  // Look for TLDs (not exhaustive, just common ones)
  const commonTlds = ['.com', '.org', '.net', '.edu', '.gov', '.io', '.co', '.ai', '.app'];
  const hasTld = commonTlds.some(tld => trimmed.includes(tld));
  
  // Special case for IP addresses
  const isIpAddress = /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?(\/.*)?$/i.test(trimmed);
  
  // Return true if this looks like a URL
  return (hasProtocol || hasWww || (hasDomain && hasTld) || isIpAddress);
}

/**
 * Ensure URL has a protocol (adds https:// if missing)
 * @param {string} url - The URL to normalize
 * @returns {string} - The normalized URL with protocol
 */
function ensureUrlProtocol(url) {
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
}

// Make these functions available globally
window.formatJsonForDisplay = formatJsonForDisplay;
window.copyJsonToClipboard = copyJsonToClipboard;
window.toggleJsonVisibility = toggleJsonVisibility;
window.getHttpStatusExplanation = getHttpStatusExplanation;
window.CookieUtils = CookieUtils;
window.isLikelyUrl = isLikelyUrl;
window.ensureUrlProtocol = ensureUrlProtocol;

console.log('Gnosis Utils loaded successfully - v1.0.1');

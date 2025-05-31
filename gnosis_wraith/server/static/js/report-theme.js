/**
 * Theme switching functionality for Gnosis Wraith reports
 */
document.addEventListener('DOMContentLoaded', function() {
    // Theme toggle button
    const themeToggleBtn = document.getElementById('theme-toggle');
    
    // Check for saved theme preference or use dark theme as default
    const savedTheme = localStorage.getItem('gnosis-wraith-report-theme') || 'dark';
    
    // Apply saved theme
    setTheme(savedTheme);
    
    // Handle theme toggle click
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', function() {
            const currentTheme = document.body.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            setTheme(newTheme);
            
            // Save theme preference
            try {
                localStorage.setItem('gnosis-wraith-report-theme', newTheme);
            } catch (e) {
                // localStorage might not be available (e.g. in incognito mode)
                console.warn('Could not save theme preference:', e);
            }
        });
    }
    
    // Close button functionality
    const closeBtn = document.getElementById('close-report');
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            window.close();
            // Fallback if window.close() doesn't work (e.g. not opened by JavaScript)
            setTimeout(function() {
                window.history.back();
            }, 100);
        });
    }
    
    /**
     * Set the theme by updating the data-theme attribute and the theme icon
     */
    function setTheme(theme) {
        document.body.setAttribute('data-theme', theme);
        
        // Update button icon and tooltip
        if (themeToggleBtn) {
            const icon = themeToggleBtn.querySelector('i');
            const themeText = themeToggleBtn.querySelector('span');
            
            if (theme === 'light') {
                if (icon) icon.className = 'fas fa-moon';
                if (themeText) themeText.textContent = 'Dark Mode';
                themeToggleBtn.setAttribute('title', 'Switch to Dark Mode');
            } else {
                if (icon) icon.className = 'fas fa-sun';
                if (themeText) themeText.textContent = 'Light Mode';
                themeToggleBtn.setAttribute('title', 'Switch to Light Mode');
            }
        }
    }
});

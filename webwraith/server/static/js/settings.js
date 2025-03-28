document.addEventListener('DOMContentLoaded', function() {
    // Default settings
    const defaultSettings = {
        'server-url': 'http://localhost:5678',
        'llm-api-token': '',
        'screenshot-quality': 'medium',
        'javascript-enabled': 'false',
        'storage-path': '~/.webwraith'
    };

    // Load settings from localStorage
    function loadSettings() {
        Object.keys(defaultSettings).forEach(key => {
            const storedValue = localStorage.getItem(`webwraith-${key}`);
            if (storedValue !== null) {
                const element = document.getElementById(key);
                if (element) {
                    if (element.tagName === 'SELECT') {
                        element.value = storedValue;
                    } else {
                        element.value = storedValue;
                    }
                }
            }
        });
    }

    // Save settings to localStorage
    function saveSettings() {
        Object.keys(defaultSettings).forEach(key => {
            const element = document.getElementById(key);
            if (element) {
                localStorage.setItem(`webwraith-${key}`, element.value);
            }
        });
    }

    // Reset settings to default
    function resetSettings() {
        Object.keys(defaultSettings).forEach(key => {
            const element = document.getElementById(key);
            if (element) {
                element.value = defaultSettings[key];
            }
            localStorage.setItem(`webwraith-${key}`, defaultSettings[key]);
        });
    }

    // Form submission
    const settingsForm = document.getElementById('settings-form');
    if (settingsForm) {
        settingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            saveSettings();
            
            // Show confirmation message
            const confirmation = document.createElement('div');
            confirmation.className = 'confirmation-message';
            confirmation.textContent = 'Settings saved successfully!';
            
            settingsForm.appendChild(confirmation);
            
            // Remove confirmation after 3 seconds
            setTimeout(() => {
                confirmation.remove();
            }, 3000);
        });
    }

    // Reset button
    const resetBtn = document.getElementById('reset-btn');
    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            if (confirm('Are you sure you want to reset all settings to default values?')) {
                resetSettings();
                
                // Show confirmation message
                const confirmation = document.createElement('div');
                confirmation.className = 'confirmation-message';
                confirmation.textContent = 'Settings reset to defaults!';
                
                settingsForm.appendChild(confirmation);
                
                // Remove confirmation after 3 seconds
                setTimeout(() => {
                    confirmation.remove();
                }, 3000);
            }
        });
    }

    // Initialize
    loadSettings();

    // Add styles for confirmation message
    const style = document.createElement('style');
    style.textContent = `
        .confirmation-message {
            background-color: var(--success-color);
            color: white;
            padding: 10px;
            border-radius: var(--border-radius);
            margin-top: 20px;
            text-align: center;
            animation: fadeOut 3s forwards;
        }
        
        @keyframes fadeOut {
            0% { opacity: 1; }
            70% { opacity: 1; }
            100% { opacity: 0; }
        }
    `;
    document.head.appendChild(style);
});
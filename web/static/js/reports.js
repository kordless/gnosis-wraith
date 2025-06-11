document.addEventListener('DOMContentLoaded', function() {
    // Server URL from localStorage or default
    const serverUrl = localStorage.getItem('gnosis-wraith-server-url') || 'http://localhost:5678';
    console.log(`Using server URL: ${serverUrl}`);

    // Add current timestamp to template for report age calculation
    window.now = new Date();

    // Enhanced search functionality with dynamic filtering
    const searchInput = document.getElementById('search-reports');
    const searchButton = document.getElementById('search-button');
    
    function performSearch() {
        if (!searchInput) return;
        
        const searchTerm = searchInput.value.toLowerCase();
        const rows = document.querySelectorAll('tbody tr');
        let matchCount = 0;
        
        rows.forEach(row => {
            // Get all text content from the row for more comprehensive searching
            const reportTitle = row.querySelector('.report-title').textContent.toLowerCase();
            const timestamp = row.querySelector('.timestamp').textContent.toLowerCase();
            const allText = reportTitle + ' ' + timestamp;
            
            if (allText.includes(searchTerm)) {
                row.style.display = '';
                matchCount++;
                
                // Highlight matching text if search term is not empty
                if (searchTerm.length > 0) {
                    // Add subtle highlight effect
                    row.style.backgroundColor = 'rgba(108, 99, 255, 0.08)';
                    row.style.transition = 'background-color 0.3s ease';
                    
                    // Remove highlight after a short delay
                    setTimeout(() => {
                        row.style.backgroundColor = '';
                    }, 1000);
                }
            } else {
                row.style.display = 'none';
            }
        });
        
        // Focus back on the search input
        searchInput.focus();
        
        // Provide visual feedback if no results
        const noResultsMessage = document.getElementById('no-results-message');
        
        if (searchTerm.length > 0 && matchCount === 0) {
            if (!noResultsMessage) {
                // Create a no results message
                const message = document.createElement('div');
                message.id = 'no-results-message';
                message.style.padding = '20px';
                message.style.textAlign = 'center';
                message.style.color = 'var(--text-muted)';
                message.style.backgroundColor = 'rgba(255, 97, 97, 0.1)';
                message.style.borderRadius = '8px';
                message.style.marginTop = '20px';
                message.innerHTML = `<i class="fas fa-search" style="margin-right: 8px;"></i> No reports found matching "${searchTerm}"`;
                
                const reportsList = document.querySelector('.reports-list');
                reportsList.appendChild(message);
            }
        } else if (noResultsMessage) {
            noResultsMessage.remove();
        }
    }

    // Search on input (real-time)
    if (searchInput) {
        searchInput.addEventListener('input', performSearch);
        
        // Also handle Enter key
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                performSearch();
            }
        });
    }
    
    // Search button click
    if (searchButton) {
        searchButton.addEventListener('click', performSearch);
    }

    // Add ghost search box focus effects
    const searchBox = document.querySelector('.ghost-search-box');
    if (searchBox && searchInput) {
        // Add focus effect
        searchInput.addEventListener('focus', () => {
            searchBox.classList.add('highlight');
        });
        
        searchInput.addEventListener('blur', () => {
            searchBox.classList.remove('highlight');
        });
    }

    // Auto-refresh every 2 minutes silently
    setInterval(() => {
        // Check if there are any reports
        const rows = document.querySelectorAll('tbody tr');
        if (rows.length > 0) {
            // Make a lightweight fetch request to check for updates
            fetch(window.location.href, { 
                method: 'HEAD',
                cache: 'no-store'
            });
        }
    }, 120000); // 2 minutes

    // Enhanced delete report functionality with better UX
    const deleteButtons = document.querySelectorAll('.delete-report');
    if (deleteButtons.length > 0) {
        deleteButtons.forEach(button => {
            button.addEventListener('click', async function() {
                const row = this.closest('tr');
                const filename = this.getAttribute('data-filename');
                const reportTitle = row.querySelector('.report-title').textContent.trim();
                
                if (confirm(`Are you sure you want to delete the report "${reportTitle}"?`)) {
                    try {
                        // Show a temporary "Deleting..." message
                        const originalButtonText = this.innerHTML;
                        this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';
                        this.disabled = true;
                        
                        // Ensure consistent API URL
                        const apiUrl = `${serverUrl}/api/reports/${encodeURIComponent(filename)}`;
                        console.log(`Sending DELETE request to: ${apiUrl}`);
                        
                        const response = await fetch(apiUrl, {
                            method: 'DELETE'
                        });
                        
                        if (!response.ok) {
                            const errorText = await response.text();
                            throw new Error(`Server responded with status: ${response.status}. ${errorText}`);
                        }
                        
                        // Better animation sequence
                        row.style.transition = 'all 0.5s ease';
                        row.style.backgroundColor = 'rgba(255, 97, 97, 0.1)';
                        row.style.transform = 'translateX(10px)';
                        
                        setTimeout(() => {
                            row.style.opacity = '0';
                            row.style.transform = 'translateX(20px)';
                            
                            setTimeout(() => {
                                row.remove();
                                
                                // If no more reports, show empty state
                                const remainingRows = document.querySelectorAll('tbody tr');
                                if (remainingRows.length === 0) {
                                    const table = document.querySelector('table');
                                    const emptyState = document.createElement('div');
                                    emptyState.className = 'empty-state';
                                    emptyState.innerHTML = `
                                        <i class="fas fa-file-alt fa-3x"></i>
                                        <p>No reports found</p>
                                        <p>Reports will appear here once they've been generated.</p>
                                    `;
                                    
                                    if (table && table.parentNode) {
                                        table.parentNode.replaceChild(emptyState, table);
                                    }
                                }
                            }, 300);
                        }, 200);
                    } catch (error) {
                        console.error('Error deleting report:', error);
                        this.innerHTML = originalButtonText;
                        this.disabled = false;
                        
                        // Show error message with better styling
                        const messageContainer = document.createElement('div');
                        messageContainer.className = 'message error';
                        messageContainer.textContent = `Failed to delete report: ${error.message}`;
                        
                        const card = document.querySelector('.card');
                        card.insertBefore(messageContainer, card.firstChild);
                        
                        // Auto-remove the message after 5 seconds
                        setTimeout(() => {
                            messageContainer.style.opacity = '0';
                            setTimeout(() => messageContainer.remove(), 300);
                        }, 5000);
                    }
                }
            });
        });
    }

    // Add styles for the empty state when added dynamically
    const style = document.createElement('style');
    style.textContent = `
        .empty-state {
            text-align: center;
            padding: 40px 0;
            color: var(--text-muted);
        }

        .empty-state i {
            margin-bottom: 20px;
            opacity: 0.5;
        }

        .empty-state p {
            margin-bottom: 10px;
        }
        
        /* Animation for search highlighting */
        @keyframes highlightPulse {
            0% { background-color: rgba(108, 99, 255, 0.1); }
            50% { background-color: rgba(108, 99, 255, 0.2); }
            100% { background-color: rgba(108, 99, 255, 0.1); }
        }
        
        .highlight-match {
            animation: highlightPulse 1.5s ease infinite;
        }
    `;
    document.head.appendChild(style);
    
    // Add "New" and "Recent" badges to reports based on date
    document.querySelectorAll('.timestamp').forEach(timestamp => {
        const dateText = timestamp.textContent.trim();
        try {
            const reportDate = new Date(dateText);
            const now = new Date();
            const daysDiff = Math.floor((now - reportDate) / (1000 * 60 * 60 * 24));
            
            // Logic for badges is in the HTML with Jinja templating
        } catch (e) {
            console.warn('Error parsing date', e);
        }
    });
});
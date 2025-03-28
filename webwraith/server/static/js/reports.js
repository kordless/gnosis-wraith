document.addEventListener('DOMContentLoaded', function() {
    // Server URL from localStorage or default
    const serverUrl = localStorage.getItem('webwraith-server-url') || 'http://localhost:5678';

    // Search functionality
    const searchInput = document.getElementById('search-reports');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const rows = document.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const filename = row.querySelector('td:first-child').textContent.toLowerCase();
                if (filename.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    // Refresh button
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            window.location.reload();
        });
    }

    // Delete report functionality
    const deleteButtons = document.querySelectorAll('.delete-report');
    if (deleteButtons.length > 0) {
        deleteButtons.forEach(button => {
            button.addEventListener('click', async function() {
                const filename = this.getAttribute('data-filename');
                
                if (confirm(`Are you sure you want to delete the report "${filename}"?`)) {
                    try {
                        const response = await fetch(`${serverUrl}/api/reports/${filename}`, {
                            method: 'DELETE'
                        });
                        
                        if (!response.ok) {
                            throw new Error(`Server responded with status: ${response.status}`);
                        }
                        
                        // If successful, remove the row
                        this.closest('tr').remove();
                        
                        // If no more reports, show empty state
                        const remainingRows = document.querySelectorAll('tbody tr');
                        if (remainingRows.length === 0) {
                            const table = document.querySelector('table');
                            const emptyState = document.createElement('div');
                            emptyState.className = 'empty-state';
                            emptyState.innerHTML = `
                                <i class="fas fa-file-alt fa-3x"></i>
                                <p>No reports found</p>
                                <p>Start crawling to generate reports</p>
                            `;
                            
                            table.parentNode.replaceChild(emptyState, table);
                        }
                    } catch (error) {
                        console.error('Error deleting report:', error);
                        alert(`Failed to delete report: ${error.message}`);
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
    `;
    document.head.appendChild(style);
});
document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements for reports page
    const reportRows = document.querySelectorAll('table tbody tr');
    const deleteButtons = document.querySelectorAll('.delete-report');
    const searchInput = document.getElementById('report-search');
    const sortSelect = document.getElementById('report-sort');
    const noReportsMessage = document.querySelector('.empty-state');
    
    // Initialize tooltips if any
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(tooltip => {
        tooltip.addEventListener('mouseover', showTooltip);
        tooltip.addEventListener('mouseout', hideTooltip);
    });
    
    // Add event listeners for sorting and filtering if they exist
    if (searchInput) {
        searchInput.addEventListener('input', filterReports);
    }
    
    if (sortSelect) {
        sortSelect.addEventListener('change', sortReports);
    }
    
    // Add event listeners for delete buttons if they exist
    if (deleteButtons) {
        deleteButtons.forEach(button => {
            button.addEventListener('click', confirmDelete);
        });
    }
    
    // Functions
    function showTooltip(event) {
        const tooltipText = event.target.getAttribute('data-tooltip');
        
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = tooltipText;
        
        // Position the tooltip
        const rect = event.target.getBoundingClientRect();
        tooltip.style.position = 'absolute';
        tooltip.style.top = `${rect.bottom + window.scrollY + 5}px`;
        tooltip.style.left = `${rect.left + window.scrollX}px`;
        tooltip.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
        tooltip.style.color = 'white';
        tooltip.style.padding = '5px 10px';
        tooltip.style.borderRadius = '4px';
        tooltip.style.fontSize = '14px';
        tooltip.style.zIndex = '1000';
        
        document.body.appendChild(tooltip);
        event.target.tooltip = tooltip;
    }
    
    function hideTooltip(event) {
        if (event.target.tooltip) {
            document.body.removeChild(event.target.tooltip);
            event.target.tooltip = null;
        }
    }
    
    function filterReports() {
        const searchTerm = searchInput.value.toLowerCase();
        let visibleCount = 0;
        
        reportRows.forEach(row => {
            const reportName = row.querySelector('td:first-child').textContent.toLowerCase();
            if (reportName.includes(searchTerm)) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });
        
        // Show/hide "no reports" message
        if (visibleCount === 0 && reportRows.length > 0) {
            // Create "no matches" message if it doesn't exist
            let noMatchesMessage = document.querySelector('.no-matches');
            if (!noMatchesMessage) {
                noMatchesMessage = document.createElement('div');
                noMatchesMessage.className = 'empty-state no-matches';
                noMatchesMessage.innerHTML = '<p>No reports match your search.</p>';
                document.querySelector('.reports-list').appendChild(noMatchesMessage);
            }
            noMatchesMessage.style.display = 'block';
        } else {
            // Hide "no matches" message if it exists
            const noMatchesMessage = document.querySelector('.no-matches');
            if (noMatchesMessage) {
                noMatchesMessage.style.display = 'none';
            }
        }
    }
    
    function sortReports() {
        const sortBy = sortSelect.value;
        const tbody = document.querySelector('table tbody');
        const rows = Array.from(reportRows);
        
        rows.sort((a, b) => {
            let aValue, bValue;
            
            if (sortBy === 'name') {
                aValue = a.querySelector('td:nth-child(1)').textContent;
                bValue = b.querySelector('td:nth-child(1)').textContent;
                return aValue.localeCompare(bValue);
            } else if (sortBy === 'name-desc') {
                aValue = a.querySelector('td:nth-child(1)').textContent;
                bValue = b.querySelector('td:nth-child(1)').textContent;
                return bValue.localeCompare(aValue);
            } else if (sortBy === 'date') {
                aValue = new Date(a.querySelector('td:nth-child(2)').textContent);
                bValue = new Date(b.querySelector('td:nth-child(2)').textContent);
                return aValue - bValue;
            } else if (sortBy === 'date-desc') {
                aValue = new Date(a.querySelector('td:nth-child(2)').textContent);
                bValue = new Date(b.querySelector('td:nth-child(2)').textContent);
                return bValue - aValue;
            } else if (sortBy === 'size') {
                aValue = parseFloat(a.querySelector('td:nth-child(3)').textContent);
                bValue = parseFloat(b.querySelector('td:nth-child(3)').textContent);
                return aValue - bValue;
            } else if (sortBy === 'size-desc') {
                aValue = parseFloat(a.querySelector('td:nth-child(3)').textContent);
                bValue = parseFloat(b.querySelector('td:nth-child(3)').textContent);
                return bValue - aValue;
            }
            
            return 0;
        });
        
        // Remove all existing rows
        rows.forEach(row => tbody.removeChild(row));
        
        // Add sorted rows
        rows.forEach(row => tbody.appendChild(row));
    }
    
    function confirmDelete(event) {
        const reportName = event.target.getAttribute('data-report');
        if (confirm(`Are you sure you want to delete "${reportName}"?`)) {
            deleteReport(reportName, event.target.closest('tr'));
        }
    }
    
    async function deleteReport(reportName, rowElement) {
        try {
            const response = await fetch(`/api/reports/${encodeURIComponent(reportName)}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                // Remove the row from the table
                rowElement.remove();
                
                // Check if there are any reports left
                const remainingRows = document.querySelectorAll('tbody tr');
                if (remainingRows.length === 0) {
                    // Show "no reports" message
                    if (noReportsMessage) {
                        noReportsMessage.style.display = 'block';
                    }
                    
                    // Hide the table
                    const table = document.querySelector('table');
                    if (table) {
                        table.style.display = 'none';
                    }
                }
            } else {
                alert(`Error: ${result.error}`);
            }
        } catch (error) {
            console.error('Error deleting report:', error);
            alert(`Error: ${error.message}`);
        }
    }
    
    // Check if we should show the report in an iframe based on URL hash
    function checkForEmbeddedReport() {
        const hash = window.location.hash;
        if (hash && hash.startsWith('#view=')) {
            const reportName = decodeURIComponent(hash.substring(6));
            showEmbeddedReport(reportName);
        }
    }
    
    function showEmbeddedReport(reportName) {
        // Create modal container if it doesn't exist
        let modalContainer = document.querySelector('.report-modal');
        if (!modalContainer) {
            modalContainer = document.createElement('div');
            modalContainer.className = 'report-modal';
            modalContainer.style.position = 'fixed';
            modalContainer.style.top = '0';
            modalContainer.style.left = '0';
            modalContainer.style.width = '100%';
            modalContainer.style.height = '100%';
            modalContainer.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
            modalContainer.style.zIndex = '1000';
            modalContainer.style.display = 'flex';
            modalContainer.style.flexDirection = 'column';
            modalContainer.style.alignItems = 'center';
            modalContainer.style.justifyContent = 'center';
            modalContainer.style.padding = '20px';
            
            const closeButton = document.createElement('button');
            closeButton.textContent = 'Close';
            closeButton.className = 'btn';
            closeButton.style.marginBottom = '10px';
            closeButton.style.zIndex = '1001';
            closeButton.addEventListener('click', () => {
                document.body.removeChild(modalContainer);
                window.location.hash = '';
            });
            
            const iframe = document.createElement('iframe');
            iframe.style.width = '100%';
            iframe.style.height = 'calc(100% - 50px)';
            iframe.style.border = 'none';
            iframe.style.backgroundColor = 'white';
            
            modalContainer.appendChild(closeButton);
            modalContainer.appendChild(iframe);
            document.body.appendChild(modalContainer);
            
            // Set iframe src
            const isHtml = reportName.endsWith('.html');
            const reportPath = `/reports/${reportName}`;
            iframe.src = reportPath;
        }
    }
    
    // Check for embedded report on page load
    checkForEmbeddedReport();
    
    // Handle hash changes
    window.addEventListener('hashchange', checkForEmbeddedReport);
});
// Custom JavaScript for CCAMS

// Django template filters for JavaScript
function statusColor(status) {
    const colors = {
        'pending': 'warning',
        'confirmed': 'primary',
        'completed': 'success',
        'cancelled': 'secondary',
        'no_show': 'danger'
    };
    return colors[status] || 'secondary';
}

function actionIcon(action) {
    const icons = {
        'created': 'plus',
        'cancelled': 'times',
        'rescheduled': 'calendar-alt',
        'completed': 'check',
        'no_show': 'user-slash',
        'status_updated': 'edit'
    };
    return icons[action] || 'circle';
}

function actionTitle(action) {
    const titles = {
        'created': 'Created',
        'cancelled': 'Cancelled',
        'rescheduled': 'Rescheduled',
        'completed': 'Completed',
        'no_show': 'Marked as No-Show',
        'status_updated': 'Status Updated'
    };
    return titles[action] || action.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
}

// Utility functions
function formatDateTime(datetime) {
    const date = new Date(datetime);
    return date.toLocaleString();
}

function formatDate(date) {
    const d = new Date(date);
    return d.toLocaleDateString();
}

function formatTime(time) {
    const [hours, minutes] = time.split(':');
    const h = parseInt(hours);
    const ampm = h >= 12 ? 'PM' : 'AM';
    const displayHour = h > 12 ? h - 12 : h;
    return `${displayHour}:${minutes} ${ampm}`;
}

// Form validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
        }
    });
    
    return isValid;
}

// AJAX wrapper
function ajaxRequest(url, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    };
    
    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }
    
    return fetch(url, options)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        });
}

// CSRF token helper
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Loading indicator
function showLoading() {
    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.innerHTML = '<div class="spinner"></div>';
    document.body.appendChild(overlay);
}

function hideLoading() {
    const overlay = document.querySelector('.loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}

// Toast notifications
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 5000);
}

// Confirm dialog
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Date picker initialization
function initializeDatePicker(selector, options = {}) {
    const defaultOptions = {
        format: 'yyyy-mm-dd',
        autoclose: true,
        todayHighlight: true,
        startDate: new Date()
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    // Initialize date picker if library is available
    if (typeof bootstrap !== 'undefined' && bootstrap.Datepicker) {
        return new bootstrap.Datepicker(document.querySelector(selector), finalOptions);
    }
    
    return null;
}

// Time picker initialization
function initializeTimePicker(selector, options = {}) {
    const defaultOptions = {
        format: 'HH:mm',
        interval: 30,
        minTime: '08:00',
        maxTime: '17:00'
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    // Initialize time picker if library is available
    if (typeof $ !== 'undefined' && $.fn.timepicker) {
        return $(selector).timepicker(finalOptions);
    }
    
    return null;
}

// Table sorting
function initializeTableSort(selector) {
    const table = document.querySelector(selector);
    if (!table) return;
    
    const headers = table.querySelectorAll('th[data-sort]');
    headers.forEach(header => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', () => {
            const column = header.dataset.sort;
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            const isAsc = header.classList.contains('sort-asc');
            
            rows.sort((a, b) => {
                const aVal = a.children[column].textContent.trim();
                const bVal = b.children[column].textContent.trim();
                
                if (isAsc) {
                    return bVal.localeCompare(aVal);
                } else {
                    return aVal.localeCompare(bVal);
                }
            });
            
            // Clear sort classes
            headers.forEach(h => {
                h.classList.remove('sort-asc', 'sort-desc');
            });
            
            // Add sort class
            header.classList.add(isAsc ? 'sort-desc' : 'sort-asc');
            
            // Reorder rows
            rows.forEach(row => tbody.appendChild(row));
        });
    });
}

// Auto-resize textareas
function autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

// Initialize auto-resize for all textareas
document.addEventListener('DOMContentLoaded', function() {
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', () => autoResizeTextarea(textarea));
        autoResizeTextarea(textarea);
    });
});

// Print functionality
function printElement(elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <!DOCTYPE html>
        <html>
            <head>
                <title>Print</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                <style>
                    body { padding: 20px; }
                    .no-print { display: none !important; }
                </style>
            </head>
            <body>
                ${element.innerHTML}
                <script>
                    window.onload = function() {
                        window.print();
                        window.close();
                    };
                </script>
            </body>
        </html>
    `);
    printWindow.document.close();
}

// Export to CSV
function exportToCSV(data, filename) {
    const csv = convertToCSV(data);
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.setAttribute('hidden', '');
    a.setAttribute('href', url);
    a.setAttribute('download', filename);
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

function convertToCSV(data) {
    if (!data || data.length === 0) return '';
    
    const headers = Object.keys(data[0]);
    const csvHeaders = headers.join(',');
    
    const csvRows = data.map(row => {
        return headers.map(header => {
            const value = row[header];
            return typeof value === 'string' && value.includes(',') 
                ? `"${value}"` 
                : value;
        }).join(',');
    });
    
    return [csvHeaders, ...csvRows].join('\n');
}

// Form submission with AJAX
function submitFormWithAjax(formId, successCallback, errorCallback) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (!validateForm(formId)) {
            showToast('Please fill in all required fields', 'warning');
            return;
        }
        
        const formData = new FormData(form);
        const url = form.action;
        const method = form.method || 'POST';
        
        showLoading();
        
        fetch(url, {
            method: method,
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            hideLoading();
            if (successCallback) {
                successCallback(data);
            } else {
                showToast('Operation completed successfully', 'success');
                if (data.redirect) {
                    window.location.href = data.redirect;
                }
            }
        })
        .catch(error => {
            hideLoading();
            if (errorCallback) {
                errorCallback(error);
            } else {
                showToast('An error occurred. Please try again.', 'danger');
            }
        });
    });
}

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Initialize popovers
document.addEventListener('DOMContentLoaded', function() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// Global error handler
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    showToast('An unexpected error occurred', 'danger');
});

// Global unhandled promise rejection handler
window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
    showToast('An unexpected error occurred', 'danger');
});

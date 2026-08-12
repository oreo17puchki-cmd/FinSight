/* ============================================================
   FinSight Financial Goal Planning Module - Main JS Utilities
   File: static/js/goal_main.js
   ============================================================ */

/**
 * Toast Notification System
 * Displays luxury animated success or error notifications.
 * 
 * @param {string} message - Message text to display.
 * @param {string} type - Notification type: 'success' or 'error'.
 * @param {number} duration - Display time in milliseconds (default: 4000ms).
 */
function showToast(message, type = 'success', duration = 4000) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type} animate-toast`;

    const iconClass = type === 'success' ? 'fa-circle-check' : 'fa-circle-exclamation';

    toast.innerHTML = `
        <div class="toast-icon">
            <i class="fa-solid ${iconClass}"></i>
        </div>
        <div class="toast-content">
            <span class="toast-message">${escapeHtml(message)}</span>
        </div>
        <button type="button" class="toast-close" onclick="this.parentElement.remove()" aria-label="Close">
            <i class="fa-solid fa-xmark"></i>
        </button>
    `;

    container.appendChild(toast);

    // Auto-remove toast after specified duration
    setTimeout(() => {
        if (toast.parentElement) {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100px)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }
    }, duration);
}

/**
 * Formats a numeric value into Indian Rupee currency format (₹2,50,000.00).
 * 
 * @param {number|string} amount - The amount to format.
 * @returns {string} Formatted currency string.
 */
function formatCurrency(amount) {
    const numericAmount = parseFloat(amount) || 0;
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(numericAmount);
}

/**
 * Formats a date string (YYYY-MM-DD) into readable format (e.g. 30 June 2027).
 * 
 * @param {string} dateStr - Date string in YYYY-MM-DD format.
 * @returns {string} Formatted human-readable date.
 */
function formatDateReadable(dateStr) {
    if (!dateStr) return '-';
    try {
        const parts = dateStr.split('-');
        if (parts.length === 3) {
            const year = parseInt(parts[0], 10);
            const month = parseInt(parts[1], 10) - 1;
            const day = parseInt(parts[2], 10);
            const dt = new Date(year, month, day);
            return dt.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
        }
        return dateStr;
    } catch (e) {
        return dateStr;
    }
}

/**
 * Escapes HTML characters to prevent XSS vulnerability when inserting string content dynamically.
 * 
 * @param {string} str - Raw input string.
 * @returns {string} Sanitized string.
 */
function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

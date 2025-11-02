// Global site functionality
class PerformanceReviewApp {
    constructor() {
        this.connection = null;
        this.init();
    }

    init() {
        this.initSignalR();
        this.initNotifications();
        this.initGlobalHandlers();
    }

    // SignalR for real-time notifications
    initSignalR() {
        this.connection = new signalR.HubConnectionBuilder()
            .withUrl("/notificationHub")
            .withAutomaticReconnect()
            .build();

        this.connection.on("ReceiveNotification", (title, message, type) => {
            this.showNotification(title, message, type);
            this.updateNotificationCount();
        });

        this.connection.on("UpdateUnreadCount", (count) => {
            this.updateNotificationBadge(count);
        });

        this.connection.start().catch(err => console.error('SignalR Connection Error: ', err));
    }

    // Notification system
    initNotifications() {
        this.updateNotificationCount();
        this.loadNotificationDropdown();
    }

    async updateNotificationCount() {
        try {
            const response = await fetch('/notifications/unread-count');
            if (response.ok) {
                const data = await response.json();
                this.updateNotificationBadge(data.count);
            }
        } catch (error) {
            console.error('Error fetching notification count:', error);
        }
    }

    updateNotificationBadge(count) {
        const badge = document.getElementById('notificationCount');
        if (badge) {
            if (count > 0) {
                badge.textContent = count > 99 ? '99+' : count;
                badge.classList.remove('d-none');
            } else {
                badge.classList.add('d-none');
            }
        }
    }

    async loadNotificationDropdown() {
        try {
            const response = await fetch('/notifications?unreadOnly=true&limit=5');
            if (response.ok) {
                const html = await response.text();
                const notificationList = document.getElementById('notificationList');
                if (notificationList) {
                    notificationList.innerHTML = html;
                }
            }
        } catch (error) {
            console.error('Error loading notifications:', error);
        }
    }

    showNotification(title, message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-bg-${this.getNotificationType(type)} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <strong>${title}</strong><br>${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        const container = document.getElementById('toastContainer') || this.createToastContainer();
        container.appendChild(toast);

        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        // Remove toast after hide
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    getNotificationType(type) {
        const types = {
            'success': 'success',
            'error': 'danger',
            'warning': 'warning',
            'info': 'info'
        };
        return types[type] || 'info';
    }

    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
        return container;
    }

    // Global event handlers
    initGlobalHandlers() {
        // Auto-dismiss alerts after 5 seconds
        document.addEventListener('DOMContentLoaded', () => {
            const alerts = document.querySelectorAll('.alert');
            alerts.forEach(alert => {
                setTimeout(() => {
                    if (alert.parentNode) {
                        const bsAlert = new bootstrap.Alert(alert);
                        bsAlert.close();
                    }
                }, 5000);
            });
        });

        // Confirm dialogs for destructive actions
        document.addEventListener('click', (e) => {
            if (e.target.closest('[data-confirm]')) {
                const message = e.target.closest('[data-confirm]').getAttribute('data-confirm');
                if (!confirm(message || 'Вы уверены?')) {
                    e.preventDefault();
                    e.stopPropagation();
                }
            }
        });

        // Form validation enhancement
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.classList.contains('needs-validation')) {
                if (!form.checkValidity()) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                form.classList.add('was-validated');
            }
        });
    }

    // Utility methods
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('ru-RU', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    formatDateTime(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('ru-RU', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.perfReviewApp = new PerformanceReviewApp();
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    const popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// API helper functions
const ApiHelper = {
    async get(url) {
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('GET request failed:', error);
            throw error;
        }
    },

    async post(url, data) {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('POST request failed:', error);
            throw error;
        }
    },

    async put(url, data) {
        try {
            const response = await fetch(url, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('PUT request failed:', error);
            throw error;
        }
    },

    async delete(url) {
        try {
            const response = await fetch(url, { method: 'DELETE' });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.ok;
        } catch (error) {
            console.error('DELETE request failed:', error);
            throw error;
        }
    }
};

// Form helper functions
const FormHelper = {
    serializeForm(form) {
        const formData = new FormData(form);
        const data = {};
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }
        return data;
    },

    validateForm(form) {
        let isValid = true;
        const requiredFields = form.querySelectorAll('[required]');
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.classList.add('is-invalid');
                isValid = false;
            } else {
                field.classList.remove('is-invalid');
            }
        });

        return isValid;
    },

    showFormErrors(form, errors) {
        // Clear previous errors
        form.querySelectorAll('.is-invalid').forEach(field => {
            field.classList.remove('is-invalid');
        });
        form.querySelectorAll('.invalid-feedback').forEach(el => el.remove());

        // Add new errors
        Object.keys(errors).forEach(fieldName => {
            const field = form.querySelector(`[name="${fieldName}"]`);
            if (field) {
                field.classList.add('is-invalid');
                const errorDiv = document.createElement('div');
                errorDiv.className = 'invalid-feedback';
                errorDiv.textContent = errors[fieldName];
                field.parentNode.appendChild(errorDiv);
            }
        });
    }
};

// Notification helper
const NotificationHelper = {
    show(message, type = 'info', duration = 5000) {
        if (window.perfReviewApp) {
            window.perfReviewApp.showNotification('Уведомление', message, type);
        } else {
            // Fallback to basic alert
            alert(message);
        }
    },

    success(message) {
        this.show(message, 'success');
    },

    error(message) {
        this.show(message, 'error');
    },

    warning(message) {
        this.show(message, 'warning');
    },

    info(message) {
        this.show(message, 'info');
    }
};

// Export for global usage
window.ApiHelper = ApiHelper;
window.FormHelper = FormHelper;
window.NotificationHelper = NotificationHelper;
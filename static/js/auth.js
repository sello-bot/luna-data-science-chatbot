// Authentication JavaScript
class AuthManager {
    constructor() {
        this.apiKey = localStorage.getItem('apiKey');
        this.userPlan = localStorage.getItem('userPlan');
        this.initializeAuth();
    }

    initializeAuth() {
        // Check if user is already logged in
        if (this.apiKey && window.location.pathname !== '/') {
            this.validateSession();
        }
    }

    async validateSession() {
        try {
            const response = await fetch('/api/usage', {
                headers: {
                    'X-API-Key': this.apiKey,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                this.logout();
                return false;
            }

            return true;
        } catch (error) {
            console.error('Session validation error:', error);
            return false;
        }
    }

    async login(email, password) {
        try {
            const response = await fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (data.success) {
                this.apiKey = data.api_key;
                this.userPlan = data.plan;
                
                localStorage.setItem('apiKey', this.apiKey);
                localStorage.setItem('userPlan', this.userPlan);
                localStorage.setItem('loginTime', Date.now().toString());

                return { success: true, data };
            } else {
                return { success: false, error: data.error };
            }
        } catch (error) {
            return { success: false, error: 'Network error. Please try again.' };
        }
    }

    async register(email, password, plan = 'free') {
        try {
            const response = await fetch('/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password, plan })
            });

            const data = await response.json();

            if (data.success) {
                return { success: true, data };
            } else {
                return { success: false, error: data.error };
            }
        } catch (error) {
            return { success: false, error: 'Network error. Please try again.' };
        }
    }

    logout() {
        localStorage.removeItem('apiKey');
        localStorage.removeItem('userPlan');
        localStorage.removeItem('loginTime');
        
        // Clear session
        this.apiKey = null;
        this.userPlan = null;
        
        window.location.href = '/login';
    }

    getApiKey() {
        return this.apiKey;
    }

    getUserPlan() {
        return this.userPlan;
    }

    isAuthenticated() {
        return !!this.apiKey;
    }
}

// Utility functions
function showNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `flash-message flash-${type}`;
    notification.innerHTML = `
        <span>${message}</span>
        <button class="close-flash">&times;</button>
    `;

    const container = document.querySelector('.flash-messages') || createFlashContainer();
    container.appendChild(notification);

    // Auto remove
    setTimeout(() => {
        notification.remove();
    }, duration);

    // Close button
    notification.querySelector('.close-flash').addEventListener('click', () => {
        notification.remove();
    });
}

function createFlashContainer() {
    const container = document.createElement('div');
    container.className = 'flash-messages';
    document.body.appendChild(container);
    return container;
}

function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function validatePassword(password) {
    return password.length >= 8;
}

function showLoading(button) {
    const btnText = button.querySelector('.btn-text');
    const btnSpinner = button.querySelector('.btn-spinner');
    
    if (btnText) btnText.style.display = 'none';
    if (btnSpinner) btnSpinner.style.display = 'inline-block';
    button.disabled = true;
}

function hideLoading(button) {
    const btnText = button.querySelector('.btn-text');
    const btnSpinner = button.querySelector('.btn-spinner');
    
    if (btnText) btnText.style.display = 'inline-block';
    if (btnSpinner) btnSpinner.style.display = 'none';
    button.disabled = false;
}

// Form validation utilities
class FormValidator {
    constructor(formElement) {
        this.form = formElement;
        this.errors = {};
    }

    validateField(fieldName, value, rules) {
        const fieldErrors = [];

        rules.forEach(rule => {
            switch (rule.type) {
                case 'required':
                    if (!value || value.trim() === '') {
                        fieldErrors.push(rule.message || `${fieldName} is required`);
                    }
                    break;
                case 'email':
                    if (value && !validateEmail(value)) {
                        fieldErrors.push(rule.message || 'Please enter a valid email address');
                    }
                    break;
                case 'minLength':
                    if (value && value.length < rule.value) {
                        fieldErrors.push(rule.message || `${fieldName} must be at least ${rule.value} characters`);
                    }
                    break;
                case 'pattern':
                    if (value && !rule.value.test(value)) {
                        fieldErrors.push(rule.message || `${fieldName} format is invalid`);
                    }
                    break;
            }
        });

        this.errors[fieldName] = fieldErrors;
        return fieldErrors.length === 0;
    }

    displayErrors() {
        // Remove existing error messages
        this.form.querySelectorAll('.field-error').forEach(error => error.remove());

        Object.keys(this.errors).forEach(fieldName => {
            const field = this.form.querySelector(`[name="${fieldName}"]`);
            const errors = this.errors[fieldName];

            if (errors.length > 0 && field) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'field-error';
                errorDiv.style.color = 'var(--error-color)';
                errorDiv.style.fontSize = '0.75rem';
                errorDiv.style.marginTop = '0.25rem';
                errorDiv.textContent = errors[0];

                field.parentNode.insertBefore(errorDiv, field.nextSibling);
                field.style.borderColor = 'var(--error-color)';
            } else if (field) {
                field.style.borderColor = 'var(--border-color)';
            }
        });
    }

    isValid() {
        return Object.values(this.errors).every(errors => errors.length === 0);
    }
}

// API Client
class ApiClient {
    constructor(apiKey) {
        this.apiKey = apiKey;
        this.baseUrl = '/api';
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...(this.apiKey && { 'X-API-Key': this.apiKey }),
            ...options.headers
        };

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API request failed: ${endpoint}`, error);
            throw error;
        }
    }

    async get(endpoint) {
        return this.request(endpoint);
    }

    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    }
}

// Usage tracking
class UsageTracker {
    constructor(apiClient) {
        this.apiClient = apiClient;
        this.usage = null;
        this.loadUsage();
    }

    async loadUsage() {
        try {
            this.usage = await this.apiClient.get('/usage');
            this.updateUsageDisplay();
        } catch (error) {
            console.error('Failed to load usage data:', error);
        }
    }

    updateUsageDisplay() {
        const usageElements = document.querySelectorAll('[data-usage]');
        if (this.usage && usageElements.length > 0) {
            usageElements.forEach(element => {
                const type = element.dataset.usage;
                switch (type) {
                    case 'remaining':
                        element.textContent = this.usage.remaining_usage || 0;
                        break;
                    case 'plan':
                        element.textContent = this.usage.plan || 'Free';
                        break;
                }
            });
        }
    }

    getRemainingUsage() {
        return this.usage ? this.usage.remaining_usage : 0;
    }

    getPlan() {
        return this.usage ? this.usage.plan : 'free';
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.authManager = new AuthManager();
    
    // Initialize API client if authenticated
    if (window.authManager.isAuthenticated()) {
        window.apiClient = new ApiClient(window.authManager.getApiKey());
        window.usageTracker = new UsageTracker(window.apiClient);
    }
});

// Export for use in other scripts
window.AuthManager = AuthManager;
window.FormValidator = FormValidator;
window.ApiClient = ApiClient;
window.UsageTracker = UsageTracker;
window.showNotification = showNotification;
window.validateEmail = validateEmail;
window.validatePassword = validatePassword;
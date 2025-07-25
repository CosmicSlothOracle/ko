// API Configuration - Standardized URLs
const config = {
    // API Base URLs - Standardized across environments
    API_BASE_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:10000/api'
        : 'https://kosge-backend.onrender.com/api',
    
    // API Endpoints - Standardized
    ENDPOINTS: {
        HEALTH: '/health',
        LOGIN: '/login',
        BANNERS: '/banners',
        UPLOADS: '/uploads',
        PARTICIPANTS: '/participants',
        CMS_CONTENT: '/cms/content',
        CMS_SECTIONS: '/cms/sections'
    },
    
    // Request Configuration
    MAX_RETRIES: 3,
    RETRY_DELAY: 1000,
    TIMEOUT: 10000, // 10 seconds
    
    // Event Limits
    EVENT_LIMITS: {
        MAX_PARTICIPANTS: 100,
        MAX_FILE_SIZE: 16 * 1024 * 1024, // 16MB in bytes
        MAX_MESSAGE_LENGTH: 1000
    },
    
    // Validation Rules
    VALIDATION: {
        MIN_NAME_LENGTH: 2,
        MAX_NAME_LENGTH: 100,
        MIN_PASSWORD_LENGTH: 8,
        EMAIL_REGEX: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
    },
    
    DEBUG: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
};

// Debug logging
function debugLog(...args) {
    if (config.DEBUG) {
        console.log('[KOSGE]', ...args);
    }
}

// Error handling utility
function handleApiError(error, context = '') {
    debugLog(`API Error in ${context}:`, error);
    
    if (error.response) {
        // Server responded with error status
        const status = error.response.status;
        const data = error.response.data;
        
        switch (status) {
            case 400:
                return `Validation error: ${data.error || 'Invalid data provided'}`;
            case 401:
                return 'Authentication failed. Please check your credentials.';
            case 403:
                return 'Access denied. You do not have permission for this action.';
            case 404:
                return 'Resource not found.';
            case 429:
                return 'Too many requests. Please try again later.';
            case 500:
                return 'Server error. Please try again later.';
            default:
                return `Server error (${status}): ${data.error || 'Unknown error'}`;
        }
    } else if (error.request) {
        // Network error
        return 'Network error. Please check your connection.';
    } else {
        // Other error
        return 'An unexpected error occurred.';
    }
}

// API request utility
async function apiRequest(endpoint, options = {}) {
    const url = `${config.API_BASE_URL}${endpoint}`;
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
        timeout: config.TIMEOUT
    };
    
    const requestOptions = { ...defaultOptions, ...options };
    
    debugLog(`API Request: ${requestOptions.method} ${url}`);
    
    try {
        const response = await fetch(url, requestOptions);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw {
                response: {
                    status: response.status,
                    data: errorData
                }
            };
        }
        
        const data = await response.json();
        debugLog(`API Response:`, data);
        return data;
    } catch (error) {
        throw error;
    }
}

// Retry mechanism
async function apiRequestWithRetry(endpoint, options = {}, retries = config.MAX_RETRIES) {
    for (let i = 0; i < retries; i++) {
        try {
            return await apiRequest(endpoint, options);
        } catch (error) {
            if (i === retries - 1) {
                throw error;
            }
            debugLog(`Retry ${i + 1}/${retries} for ${endpoint}`);
            await new Promise(resolve => setTimeout(resolve, config.RETRY_DELAY * (i + 1)));
        }
    }
}

// Log configuration on load
debugLog('Configuration loaded:', config);

// Prevent accidental modification
Object.freeze(config);
Object.freeze(config.ENDPOINTS);
Object.freeze(config.EVENT_LIMITS);
Object.freeze(config.VALIDATION);

// Export configuration and utilities
window.APP_CONFIG = config;
window.API_UTILS = {
    request: apiRequest,
    requestWithRetry: apiRequestWithRetry,
    handleError: handleApiError
};
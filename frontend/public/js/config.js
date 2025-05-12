// API Configuration
const config = {
    // Dynamically set API URL based on environment
    API_BASE_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:10000/api'
        : 'https://kosge-backend.onrender.com/api',
    MAX_RETRIES: 3,
    RETRY_DELAY: 1000,
    DEBUG: false // Disable debug logging in production
};

// Debug logging
function debugLog(...args) {
    if (config.DEBUG) {
        console.log('[KOSGE]', ...args);
    }
}

// Log configuration on load
debugLog('Configuration loaded:', config);

// Prevent accidental modification
Object.freeze(config);

// Export configuration
window.APP_CONFIG = config;
// Get configuration from global config
const { API_BASE_URL, MAX_RETRIES, RETRY_DELAY, DEBUG } = window.APP_CONFIG;

// DOM Elements
const eventsGrid = document.querySelector('.events-grid');
const participantModal = document.getElementById('participant-modal');
const participantDetails = document.getElementById('participant-details');
const closeModal = document.querySelector('.close');
const logoutButton = document.getElementById('logout-button');
const participationList = document.getElementById('participation-list');

// Debug logging function
function debugLog(...args) {
    if (DEBUG) {
        console.log('[KOSGE Admin]', ...args);
    }
}

// Sleep function for retry delay
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Authentication handling
function getAuthToken() {
    return localStorage.getItem('authToken');
}

function checkAuth() {
    const authToken = getAuthToken();
    debugLog('Checking authentication...');

    if (!authToken) {
        debugLog('No auth token found');
        redirectToLogin();
        return false;
    }

    // Validate token format
    try {
        const tokenParts = authToken.split('.');
        if (tokenParts.length !== 3) {
            debugLog('Invalid token format');
            redirectToLogin();
            return false;
        }
    } catch (error) {
        debugLog('Token validation error:', error);
        redirectToLogin();
        return false;
    }

    return true;
}

function redirectToLogin() {
    sessionStorage.removeItem('adminAuthenticated');
    localStorage.removeItem('authToken');
    window.location.href = '../index.html';
}

// Load banners from API
async function loadBanners() {
    debugLog('Loading banners...');
    try {
        const url = `${API_BASE_URL}/banners`;
        debugLog('Fetching banners from:', url);

        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            mode: 'cors'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        debugLog('Received banners:', data);
        return data.banners || [];
    } catch (error) {
        debugLog('Error loading banners:', error);
        throw error;
    }
}

// Update fetchParticipants with authentication
async function fetchParticipants(retryCount = 0) {
    debugLog(`Fetching participants... (attempt ${retryCount + 1}/${MAX_RETRIES})`);

    if (!checkAuth()) {
        throw new Error('Not authenticated');
    }

    try {
        const url = `${API_BASE_URL}/participants`;
        debugLog('Fetching from URL:', url);

        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            },
            mode: 'cors'
        });

        if (response.status === 401) {
            debugLog('Authentication expired');
            redirectToLogin();
            throw new Error('Authentication expired');
        }

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const text = await response.text();
        debugLog('Raw response:', text);

        try {
            const data = JSON.parse(text);
            debugLog('Parsed data:', data);
            return data.participants || [];
        } catch (parseError) {
            debugLog('JSON parse error:', parseError);
            throw new Error(`JSON parse error: ${parseError.message}`);
        }
    } catch (error) {
        console.error('Error fetching participants:', error);

        if (retryCount < MAX_RETRIES - 1 && error.message !== 'Authentication expired') {
            debugLog(`Retrying in ${RETRY_DELAY}ms...`);
            await sleep(RETRY_DELAY);
            return fetchParticipants(retryCount + 1);
        }

        throw error;
    }
}

// Safe HTML rendering
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Update renderParticipants with safe HTML
function renderParticipants(participants) {
    debugLog('Rendering participants:', participants);

    if (!participationList) {
        console.error('Participation list element not found');
        return;
    }

    if (!participants || participants.length === 0) {
        participationList.innerHTML = `
            <div class="no-participations">
                Keine Teilnahmen vorhanden.
            </div>
        `;
        return;
    }

    participationList.innerHTML = participants.map(participant => `
        <div class="participation-entry">
            <div class="participation-banner banner-tag-${escapeHtml(participant.banner || '1')}">
                Banner ${escapeHtml(participant.banner || 'Kein Banner')}
            </div>
            <h3>${escapeHtml(participant.name)}</h3>
            ${participant.email ? `<p><strong>Email:</strong> ${escapeHtml(participant.email)}</p>` : ''}
            ${participant.message ? `<p><strong>Nachricht:</strong> ${escapeHtml(participant.message)}</p>` : ''}
            <p><strong>Datum:</strong> ${new Date(participant.timestamp || Date.now()).toLocaleString('de-DE')}</p>
        </div>
    `).join('');

    debugLog('Rendered participants list');
}

// Initialize dashboard
async function initializeDashboard() {
    debugLog('Initializing dashboard...');
    try {
        participationList.innerHTML = `
            <div class="loading-message">
                <p>Lade Teilnahmen...</p>
            </div>
        `;

        // Load banners first
        try {
            const banners = await loadBanners();
            debugLog('Loaded banners:', banners);
        } catch (error) {
            debugLog('Error loading banners:', error);
        }

        // Then load participants
        const participants = await fetchParticipants();
        renderParticipants(participants);
        debugLog('Dashboard initialized successfully');
    } catch (error) {
        console.error('Dashboard initialization error:', error);
        participationList.innerHTML = `
            <div class="error-message">
                <p>Fehler beim Laden der Teilnahmen: ${error.message}</p>
                <button onclick="initializeDashboard()">Erneut versuchen</button>
            </div>
        `;
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    debugLog('DOM Content Loaded');
    debugLog('Using API URL:', API_BASE_URL);
    checkAuth();
    initializeDashboard();

    // Close modal when clicking the close button
    if (closeModal) {
        closeModal.addEventListener('click', () => {
            participantModal.style.display = 'none';
        });
    }

    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
        if (e.target === participantModal) {
            participantModal.style.display = 'none';
        }
    });

    // Logout handler
    if (logoutButton) {
        logoutButton.addEventListener('click', () => {
            sessionStorage.removeItem('adminAuthenticated');
            window.location.href = '../index.html';
        });
    }
});
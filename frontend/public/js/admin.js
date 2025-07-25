// Admin Authentication - now handled by backend

// Use centralized configuration with fallback
const API_BASE_URL = (window.APP_CONFIG && window.APP_CONFIG.API_BASE_URL) ||
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:10000/api'
        : 'https://kosge-backend.onrender.com/api');

// DOM Elements
const adminLoginModal = document.getElementById('admin-login-modal');
const adminModal = document.getElementById('adminModal');
const adminLoginForm = document.getElementById('admin-login-form');
const eventForm = document.getElementById('eventForm');
const logoutBtn = document.getElementById('logout-btn');
const addEventBtn = document.getElementById('add-event-btn');
const closeButtons = document.querySelectorAll('.close');

// Zusätzliche DOM-Elemente für das Bild-Edit-Modal
const eventEditModal = document.getElementById('event-edit-modal');
const eventEditForm = document.getElementById('event-edit-form');
const eventEditUrlInput = document.getElementById('event-edit-url');
const eventEditPreview = document.getElementById('event-edit-preview');
const eventEditMessage = document.getElementById('event-edit-message');
const eventEditCurrentUrl = document.getElementById('current-url');

// State
let isAdminLoggedIn = false;
let editingImageEventId = null;

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    initializeEventsStorage();
    checkAdminStatus();
    loadEvents();
    setupShowParticipantsButtons();
    // Attach event listener to the static edit event button if it exists
    const editEventBtn = document.getElementById('edit-event-btn');
    if (editEventBtn) {
        editEventBtn.addEventListener('click', () => {
            if (!isAdminLoggedIn) {
                adminLoginModal.style.display = 'block';
                return;
            }
            // Auswahl der Event-Sektion (1-4)
            let eventSection = prompt('Welches Event möchten Sie bearbeiten? (1-4)');
            if (!eventSection || !['1','2','3','4'].includes(eventSection.trim())) {
                alert('Ungültige Auswahl. Bitte geben Sie eine Zahl von 1 bis 4 ein.');
                return;
            }
            eventForm.reset();
            eventForm.dataset.eventSection = eventSection.trim();
            adminModal.style.display = 'block';
        });
    }

    // Intercept event participation form submissions and send to backend
    document.querySelectorAll('.event-participation-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const data = {
                name: form.elements['name'].value,
                email: form.elements['email'].value,
                message: form.elements['message'].value,
                banner: '', // or any other field you want to send
            };
            fetch(`${API_BASE_URL}/participants`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
            .then(res => res.json())
            .then(response => {
                if (response.success) {
                    alert('Teilnahme gespeichert!');
                    form.reset();
                } else {
                    alert('Fehler beim Speichern: ' + (response.error || 'Unbekannter Fehler'));
                }
            })
            .catch(() => alert('Netzwerkfehler beim Speichern!'));
        });
    });
});

function setupEventListeners() {
    // Close buttons
    closeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            btn.closest('.modal').style.display = 'none';
        });
    });

    // Admin Login Form
    if (adminLoginForm) {
        adminLoginForm.addEventListener('submit', handleAdminLogin);
    }

    // Event Form
    if (eventForm) {
        eventForm.addEventListener('submit', handleEventSubmit);
    }

    // Logout Button
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }

    // Add Event Button
    if (addEventBtn) {
        addEventBtn.addEventListener('click', () => {
            if (!isAdminLoggedIn) {
                adminLoginModal.style.display = 'block';
                return;
            }
            // Auswahl der Event-Sektion (1-4)
            let eventSection = prompt('Welches Event möchten Sie bearbeiten? (1-4)');
            if (!eventSection || !['1','2','3','4'].includes(eventSection.trim())) {
                alert('Ungültige Auswahl. Bitte geben Sie eine Zahl von 1 bis 4 ein.');
                return;
            }
            eventForm.reset();
            eventForm.dataset.eventSection = eventSection.trim();
            adminModal.style.display = 'block';
        });
    }

    // Window click to close modals
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            e.target.style.display = 'none';
        }
    });

    // Event delegation for edit buttons
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('edit-event-btn')) {
            handleEditEvent(e.target.dataset.id);
        }
        if (e.target.classList.contains('edit-image-btn')) {
            const eventId = e.target.dataset.id;
            openImageEditModal(eventId);
        }
        if (e.target.classList.contains('modal-close') || e.target.classList.contains('modal-cancel')) {
            eventEditModal.style.display = 'none';
            eventEditMessage.textContent = '';
            eventEditPreview.src = '';
            eventEditUrlInput.value = '';
            eventEditCurrentUrl.textContent = '';
        }
    });
}

function checkAdminStatus() {
    isAdminLoggedIn = localStorage.getItem('adminLoggedIn') === 'true';
    updateUIForAdminStatus();
}

function updateUIForAdminStatus() {
    if (logoutBtn) {
        logoutBtn.style.display = isAdminLoggedIn ? 'block' : 'none';
    }
    if (addEventBtn) {
        addEventBtn.style.display = isAdminLoggedIn ? 'block' : 'none';
    }
    // Show/hide show-participants buttons
    for (let i = 1; i <= 4; i++) {
        const btn = document.getElementById(`show-participants-btn-${i}`);
        if (btn) btn.style.display = isAdminLoggedIn ? 'block' : 'none';
    }
}

async function handleAdminLogin(e) {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            // Store JWT tokens
            localStorage.setItem('accessToken', data.access_token);
            localStorage.setItem('refreshToken', data.refresh_token);
            localStorage.setItem('adminLoggedIn', 'true');

            isAdminLoggedIn = true;
            adminLoginModal.style.display = 'none';
            updateUIForAdminStatus();
            alert('Successfully logged in!');
            loadEvents(); // Reload events to show edit buttons
        } else {
            alert(data.error || 'Login failed');
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('Network error during login');
    }
}

function handleLogout() {
    isAdminLoggedIn = false;
    localStorage.removeItem('adminLoggedIn');
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    updateUIForAdminStatus();
    loadEvents(); // Reload events to hide edit buttons
}

async function handleEventSubmit(e) {
    e.preventDefault();
    if (!isAdminLoggedIn) {
        adminLoginModal.style.display = 'block';
        return;
    }

    const eventData = {
        title: document.getElementById('eventTitle').value,
        date: document.getElementById('eventDate').value,
        time: document.getElementById('eventTime').value,
        location: document.getElementById('eventLocation').value,
        description: document.getElementById('eventDescription').value,
        imageUrl: document.getElementById('eventImageUrl') ? document.getElementById('eventImageUrl').value : '',
        section: eventForm.dataset.eventSection || ''
    };

    let events = [];
    try {
        const eventsData = localStorage.getItem('events');
        events = eventsData ? JSON.parse(eventsData) : [];

        // Validate that events is actually an array
        if (!Array.isArray(events)) {
            console.error('Events data is not an array, resetting to empty array');
            events = [];
            localStorage.setItem('events', '[]');
        }
    } catch (error) {
        console.error('Error parsing events:', error);
        events = [];
        localStorage.setItem('events', '[]');
    }

    const editingEventId = eventForm.dataset.editingEventId;

    if (editingEventId) {
        // Update existing event
        const eventIndex = events.findIndex(e => e.id.toString() === editingEventId);
        if (eventIndex !== -1) {
            events[eventIndex] = {
                ...events[eventIndex],
                ...eventData,
                lastModified: new Date().toISOString()
            };
        }
    } else {
        // Add new event
        events.push({
            ...eventData,
            id: Date.now(),
            timestamp: new Date().toISOString()
        });
    }

    try {
        localStorage.setItem('events', JSON.stringify(events));
        eventForm.reset();
        delete eventForm.dataset.editingEventId;
        adminModal.style.display = 'none';
        alert('Event saved successfully!');
        await loadEvents();
    } catch (error) {
        console.error('Error saving events:', error);
        alert('Error saving event. Please try again.');
    }
}

async function loadEvents() {
    let events = [];
    try {
        const eventsData = localStorage.getItem('events');
        events = eventsData ? JSON.parse(eventsData) : [];
        if (!Array.isArray(events)) {
            console.error('Events data is not an array, resetting to empty array');
            events = [];
            localStorage.setItem('events', '[]');
        }
    } catch (error) {
        console.error('Error parsing events:', error);
        events = [];
        localStorage.setItem('events', '[]');
    }

    // Events in die jeweiligen Sektionen einfügen
    for (let i = 1; i <= 4; i++) {
        const section = document.getElementById(`event${i}`);
        if (section) {
            const event = events.find(ev => ev.section === String(i));
            if (event) {
                const imgUrl = event.imageUrl && event.imageUrl.trim() !== '' ? event.imageUrl : 'https://i.postimg.cc/L5fgbxQJ/image.png';
                section.querySelector('.event-image').src = imgUrl;
                section.querySelector('h2').textContent = event.title || `Event ${i}`;
                section.querySelector('.event-participation').insertAdjacentHTML('beforebegin', `
                    <div class="event-details">
                        <p><strong>Date:</strong> ${formatDate(event.date)}</p>
                        <p><strong>Time:</strong> ${event.time}</p>
                        <p><strong>Location:</strong> ${event.location}</p>
                        <p>${event.description}</p>
                        ${isAdminLoggedIn ? `<button class=\"edit-image-btn\" data-id=\"${event.id}\">Bild bearbeiten</button>` : ''}
                    </div>
                `);
            }
        }
    }

    // Events-Container für Übersicht (optional)
    const eventsContainer = document.getElementById('events-container');
    if (eventsContainer) {
        eventsContainer.innerHTML = events.map(event => `
            <div class="event-card">
                <h3>${event.title}</h3>
                <img src="${event.imageUrl && event.imageUrl.trim() !== '' ? event.imageUrl : 'https://i.postimg.cc/L5fgbxQJ/image.png'}" alt="Event Bild" class="event-image" style="max-width:100%;height:auto;" />
                <p><strong>Date:</strong> ${formatDate(event.date)}</p>
                <p><strong>Time:</strong> ${event.time}</p>
                <p><strong>Location:</strong> ${event.location}</p>
                <p>${event.description}</p>
                ${isAdminLoggedIn ? `<button class=\"edit-image-btn\" data-id=\"${event.id}\">Bild bearbeiten</button>` : ''}
            </div>
        `).join('');
    }
}

function handleEditEvent(eventId) {
    if (!isAdminLoggedIn) {
        adminLoginModal.style.display = 'block';
        return;
    }

    let events = [];
    try {
        const eventsData = localStorage.getItem('events');
        events = eventsData ? JSON.parse(eventsData) : [];

        // Validate that events is actually an array
        if (!Array.isArray(events)) {
            console.error('Events data is not an array, resetting to empty array');
            events = [];
            localStorage.setItem('events', '[]');
            return;
        }
    } catch (error) {
        console.error('Error parsing events:', error);
        events = [];
        localStorage.setItem('events', '[]');
        return;
    }

    const event = events.find(e => e.id.toString() === eventId);

    if (event) {
        document.getElementById('eventTitle').value = event.title;
        document.getElementById('eventDate').value = event.date;
        document.getElementById('eventTime').value = event.time;
        document.getElementById('eventLocation').value = event.location;
        document.getElementById('eventDescription').value = event.description;
        if(document.getElementById('eventImageUrl')) {
            document.getElementById('eventImageUrl').value = event.imageUrl || '';
        }
        eventForm.dataset.editingEventId = eventId;
        adminModal.style.display = 'block';
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

// Helper functions for modal management
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.style.display = 'block';
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.style.display = 'none';
}

function resetForm(formId) {
    const form = document.getElementById(formId);
    if (form) form.reset();
}

// Debug helper
function debugLog(...args) {
    if (process.env.NODE_ENV === 'development') {
        console.log(...args);
    }
}

function initializeEventsStorage() {
    try {
        const eventsData = localStorage.getItem('events');
        if (!eventsData) {
            localStorage.setItem('events', '[]');
            return;
        }

        const events = JSON.parse(eventsData);
        if (!Array.isArray(events)) {
            console.warn('Events data was corrupted, resetting to empty array');
            localStorage.setItem('events', '[]');
        }
    } catch (error) {
        console.error('Error initializing events storage:', error);
        localStorage.setItem('events', '[]');
    }
}

// Bild-Edit-Modal öffnen
function openImageEditModal(eventId) {
    let events = [];
    try {
        const eventsData = localStorage.getItem('events');
        events = eventsData ? JSON.parse(eventsData) : [];
    } catch (error) { events = []; }
    const event = events.find(e => e.id.toString() === eventId);
    if (event) {
        editingImageEventId = eventId;
        eventEditModal.style.display = 'block';
        eventEditCurrentUrl.textContent = event.imageUrl || '';
        eventEditUrlInput.value = event.imageUrl || '';
        eventEditPreview.src = event.imageUrl || '';
        eventEditMessage.textContent = '';
    }
}

// Vorschau aktualisieren
if (eventEditUrlInput) {
    eventEditUrlInput.addEventListener('input', () => {
        eventEditPreview.src = eventEditUrlInput.value;
    });
}

// Bild-URL speichern
if (eventEditForm) {
    eventEditForm.addEventListener('submit', function(e) {
        e.preventDefault();
        if (!editingImageEventId) return;
        let events = [];
        try {
            const eventsData = localStorage.getItem('events');
            events = eventsData ? JSON.parse(eventsData) : [];
        } catch (error) { events = []; }
        const eventIndex = events.findIndex(e => e.id.toString() === editingImageEventId);
        if (eventIndex !== -1) {
            events[eventIndex].imageUrl = eventEditUrlInput.value;
            localStorage.setItem('events', JSON.stringify(events));
            eventEditMessage.textContent = 'Bild-URL gespeichert!';
            eventEditPreview.src = eventEditUrlInput.value;
            eventEditCurrentUrl.textContent = eventEditUrlInput.value;
            loadEvents();
            setTimeout(() => { eventEditModal.style.display = 'none'; }, 1000);
        } else {
            eventEditMessage.textContent = 'Fehler beim Speichern.';
        }
    });
}

// --- Show Participants Modal Logic ---
function setupShowParticipantsButtons() {
    for (let i = 1; i <= 4; i++) {
        const btn = document.getElementById(`show-participants-btn-${i}`);
        const modal = document.getElementById(`participants-modal-${i}`);
        const closeBtn = modal ? modal.querySelector('.participants-modal-close') : null;
        if (btn && modal && closeBtn) {
            btn.addEventListener('click', () => {
                fetchAndShowParticipants(i);
            });
            closeBtn.addEventListener('click', () => {
                modal.style.display = 'none';
            });
        }
    }
    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
        for (let i = 1; i <= 4; i++) {
            const modal = document.getElementById(`participants-modal-${i}`);
            if (modal && e.target === modal) {
                modal.style.display = 'none';
            }
        }
    });
}

async function fetchAndShowParticipants(eventNumber) {
    const modal = document.getElementById(`participants-modal-${eventNumber}`);
    const listDiv = document.getElementById(`participants-list-${eventNumber}`);
    if (!modal || !listDiv) return;
    listDiv.innerHTML = '<p>Lade Teilnehmer...</p>';
    modal.style.display = 'block';

    const accessToken = localStorage.getItem('accessToken');
    if (!accessToken) {
        listDiv.innerHTML = '<p>Nicht angemeldet. Bitte zuerst einloggen.</p>';
        return;
    }

    try {
        const res = await fetch(`${API_BASE_URL}/participants`, {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });

        if (res.status === 401) {
            // Token expired, try to refresh
            const refreshToken = localStorage.getItem('refreshToken');
            if (refreshToken) {
                const refreshResponse = await fetch(`${API_BASE_URL}/refresh`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ refresh_token: refreshToken })
                });

                if (refreshResponse.ok) {
                    const refreshData = await refreshResponse.json();
                    localStorage.setItem('accessToken', refreshData.access_token);
                    localStorage.setItem('refreshToken', refreshData.refresh_token);

                    // Retry the original request
                    const retryRes = await fetch(`${API_BASE_URL}/participants`, {
                        headers: {
                            'Authorization': `Bearer ${refreshData.access_token}`
                        }
                    });

                    if (retryRes.ok) {
                        const data = await retryRes.json();
                        displayParticipants(data, eventNumber, listDiv);
                    } else {
                        listDiv.innerHTML = '<p>Fehler beim Laden der Teilnehmer.</p>';
                    }
                } else {
                    // Refresh failed, redirect to login
                    handleLogout();
                    listDiv.innerHTML = '<p>Session abgelaufen. Bitte erneut anmelden.</p>';
                }
            } else {
                handleLogout();
                listDiv.innerHTML = '<p>Session abgelaufen. Bitte erneut anmelden.</p>';
            }
        } else if (res.ok) {
            const data = await res.json();
            displayParticipants(data, eventNumber, listDiv);
        } else {
            listDiv.innerHTML = '<p>Fehler beim Laden der Teilnehmer.</p>';
        }
    } catch (e) {
        listDiv.innerHTML = `<p>Fehler beim Laden: ${e.message}</p>`;
    }
}

function displayParticipants(data, eventNumber, listDiv) {
    if (!data.participants) {
        listDiv.innerHTML = '<p>Keine Teilnehmer gefunden</p>';
        return;
    }

    // Filter by banner/section
    const filtered = data.participants.filter(p => (p.banner || '1') === String(eventNumber));
    if (filtered.length === 0) {
        listDiv.innerHTML = '<p>Keine Teilnehmer für dieses Event.</p>';
    } else {
        listDiv.innerHTML = filtered.map(p => `
            <div class="participant-item${p.message ? ' has-message' : ''}${p.email ? ' has-email' : ''}">
                <strong>${p.name}</strong>
                ${p.email ? `<div><span class='detail-label'>E-Mail:</span> ${p.email}</div>` : ''}
                ${p.message ? `<div><span class='detail-label'>Nachricht:</span> ${p.message}</div>` : ''}
                ${p.timestamp ? `<div><small>${new Date(p.timestamp).toLocaleString('de-DE')}</small></div>` : ''}
            </div>
        `).join('');
    }
}
// Main JavaScript - Cleaned up event handlers and standardized API calls
document.addEventListener('DOMContentLoaded', function () {
    // Initialize all modules
    initAdminLogin();
    initHeroSlideshow();
    initPrivacyModal();
    initLogoAnimation();
    initFormValidation();
    
    // Log initialization
    if (window.APP_CONFIG && window.APP_CONFIG.DEBUG) {
        console.log('[KOSGE] Main application initialized');
    }
});

// Admin Login Functionality - Cleaned up
function initAdminLogin() {
    const adminButton = document.getElementById('admin-login-button');
    const adminModal = document.getElementById('admin-login-modal');
    
    if (!adminButton || !adminModal) {
        console.warn('[KOSGE] Admin login elements not found');
        return;
    }
    
    const closeBtn = adminModal.querySelector('.close');
    const loginForm = document.getElementById('admin-login-form');

    // Modal open handler
    adminButton.addEventListener('click', function (e) {
        e.preventDefault();
        adminModal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    });

    // Modal close handlers
    const closeModal = () => {
        adminModal.style.display = 'none';
        document.body.style.overflow = '';
    };

    closeBtn.addEventListener('click', closeModal);

    // Close modal when clicking outside
    window.addEventListener('click', function (event) {
        if (event.target === adminModal) {
            closeModal();
        }
    });

    // Close modal with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && adminModal.style.display === 'block') {
            closeModal();
        }
    });

    // Login form submission with proper API integration
    loginForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        
        const username = document.getElementById('admin-username').value.trim();
        const password = document.getElementById('admin-password').value;
        const submitBtn = loginForm.querySelector('button[type="submit"]');
        
        // Disable submit button during request
        submitBtn.disabled = true;
        submitBtn.textContent = 'Logging in...';
        
        try {
            // Validate input
            if (!username || !password) {
                throw new Error('Username and password are required');
            }
            
            // API call using standardized utilities
            const response = await window.API_UTILS.requestWithRetry(
                window.APP_CONFIG.ENDPOINTS.LOGIN,
                {
                    method: 'POST',
                    body: JSON.stringify({ username, password })
                }
            );
            
            // Success handling
            showNotification('Login successful!', 'success');
            closeModal();
            
            // Store token for future requests
            if (response.token) {
                localStorage.setItem('admin_token', response.token);
            }
            
            // Redirect to admin dashboard
            setTimeout(() => {
                window.location.href = '/admin/dashboard.html';
            }, 1000);
            
        } catch (error) {
            const errorMessage = window.API_UTILS.handleError(error, 'Admin Login');
            showNotification(errorMessage, 'error');
        } finally {
            // Re-enable submit button
            submitBtn.disabled = false;
            submitBtn.textContent = 'Login';
        }
    });
}

// Hero Slideshow functionality - Improved
function initHeroSlideshow() {
    const heroSlides = document.querySelectorAll('.hero-slide');
    
    if (heroSlides.length === 0) {
        return;
    }
    
    let currentSlide = 0;
    let slideInterval;

    function showSlide(index) {
        // Validate index
        if (index < 0 || index >= heroSlides.length) {
            return;
        }
        
        // Hide all slides
        heroSlides.forEach(slide => {
            slide.classList.remove('active');
        });

        // Show the current slide
        heroSlides[index].classList.add('active');
    }

    function nextSlide() {
        currentSlide = (currentSlide + 1) % heroSlides.length;
        showSlide(currentSlide);
    }

    function prevSlide() {
        currentSlide = (currentSlide - 1 + heroSlides.length) % heroSlides.length;
        showSlide(currentSlide);
    }

    // Initialize slideshow
    showSlide(currentSlide);

    // Auto-advance slides
    function startSlideshow() {
        slideInterval = setInterval(nextSlide, 4000);
    }

    function stopSlideshow() {
        if (slideInterval) {
            clearInterval(slideInterval);
        }
    }

    // Pause on hover
    const slideshowContainer = document.querySelector('.hero-slideshow');
    if (slideshowContainer) {
        slideshowContainer.addEventListener('mouseenter', stopSlideshow);
        slideshowContainer.addEventListener('mouseleave', startSlideshow);
    }

    // Keyboard navigation
    document.addEventListener('keydown', function(e) {
        if (e.key === 'ArrowLeft') {
            prevSlide();
        } else if (e.key === 'ArrowRight') {
            nextSlide();
        }
    });

    // Start slideshow
    startSlideshow();
}

// Privacy Policy Modal Functionality - Cleaned up
function initPrivacyModal() {
    const modal = document.getElementById('privacy-policy-modal');
    const link = document.getElementById('privacy-policy-link');
    
    if (!modal || !link) {
        return;
    }
    
    const closeBtn = modal.querySelector('.close');

    // Open modal
    link.addEventListener('click', function(e) {
        e.preventDefault();
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    });

    // Close modal handlers
    const closeModal = () => {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    };

    closeBtn.addEventListener('click', closeModal);

    // Close modal when clicking outside
    window.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeModal();
        }
    });

    // Close modal with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal.style.display === 'block') {
            closeModal();
        }
    });
}

// Logo Animation Functionality - Improved
function initLogoAnimation() {
    const logoWrapper = document.querySelector('.logo-wrapper');
    const staticLogo = document.querySelector('.static-logo');
    const animatedLogo = document.querySelector('.animated-logo');
    
    if (!logoWrapper || !staticLogo || !animatedLogo) {
        return;
    }
    
    let isAnimating = false;
    let animationTimeout;

    // Function to show animated logo
    function showAnimatedLogo() {
        if (!isAnimating) {
            isAnimating = true;
            animatedLogo.style.display = 'block';
            staticLogo.style.opacity = '0';
            animatedLogo.style.opacity = '1';
        }
    }

    // Function to show static logo
    function showStaticLogo() {
        if (isAnimating) {
            isAnimating = false;
            staticLogo.style.opacity = '1';
            animatedLogo.style.opacity = '0';
            
            // Clear existing timeout
            if (animationTimeout) {
                clearTimeout(animationTimeout);
            }
            
            // Wait for fade out animation before hiding
            animationTimeout = setTimeout(() => {
                animatedLogo.style.display = 'none';
            }, 300);
        }
    }

    // Add event listeners
    logoWrapper.addEventListener('mouseenter', showAnimatedLogo);
    logoWrapper.addEventListener('mouseleave', showStaticLogo);
    logoWrapper.addEventListener('click', function() {
        if (isAnimating) {
            showStaticLogo();
        } else {
            showAnimatedLogo();
        }
    });
}

// Form Validation - New standardized validation
function initFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(form)) {
                e.preventDefault();
            }
        });
    });
}

function validateForm(form) {
    const inputs = form.querySelectorAll('input, textarea, select');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!validateInput(input)) {
            isValid = false;
        }
    });
    
    return isValid;
}

function validateInput(input) {
    const value = input.value.trim();
    const type = input.type;
    const required = input.hasAttribute('required');
    
    // Clear previous error
    clearInputError(input);
    
    // Check required fields
    if (required && !value) {
        showInputError(input, 'This field is required');
        return false;
    }
    
    // Type-specific validation
    switch (type) {
        case 'email':
            if (value && !window.APP_CONFIG.VALIDATION.EMAIL_REGEX.test(value)) {
                showInputError(input, 'Please enter a valid email address');
                return false;
            }
            break;
        case 'password':
            if (value && value.length < window.APP_CONFIG.VALIDATION.MIN_PASSWORD_LENGTH) {
                showInputError(input, `Password must be at least ${window.APP_CONFIG.VALIDATION.MIN_PASSWORD_LENGTH} characters`);
                return false;
            }
            break;
        case 'text':
            if (value && value.length < window.APP_CONFIG.VALIDATION.MIN_NAME_LENGTH) {
                showInputError(input, `Name must be at least ${window.APP_CONFIG.VALIDATION.MIN_NAME_LENGTH} characters`);
                return false;
            }
            break;
    }
    
    return true;
}

function showInputError(input, message) {
    input.classList.add('error');
    
    // Create or update error message
    let errorElement = input.parentNode.querySelector('.error-message');
    if (!errorElement) {
        errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        input.parentNode.appendChild(errorElement);
    }
    errorElement.textContent = message;
}

function clearInputError(input) {
    input.classList.remove('error');
    const errorElement = input.parentNode.querySelector('.error-message');
    if (errorElement) {
        errorElement.remove();
    }
}

// Notification system
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 5000);
    
    // Allow manual close
    notification.addEventListener('click', () => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    });
}

// Utility function to check if element exists
function elementExists(selector) {
    return document.querySelector(selector) !== null;
}

// Export utilities for use in other modules
window.KOSGE_UTILS = {
    showNotification,
    validateForm,
    validateInput,
    elementExists
};
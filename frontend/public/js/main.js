// Admin Login Funktionalität
document.addEventListener('DOMContentLoaded', function () {
    const adminButton = document.getElementById('admin-login-button');
    const adminModal = document.getElementById('admin-login-modal');
    const closeBtn = adminModal.querySelector('.close');
    const loginForm = document.getElementById('admin-login-form');

    // Modal öffnen
    adminButton.addEventListener('click', function () {
        adminModal.style.display = 'block';
    });

    // Modal schließen
    closeBtn.addEventListener('click', function () {
        adminModal.style.display = 'none';
    });

    // Modal schließen wenn außerhalb geklickt wird
    window.addEventListener('click', function (event) {
        if (event.target == adminModal) {
            adminModal.style.display = 'none';
        }
    });

    // Login Formular absenden
    loginForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const username = document.getElementById('admin-username').value;
        const password = document.getElementById('admin-password').value;

        // Hier können Sie die Login-Logik implementieren
        console.log('Login attempt:', username);

        // Beispiel für eine einfache Validierung
        if (username === 'admin' && password === 'password') {
            alert('Login erfolgreich!');
            adminModal.style.display = 'none';
            // Hier können Sie zur Admin-Seite weiterleiten
            // window.location.href = '/admin';
        } else {
            alert('Ungültige Anmeldedaten!');
        }
    });
});

// Hero Slideshow functionality
document.addEventListener('DOMContentLoaded', function () {
    const heroSlides = document.querySelectorAll('.hero-slide');
    let currentSlide = 0;

    function showSlide(index) {
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

    // Initialize slideshow
    showSlide(currentSlide);

    // Change slide every 4 seconds (adjusted for more images)
    setInterval(nextSlide, 4000);
});

// Privacy Policy Modal Functionality
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('privacy-policy-modal');
    const link = document.getElementById('privacy-policy-link');
    const closeBtn = modal.querySelector('.close');

    // Open modal
    link.addEventListener('click', function(e) {
        e.preventDefault();
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
    });

    // Close modal with X button
    closeBtn.addEventListener('click', function() {
        modal.style.display = 'none';
        document.body.style.overflow = ''; // Restore scrolling
    });

    // Close modal when clicking outside
    window.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.style.display = 'none';
            document.body.style.overflow = ''; // Restore scrolling
        }
    });

    // Close modal with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal.style.display === 'block') {
            modal.style.display = 'none';
            document.body.style.overflow = ''; // Restore scrolling
        }
    });
});

// Logo Animation Functionality
document.addEventListener('DOMContentLoaded', function() {
    const logoWrapper = document.querySelector('.logo-wrapper');
    const staticLogo = document.querySelector('.static-logo');
    const animatedLogo = document.querySelector('.animated-logo');
    let isAnimating = false;

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
            // Wait for fade out animation before hiding
            setTimeout(() => {
                animatedLogo.style.display = 'none';
            }, 300);
        }
    }

    // Add event listeners for both hover and click
    logoWrapper.addEventListener('mouseenter', showAnimatedLogo);
    logoWrapper.addEventListener('mouseleave', showStaticLogo);
    logoWrapper.addEventListener('click', function() {
        if (isAnimating) {
            showStaticLogo();
        } else {
            showAnimatedLogo();
        }
    });
});
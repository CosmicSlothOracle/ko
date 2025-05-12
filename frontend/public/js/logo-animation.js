document.addEventListener('DOMContentLoaded', function() {
    const staticLogo = document.querySelector('.static-logo');
    const animatedLogo = document.querySelector('.animated-logo');
    let isAnimating = false;
    // Duration of the GIF in ms (adjust to actual GIF length)
    const GIF_DURATION = 2000;

    if (staticLogo && animatedLogo) {
        staticLogo.addEventListener('click', function() {
            if (isAnimating) return;
            isAnimating = true;
            // Fade out static logo
            staticLogo.classList.add('fade-out');
            // Show and fade in animated logo
            animatedLogo.classList.add('visible');
            // Reset GIF by re-assigning src
            const src = animatedLogo.src;
            animatedLogo.style.display = 'none';
            animatedLogo.offsetHeight; // force reflow
            animatedLogo.src = '';
            animatedLogo.src = src;
            animatedLogo.style.display = 'block';
            // After GIF duration, keep last frame
            setTimeout(function() {
                // Keep animated logo visible (last frame)
                animatedLogo.classList.add('visible');
                isAnimating = false;
            }, GIF_DURATION);
        });
    }
});
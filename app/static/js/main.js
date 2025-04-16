/**
 * Product Analytics - Main JavaScript
 * Contains animation controls, loading states, and UI interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize components
    initializeDarkMode();
    initializeAnimations();
    initializeLoaders();
    initializeTooltips();
    initializeMobileMenu();
    
    // Add page transition effect
    addPageTransition();
});

/**
 * Dark mode initialization and toggle
 */
function initializeDarkMode() {
    // Dark mode is enforced by default
    document.documentElement.classList.add('dark');
    
    // Optional: Add dark mode toggle if needed
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', function() {
            document.documentElement.classList.toggle('dark');
        });
    }
}

/**
 * Initialize animations with staggered timing
 */
function initializeAnimations() {
    // Staggered animations for lists
    const staggeredItems = document.querySelectorAll('.stagger-item');
    staggeredItems.forEach((item, index) => {
        item.style.animationDelay = `${index * 0.1}s`;
        item.classList.add('animate-slide-up');
    });
    
    // Count-up animation for number displays
    const countElements = document.querySelectorAll('.count-up');
    countElements.forEach(element => {
        const target = parseInt(element.getAttribute('data-target'), 10);
        animateCountUp(element, target);
    });
}

/**
 * Animate numbers counting up
 */
function animateCountUp(element, target) {
    const duration = 2000; // 2 seconds
    const frameDuration = 1000 / 60; // 60fps
    const totalFrames = Math.round(duration / frameDuration);
    const start = 0;
    
    let frame = 0;
    const counter = setInterval(() => {
        frame++;
        const progress = frame / totalFrames;
        const currentCount = Math.round(progress * (target - start) + start);
        
        if (frame === totalFrames) {
            clearInterval(counter);
            element.textContent = target.toLocaleString();
        } else {
            element.textContent = currentCount.toLocaleString();
        }
    }, frameDuration);
}

/**
 * Initialize loading states and indicators
 */
function initializeLoaders() {
    // Show loading overlay for links with data-loading attribute
    const loadingLinks = document.querySelectorAll('[data-loading="true"]');
    loadingLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Prevent showing loader if link is to external site
            if (this.getAttribute('target') === '_blank' || 
                this.getAttribute('href').startsWith('http') ||
                this.getAttribute('href').startsWith('mailto:')) {
                return;
            }
            
            // Create and append loading overlay
            const loadingOverlay = document.createElement('div');
            loadingOverlay.className = 'fixed inset-0 bg-dark-DEFAULT bg-opacity-50 flex items-center justify-center z-50 animate-fade-in';
            loadingOverlay.innerHTML = `
                <div class="bg-dark-lighter p-5 rounded-lg shadow-lg flex flex-col items-center">
                    <div class="loading-spinner text-primary-light">
                        <i class="fas fa-circle-notch fa-spin fa-3x"></i>
                    </div>
                    <p class="mt-3 text-white">Loading...</p>
                </div>
            `;
            document.body.appendChild(loadingOverlay);
        });
    });
    
    // Add loading state to buttons with data-loading attribute
    const loadingButtons = document.querySelectorAll('button[data-loading="true"]');
    loadingButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Don't add loading state if button is disabled or has type="button"
            if (this.disabled || this.getAttribute('type') === 'button') {
                return;
            }
            
            // Store original content and add spinner
            const originalContent = this.innerHTML;
            this.setAttribute('data-original-content', originalContent);
            this.innerHTML = `
                <span class="inline-block animate-spin mr-2">
                    <i class="fas fa-circle-notch"></i>
                </span>
                Processing...
            `;
            this.disabled = true;
        });
    });
}

/**
 * Initialize tooltips
 */
function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            const tooltipText = this.getAttribute('data-tooltip');
            
            // Create tooltip element
            const tooltip = document.createElement('div');
            tooltip.className = 'absolute z-50 px-2 py-1 text-xs bg-dark-lightest text-white rounded shadow-lg animate-fade-in';
            tooltip.textContent = tooltipText;
            tooltip.style.bottom = '100%';
            tooltip.style.left = '50%';
            tooltip.style.transform = 'translateX(-50%) translateY(-5px)';
            tooltip.style.whiteSpace = 'nowrap';
            
            // Add arrow
            const arrow = document.createElement('div');
            arrow.className = 'absolute w-2 h-2 bg-dark-lightest rotate-45';
            arrow.style.bottom = '-4px';
            arrow.style.left = '50%';
            arrow.style.transform = 'translateX(-50%)';
            tooltip.appendChild(arrow);
            
            this.appendChild(tooltip);
            this.setAttribute('data-tooltip-active', 'true');
        });
        
        element.addEventListener('mouseleave', function() {
            const activeTooltip = this.querySelector('[data-tooltip-active="true"]');
            if (activeTooltip) {
                this.removeChild(activeTooltip);
            }
            this.removeAttribute('data-tooltip-active');
        });
    });
}

/**
 * Initialize mobile menu toggle
 */
function initializeMobileMenu() {
    const mobileMenuButton = document.querySelector('[aria-controls="mobile-menu"]');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function() {
            const expanded = this.getAttribute('aria-expanded') === 'true';
            this.setAttribute('aria-expanded', String(!expanded));
            
            if (expanded) {
                mobileMenu.classList.add('animate-slide-up-reverse');
                setTimeout(() => {
                    mobileMenu.classList.add('hidden');
                    mobileMenu.classList.remove('animate-slide-up-reverse');
                }, 300);
            } else {
                mobileMenu.classList.remove('hidden');
                mobileMenu.classList.add('animate-slide-up');
            }
        });
    }
}

/**
 * Add page transition effect
 */
function addPageTransition() {
    // Add transition out effect on all internal links
    document.querySelectorAll('a').forEach(link => {
        // Skip external links and links with specific attributes
        if (link.getAttribute('target') === '_blank' || 
            link.getAttribute('href').startsWith('http') || 
            link.getAttribute('href').startsWith('#') ||
            link.getAttribute('href').startsWith('mailto:') ||
            link.getAttribute('download') !== null) {
            return;
        }
        
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const href = this.getAttribute('href');
            
            // Fade out the page
            document.body.classList.add('opacity-0');
            document.body.classList.add('transition-opacity');
            document.body.classList.add('duration-300');
            
            // Navigate after transition
            setTimeout(() => {
                window.location.href = href;
            }, 300);
        });
    });
}

/**
 * Show notification toast
 * @param {string} message - Message to display
 * @param {string} type - success, error, warning, or info
 * @param {number} duration - Duration in milliseconds
 */
function showToast(message, type = 'info', duration = 3000) {
    // Remove existing toasts
    const existingToasts = document.querySelectorAll('.toast-notification');
    existingToasts.forEach(toast => {
        toast.remove();
    });
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast-notification fixed bottom-4 right-4 p-4 rounded-md shadow-lg z-50 animate-slide-up`;
    
    // Set appropriate styles based on type
    switch (type) {
        case 'success':
            toast.classList.add('bg-green-700', 'text-green-50', 'border', 'border-green-600');
            toast.innerHTML = `<i class="fas fa-check-circle mr-2"></i>${message}`;
            break;
        case 'error':
            toast.classList.add('bg-red-700', 'text-red-50', 'border', 'border-red-600');
            toast.innerHTML = `<i class="fas fa-times-circle mr-2"></i>${message}`;
            break;
        case 'warning':
            toast.classList.add('bg-yellow-700', 'text-yellow-50', 'border', 'border-yellow-600');
            toast.innerHTML = `<i class="fas fa-exclamation-triangle mr-2"></i>${message}`;
            break;
        default:
            toast.classList.add('bg-blue-700', 'text-blue-50', 'border', 'border-blue-600');
            toast.innerHTML = `<i class="fas fa-info-circle mr-2"></i>${message}`;
    }
    
    // Add toast to DOM
    document.body.appendChild(toast);
    
    // Remove toast after duration
    setTimeout(() => {
        toast.classList.remove('animate-slide-up');
        toast.classList.add('animate-slide-down');
        
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, duration);
}

// Expose functions globally
window.showToast = showToast;
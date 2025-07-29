/**
 * Shut Up and Drive - Aggressive UI Animations
 * High-energy interactions that match the app's attitude
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // Aggressive button hover effects
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05) rotateX(5deg)';
            this.style.transition = 'all 0.2s cubic-bezier(0.68, -0.55, 0.265, 1.55)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1) rotateX(0deg)';
        });
        
        button.addEventListener('mousedown', function() {
            this.style.transform = 'scale(0.95)';
        });
        
        button.addEventListener('mouseup', function() {
            this.style.transform = 'scale(1.05) rotateX(5deg)';
        });
    });
    
    // Execute Mission button special effects
    const executeMissionBtn = document.getElementById('generateRoutesBtn');
    if (executeMissionBtn) {
        executeMissionBtn.addEventListener('click', function(e) {
            // Add dramatic effect
            this.classList.add('generating-routes');
            this.innerHTML = '<i data-feather="zap"></i> EXECUTING...';
            feather.replace();
            
            // Create energy pulse effect
            const pulse = document.createElement('div');
            pulse.className = 'energy-pulse';
            pulse.style.cssText = `
                position: absolute;
                top: 50%;
                left: 50%;
                width: 0;
                height: 0;
                background: radial-gradient(circle, rgba(255,215,0,0.8) 0%, rgba(255,69,0,0.4) 50%, transparent 70%);
                border-radius: 50%;
                transform: translate(-50%, -50%);
                animation: energy-pulse 0.6s ease-out;
                pointer-events: none;
                z-index: 1000;
            `;
            
            this.style.position = 'relative';
            this.appendChild(pulse);
            
            setTimeout(() => {
                if (pulse.parentNode) {
                    pulse.parentNode.removeChild(pulse);
                }
            }, 600);
        });
    }
    
    // Lock Target button effects
    const lockTargetBtn = document.getElementById('addStopBtn');
    if (lockTargetBtn) {
        lockTargetBtn.addEventListener('click', function(e) {
            // Targeting animation
            this.style.animation = 'target-lock 0.5s ease-in-out';
            
            const crosshair = this.querySelector('[data-feather="crosshair"]');
            if (crosshair) {
                crosshair.style.animation = 'crosshair-spin 0.5s linear';
            }
        });
    }
    
    // Card entrance animations
    const cards = document.querySelectorAll('.card');
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const cardObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animation = 'card-slam 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55)';
                cardObserver.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    cards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(50px) rotateX(-15deg)';
        cardObserver.observe(card);
    });
    
    // Aggressive form validation feedback
    const formInputs = document.querySelectorAll('.form-control');
    formInputs.forEach(input => {
        input.addEventListener('invalid', function() {
            this.style.animation = 'invalid-shake 0.5s ease-in-out';
            this.style.borderColor = '#FF1744';
            this.style.boxShadow = '0 0 20px rgba(255, 23, 68, 0.6)';
        });
        
        input.addEventListener('input', function() {
            if (this.checkValidity()) {
                this.style.animation = 'valid-glow 0.3s ease-in-out';
                this.style.borderColor = '#32CD32';
                this.style.boxShadow = '0 0 15px rgba(50, 205, 50, 0.4)';
            }
        });
    });
    
    // Counter animation for stop numbers
    const counters = document.querySelectorAll('.card h2');
    counters.forEach(counter => {
        const target = parseInt(counter.textContent);
        let current = 0;
        const increment = target / 30; // 30 frames
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                counter.textContent = target;
                clearInterval(timer);
                // Flash effect when complete
                counter.style.animation = 'counter-complete 0.5s ease-in-out';
            } else {
                counter.textContent = Math.floor(current);
            }
        }, 50);
    });
    
    // Aggressive hover effects for route cards
    const routeCards = document.querySelectorAll('.route-card');
    routeCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateX(10px) scale(1.02)';
            this.style.borderLeftWidth = '8px';
            this.style.transition = 'all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateX(0) scale(1)';
            this.style.borderLeftWidth = '6px';
        });
    });
});

// Add CSS animations
const aggressiveStyles = document.createElement('style');
aggressiveStyles.textContent = `
    @keyframes energy-pulse {
        0% { width: 0; height: 0; opacity: 1; }
        100% { width: 200px; height: 200px; opacity: 0; }
    }
    
    @keyframes target-lock {
        0%, 100% { transform: scale(1); }
        25% { transform: scale(1.1) rotateZ(5deg); }
        75% { transform: scale(1.05) rotateZ(-5deg); }
    }
    
    @keyframes crosshair-spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(180deg); }
    }
    
    @keyframes card-slam {
        0% { 
            opacity: 0; 
            transform: translateY(50px) rotateX(-15deg) scale(0.8); 
        }
        60% { 
            opacity: 1; 
            transform: translateY(-10px) rotateX(5deg) scale(1.05); 
        }
        100% { 
            opacity: 1; 
            transform: translateY(0) rotateX(0deg) scale(1); 
        }
    }
    
    @keyframes invalid-shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-10px); }
        75% { transform: translateX(10px); }
    }
    
    @keyframes valid-glow {
        0% { box-shadow: 0 0 5px rgba(50, 205, 50, 0.2); }
        50% { box-shadow: 0 0 25px rgba(50, 205, 50, 0.8); }
        100% { box-shadow: 0 0 15px rgba(50, 205, 50, 0.4); }
    }
    
    @keyframes counter-complete {
        0%, 100% { transform: scale(1); color: inherit; }
        50% { transform: scale(1.2); color: #FFD700; text-shadow: 0 0 20px #FFD700; }
    }
`;

document.head.appendChild(aggressiveStyles);
// Fix UI refresh issues after route generation

function forceUIRefreshAfterRoutes() {
    console.log('Forcing UI refresh after route generation');
    
    // Clear any existing refresh timers
    if (window.refreshTimer) {
        clearTimeout(window.refreshTimer);
    }
    
    // Force immediate page reload with cache busting
    window.refreshTimer = setTimeout(() => {
        const timestamp = Date.now();
        const currentUrl = new URL(window.location.href);
        currentUrl.searchParams.set('refresh', timestamp);
        currentUrl.searchParams.set('routes_updated', 'true');
        
        console.log('Redirecting to:', currentUrl.toString());
        window.location.href = currentUrl.toString();
    }, 500);
}

// Enhanced route generation form handling
function handleRouteGenerationForm(form) {
    console.log('Route generation form submitted');
    
    const submitButton = form.querySelector('button[type="submit"]');
    if (submitButton) {
        submitButton.disabled = true;
        submitButton.innerHTML = '<i data-feather="clock"></i> Generating Routes...';
        feather.replace();
    }
    
    // Set up response handling
    fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        console.log('Route generation response received');
        
        if (response.redirected || response.ok) {
            console.log('Route generation successful, refreshing UI');
            forceUIRefreshAfterRoutes();
        } else {
            throw new Error('Route generation failed');
        }
    })
    .catch(error => {
        console.error('Route generation error:', error);
        
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.innerHTML = '<i data-feather="refresh-cw"></i> Generate Routes';
            feather.replace();
        }
        
        // Still try to refresh in case routes were partially generated
        setTimeout(forceUIRefreshAfterRoutes, 1000);
    });
    
    return false; // Prevent default form submission
}

// Auto-setup when page loads
document.addEventListener('DOMContentLoaded', function() {
    const routeForm = document.querySelector('form[action*="generate_routes"]');
    if (routeForm) {
        routeForm.onsubmit = function(e) {
            e.preventDefault();
            return handleRouteGenerationForm(this);
        };
        console.log('Route generation form handler attached');
    }
});
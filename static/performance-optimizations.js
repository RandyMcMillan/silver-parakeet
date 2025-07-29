/**
 * Performance optimizations and caching
 * Implements client-side caching and lazy loading
 */

// Simple client-side cache for geocoding results
class GeocodeCache {
    constructor() {
        this.cache = new Map();
        this.maxEntries = 100;
        this.loadFromStorage();
    }
    
    get(address) {
        const key = this.normalizeAddress(address);
        return this.cache.get(key);
    }
    
    set(address, coordinates) {
        const key = this.normalizeAddress(address);
        
        // Implement LRU eviction
        if (this.cache.size >= this.maxEntries) {
            const firstKey = this.cache.keys().next().value;
            this.cache.delete(firstKey);
        }
        
        this.cache.set(key, {
            coords: coordinates,
            timestamp: Date.now()
        });
        
        this.saveToStorage();
    }
    
    normalizeAddress(address) {
        return address.toLowerCase().trim().replace(/\s+/g, ' ');
    }
    
    loadFromStorage() {
        try {
            const stored = localStorage.getItem('geocodeCache');
            if (stored) {
                const data = JSON.parse(stored);
                // Only load recent entries (< 7 days old)
                const weekAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
                Object.entries(data).forEach(([key, value]) => {
                    if (value.timestamp > weekAgo) {
                        this.cache.set(key, value);
                    }
                });
            }
        } catch (error) {
            console.warn('Failed to load geocode cache:', error);
        }
    }
    
    saveToStorage() {
        try {
            const data = Object.fromEntries(this.cache);
            localStorage.setItem('geocodeCache', JSON.stringify(data));
        } catch (error) {
            console.warn('Failed to save geocode cache:', error);
        }
    }
}

// Initialize cache
const geocodeCache = new GeocodeCache();

// Lazy loading for route maps
function initializeMapLazily(mapContainerId, routes) {
    const mapContainer = document.getElementById(mapContainerId);
    if (!mapContainer) return;
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Initialize map when it becomes visible
                if (typeof initializeRouteMap === 'function') {
                    initializeRouteMap(mapContainerId, routes);
                }
                observer.unobserve(entry.target);
            }
        });
    }, { rootMargin: '50px' });
    
    observer.observe(mapContainer);
}

// Debounced form validation
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Optimize form field validation with debouncing
document.addEventListener('DOMContentLoaded', function() {
    const formFields = document.querySelectorAll('input[type="text"], input[type="email"], textarea, select');
    
    formFields.forEach(field => {
        const debouncedValidation = debounce(() => {
            // Trigger validation after user stops typing
            field.dispatchEvent(new Event('validate', { bubbles: true }));
        }, 300);
        
        field.addEventListener('input', debouncedValidation);
    });
});

// Preload critical resources
function preloadCriticalResources() {
    // Preload map tiles for common Atlanta area
    if (typeof L !== 'undefined') {
        const preloadTiles = [
            'https://tile.openstreetmap.org/12/1071/1626.png', // Atlanta center
            'https://tile.openstreetmap.org/12/1072/1626.png',
            'https://tile.openstreetmap.org/12/1071/1627.png',
            'https://tile.openstreetmap.org/12/1072/1627.png'
        ];
        
        preloadTiles.forEach(url => {
            const img = new Image();
            img.src = url;
        });
    }
}

// Initialize performance optimizations
document.addEventListener('DOMContentLoaded', preloadCriticalResources);

// Export cache for use by other scripts
window.geocodeCache = geocodeCache;
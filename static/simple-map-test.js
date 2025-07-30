// Simple Leaflet Map Test - Direct initialization without complexities

function createSimpleTestMap(routeId) {
    console.log(`Creating simple test map for route ${routeId}`);
    
    const mapElement = document.getElementById(`map-${routeId}`);
    if (!mapElement) {
        console.error(`Map element not found: map-${routeId}`);
        return;
    }
    
    // Clear any existing content
    mapElement.innerHTML = '';
    
    try {
        // Create basic Leaflet map
        const map = L.map(mapElement).setView([33.7490, -84.3880], 11);
        
        // Add tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap'
        }).addTo(map);
        
        // Add a simple marker
        L.marker([33.7490, -84.3880]).addTo(map)
            .bindPopup('Atlanta Test Location')
            .openPopup();
            
        console.log(`Simple test map created successfully for route ${routeId}`);
        
        // Force resize
        setTimeout(() => {
            map.invalidateSize();
        }, 100);
        
        return map;
        
    } catch (error) {
        console.error(`Simple test map failed:`, error);
        mapElement.innerHTML = `
            <div class="alert alert-warning">
                <strong>Leaflet Test Failed:</strong><br>
                ${error.message}
            </div>
        `;
    }
}

// Function to test Leaflet in current environment
function testLeafletEnvironment() {
    console.log('=== LEAFLET ENVIRONMENT TEST ===');
    console.log('Leaflet available:', typeof L !== 'undefined');
    if (typeof L !== 'undefined') {
        console.log('Leaflet version:', L.version);
    }
    console.log('Document ready:', document.readyState);
    console.log('=== END LEAFLET TEST ===');
}

// Run test on load
document.addEventListener('DOMContentLoaded', testLeafletEnvironment);
/**
 * Working Map Implementation - Direct Leaflet integration with proper error handling
 */

// Global map storage
const workingMaps = {};
const mapMarkers = {};

// Function to toggle route map visibility and initialization
function toggleRouteMap(routeId) {
    console.log(`Toggling map for route ${routeId}`);
    
    const mapContainer = document.getElementById(`map-container-${routeId}`);
    const toggleBtn = document.getElementById(`map-toggle-${routeId}`);
    
    if (!mapContainer || !toggleBtn) {
        console.error(`Map elements not found for route ${routeId}`);
        return;
    }
    
    if (mapContainer.style.display === 'none') {
        // Show map
        console.log(`Showing map for route ${routeId}`);
        mapContainer.style.display = 'block';
        mapContainer.style.position = 'static';
        mapContainer.style.visibility = 'visible';
        mapContainer.style.height = 'auto';
        mapContainer.style.overflow = 'visible';
        
        toggleBtn.innerHTML = '<i data-feather="eye-off" style="width: 14px; height: 14px;"></i> Hide Map';
        
        // Initialize map if not already created
        if (!workingMaps[routeId]) {
            initializeWorkingMap(routeId);
        } else {
            // Resize existing map
            setTimeout(() => {
                if (workingMaps[routeId]) {
                    workingMaps[routeId].invalidateSize();
                }
            }, 100);
        }
        
        // Update icons
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
        
    } else {
        // Hide map
        console.log(`Hiding map for route ${routeId}`);
        mapContainer.style.display = 'none';
        toggleBtn.innerHTML = '<i data-feather="map" style="width: 14px; height: 14px;"></i> Show Map';
        
        // Update icons
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }
}

// Function to initialize a working map for a route
function initializeWorkingMap(routeId) {
    console.log(`Initializing working map for route ${routeId}`);
    
    const mapElement = document.getElementById(`map-${routeId}`);
    if (!mapElement) {
        console.error(`Map element not found: map-${routeId}`);
        return;
    }
    
    try {
        // Create Leaflet map
        const map = L.map(mapElement).setView([33.7490, -84.3880], 11);
        
        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);
        
        // Store map reference
        workingMaps[routeId] = map;
        mapMarkers[routeId] = [];
        
        // Get route data from script tag
        const routeDataScript = document.getElementById(`route-data-${routeId}`);
        if (!routeDataScript) {
            console.warn(`No route data found for route ${routeId}, showing basic map`);
            addFallbackMarker(map, routeId);
            return;
        }
        
        let stopsData;
        try {
            stopsData = JSON.parse(routeDataScript.textContent);
        } catch (error) {
            console.error(`Failed to parse route data for route ${routeId}:`, error);
            addFallbackMarker(map, routeId);
            return;
        }
        
        // Get departure address from route card
        const routeCard = document.querySelector(`[data-route-id="${routeId}"]`);
        const departureAddress = routeCard ? routeCard.dataset.departureAddress : "183 DeKalb Industrial Way, Decatur, GA 30030";
        
        console.log(`Route ${routeId}: Loading ${stopsData.length} stops`);
        
        // Add departure marker first
        geocodeAndAddMarker(map, routeId, departureAddress, 'S', '#28a745', 'START: Departure')
            .then(() => {
                // Add stop markers
                const promises = stopsData.map((stop, index) => {
                    const stopNumber = index + 1;
                    const label = `Stop ${stopNumber}: ${stop.post_type}`;
                    return geocodeAndAddMarker(map, routeId, stop.address, stopNumber.toString(), '#007bff', label);
                });
                
                // Add return marker
                promises.push(geocodeAndAddMarker(map, routeId, departureAddress, 'E', '#dc3545', 'END: Return'));
                
                return Promise.all(promises);
            })
            .then(() => {
                // Fit map to show all markers
                if (mapMarkers[routeId] && mapMarkers[routeId].length > 0) {
                    const group = new L.featureGroup(mapMarkers[routeId]);
                    map.fitBounds(group.getBounds().pad(0.1));
                    
                    // Draw simple connecting lines
                    drawConnectingLines(map, routeId);
                }
            })
            .catch(error => {
                console.error(`Error setting up map for route ${routeId}:`, error);
                addFallbackMarker(map, routeId);
            });
            
    } catch (error) {
        console.error(`Failed to create map for route ${routeId}:`, error);
    }
}

// Function to geocode an address and add a marker
async function geocodeAndAddMarker(map, routeId, address, text, color, label) {
    try {
        const coords = await geocodeAddress(address);
        if (coords) {
            const marker = L.marker(coords, {
                icon: createMapIcon(text, color)
            }).addTo(map);
            
            marker.bindPopup(`
                <div>
                    <strong>${label}</strong><br>
                    <small>${address}</small>
                </div>
            `);
            
            mapMarkers[routeId].push(marker);
            return coords;
        }
        return null;
    } catch (error) {
        console.warn(`Geocoding failed for ${address}:`, error);
        return null;
    }
}

// Function to geocode an address using Nominatim
async function geocodeAddress(address) {
    try {
        const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address + ", Georgia, USA")}&limit=1&countrycodes=us`;
        
        const response = await Promise.race([
            fetch(url, {
                headers: {
                    'User-Agent': 'ShutUpAndDrive/1.0 (Route Optimization App)'
                }
            }),
            new Promise((_, reject) => 
                setTimeout(() => reject(new Error('Geocoding timeout')), 12000)
            )
        ]);
        
        if (response.ok) {
            const data = await response.json();
            if (data && data.length > 0) {
                const result = data[0];
                return [parseFloat(result.lat), parseFloat(result.lon)];
            }
        }
        
        return null;
    } catch (error) {
        console.warn(`Geocoding error for ${address}:`, error.message);
        return null;
    }
}

// Function to create a custom map icon
function createMapIcon(text, color) {
    return L.divIcon({
        html: `
            <div style="
                background-color: ${color};
                border: 2px solid white;
                border-radius: 50%;
                width: 30px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
                font-size: 11px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            ">${text}</div>
        `,
        className: 'custom-map-icon',
        iconSize: [30, 30],
        iconAnchor: [15, 15]
    });
}

// Function to draw simple connecting lines between markers
function drawConnectingLines(map, routeId) {
    const markers = mapMarkers[routeId];
    if (!markers || markers.length < 2) return;
    
    const coordinates = markers.map(marker => marker.getLatLng());
    
    // Draw lines between consecutive markers
    for (let i = 0; i < coordinates.length - 1; i++) {
        L.polyline([coordinates[i], coordinates[i + 1]], {
            color: '#007bff',
            weight: 3,
            opacity: 0.7,
            dashArray: '8, 4'
        }).addTo(map);
    }
}

// Function to add a fallback marker when geocoding fails
function addFallbackMarker(map, routeId) {
    const marker = L.marker([33.7490, -84.3880], {
        icon: createMapIcon('!', '#ffc107')
    }).addTo(map);
    
    marker.bindPopup(`
        <div>
            <strong>Route ${routeId}</strong><br>
            <small>Map temporarily unavailable</small><br>
            <small>Geocoding service error</small>
        </div>
    `);
    
    mapMarkers[routeId] = [marker];
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Working maps system ready');
});
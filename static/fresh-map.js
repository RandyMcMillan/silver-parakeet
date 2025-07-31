// Fresh map implementation - bypassing all existing issues
const freshMaps = {};

function createFreshMap(routeId) {
    console.log(`Creating fresh map for route ${routeId}`);
    
    const mapElement = document.getElementById(`map-${routeId}`);
    if (!mapElement) {
        console.error(`Map element not found: map-${routeId}`);
        return;
    }
    
    // Completely clear and reset the container
    mapElement.innerHTML = '';
    mapElement.className = '';
    mapElement.style.cssText = 'height: 400px; width: 100%; background: #f0f0f0; border: 2px solid #007bff; position: relative; overflow: hidden;';
    
    try {
        // Create map with very basic configuration
        const map = L.map(mapElement, {
            center: [33.7490, -84.3880],
            zoom: 10,
            zoomControl: true,
            attributionControl: false,
            preferCanvas: false
        });
        
        // Use a very reliable tile server with error handling
        const tileLayer = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap',
            maxZoom: 18,
            errorTileUrl: '',
            crossOrigin: null
        });
        
        // Add immediate success feedback
        tileLayer.on('loading', function() {
            console.log(`Fresh map tiles starting to load for route ${routeId}`);
        });
        
        tileLayer.on('load', function() {
            console.log(`Fresh map tiles finished loading for route ${routeId}`);
            mapElement.style.backgroundColor = '#e8f4fd';
        });
        
        tileLayer.on('tileload', function(e) {
            console.log(`Fresh tile loaded for route ${routeId}:`, e.tile.src);
            // Force tile visibility
            e.tile.style.opacity = '1';
            e.tile.style.display = 'block';
        });
        
        tileLayer.on('tileerror', function(e) {
            console.error(`Fresh tile error for route ${routeId}:`, e);
            // Show a clear error state
            mapElement.style.backgroundColor = '#ffe6e6';
            mapElement.innerHTML = '<div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; color: #d63384; font-weight: bold;">Map tiles failed to load<br>Check network connection</div>';
        });
        
        // Add the tile layer
        tileLayer.addTo(map);
        
        // Store reference
        freshMaps[routeId] = map;
        
        // Force refresh after creation
        setTimeout(() => {
            map.invalidateSize();
            console.log(`Fresh map size invalidated for route ${routeId}`);
        }, 100);
        
        console.log(`Fresh map created successfully for route ${routeId}`);
        return map;
        
    } catch (error) {
        console.error(`Failed to create fresh map for route ${routeId}:`, error);
        mapElement.style.backgroundColor = '#ffe6e6';
        mapElement.innerHTML = '<div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; color: #d63384;">Map creation failed</div>';
    }
}

function addFreshRouteData(routeId, routeData) {
    const map = freshMaps[routeId];
    if (!map || !routeData) return;
    
    console.log(`Adding route data to fresh map ${routeId}`);
    
    try {
        // Add departure marker
        if (routeData.departure_lat && routeData.departure_lng) {
            L.marker([routeData.departure_lat, routeData.departure_lng])
                .bindPopup('Departure: ' + routeData.departure_address)
                .addTo(map);
        }
        
        // Add stop markers
        routeData.stops.forEach((stop, index) => {
            if (stop.lat && stop.lng) {
                const marker = L.circleMarker([stop.lat, stop.lng], {
                    radius: 8,
                    fillColor: '#007bff',
                    color: '#fff',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.8
                }).addTo(map);
                
                marker.bindPopup(`Stop ${index + 1}: ${stop.address}`);
            }
        });
        
        console.log(`Added ${routeData.stops.length} stops to fresh map ${routeId}`);
        
    } catch (error) {
        console.error(`Error adding route data to fresh map ${routeId}:`, error);
    }
}

// Toggle function for fresh maps
function toggleFreshMap(routeId) {
    console.log(`Toggling fresh map for route ${routeId}`);
    
    const container = document.getElementById(`map-container-${routeId}`);
    const button = document.getElementById(`map-toggle-${routeId}`);
    
    if (!container || !button) {
        console.error(`Missing elements for route ${routeId}`);
        return;
    }
    
    if (container.style.display === 'none') {
        // Show map
        container.style.display = 'block';
        button.innerHTML = '<i data-feather="map" style="width: 14px; height: 14px;"></i> Hide Map';
        
        // Create fresh map
        const map = createFreshMap(routeId);
        
        if (map) {
            // Load route data from script tag
            const routeDataScript = document.getElementById(`route-data-${routeId}`);
            if (routeDataScript) {
                try {
                    const routeData = JSON.parse(routeDataScript.textContent);
                    addFreshRouteData(routeId, routeData);
                } catch (error) {
                    console.error(`Error parsing route data for ${routeId}:`, error);
                }
            }
        }
        
    } else {
        // Hide map
        container.style.display = 'none';
        button.innerHTML = '<i data-feather="map" style="width: 14px; height: 14px;"></i> Show Map';
        
        // Clean up map
        if (freshMaps[routeId]) {
            freshMaps[routeId].remove();
            delete freshMaps[routeId];
        }
    }
    
    // Refresh feather icons
    feather.replace();
}
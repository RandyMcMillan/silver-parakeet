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
    if (!map) {
        console.error(`No map found for route ${routeId}`);
        return;
    }
    
    console.log(`Adding route data to fresh map ${routeId}`, routeData);
    
    try {
        // Check if routeData is valid
        if (!routeData || typeof routeData !== 'object') {
            console.error(`Invalid route data for ${routeId}:`, routeData);
            return;
        }
        
        // Create a group for all route elements
        const routeGroup = L.layerGroup().addTo(map);
        const bounds = [];
        
        // Add departure marker if available
        if (routeData.departure_lat && routeData.departure_lng) {
            const lat = parseFloat(routeData.departure_lat);
            const lng = parseFloat(routeData.departure_lng);
            
            L.marker([lat, lng], {
                icon: L.divIcon({
                    className: 'departure-marker',
                    html: '<div style="background: #28a745; color: white; border-radius: 50%; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold; border: 2px solid white;">🏠</div>',
                    iconSize: [20, 20]
                })
            }).bindPopup(`Departure: ${routeData.departure_address || 'Start Location'}`)
              .addTo(routeGroup);
            
            bounds.push([lat, lng]);
        }
        
        // Add stop markers
        if (routeData.stops && Array.isArray(routeData.stops)) {
            routeData.stops.forEach((stop, index) => {
                if (stop && stop.lat && stop.lng) {
                    const lat = parseFloat(stop.lat);
                    const lng = parseFloat(stop.lng);
                    
                    const marker = L.marker([lat, lng], {
                        icon: L.divIcon({
                            className: 'numbered-marker',
                            html: `<div style="background: #007bff; color: white; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold; border: 2px solid white;">${index + 1}</div>`,
                            iconSize: [24, 24]
                        })
                    }).bindPopup(`Stop ${index + 1}: ${stop.address || 'Unknown Address'}`)
                      .addTo(routeGroup);
                    
                    bounds.push([lat, lng]);
                }
            });
        }
        
        // Fit map to show all markers
        if (bounds.length > 0) {
            map.fitBounds(bounds, { padding: [20, 20] });
        }
        
        console.log(`Added ${routeData.stops ? routeData.stops.length : 0} stops to fresh map ${routeId}`);
        
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
                    console.log(`Parsed route data for ${routeId}:`, routeData);
                    
                    // Add a small delay to ensure map is fully initialized
                    setTimeout(() => {
                        addFreshRouteData(routeId, routeData);
                    }, 200);
                } catch (error) {
                    console.error(`Error parsing route data for ${routeId}:`, error);
                    console.log(`Script content:`, routeDataScript.textContent);
                }
            } else {
                console.log(`No route data script found for route ${routeId}`);
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
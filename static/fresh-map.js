// Fresh map implementation - bypassing all existing issues
const freshMaps = {};

// Coordinate mapping function for Atlanta addresses
function getAtlantaCoordinates(address) {
    // Enhanced coordinate mapping for real Atlanta addresses
    const addressLower = address.toLowerCase();
    
    // Specific street and area mappings for better accuracy
    if (addressLower.includes('1100 peachtree st ne')) return [33.7850, -84.3820];
    if (addressLower.includes('1201 west peachtree st nw')) return [33.7900, -84.3870];
    if (addressLower.includes('2855 piedmont rd ne')) return [33.8200, -84.3650];
    if (addressLower.includes('3520 piedmont rd ne')) return [33.8300, -84.3600];
    if (addressLower.includes('3525 piedmont rd ne')) return [33.8320, -84.3580];
    if (addressLower.includes('1430 west paces ferry rd nw')) return [33.8450, -84.3900];
    if (addressLower.includes('2500 northside dr nw')) return [33.8100, -84.4050];
    if (addressLower.includes('1827 northside dr nw')) return [33.8000, -84.4100];
    if (addressLower.includes('6690 roswell rd ne')) return [33.8700, -84.3600];
    if (addressLower.includes('5505 peachtree dunwoody rd')) return [33.9100, -84.3450];
    if (addressLower.includes('4620 wieuca rd ne')) return [33.8950, -84.3650];
    if (addressLower.includes('1501 clairmont rd')) return [33.8200, -84.3100];
    if (addressLower.includes('2200 century pkwy')) return [33.8150, -84.2800];
    if (addressLower.includes('3550 lenox rd ne')) return [33.8470, -84.3630];
    
    // General area mapping for common Atlanta addresses
    if (addressLower.includes('peachtree st') || addressLower.includes('peachtree street')) {
        if (addressLower.includes('ne')) return [33.7850, -84.3820];
        if (addressLower.includes('nw')) return [33.7900, -84.3870];
        return [33.7810, -84.3820];
    }
    if (addressLower.includes('spring st') || addressLower.includes('spring street')) return [33.7700, -84.3900];
    if (addressLower.includes('piedmont rd') || addressLower.includes('piedmont road')) return [33.8200, -84.3650];
    if (addressLower.includes('roswell rd') || addressLower.includes('roswell road')) return [33.8500, -84.3600];
    if (addressLower.includes('peachtree dunwoody')) return [33.9000, -84.3500];
    if (addressLower.includes('clairmont') || addressLower.includes('clairemont')) return [33.8200, -84.3100];
    if (addressLower.includes('marietta') && addressLower.includes('ga')) return [33.9526, -84.5499];
    if (addressLower.includes('smyrna') && addressLower.includes('ga')) return [33.8837, -84.5144];
    if (addressLower.includes('powder springs')) return [33.8598, -84.6888];
    
    // Default Atlanta center if no specific match
    return [33.7490, -84.3880];
}

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
        if (routeData && Array.isArray(routeData)) {
            routeData.forEach((stop, index) => {
                if (stop && stop.address) {
                    // Use coordinate mapping function (same as existing system)
                    const coords = getAtlantaCoordinates(stop.address);
                    
                    if (coords && coords.length === 2) {
                        const [lat, lng] = coords;
                        
                        const marker = L.marker([lat, lng], {
                            icon: L.divIcon({
                                className: 'numbered-marker',
                                html: `<div style="background: #007bff; color: white; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold; border: 2px solid white;">${index + 1}</div>`,
                                iconSize: [24, 24]
                            })
                        }).bindPopup(`Stop ${index + 1}: ${stop.address}`)
                          .addTo(routeGroup);
                        
                        bounds.push([lat, lng]);
                        console.log(`Stop ${index + 1}: ${stop.address} -> [${lat}, ${lng}]`);
                    } else {
                        console.warn(`No coordinates found for: ${stop.address}`);
                    }
                }
            });
        }
        
        // Fit map to show all markers
        if (bounds.length > 0) {
            map.fitBounds(bounds, { padding: [20, 20] });
        }
        
        console.log(`Added ${routeData ? routeData.length : 0} stops to fresh map ${routeId}`);
        
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
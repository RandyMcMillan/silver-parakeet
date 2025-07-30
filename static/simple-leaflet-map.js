// Simple, reliable Leaflet map implementation

const simpleMaps = {};
const simpleMarkers = {};

function createSimpleMap(routeId) {
    console.log(`Creating simple map for route ${routeId}`);
    
    const mapElement = document.getElementById(`map-${routeId}`);
    if (!mapElement) {
        console.error(`Map element not found: map-${routeId}`);
        return;
    }
    
    // Remove existing map if present
    if (simpleMaps[routeId]) {
        simpleMaps[routeId].remove();
        delete simpleMaps[routeId];
    }
    
    // Clear container
    mapElement.innerHTML = '';
    
    // Set explicit dimensions
    mapElement.style.height = '400px';
    mapElement.style.width = '100%';
    mapElement.style.position = 'relative';
    
    try {
        // Create map with Atlanta center
        const map = L.map(mapElement, {
            center: [33.7490, -84.3880],
            zoom: 10,
            zoomControl: true,
            attributionControl: true
        });
        
        // Try multiple tile servers for reliability
        console.log(`Adding map tiles for route ${routeId}`);
        
        // Primary tile layer
        const tileLayer = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 18
        });
        
        let tilesLoaded = false;
        
        tileLayer.on('tileload', function() {
            if (!tilesLoaded) {
                tilesLoaded = true;
                console.log(`OpenStreetMap tiles loaded successfully for route ${routeId}`);
            }
        });
        
        tileLayer.on('tileerror', function(error) {
            console.error(`OpenStreetMap tile error for route ${routeId}:`, error);
            
            // Try CartoDB tile server as fallback
            console.log(`Trying CartoDB tiles for route ${routeId}...`);
            const cartoTileLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
                attribution: '© CARTO',
                subdomains: 'abcd',
                maxZoom: 19
            });
            cartoTileLayer.addTo(map);
            
            cartoTileLayer.on('tileerror', function() {
                console.error(`CartoDB tiles also failed for route ${routeId}, using basic background`);
                mapElement.style.backgroundColor = '#e6e6e6';
            });
        });
        
        try {
            tileLayer.addTo(map);
        } catch (error) {
            console.error(`Failed to add tile layer for route ${routeId}:`, error);
            mapElement.style.backgroundColor = '#e6e6e6';
        }
        
        // Store map reference
        simpleMaps[routeId] = map;
        simpleMarkers[routeId] = [];
        
        console.log(`Simple map created successfully for route ${routeId}`);
        
        // Force resize and check tiles after creation
        setTimeout(() => {
            map.invalidateSize();
            console.log(`Map size invalidated for route ${routeId}`);
            
            // Force tile refresh if they haven't loaded
            setTimeout(() => {
                const hasLoadedTiles = mapElement.querySelector('.leaflet-tile-loaded');
                if (!hasLoadedTiles) {
                    console.warn(`No tiles loaded for route ${routeId}, forcing refresh`);
                    map.eachLayer(function(layer) {
                        if (layer._url && layer._url.includes('openstreetmap')) {
                            layer.redraw();
                        }
                    });
                }
            }, 2000);
            
        }, 100);
        
        // Load route data and add markers
        loadSimpleRouteData(map, routeId);
        
        return map;
        
    } catch (error) {
        console.error(`Simple map creation failed for route ${routeId}:`, error);
        mapElement.innerHTML = `
            <div class="alert alert-danger p-3">
                <h6>Map Error</h6>
                <p>Failed to create map: ${error.message}</p>
                <button class="btn btn-sm btn-outline-primary" onclick="createSimpleMap(${routeId})">
                    Retry Map
                </button>
            </div>
        `;
    }
}

function loadSimpleRouteData(map, routeId) {
    console.log(`Loading route data for map ${routeId}`);
    
    // Get route data from script tag
    const routeDataScript = document.getElementById(`route-data-${routeId}`);
    if (!routeDataScript) {
        console.warn(`No route data found for route ${routeId}`);
        return;
    }
    
    let stopsData;
    try {
        stopsData = JSON.parse(routeDataScript.textContent);
        console.log(`Parsed ${stopsData.length} stops for route ${routeId}`);
    } catch (error) {
        console.error(`Failed to parse route data for route ${routeId}:`, error);
        return;
    }
    
    // Add departure marker (green S)
    const departureCoords = [33.7810, -84.2950]; // DeKalb Industrial Way
    const departureMarker = L.circleMarker(departureCoords, {
        radius: 12,
        fillColor: '#28a745',
        color: '#ffffff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8
    }).addTo(map);
    
    departureMarker.bindPopup('<strong>START</strong><br>183 DeKalb Industrial Way');
    simpleMarkers[routeId].push(departureMarker);
    
    console.log(`Added departure marker for route ${routeId}`);
    
    // Add stop markers with numbers
    const allCoords = [departureCoords];
    
    stopsData.forEach((stop, index) => {
        // Use simple coordinate mapping for Atlanta stops
        const coords = getAtlantaCoordinates(stop.address);
        allCoords.push(coords);
        
        // Create numbered marker
        const marker = L.circleMarker(coords, {
            radius: 10,
            fillColor: '#007bff',
            color: '#ffffff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8
        }).addTo(map);
        
        // Add number label
        const divIcon = L.divIcon({
            html: `<div style="color: white; font-weight: bold; font-size: 12px; text-align: center; line-height: 20px;">${index + 1}</div>`,
            iconSize: [20, 20],
            className: 'numbered-marker'
        });
        
        L.marker(coords, { icon: divIcon }).addTo(map);
        
        marker.bindPopup(`
            <strong>Stop ${index + 1}</strong><br>
            ${stop.address}<br>
            <small>${stop.service_type} - ${stop.post_type}</small>
        `);
        
        simpleMarkers[routeId].push(marker);
    });
    
    // Add return marker (gray E)
    const returnMarker = L.circleMarker(departureCoords, {
        radius: 12,
        fillColor: '#6c757d',
        color: '#ffffff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8
    }).addTo(map);
    
    returnMarker.bindPopup('<strong>END</strong><br>Return to Departure');
    simpleMarkers[routeId].push(returnMarker);
    
    // Draw street-following route lines
    if (allCoords.length > 1) {
        addStreetRouteLines(map, routeId, allCoords);
        
        // Fit map to show all markers
        const group = new L.featureGroup(simpleMarkers[routeId]);
        map.fitBounds(group.getBounds(), { padding: [20, 20] });
    }
    
    console.log(`Added ${stopsData.length} stop markers and route line for route ${routeId}`);
}

function getAtlantaCoordinates(address) {
    // Simple coordinate mapping for Atlanta area addresses
    const addressLower = address.toLowerCase();
    
    // Common Atlanta coordinates mapping
    if (addressLower.includes('peachtree')) return [33.7740, -84.3820];
    if (addressLower.includes('piedmont')) return [33.7850, -84.3900];
    if (addressLower.includes('buckhead')) return [33.8480, -84.3780];
    if (addressLower.includes('midtown')) return [33.7850, -84.3860];
    if (addressLower.includes('downtown')) return [33.7550, -84.3900];
    if (addressLower.includes('decatur')) return [33.7750, -84.2960];
    if (addressLower.includes('tucker')) return [33.8180, -84.2190];
    if (addressLower.includes('marietta')) return [33.9520, -84.5470];
    if (addressLower.includes('sandy springs')) return [33.9240, -84.3780];
    if (addressLower.includes('roswell')) return [34.0230, -84.3610];
    
    // Default to central Atlanta with slight randomization
    const baseCoords = [33.7490, -84.3880];
    const offset = 0.02; // ~2km offset
    return [
        baseCoords[0] + (Math.random() - 0.5) * offset,
        baseCoords[1] + (Math.random() - 0.5) * offset
    ];
}

// Function to add street-following route lines using OSRM
async function addStreetRouteLines(map, routeId, allCoords) {
    console.log(`Adding street route lines for route ${routeId}`);
    
    // Add route segments between consecutive stops
    for (let i = 0; i < allCoords.length - 1; i++) {
        try {
            const routeGeometry = await getOSRMRoute(allCoords[i], allCoords[i + 1]);
            
            if (routeGeometry && routeGeometry.length > 0) {
                // Use OSRM route geometry
                const routeLine = L.polyline(routeGeometry, {
                    color: '#007bff',
                    weight: 3,
                    opacity: 0.7
                }).addTo(map);
                
                simpleMarkers[routeId].push(routeLine);
            } else {
                // Fallback to straight line
                const straightLine = L.polyline([allCoords[i], allCoords[i + 1]], {
                    color: '#007bff',
                    weight: 3,
                    opacity: 0.7,
                    dashArray: '5, 5'  // Dashed to indicate fallback
                }).addTo(map);
                
                simpleMarkers[routeId].push(straightLine);
            }
        } catch (error) {
            console.warn(`OSRM routing failed for segment ${i}, using straight line:`, error);
            
            // Fallback to straight line
            const straightLine = L.polyline([allCoords[i], allCoords[i + 1]], {
                color: '#007bff',
                weight: 3,
                opacity: 0.7,
                dashArray: '5, 5'  // Dashed to indicate fallback
            }).addTo(map);
            
            simpleMarkers[routeId].push(straightLine);
        }
    }
    
    // Add return route from last stop to departure
    try {
        const returnGeometry = await getOSRMRoute(allCoords[allCoords.length - 1], allCoords[0]);
        
        if (returnGeometry && returnGeometry.length > 0) {
            const returnLine = L.polyline(returnGeometry, {
                color: '#6c757d',
                weight: 2,
                opacity: 0.5,
                dashArray: '10, 5'
            }).addTo(map);
            
            simpleMarkers[routeId].push(returnLine);
        } else {
            // Fallback straight return line
            const returnLine = L.polyline([allCoords[allCoords.length - 1], allCoords[0]], {
                color: '#6c757d',
                weight: 2,
                opacity: 0.5,
                dashArray: '5, 5'
            }).addTo(map);
            
            simpleMarkers[routeId].push(returnLine);
        }
    } catch (error) {
        console.warn(`OSRM return routing failed, using straight line:`, error);
        
        // Fallback straight return line
        const returnLine = L.polyline([allCoords[allCoords.length - 1], allCoords[0]], {
            color: '#6c757d',
            weight: 2,
            opacity: 0.5,
            dashArray: '5, 5'
        }).addTo(map);
        
        simpleMarkers[routeId].push(returnLine);
    }
    
    console.log(`Street routing completed for route ${routeId}`);
}

// Function to get route geometry from OSRM
async function getOSRMRoute(startCoords, endCoords) {
    const osrmUrl = `https://router.project-osrm.org/route/v1/driving/${startCoords[1]},${startCoords[0]};${endCoords[1]},${endCoords[0]}?geometries=geojson`;
    
    try {
        const response = await fetch(osrmUrl, { 
            method: 'GET',
            timeout: 5000  // 5 second timeout
        });
        
        if (!response.ok) {
            throw new Error(`OSRM API error: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.routes && data.routes.length > 0 && data.routes[0].geometry) {
            // Convert GeoJSON coordinates to Leaflet format [lat, lng]
            return data.routes[0].geometry.coordinates.map(coord => [coord[1], coord[0]]);
        }
        
        return null;
    } catch (error) {
        console.warn('OSRM routing request failed:', error);
        return null;
    }
}

// Function to toggle simple map display
function toggleSimpleMap(routeId) {
    console.log(`Toggling simple map for route ${routeId}`);
    
    const mapContainer = document.getElementById(`map-container-${routeId}`);
    const toggleBtn = document.getElementById(`map-toggle-${routeId}`);
    
    if (!mapContainer || !toggleBtn) {
        console.error(`Map elements not found for route ${routeId}`);
        return;
    }
    
    if (mapContainer.style.display === 'none') {
        // Show map
        mapContainer.style.display = 'block';
        toggleBtn.innerHTML = '<i data-feather="eye-off" style="width: 14px; height: 14px;"></i> Hide Map';
        
        // Create map if it doesn't exist
        if (!simpleMaps[routeId]) {
            setTimeout(() => createSimpleMap(routeId), 100);
        } else {
            // Resize existing map
            setTimeout(() => {
                if (simpleMaps[routeId]) {
                    simpleMaps[routeId].invalidateSize();
                }
            }, 100);
        }
    } else {
        // Hide map
        mapContainer.style.display = 'none';
        toggleBtn.innerHTML = '<i data-feather="map" style="width: 14px; height: 14px;"></i> Show Map';
    }
    
    // Update feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}
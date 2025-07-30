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
        
        console.log(`Stop ${index + 1}: ${stop.address} -> [${coords[0]}, ${coords[1]}]`);
        
        // Create numbered marker
        const marker = L.circleMarker(coords, {
            radius: 10,
            fillColor: '#007bff',
            color: '#ffffff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8
        }).addTo(map);
        
        // Add number label with better visibility
        const divIcon = L.divIcon({
            html: `<div style="
                background: #007bff; 
                color: white; 
                font-weight: bold; 
                font-size: 11px; 
                text-align: center; 
                line-height: 20px; 
                border-radius: 50%; 
                border: 2px solid white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                width: 20px;
                height: 20px;
            ">${index + 1}</div>`,
            iconSize: [20, 20],
            iconAnchor: [10, 10],
            className: 'numbered-marker'
        });
        
        const numberMarker = L.marker(coords, { icon: divIcon }).addTo(map);
        simpleMarkers[routeId].push(numberMarker);
        
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
        
        // Fit map to show all markers with proper bounds
        setTimeout(() => {
            if (simpleMarkers[routeId] && simpleMarkers[routeId].length > 0) {
                const group = new L.featureGroup(simpleMarkers[routeId]);
                try {
                    map.fitBounds(group.getBounds(), { padding: [20, 20] });
                } catch (error) {
                    console.warn(`Failed to fit bounds for route ${routeId}, using default view`);
                    map.setView([33.7490, -84.3880], 11);
                }
            }
        }, 500);
    }
    
    console.log(`Added ${stopsData.length} stop markers and route line for route ${routeId}`);
}

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
    
    // Area-based fallback mapping
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
    if (addressLower.includes('lenox')) return [33.8470, -84.3630];
    if (addressLower.includes('northside')) return [33.8050, -84.4000];
    if (addressLower.includes('paces ferry')) return [33.8450, -84.3900];
    if (addressLower.includes('century')) return [33.8150, -84.2800];
    if (addressLower.includes('clairmont')) return [33.8200, -84.3100];
    if (addressLower.includes('wieuca')) return [33.8950, -84.3650];
    
    // Hash-based consistent positioning for unknown addresses
    let hash = 0;
    for (let i = 0; i < address.length; i++) {
        const char = address.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32bit integer
    }
    
    const baseCoords = [33.7490, -84.3880];
    const offset = 0.05; // ~5km spread
    const latOffset = (Math.sin(hash) + 1) / 2 * offset - offset/2;
    const lngOffset = (Math.cos(hash) + 1) / 2 * offset - offset/2;
    
    return [
        baseCoords[0] + latOffset,
        baseCoords[1] + lngOffset
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
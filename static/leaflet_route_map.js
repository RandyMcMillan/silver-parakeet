class LeafletRouteMapper {
    constructor() {
        this.maps = {};
        this.markers = {};
        this.routeLines = {};
    }

    async initializeMap(routeId, stops, departureAddress) {
        const mapContainer = document.getElementById(`map-${routeId}`);
        if (!mapContainer) {
            console.error(`Map container not found: map-${routeId}`);
            return;
        }

        console.log(`Creating Leaflet map for route ${routeId} with ${stops.length} stops`);

        // Initialize Leaflet map centered on Atlanta
        const map = L.map(mapContainer).setView([33.7490, -84.3880], 10);
        
        // Add OpenStreetMap tiles (free)
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '© <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        }).addTo(map);

        this.maps[routeId] = map;
        this.markers[routeId] = [];

        // Geocode addresses and add markers
        const allAddresses = [departureAddress, ...stops.map(stop => stop.address), departureAddress]; // Start, stops, return
        const coordinates = [];

        try {
            // Add departure marker first
            const depCoords = await this.geocodeAddress(departureAddress);
            if (depCoords) {
                const startMarker = L.marker(depCoords, {
                    icon: this.createCustomIcon('S', '#28a745')
                }).addTo(map);
                
                startMarker.bindPopup(`
                    <div>
                        <h6><strong>START: Departure</strong></h6>
                        <p><small>${departureAddress}</small></p>
                    </div>
                `);
                
                this.markers[routeId].push(startMarker);
                coordinates.push(depCoords);
            }

            // Add stop markers
            for (let i = 0; i < stops.length; i++) {
                const stop = stops[i];
                const coords = await this.geocodeAddress(stop.address);
                
                if (coords) {
                    const stopNumber = i + 1;
                    const marker = L.marker(coords, {
                        icon: this.createCustomIcon(stopNumber.toString(), '#007bff')
                    }).addTo(map);
                    
                    marker.bindPopup(`
                        <div>
                            <h6><strong>Stop ${stopNumber}</strong></h6>
                            <p><strong>${stop.post_type}</strong></p>
                            <p><small>${stop.address}</small></p>
                            <p><span class="badge bg-${stop.service_type === 'install' ? 'primary' : stop.service_type === 'deliver' ? 'warning' : 'secondary'}">${stop.service_type}</span></p>
                        </div>
                    `);
                    
                    this.markers[routeId].push(marker);
                    coordinates.push(coords);
                }
            }

            // Add return marker (same as departure)
            if (depCoords) {
                const endMarker = L.marker(depCoords, {
                    icon: this.createCustomIcon('E', '#6c757d')
                }).addTo(map);
                
                endMarker.bindPopup(`
                    <div>
                        <h6><strong>RETURN: Back to Base</strong></h6>
                        <p><small>${departureAddress}</small></p>
                    </div>
                `);
                
                this.markers[routeId].push(endMarker);
                coordinates.push(depCoords);
            }

            // Draw route lines following actual street routes
            if (coordinates.length > 1) {
                await this.drawStreetRoutes(map, routeId, coordinates, stops);
                
                // Fit map to show all markers
                const group = new L.featureGroup(this.markers[routeId]);
                map.fitBounds(group.getBounds().pad(0.1));
            }

        } catch (error) {
            console.error('Error creating route map:', error);
        }
    }

    createCustomIcon(text, color) {
        return L.divIcon({
            html: `
                <div style="
                    background-color: ${color};
                    border: 2px solid white;
                    border-radius: 50%;
                    width: 32px;
                    height: 32px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: bold;
                    font-size: 12px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                ">${text}</div>
            `,
            className: 'custom-div-icon',
            iconSize: [32, 32],
            iconAnchor: [16, 16]
        });
    }

    async geocodeAddress(address) {
        try {
            // Use Nominatim (OpenStreetMap) geocoding service - free with improved parameters
            const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address + ", Georgia, USA")}&limit=1&countrycodes=us`;
            
            const response = await fetch(url, {
                headers: {
                    'User-Agent': 'ShutUpAndDrive/1.0 (Route Optimization App)'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data && data.length > 0) {
                const lat = parseFloat(data[0].lat);
                const lon = parseFloat(data[0].lon);
                console.log(`Geocoded ${address}: [${lat}, ${lon}]`);
                return [lat, lon];
            }
            
            console.warn(`Geocoding failed for address: ${address}`);
            return null;
        } catch (error) {
            console.error(`Geocoding error for ${address}:`, error);
            return null;
        }
    }

    async drawStreetRoutes(map, routeId, coordinates, stops) {
        const routeSegments = [];
        
        try {
            // Draw route segments between consecutive points using OSRM routing
            for (let i = 0; i < coordinates.length - 1; i++) {
                const start = coordinates[i];
                const end = coordinates[i + 1];
                
                const routeGeometry = await this.getRouteGeometry(start, end);
                
                if (routeGeometry && routeGeometry.length > 0) {
                    // Create polyline from route geometry
                    const polyline = L.polyline(routeGeometry, {
                        color: '#007bff',
                        weight: 4,
                        opacity: 0.8
                    }).addTo(map);
                    
                    routeSegments.push(polyline);
                } else {
                    // Fallback to straight line if routing fails
                    const fallbackLine = L.polyline([start, end], {
                        color: '#6c757d',
                        weight: 3,
                        opacity: 0.6,
                        dashArray: '5, 10'
                    }).addTo(map);
                    
                    routeSegments.push(fallbackLine);
                }
                
                // Add small delay to respect API rate limits
                await new Promise(resolve => setTimeout(resolve, 200));
            }
            
            this.routeLines[routeId] = routeSegments;
            
        } catch (error) {
            console.error('Error drawing street routes:', error);
            
            // Fallback to simple polyline
            const fallbackPolyline = L.polyline(coordinates, {
                color: '#6c757d',
                weight: 3,
                opacity: 0.6,
                dashArray: '5, 10'
            }).addTo(map);
            
            this.routeLines[routeId] = [fallbackPolyline];
        }
    }

    async getRouteGeometry(start, end) {
        try {
            // Use OSRM (Open Source Routing Machine) - free routing service
            const url = `https://router.project-osrm.org/route/v1/driving/${start[1]},${start[0]};${end[1]},${end[0]}?geometries=geojson&overview=full`;
            
            const response = await fetch(url, {
                headers: {
                    'User-Agent': 'ShutUpAndDrive/1.0 (Route Optimization App)'
                }
            });
            
            if (!response.ok) {
                console.warn(`OSRM HTTP ${response.status}: ${response.statusText}`);
                return null;
            }
            
            const data = await response.json();
            
            if (data.code === 'Ok' && data.routes && data.routes.length > 0) {
                const route = data.routes[0];
                
                // Convert GeoJSON coordinates to Leaflet format [lat, lng]
                return route.geometry.coordinates.map(coord => [coord[1], coord[0]]);
            }
            
            console.warn('OSRM: No valid route found');
            return null;
        } catch (error) {
            console.error('OSRM routing error:', error);
            return null;
        }
    }

    resizeMap(routeId) {
        if (this.maps[routeId]) {
            this.maps[routeId].invalidateSize();
        }
    }
}

// Global instance
const leafletRouteMapper = new LeafletRouteMapper();

// Function to initialize a specific route map with Leaflet
function initializeLeafletRouteMap(routeId, stops, departureAddress) {
    leafletRouteMapper.initializeMap(routeId, stops, departureAddress);
}

// Function to handle map visibility toggle (updated for Leaflet)
function toggleRouteMap(routeId) {
    const mapContainer = document.getElementById(`map-container-${routeId}`);
    const toggleBtn = document.getElementById(`map-toggle-${routeId}`);
    
    if (mapContainer.style.display === 'none') {
        // Show map with proper layout restoration
        mapContainer.style.display = 'block';
        mapContainer.style.position = 'static';
        mapContainer.style.visibility = 'visible';
        mapContainer.style.height = 'auto';
        mapContainer.style.width = '100%';
        mapContainer.style.overflow = 'visible';
        mapContainer.style.zIndex = 'auto';
        toggleBtn.innerHTML = '<i data-feather="eye-off" style="width: 14px; height: 14px;"></i> Hide Map';
        
        // Initialize the map if it hasn't been created yet
        if (!leafletRouteMapper.maps[routeId]) {
            const routeCard = document.querySelector(`[data-route-id="${routeId}"]`);
            if (routeCard) {
                try {
                    // Get route data from script tag
                    const routeDataScript = document.getElementById(`route-data-${routeId}`);
                    if (!routeDataScript) {
                        console.error(`Route data script not found for route ${routeId}`);
                        return;
                    }
                    
                    const stopsData = JSON.parse(routeDataScript.textContent);
                    const departureAddress = routeCard.dataset.departureAddress;
                    
                    console.log(`Initializing Leaflet map for route ${routeId} with ${stopsData.length} stops`);
                    
                    initializeLeafletRouteMap(routeId, stopsData, departureAddress);
                } catch (error) {
                    console.error(`Failed to parse stops data for route ${routeId}:`, error);
                }
            }
        } else {
            // Trigger resize for existing map
            setTimeout(() => leafletRouteMapper.resizeMap(routeId), 100);
        }
        
        // Update icons
        feather.replace();
    } else {
        // Hide map completely from layout
        mapContainer.style.display = 'none';
        mapContainer.style.position = 'absolute';
        mapContainer.style.visibility = 'hidden';
        mapContainer.style.height = '0';
        mapContainer.style.width = '0';
        mapContainer.style.overflow = 'hidden';
        mapContainer.style.zIndex = '-1';
        toggleBtn.innerHTML = '<i data-feather="map" style="width: 14px; height: 14px;"></i> Show Map';
        feather.replace();
    }
}
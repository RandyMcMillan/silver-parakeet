/**
 * Simple Route Mapper - Reliable Leaflet maps without external routing dependencies
 * Uses only OpenStreetMap tiles and Nominatim geocoding for maximum reliability
 */

class SimpleRouteMapper {
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

        console.log(`Creating simple map for route ${routeId} with ${stops.length} stops`);

        // Initialize Leaflet map centered on Atlanta
        const map = L.map(mapContainer).setView([33.7490, -84.3880], 10);
        
        // Add OpenStreetMap tiles (free and reliable)
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '© <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        }).addTo(map);

        this.maps[routeId] = map;
        this.markers[routeId] = [];

        try {
            const coordinates = [];

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

            // Add return marker
            if (depCoords) {
                const endMarker = L.marker(depCoords, {
                    icon: this.createCustomIcon('E', '#dc3545')
                }).addTo(map);
                
                endMarker.bindPopup(`
                    <div>
                        <h6><strong>END: Return to Base</strong></h6>
                        <p><small>${departureAddress}</small></p>
                    </div>
                `);
                
                this.markers[routeId].push(endMarker);
                coordinates.push(depCoords);
            }

            // Draw simple connecting lines between consecutive stops
            if (coordinates.length > 1) {
                this.drawSimpleRoute(map, routeId, coordinates);
                
                // Fit map to show all markers
                const group = new L.featureGroup(this.markers[routeId]);
                map.fitBounds(group.getBounds().pad(0.1));
            }

        } catch (error) {
            console.error('Error creating map:', error);
            // Show basic map even if geocoding fails
            this.showFallbackMap(map, routeId, stops, departureAddress);
        }
    }

    drawSimpleRoute(map, routeId, coordinates) {
        // Draw simple polylines connecting consecutive stops
        const routeSegments = [];
        
        for (let i = 0; i < coordinates.length - 1; i++) {
            const segment = L.polyline([coordinates[i], coordinates[i + 1]], {
                color: '#007bff',
                weight: 4,
                opacity: 0.7,
                dashArray: '10, 5'
            }).addTo(map);
            
            routeSegments.push(segment);
        }
        
        this.routeLines[routeId] = routeSegments;
    }

    showFallbackMap(map, routeId, stops, departureAddress) {
        console.log('Showing fallback map with basic info');
        
        // Show map centered on Atlanta with a single info marker
        map.setView([33.7490, -84.3880], 10);
        
        const fallbackMarker = L.marker([33.7490, -84.3880], {
            icon: this.createCustomIcon('!', '#ffc107')
        }).addTo(map);
        
        fallbackMarker.bindPopup(`
            <div>
                <h6><strong>Route ${routeId}</strong></h6>
                <p>${stops.length} stops scheduled</p>
                <p><small>Map temporarily unavailable</small></p>
                <p><small>Departure: ${departureAddress.substring(0, 30)}...</small></p>
            </div>
        `);
        
        this.markers[routeId] = [fallbackMarker];
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
            // Use Nominatim (OpenStreetMap) geocoding service
            const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address + ", Georgia, USA")}&limit=1&countrycodes=us`;
            
            const response = await Promise.race([
                fetch(url, {
                    headers: {
                        'User-Agent': 'ShutUpAndDrive/1.0 (Route Optimization App)'
                    }
                }),
                new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('Geocoding timeout')), 5000)
                )
            ]);
            
            if (response.ok) {
                const data = await response.json();
                
                if (data && data.length > 0) {
                    const result = data[0];
                    const coords = [parseFloat(result.lat), parseFloat(result.lon)];
                    console.log(`Geocoded ${address}: [${coords[0]}, ${coords[1]}]`);
                    return coords;
                }
            }
            
            console.warn(`No geocoding result for: ${address}`);
            return null;
            
        } catch (error) {
            console.warn(`Geocoding failed for ${address}:`, error.message);
            return null;
        }
    }

    resizeMap(routeId) {
        if (this.maps[routeId]) {
            // Small delay to ensure container is visible
            setTimeout(() => {
                this.maps[routeId].invalidateSize();
            }, 100);
        }
    }

    clearRoute(routeId) {
        // Clear existing markers and lines
        if (this.markers[routeId]) {
            this.markers[routeId].forEach(marker => {
                this.maps[routeId].removeLayer(marker);
            });
            this.markers[routeId] = [];
        }
        
        if (this.routeLines[routeId]) {
            this.routeLines[routeId].forEach(line => {
                this.maps[routeId].removeLayer(line);
            });
            this.routeLines[routeId] = [];
        }
    }
}

// Global instance
const simpleRouteMapper = new SimpleRouteMapper();

// Function to initialize a route map
function initializeSimpleRouteMap(routeId, stops, departureAddress) {
    console.log(`Initializing simple map for route ${routeId} with ${stops.length} stops`);
    simpleRouteMapper.initializeMap(routeId, stops, departureAddress);
}

// Function to handle map visibility toggle
function toggleRouteMap(routeId) {
    const mapContainer = document.getElementById(`map-container-${routeId}`);
    const toggleBtn = document.getElementById(`map-toggle-${routeId}`);
    
    if (mapContainer.style.display === 'none') {
        // Show map
        mapContainer.style.display = 'block';
        toggleBtn.textContent = 'Hide Map';
        
        // Resize map after showing
        setTimeout(() => {
            simpleRouteMapper.resizeMap(routeId);
        }, 100);
        
    } else {
        // Hide map
        mapContainer.style.display = 'none';
        toggleBtn.textContent = 'Show Map';
    }
}

// Initialize maps when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Simple route mapper ready');
});
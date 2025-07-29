class RouteMapper {
    constructor() {
        this.maps = {};
        this.directionsServices = {};
        this.directionsRenderers = {};
        this.markers = {};
    }

    async initializeMap(routeId, stops, departureAddress) {
        const mapContainer = document.getElementById(`map-${routeId}`);
        if (!mapContainer) {
            console.error(`Map container not found: map-${routeId}`);
            return;
        }

        console.log(`Creating map for route ${routeId} with stops:`, stops);

        // Initialize Google Map
        const map = new google.maps.Map(mapContainer, {
            zoom: 10,
            center: { lat: 33.7490, lng: -84.3880 }, // Atlanta center
            mapTypeId: 'roadmap',
            styles: [
                {
                    featureType: 'poi',
                    elementType: 'labels',
                    stylers: [{ visibility: 'off' }]
                }
            ]
        });

        const directionsService = new google.maps.DirectionsService();
        const directionsRenderer = new google.maps.DirectionsRenderer({
            suppressMarkers: true, // We'll add custom markers
            polylineOptions: {
                strokeColor: '#007bff',
                strokeWeight: 4,
                strokeOpacity: 0.8
            }
        });

        directionsRenderer.setMap(map);

        this.maps[routeId] = map;
        this.directionsServices[routeId] = directionsService;
        this.directionsRenderers[routeId] = directionsRenderer;
        this.markers[routeId] = [];

        // Create waypoints from stops
        const waypoints = stops.map(stop => ({
            location: stop.address,
            stopover: true
        }));

        // Calculate and display route
        if (stops.length > 0) {
            const request = {
                origin: departureAddress,
                destination: departureAddress, // Return to start
                waypoints: waypoints,
                optimizeWaypoints: false, // Keep our order
                travelMode: google.maps.TravelMode.DRIVING,
                avoidHighways: false,
                avoidTolls: false
            };

            try {
                const result = await this.calculateRoute(directionsService, request);
                directionsRenderer.setDirections(result);
                this.addCustomMarkers(map, routeId, departureAddress, stops);
            } catch (error) {
                console.error('Route calculation failed:', error);
                // Fallback: show individual markers without route line
                this.addCustomMarkers(map, routeId, departureAddress, stops);
            }
        }
    }

    calculateRoute(directionsService, request) {
        return new Promise((resolve, reject) => {
            directionsService.route(request, (result, status) => {
                if (status === 'OK') {
                    resolve(result);
                } else {
                    reject(new Error(`Directions request failed: ${status}`));
                }
            });
        });
    }

    addCustomMarkers(map, routeId, departureAddress, stops) {
        // Clear existing markers
        this.markers[routeId].forEach(marker => marker.setMap(null));
        this.markers[routeId] = [];

        // Add departure marker
        const departureMarker = new google.maps.Marker({
            position: null, // Will be geocoded
            map: map,
            title: 'START: Departure',
            icon: {
                url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                    <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="16" cy="16" r="14" fill="#28a745" stroke="white" stroke-width="2"/>
                        <text x="16" y="20" text-anchor="middle" fill="white" font-family="Arial" font-size="12" font-weight="bold">S</text>
                    </svg>
                `),
                scaledSize: new google.maps.Size(32, 32),
                anchor: new google.maps.Point(16, 16)
            }
        });

        this.geocodeAndPlaceMarker(departureMarker, departureAddress);
        this.markers[routeId].push(departureMarker);

        // Add numbered stop markers
        stops.forEach((stop, index) => {
            const stopNumber = index + 1;
            const marker = new google.maps.Marker({
                position: null, // Will be geocoded
                map: map,
                title: `Stop ${stopNumber}: ${stop.post_type}`,
                icon: {
                    url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                        <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
                            <circle cx="16" cy="16" r="14" fill="#007bff" stroke="white" stroke-width="2"/>
                            <text x="16" y="20" text-anchor="middle" fill="white" font-family="Arial" font-size="10" font-weight="bold">${stopNumber}</text>
                        </svg>
                    `),
                    scaledSize: new google.maps.Size(32, 32),
                    anchor: new google.maps.Point(16, 16)
                }
            });

            // Add info window
            const infoWindow = new google.maps.InfoWindow({
                content: `
                    <div style="max-width: 200px;">
                        <h6><strong>Stop ${stopNumber}</strong></h6>
                        <p><strong>${stop.post_type}</strong></p>
                        <p><small>${stop.address}</small></p>
                        <p><span class="badge bg-${stop.service_type === 'install' ? 'primary' : stop.service_type === 'deliver' ? 'warning' : 'secondary'}">${stop.service_type}</span></p>
                    </div>
                `
            });

            marker.addListener('click', () => {
                // Close other info windows
                this.markers[routeId].forEach(m => {
                    if (m.infoWindow) m.infoWindow.close();
                });
                infoWindow.open(map, marker);
            });

            marker.infoWindow = infoWindow;
            this.geocodeAndPlaceMarker(marker, stop.address);
            this.markers[routeId].push(marker);
        });

        // Add return marker
        const returnMarker = new google.maps.Marker({
            position: null, // Will be geocoded (same as departure)
            map: map,
            title: 'RETURN: Back to Base',
            icon: {
                url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                    <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="16" cy="16" r="14" fill="#6c757d" stroke="white" stroke-width="2"/>
                        <text x="16" y="20" text-anchor="middle" fill="white" font-family="Arial" font-size="12" font-weight="bold">E</text>
                    </svg>
                `),
                scaledSize: new google.maps.Size(32, 32),
                anchor: new google.maps.Point(16, 16)
            }
        });

        this.geocodeAndPlaceMarker(returnMarker, departureAddress);
        this.markers[routeId].push(returnMarker);
    }

    geocodeAndPlaceMarker(marker, address) {
        const geocoder = new google.maps.Geocoder();
        geocoder.geocode({ address: address }, (results, status) => {
            if (status === 'OK' && results[0]) {
                marker.setPosition(results[0].geometry.location);
            } else {
                console.warn(`Geocoding failed for address: ${address}`);
                // Fallback to Atlanta center
                marker.setPosition({ lat: 33.7490, lng: -84.3880 });
            }
        });
    }

    resizeMap(routeId) {
        if (this.maps[routeId]) {
            google.maps.event.trigger(this.maps[routeId], 'resize');
        }
    }
}

// Global instance
const routeMapper = new RouteMapper();

// Initialize maps when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Maps will be initialized when route data is available
    console.log('Route mapper ready');
});

// Function to initialize a specific route map
function initializeRouteMap(routeId, stops, departureAddress) {
    if (typeof google !== 'undefined' && google.maps) {
        routeMapper.initializeMap(routeId, stops, departureAddress);
    } else {
        console.error('Google Maps API not loaded');
    }
}

// Function to handle map visibility toggle
function toggleRouteMap(routeId) {
    const mapContainer = document.getElementById(`map-container-${routeId}`);
    const toggleBtn = document.getElementById(`map-toggle-${routeId}`);
    
    if (mapContainer.style.display === 'none') {
        mapContainer.style.display = 'block';
        toggleBtn.innerHTML = '<i data-feather="eye-off" style="width: 14px; height: 14px;"></i> Hide Map';
        
        // Initialize the map if it hasn't been created yet
        if (!routeMapper.maps[routeId]) {
            const routeCard = document.querySelector(`[data-route-id="${routeId}"]`);
            if (routeCard) {
                try {
                    const stopsDataRaw = routeCard.dataset.stopsData || '[]';
                    console.log(`Raw stops data for route ${routeId}:`, stopsDataRaw);
                    
                    // Decode HTML entities and parse JSON
                    const decodedData = stopsDataRaw.replace(/&quot;/g, '"').replace(/&#39;/g, "'");
                    const stopsData = JSON.parse(decodedData);
                    const departureAddress = routeCard.dataset.departureAddress;
                    
                    console.log(`Initializing map for route ${routeId} with ${stopsData.length} stops:`, stopsData);
                    console.log(`Departure address: ${departureAddress}`);
                    
                    if (typeof google !== 'undefined' && google.maps) {
                        routeMapper.initializeMap(routeId, stopsData, departureAddress);
                    } else {
                        console.error('Google Maps API not available');
                    }
                } catch (error) {
                    console.error(`Failed to parse stops data for route ${routeId}:`, error);
                    console.error('Raw data:', routeCard.dataset.stopsData);
                }
            }
        } else {
            // Trigger resize for existing map
            setTimeout(() => routeMapper.resizeMap(routeId), 100);
        }
        
        // Update icons
        feather.replace();
    } else {
        mapContainer.style.display = 'none';
        toggleBtn.innerHTML = '<i data-feather="map" style="width: 14px; height: 14px;"></i> Show Map';
        feather.replace();
    }
}
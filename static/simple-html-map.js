// Simple HTML-based map using absolute positioning - no canvas/CSS dependencies
const htmlMaps = {};

function createHTMLMap(routeId) {
    console.log(`Creating HTML map for route ${routeId}`);
    
    const mapElement = document.getElementById(`map-${routeId}`);
    if (!mapElement) {
        console.error(`Map element not found: map-${routeId}`);
        return;
    }
    
    // Clear and create a highly visible container
    mapElement.innerHTML = '';
    mapElement.style.cssText = 'height: 400px; width: 100%; background: linear-gradient(45deg, #e3f2fd, #bbdefb); border: 3px solid #1976d2; position: relative; overflow: hidden;';
    
    // Add title
    const title = document.createElement('div');
    title.style.cssText = 'position: absolute; top: 10px; left: 50%; transform: translateX(-50%); background: #1976d2; color: white; padding: 8px 16px; border-radius: 4px; font-weight: bold; z-index: 1000;';
    title.textContent = `Route ${routeId} - Atlanta Metro Area`;
    mapElement.appendChild(title);
    
    // Add grid background using divs
    for (let i = 0; i < 8; i++) {
        for (let j = 0; j < 10; j++) {
            const gridCell = document.createElement('div');
            gridCell.style.cssText = `position: absolute; left: ${j * 10}%; top: ${i * 12.5}%; width: 10%; height: 12.5%; border: 1px solid rgba(25, 118, 210, 0.2); box-sizing: border-box;`;
            mapElement.appendChild(gridCell);
        }
    }
    
    console.log(`HTML map container created successfully for route ${routeId}`);
    htmlMaps[routeId] = { container: mapElement, markers: [] };
    return htmlMaps[routeId];
}

function addHTMLRouteData(routeId, routeData) {
    const mapData = htmlMaps[routeId];
    if (!mapData) {
        console.error(`No HTML map found for route ${routeId}`);
        return;
    }
    
    console.log(`Adding route data to HTML map ${routeId}`, routeData);
    
    const container = mapData.container;
    
    if (!routeData || !Array.isArray(routeData)) {
        console.error(`Invalid route data for ${routeId}:`, routeData);
        return;
    }
    
    // Remove existing markers and SVG (keep title and grid)
    const existingMarkers = container.querySelectorAll('.route-marker, .route-line, svg');
    existingMarkers.forEach(marker => marker.remove());
    
    // Calculate all coordinates
    const coords = [];
    
    // Add departure coordinates
    const departureCoords = [33.7810, -84.2950]; // DeKalb Industrial Way
    coords.push({ lat: departureCoords[0], lng: departureCoords[1], type: 'start', address: '183 DeKalb Industrial Way, Decatur, GA 30030' });
    
    // Get coordinates for all stops
    routeData.forEach((stop, index) => {
        if (stop && stop.address) {
            const stopCoords = getAtlantaCoordinates(stop.address);
            if (stopCoords) {
                coords.push({ 
                    lat: stopCoords[0], 
                    lng: stopCoords[1], 
                    type: 'stop', 
                    index: index + 1, 
                    address: stop.address,
                    service_type: stop.service_type,
                    post_type: stop.post_type
                });
            }
        }
    });
    
    if (coords.length === 0) {
        console.warn(`No valid coordinates found for route ${routeId}`);
        return;
    }
    
    // Calculate bounds
    const lats = coords.map(c => c.lat);
    const lngs = coords.map(c => c.lng);
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLng = Math.min(...lngs);
    const maxLng = Math.max(...lngs);
    
    // Add padding
    const latPadding = (maxLat - minLat) * 0.1 || 0.01;
    const lngPadding = (maxLng - minLng) * 0.1 || 0.01;
    
    // Convert lat/lng to percentage positions
    function latLngToPercent(lat, lng) {
        const x = ((lng - (minLng - lngPadding)) / ((maxLng + lngPadding) - (minLng - lngPadding))) * 100;
        const y = (1 - (lat - (minLat - latPadding)) / ((maxLat + latPadding) - (minLat - latPadding))) * 100;
        return [Math.max(5, Math.min(95, x)), Math.max(5, Math.min(95, y))];
    }
    
    // Draw connections between consecutive stops using SVG lines for better rendering
    const svg = document.createElement('svg');
    svg.style.cssText = 'position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 1; pointer-events: none;';
    svg.setAttribute('viewBox', '0 0 100 100');
    svg.setAttribute('preserveAspectRatio', 'none');
    
    for (let i = 0; i < coords.length - 1; i++) {
        const [x1, y1] = latLngToPercent(coords[i].lat, coords[i].lng);
        const [x2, y2] = latLngToPercent(coords[i + 1].lat, coords[i + 1].lng);
        
        // Create SVG line element
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', x1);
        line.setAttribute('y1', y1);
        line.setAttribute('x2', x2);
        line.setAttribute('y2', y2);
        line.setAttribute('stroke', '#1976d2');
        line.setAttribute('stroke-width', '0.8');
        line.setAttribute('stroke-dasharray', '2,1');
        line.setAttribute('opacity', '0.8');
        
        svg.appendChild(line);
    }
    
    container.appendChild(svg);
    
    // Create markers for all points
    coords.forEach((point, index) => {
        const [x, y] = latLngToPercent(point.lat, point.lng);
        
        const marker = document.createElement('div');
        marker.className = 'route-marker';
        
        if (point.type === 'start') {
            // Departure marker with enhanced visibility
            marker.style.cssText = `
                position: absolute;
                left: ${x}%;
                top: ${y}%;
                width: 36px;
                height: 36px;
                background: #2e7d32;
                border: 3px solid #fff;
                border-radius: 50%;
                transform: translate(-50%, -50%);
                z-index: 20;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
                font-size: 14px;
                box-shadow: 0 3px 12px rgba(46, 125, 50, 0.4);
                cursor: pointer;
            `;
            marker.textContent = 'START';
            marker.style.fontSize = '8px';
            marker.title = `START: ${point.address}`;
        } else {
            // Stop marker with better contrast
            const isEvenStop = point.index % 2 === 0;
            marker.style.cssText = `
                position: absolute;
                left: ${x}%;
                top: ${y}%;
                width: 28px;
                height: 28px;
                background: ${isEvenStop ? '#1976d2' : '#f57c00'};
                border: 2px solid #fff;
                border-radius: 50%;
                transform: translate(-50%, -50%);
                z-index: 20;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
                font-size: 11px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                cursor: pointer;
            `;
            marker.textContent = point.index.toString();
            marker.title = `Stop ${point.index}: ${point.address}\n${point.service_type} - ${point.post_type}`;
        }
        
        container.appendChild(marker);
        
        console.log(`HTML ${point.type} ${point.index || 'S'}: ${point.address} -> [${x.toFixed(1)}%, ${y.toFixed(1)}%]`);
    });
    
    console.log(`Added ${routeData.length} stops to HTML map ${routeId}`);
}

// Use same coordinate mapping function
function getAtlantaCoordinates(address) {
    const addressLower = address.toLowerCase();
    
    // Specific street and area mappings
    if (addressLower.includes('1100 peachtree st ne')) return [33.7850, -84.3820];
    if (addressLower.includes('1201 west peachtree st nw')) return [33.7900, -84.3870];
    if (addressLower.includes('2855 piedmont rd ne')) return [33.8200, -84.3650];
    if (addressLower.includes('marietta') && addressLower.includes('ga')) return [33.9526, -84.5499];
    if (addressLower.includes('smyrna') && addressLower.includes('ga')) return [33.8837, -84.5144];
    if (addressLower.includes('powder springs')) return [33.8598, -84.6888];
    
    // General area mapping
    if (addressLower.includes('peachtree st') || addressLower.includes('peachtree street')) {
        if (addressLower.includes('ne')) return [33.7850, -84.3820];
        if (addressLower.includes('nw')) return [33.7900, -84.3870];
        return [33.7810, -84.3820];
    }
    if (addressLower.includes('spring st') || addressLower.includes('spring street')) return [33.7700, -84.3900];
    if (addressLower.includes('piedmont rd') || addressLower.includes('piedmont road')) return [33.8200, -84.3650];
    
    // Default Atlanta center
    return [33.7490, -84.3880];
}

// Toggle function for HTML maps
function toggleHTMLMap(routeId) {
    console.log(`Toggling HTML map for route ${routeId}`);
    
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
        
        // Create HTML map
        const map = createHTMLMap(routeId);
        
        if (map) {
            // Load route data from script tag
            const routeDataScript = document.getElementById(`route-data-${routeId}`);
            if (routeDataScript) {
                try {
                    const routeData = JSON.parse(routeDataScript.textContent);
                    console.log(`Parsed route data for HTML map ${routeId}:`, routeData);
                    
                    setTimeout(() => {
                        addHTMLRouteData(routeId, routeData);
                    }, 100);
                } catch (error) {
                    console.error(`Error parsing route data for HTML map ${routeId}:`, error);
                }
            }
        }
        
    } else {
        // Hide map
        container.style.display = 'none';
        button.innerHTML = '<i data-feather="map" style="width: 14px; height: 14px;"></i> Show Map';
        
        // Clean up HTML map
        if (htmlMaps[routeId]) {
            delete htmlMaps[routeId];
        }
    }
    
    // Refresh feather icons
    feather.replace();
}
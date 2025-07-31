// Canvas-based map implementation - bypasses all CSS issues
const canvasMaps = {};

function createCanvasMap(routeId) {
    console.log(`Creating canvas map for route ${routeId}`);
    
    const mapElement = document.getElementById(`map-${routeId}`);
    if (!mapElement) {
        console.error(`Map element not found: map-${routeId}`);
        return;
    }
    
    // Clear and set up canvas container
    mapElement.innerHTML = '';
    mapElement.style.cssText = 'height: 400px; width: 100%; background: #f0f0f0; border: 2px solid #007bff; position: relative;';
    
    // Create canvas element
    const canvas = document.createElement('canvas');
    canvas.width = mapElement.offsetWidth;
    canvas.height = 400;
    canvas.style.width = '100%';
    canvas.style.height = '400px';
    canvas.style.display = 'block';
    
    mapElement.appendChild(canvas);
    
    const ctx = canvas.getContext('2d');
    
    // Store canvas reference
    canvasMaps[routeId] = { canvas, ctx, width: canvas.width, height: canvas.height };
    
    // Draw background
    ctx.fillStyle = '#e8f4fd';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Add grid pattern to simulate map tiles
    drawMapGrid(ctx, canvas.width, canvas.height);
    
    console.log(`Canvas map created successfully for route ${routeId}`);
    return canvasMaps[routeId];
}

function drawMapGrid(ctx, width, height) {
    ctx.strokeStyle = '#ddd';
    ctx.lineWidth = 1;
    
    // Draw grid lines
    for (let x = 0; x <= width; x += 50) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
    }
    
    for (let y = 0; y <= height; y += 50) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
    }
    
    // Add "Atlanta Area" label
    ctx.fillStyle = '#666';
    ctx.font = '16px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('Atlanta Metro Area', width / 2, 30);
}

function addCanvasRouteData(routeId, routeData) {
    const mapData = canvasMaps[routeId];
    if (!mapData) {
        console.error(`No canvas map found for route ${routeId}`);
        return;
    }
    
    console.log(`Adding route data to canvas map ${routeId}`, routeData);
    
    const { ctx, width, height } = mapData;
    
    // Clear and redraw background
    ctx.fillStyle = '#e8f4fd';
    ctx.fillRect(0, 0, width, height);
    drawMapGrid(ctx, width, height);
    
    if (!routeData || !Array.isArray(routeData)) {
        console.error(`Invalid route data for ${routeId}:`, routeData);
        return;
    }
    
    // Calculate bounds for all coordinates
    const coords = [];
    
    // Add departure coordinates
    const departureCoords = [33.7810, -84.2950]; // DeKalb Industrial Way
    coords.push(departureCoords);
    
    // Get coordinates for all stops
    routeData.forEach(stop => {
        if (stop && stop.address) {
            const stopCoords = getAtlantaCoordinates(stop.address);
            if (stopCoords) {
                coords.push(stopCoords);
            }
        }
    });
    
    if (coords.length === 0) {
        console.warn(`No valid coordinates found for route ${routeId}`);
        return;
    }
    
    // Calculate bounds
    const lats = coords.map(c => c[0]);
    const lngs = coords.map(c => c[1]);
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLng = Math.min(...lngs);
    const maxLng = Math.max(...lngs);
    
    // Add padding
    const latPadding = (maxLat - minLat) * 0.1;
    const lngPadding = (maxLng - minLng) * 0.1;
    
    // Convert lat/lng to canvas coordinates
    function latLngToCanvas(lat, lng) {
        const x = ((lng - (minLng - lngPadding)) / ((maxLng + lngPadding) - (minLng - lngPadding))) * width;
        const y = height - ((lat - (minLat - latPadding)) / ((maxLat + latPadding) - (minLat - latPadding))) * height;
        return [x, y];
    }
    
    // Draw connections between stops
    ctx.strokeStyle = '#007bff';
    ctx.lineWidth = 3;
    ctx.setLineDash([5, 5]);
    
    for (let i = 0; i < coords.length - 1; i++) {
        const [x1, y1] = latLngToCanvas(coords[i][0], coords[i][1]);
        const [x2, y2] = latLngToCanvas(coords[i + 1][0], coords[i + 1][1]);
        
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
    }
    
    ctx.setLineDash([]); // Reset line dash
    
    // Draw departure marker
    const [depX, depY] = latLngToCanvas(departureCoords[0], departureCoords[1]);
    ctx.fillStyle = '#28a745';
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.arc(depX, depY, 15, 0, 2 * Math.PI);
    ctx.fill();
    ctx.stroke();
    
    // Add "S" for Start
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 14px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('S', depX, depY + 5);
    
    // Draw stop markers
    routeData.forEach((stop, index) => {
        if (stop && stop.address) {
            const stopCoords = getAtlantaCoordinates(stop.address);
            if (stopCoords) {
                const [x, y] = latLngToCanvas(stopCoords[0], stopCoords[1]);
                
                // Draw marker circle
                ctx.fillStyle = '#007bff';
                ctx.strokeStyle = '#fff';
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.arc(x, y, 12, 0, 2 * Math.PI);
                ctx.fill();
                ctx.stroke();
                
                // Add number
                ctx.fillStyle = '#fff';
                ctx.font = 'bold 10px Arial';
                ctx.textAlign = 'center';
                ctx.fillText((index + 1).toString(), x, y + 3);
                
                console.log(`Canvas stop ${index + 1}: ${stop.address} -> [${x}, ${y}]`);
            }
        }
    });
    
    console.log(`Added ${routeData.length} stops to canvas map ${routeId}`);
}

// Coordinate mapping function (same as before)
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

// Toggle function for canvas maps
function toggleCanvasMap(routeId) {
    console.log(`Toggling canvas map for route ${routeId}`);
    
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
        
        // Create canvas map
        const map = createCanvasMap(routeId);
        
        if (map) {
            // Load route data from script tag
            const routeDataScript = document.getElementById(`route-data-${routeId}`);
            if (routeDataScript) {
                try {
                    const routeData = JSON.parse(routeDataScript.textContent);
                    console.log(`Parsed route data for canvas ${routeId}:`, routeData);
                    
                    setTimeout(() => {
                        addCanvasRouteData(routeId, routeData);
                    }, 100);
                } catch (error) {
                    console.error(`Error parsing route data for canvas ${routeId}:`, error);
                }
            }
        }
        
    } else {
        // Hide map
        container.style.display = 'none';
        button.innerHTML = '<i data-feather="map" style="width: 14px; height: 14px;"></i> Show Map';
        
        // Clean up canvas
        if (canvasMaps[routeId]) {
            delete canvasMaps[routeId];
        }
    }
    
    // Refresh feather icons
    feather.replace();
}
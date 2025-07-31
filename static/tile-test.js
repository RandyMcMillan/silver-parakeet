// Direct tile loading test
function testTileVisibility(routeId) {
    console.log(`Testing tile visibility for route ${routeId}`);
    
    const mapElement = document.getElementById(`map-${routeId}`);
    if (!mapElement) return;
    
    // Check if tiles are actually visible
    const tiles = mapElement.querySelectorAll('.leaflet-tile');
    const visibleTiles = Array.from(tiles).filter(tile => {
        const style = window.getComputedStyle(tile);
        return style.opacity !== '0' && style.visibility !== 'hidden' && style.display !== 'none';
    });
    
    console.log(`Found ${tiles.length} total tiles, ${visibleTiles.length} visible for route ${routeId}`);
    
    // Force tiles to be visible
    tiles.forEach((tile, index) => {
        tile.style.opacity = '1';
        tile.style.visibility = 'visible';
        tile.style.display = 'block';
        tile.style.zIndex = '1';
        console.log(`Tile ${index} src: ${tile.src}`);
    });
    
    // Check tile container
    const tilePane = mapElement.querySelector('.leaflet-tile-pane');
    if (tilePane) {
        tilePane.style.zIndex = '1';
        tilePane.style.opacity = '1';
        console.log(`Tile pane transform: ${tilePane.style.transform}`);
    }
}
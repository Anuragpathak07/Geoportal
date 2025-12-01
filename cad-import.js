// Global function to handle CAD file import
window.handleCADFile = function (event) {
    const file = event.target.files[0];
    if (!file) return;

    // Show loading state
    const loadingControl = L.control({ position: 'topright' });
    loadingControl.onAdd = function () {
        const div = L.DomUtil.create('div', 'loading-control');
        div.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading CAD file...';
        return div;
    };
    loadingControl.addTo(map);

    const reader = new FileReader();
    reader.onload = function (e) {
        try {
            console.log('Starting DXF file processing...');

            // Parse DXF content
            const parser = new DxfParser();
            const dxf = parser.parseSync(e.target.result);

            console.log('DXF parsed successfully:', dxf);
            console.log('Number of entities:', dxf.entities.length);
            console.log('Entity types:', [...new Set(dxf.entities.map(e => e.type))]);

            // Convert DXF to GeoJSON
            const geoJson = {
                type: 'FeatureCollection',
                features: []
            };

            // Track bounds for the entire drawing
            let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;

            // Process each entity in the DXF
            dxf.entities.forEach((entity, index) => {
                console.log(`Processing entity ${index}:`, entity);
                let feature = null;
                let coordinates = [];

                switch (entity.type) {
                    case 'SPLINE':
                        if (!entity.controlPoints || !entity.controlPoints.length) {
                            console.warn('Invalid SPLINE entity:', entity);
                            break;
                        }
                        // Convert spline to polyline by using control points
                        coordinates = entity.controlPoints.map(point => [point.x, point.y]);
                        feature = {
                            type: 'Feature',
                            properties: {
                                layer: entity.layer || '0',
                                type: 'SPLINE'
                            },
                            geometry: {
                                type: 'LineString',
                                coordinates: coordinates
                            }
                        };
                        break;

                    case 'LINE':
                        if (!entity.start || !entity.end) {
                            console.warn('Invalid LINE entity:', entity);
                            break;
                        }
                        coordinates = [
                            [entity.start.x, entity.start.y],
                            [entity.end.x, entity.end.y]
                        ];
                        feature = {
                            type: 'Feature',
                            properties: {
                                layer: entity.layer || '0',
                                type: 'LINE'
                            },
                            geometry: {
                                type: 'LineString',
                                coordinates: coordinates
                            }
                        };
                        break;

                    case 'LWPOLYLINE':
                    case 'POLYLINE':
                        if (!entity.vertices || !entity.vertices.length) {
                            console.warn('Invalid POLYLINE entity:', entity);
                            break;
                        }
                        coordinates = entity.vertices.map(v => [v.x, v.y]);
                        feature = {
                            type: 'Feature',
                            properties: {
                                layer: entity.layer || '0',
                                type: 'POLYLINE'
                            },
                            geometry: {
                                type: 'LineString',
                                coordinates: coordinates
                            }
                        };
                        break;

                    case 'CIRCLE':
                        if (!entity.center || typeof entity.radius !== 'number') {
                            console.warn('Invalid CIRCLE entity:', entity);
                            break;
                        }
                        // Convert circle to polygon with 32 points
                        const points = [];
                        const segments = 32;
                        for (let i = 0; i < segments; i++) {
                            const angle = (i / segments) * 2 * Math.PI;
                            points.push([
                                entity.center.x + entity.radius * Math.cos(angle),
                                entity.center.y + entity.radius * Math.sin(angle)
                            ]);
                        }
                        // Close the circle
                        points.push(points[0]);
                        coordinates = [points];

                        feature = {
                            type: 'Feature',
                            properties: {
                                layer: entity.layer || '0',
                                type: 'CIRCLE'
                            },
                            geometry: {
                                type: 'Polygon',
                                coordinates: coordinates
                            }
                        };
                        break;

                    case 'ARC':
                        if (!entity.center || typeof entity.radius !== 'number' ||
                            typeof entity.startAngle !== 'number' || typeof entity.endAngle !== 'number') {
                            console.warn('Invalid ARC entity:', entity);
                            break;
                        }
                        // Convert arc to polygon with points
                        const arcPoints = [];
                        const arcSegments = 32;
                        const startAngle = entity.startAngle * (Math.PI / 180);
                        const endAngle = entity.endAngle * (Math.PI / 180);
                        const angleStep = (endAngle - startAngle) / arcSegments;

                        for (let i = 0; i <= arcSegments; i++) {
                            const angle = startAngle + (i * angleStep);
                            arcPoints.push([
                                entity.center.x + entity.radius * Math.cos(angle),
                                entity.center.y + entity.radius * Math.sin(angle)
                            ]);
                        }
                        coordinates = arcPoints;

                        feature = {
                            type: 'Feature',
                            properties: {
                                layer: entity.layer || '0',
                                type: 'ARC'
                            },
                            geometry: {
                                type: 'LineString',
                                coordinates: coordinates
                            }
                        };
                        break;

                    case 'TEXT':
                    case 'MTEXT':
                        if (!entity.position) {
                            console.warn('Invalid TEXT entity:', entity);
                            break;
                        }
                        coordinates = [entity.position.x, entity.position.y];
                        feature = {
                            type: 'Feature',
                            properties: {
                                layer: entity.layer || '0',
                                type: 'TEXT',
                                text: entity.text || entity.textString || ''
                            },
                            geometry: {
                                type: 'Point',
                                coordinates: coordinates
                            }
                        };
                        break;

                    default:
                        console.log('Unsupported entity type:', entity.type);
                }

                if (feature) {
                    // Update bounds
                    if (feature.geometry.type === 'Point') {
                        minX = Math.min(minX, coordinates[0]);
                        minY = Math.min(minY, coordinates[1]);
                        maxX = Math.max(maxX, coordinates[0]);
                        maxY = Math.max(maxY, coordinates[1]);
                    } else {
                        coordinates.forEach(coord => {
                            if (Array.isArray(coord[0])) {
                                // Handle nested arrays (for polygons)
                                coord.forEach(point => {
                                    minX = Math.min(minX, point[0]);
                                    minY = Math.min(minY, point[1]);
                                    maxX = Math.max(maxX, point[0]);
                                    maxY = Math.max(maxY, point[1]);
                                });
                            } else {
                                minX = Math.min(minX, coord[0]);
                                minY = Math.min(minY, coord[1]);
                                maxX = Math.max(maxX, coord[0]);
                                maxY = Math.max(maxY, coord[1]);
                            }
                        });
                    }
                    geoJson.features.push(feature);
                }
            });

            console.log('Processed GeoJSON:', geoJson);
            console.log('Bounds:', { minX, minY, maxX, maxY });

            // Check if we have valid bounds
            if (minX === Infinity || minY === Infinity || maxX === -Infinity || maxY === -Infinity) {
                throw new Error('No valid geometry found in the CAD file');
            }

            // Create a layer group for the CAD elements
            const cadLayer = L.geoJSON(geoJson, {
                style: function (feature) {
                    return {
                        color: getLayerColor(feature.properties.layer),
                        weight: 2,
                        opacity: 0.8,
                        fillOpacity: feature.geometry.type === 'Polygon' ? 0.2 : 0
                    };
                },
                onEachFeature: function (feature, layer) {
                    // Add popup with CAD element information
                    const popupContent = `
                        <div class="cad-popup">
                            <h4>CAD Element</h4>
                            <p><strong>Layer:</strong> ${feature.properties.layer}</p>
                            <p><strong>Type:</strong> ${feature.properties.type}</p>
                            ${feature.properties.text ? `<p><strong>Text:</strong> ${feature.properties.text}</p>` : ''}
                        </div>
                    `;
                    layer.bindPopup(popupContent);
                }
            });

            // Add the layer to the map
            cadLayer.addTo(map);
            // Remove the current basemap
            if (typeof currentBasemap !== "undefined" && map.hasLayer(currentBasemap)) {
                map.removeLayer(currentBasemap);
            }

            // Set plain background
            document.getElementById('map').style.background = "#fff";

            // Create bounds from the calculated min/max coordinates
            const bounds = L.latLngBounds(
                L.latLng(minY, minX),
                L.latLng(maxY, maxX)
            );

            // Fit map to the bounds with some padding
            map.fitBounds(bounds, {
                padding: [50, 50],
                maxZoom: 18
            });

            // Add to layer control
            const layerName = file.name.replace('.dxf', '');
            const layerGroup = {};
            layerGroup[layerName] = cadLayer;
            L.control.layers(null, layerGroup).addTo(map);

            // Show success notification
            showNotification('CAD file imported successfully!', 'success');

        } catch (error) {
            console.error('Error processing CAD file:', error);
            showNotification('Error processing CAD file: ' + error.message, 'error');
        } finally {
            // Remove loading control
            loadingControl.remove();
        }
    };

    reader.onerror = function () {
        showNotification('Error reading file', 'error');
        loadingControl.remove();
    };

    reader.readAsText(file);
};

// Helper function to get consistent colors for CAD layers
function getLayerColor(layerName) {
    const colors = {
        '0': '#FF0000',      // Red
        'DEFPOINTS': '#0000FF', // Blue
        'Plan 1': '#00FF00',  // Green
        'default': '#000000'  // Black
    };
    return colors[layerName] || colors.default;
}

// Helper function to show notifications
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
        ${message}
    `;
    document.body.appendChild(notification);

    // Add styles for notifications
    const style = document.createElement('style');
    style.textContent = `
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 5px;
            color: white;
            font-size: 14px;
            z-index: 9999;
            display: flex;
            align-items: center;
            gap: 10px;
            animation: slideIn 0.3s ease-out;
        }
        .notification.success { background-color: #28a745; }
        .notification.error { background-color: #dc3545; }
        .notification.info { background-color: #17a2b8; }
        .notification i { font-size: 18px; }
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
    `;
    document.head.appendChild(style);

    // Remove notification after 3 seconds
    setTimeout(() => {
        notification.remove();
        style.remove();
    }, 3000);
}

// Add styles for notifications and CAD elements
const style = document.createElement('style');
style.textContent = `
    .notification {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 5px;
        color: white;
        font-family: Arial, sans-serif;
        z-index: 1000;
        animation: slideIn 0.3s ease-out;
    }
    
    .notification.success {
        background-color: #4CAF50;
    }
    
    .notification.error {
        background-color: #f44336;
    }
    
    .notification.info {
        background-color: #2196F3;
    }
    
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .cad-popup {
        font-family: Arial, sans-serif;
        font-size: 12px;
    }
    
    .cad-popup h4 {
        margin: 0 0 8px 0;
        color: #333;
        font-size: 14px;
    }
    
    .cad-popup p {
        margin: 4px 0;
        color: #666;
    }
    
    .loading-control {
        font-family: Arial, sans-serif;
        font-size: 12px;
        color: #333;
    }
    
    .loading-control i {
        margin-right: 8px;
        color: #007bff;
    }
`;
document.head.appendChild(style); 
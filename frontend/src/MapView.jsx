import { useState, useEffect, useRef } from 'react';
import './MapView.css';

const MapView = ({ breweries }) => {
  const mapContainerRef = useRef(null);
  const [isLoading, setIsLoading] = useState(true);
  const leafletMapRef = useRef(null);
  const markersRef = useRef([]);
  
  // Effect to load Leaflet script and CSS
  useEffect(() => {
    // Clean up any existing Leaflet map
    if (leafletMapRef.current) {
      leafletMapRef.current.remove();
      leafletMapRef.current = null;
    }
    
    // First, make sure we load the CSS
    const cssId = 'leaflet-css';
    if (!document.getElementById(cssId)) {
      const head = document.getElementsByTagName('head')[0];
      const link = document.createElement('link');
      link.id = cssId;
      link.rel = 'stylesheet';
      link.type = 'text/css';
      link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
      link.media = 'all';
      head.appendChild(link);
    }
    
    // Then load the Leaflet JavaScript
    const scriptId = 'leaflet-js';
    if (!document.getElementById(scriptId)) {
      const script = document.createElement('script');
      script.id = scriptId;
      script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
      script.onload = initMap;
      document.body.appendChild(script);
    } else {
      // If script already exists, initialize map directly
      initMap();
    }
    
    // Cleanup function
    return () => {
      if (leafletMapRef.current) {
        leafletMapRef.current.remove();
        leafletMapRef.current = null;
      }
    };
  }, []);
  
  // Function to initialize the Leaflet map
  const initMap = () => {
    console.log("Initializing Leaflet map");
    
    if (!mapContainerRef.current || !window.L) {
      console.error("Map container ref is null or Leaflet not loaded!");
      return;
    }
    
    // Create Leaflet map
    const map = window.L.map(mapContainerRef.current).setView([41.8781, -87.6298], 12);
    
    // Add OpenStreetMap tile layer
    window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    
    // Store map reference
    leafletMapRef.current = map;
    setIsLoading(false);
    
    // Update markers if breweries data is available
    if (breweries && breweries.length > 0) {
      updateMarkers();
    }
  };
  
  // Effect to update markers when breweries change
  useEffect(() => {
    if (leafletMapRef.current && breweries && breweries.length > 0) {
      updateMarkers();
    }
  }, [breweries]);
  
  // Function to update markers
  const updateMarkers = () => {
    if (!leafletMapRef.current || !window.L) return;
    
    const map = leafletMapRef.current;
    
    // Clear existing markers
    markersRef.current.forEach(marker => map.removeLayer(marker));
    markersRef.current = [];
    
    console.log("Creating markers for", breweries.length, "breweries");
    
    // Add new markers
    const markerPositions = [];
    
    breweries.forEach(brewery => {
      // Get coordinates
      let lat, lng;
      if (brewery.coordinates) {
        lat = brewery.coordinates.lat;
        lng = brewery.coordinates.lng;
      } else {
        // Default to Chicago with slight offset
        lat = 41.8781 + (Math.random() - 0.5) * 0.05;
        lng = -87.6298 + (Math.random() - 0.5) * 0.05;
      }
      
      // Create marker
      const marker = window.L.marker([lat, lng]);
      
      // Add popup
      marker.bindPopup(`
        <div>
          <h3>${brewery.brewery || brewery.name}</h3>
          <p>${brewery.address || ''}</p>
          <p>${brewery.city || ''}, ${brewery.state || ''}</p>
          ${brewery.website ? `<a href="${brewery.website}" target="_blank">Visit Website</a>` : ''}
        </div>
      `);
      
      // Add to map
      marker.addTo(map);
      markersRef.current.push(marker);
      markerPositions.push([lat, lng]);
    });
    
    // Fit map to marker bounds
    if (markerPositions.length > 0) {
      const bounds = window.L.latLngBounds(markerPositions);
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  };
  
  return (
    <div className="map-container">
      {isLoading && (
        <div className="map-loading">
          <div className="spinner"></div>
          <p>Loading map...</p>
        </div>
      )}
      <div ref={mapContainerRef} className="map"></div>
      
      {breweries && breweries.length > 0 && (
        <div className="map-info">
          <p>Showing {breweries.length} {breweries.length === 1 ? 'brewery' : 'breweries'}</p>
        </div>
      )}
    </div>
  );
};

export default MapView;
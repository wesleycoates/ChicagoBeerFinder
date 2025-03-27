import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './MapView.css';
import L from 'leaflet';

// Fix for Leaflet marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const MapView = ({ results }) => {
  const [mapCenter, setMapCenter] = useState([41.8781, -87.6298]); // Chicago coordinates
  
  // Update map center if we have results
  useEffect(() => {
    if (results && results.length > 0) {
      // For a real app, you'd geocode addresses to get coordinates
      // For now, we'll use dummy coordinates around Chicago
      setMapCenter([41.8781, -87.6298]);
    }
  }, [results]);

  return (
    <div className="map-container">
      <MapContainer center={mapCenter} zoom={13} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {results.map((result, index) => {
          // In a real app, these coordinates would come from geocoding the address
          // For this demo, we'll generate coordinates near Chicago
          const lat = 41.8781 + (Math.random() - 0.5) * 0.05;
          const lng = -87.6298 + (Math.random() - 0.5) * 0.05;
          
          return (
            <Marker key={index} position={[lat, lng]}>
              <Popup>
                <div>
                  <h3>{result.brewery}</h3>
                  <p>{result.address}</p>
                  <p>{result.city}, {result.state}</p>
                  <h4>Featured Beer: {result.beer}</h4>
                  <p>{result.type} - {result.abv}% ABV</p>
                  {result.website && (
                    <a href={result.website} target="_blank" rel="noopener noreferrer">
                      Visit Website
                    </a>
                  )}
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
};

export default MapView;
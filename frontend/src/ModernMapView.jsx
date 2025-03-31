import React, { useState } from 'react';
import { GoogleMap, LoadScript, Marker, InfoWindow } from '@react-google-maps/api';
import './SimpleMapView.css';

const ModernMapView = ({ breweries = [] }) => {
  const [selectedBrewery, setSelectedBrewery] = useState(null);
  
  // Chicago coordinates as default center
  const mapCenter = { lat: 41.8781, lng: -87.6298 };
  
  const mapContainerStyle = {
    width: '100%',
    height: '500px'
  };
  
  const onMarkerClick = (brewery) => {
    setSelectedBrewery(brewery);
  };
  
  const onMapClick = () => {
    if (selectedBrewery) {
      setSelectedBrewery(null);
    }
  };

  return (
    <div className="map-container">
      <LoadScript googleMapsApiKey={import.meta.env.VITE_GOOGLE_MAPS_API_KEY} loadingElement={<div>Loading Map...</div>}>
        <GoogleMap
          mapContainerStyle={mapContainerStyle}
          center={mapCenter}
          zoom={12}
          onClick={onMapClick}
        >
          {breweries.map((brewery, index) => (
            <Marker
              key={index}
              position={{ lat: brewery.lat, lng: brewery.lng }}
              onClick={() => onMarkerClick(brewery)}
            />
          ))}
          
          {selectedBrewery && (
            <InfoWindow
              position={{ lat: selectedBrewery.lat, lng: selectedBrewery.lng }}
              onCloseClick={() => setSelectedBrewery(null)}
            >
              <div className="info-window">
                <h3>{selectedBrewery.name}</h3>
                <p>{selectedBrewery.address}</p>
                <p>{selectedBrewery.city}, {selectedBrewery.state}</p>
                {selectedBrewery.website && (
                  <a href={selectedBrewery.website} target="_blank" rel="noopener noreferrer">
                    Visit Website
                  </a>
                )}
                <h4>Available Beers:</h4>
                <ul>
                  {selectedBrewery.beers && selectedBrewery.beers.map((beer, beerIndex) => (
                    <li key={beerIndex}>
                      {beer.name} - {beer.type} ({beer.abv}%)
                    </li>
                  ))}
                </ul>
              </div>
            </InfoWindow>
          )}
        </GoogleMap>
      </LoadScript>
    </div>
  );
};

export default ModernMapView;
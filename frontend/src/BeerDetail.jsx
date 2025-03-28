import React from 'react';
import './BeerDetail.css';

const BeerDetail = ({ beer, onClose }) => {
  if (!beer) return null;
  
  // Handle different data structures from different sources
  const beerName = beer.beer || beer.name || '';
  const beerType = beer.type || beer.style || beer.tagline || '';
  const beerAbv = beer.abv || 0;
  const beerIbu = beer.ibu || null;
  const beerDescription = beer.description || '';
  const breweryName = beer.brewery || 'Unknown Brewery';
  const foodPairings = beer.food_pairing || [];
  
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="close-button" onClick={onClose}>×</button>
        
        <div className="beer-modal-header">
          <h2>{beerName}</h2>
          {beer.image_url && (
            <img 
              src={beer.image_url} 
              alt={beerName} 
              className="beer-modal-image"
            />
          )}
          <div className="beer-meta">
            <span className="beer-type">{beerType}</span>
            <span className="beer-metrics">
              <span className="abv">ABV: {beerAbv}%</span>
              {beerIbu && <span className="ibu">IBU: {beerIbu}</span>}
            </span>
          </div>
        </div>
        
        <div className="beer-modal-info">
          {beerDescription && (
            <div className="beer-detail-section">
              <h3>Description</h3>
              <p>{beerDescription}</p>
            </div>
          )}
          
          <div className="beer-detail-section">
            <h3>Brewery</h3>
            <p>{breweryName}</p>
            {beer.address && (
              <p>
                {beer.address}
                {beer.city && beer.state && `, ${beer.city}, ${beer.state}`}
              </p>
            )}
            {beer.website && (
              <p>
                <a 
                  href={beer.website} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="brewery-link"
                >
                  Visit Brewery Website
                </a>
              </p>
            )}
          </div>
          
          {foodPairings && foodPairings.length > 0 && (
            <div className="beer-detail-section">
              <h3>Food Pairings</h3>
              <ul className="food-pairings">
                {foodPairings.map((food, index) => (
                  <li key={index}>{food}</li>
                ))}
              </ul>
            </div>
          )}
          
          {beer.brewers_tips && (
            <div className="beer-detail-section">
              <h3>Brewer's Tips</h3>
              <p>{beer.brewers_tips}</p>
            </div>
          )}
          
          {beer.first_brewed && (
            <div className="beer-detail-section">
              <h3>First Brewed</h3>
              <p>{beer.first_brewed}</p>
            </div>
          )}
          
          {/* Add button to save to database if from external API */}
          {beer.source === 'beer_database' && (
            <div className="beer-detail-section">
              <button 
                className="save-button"
                onClick={() => {
                  // You'll implement this functionality later
                  alert('This would save the beer to your local database');
                }}
              >
                Save to My Database
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BeerDetail;
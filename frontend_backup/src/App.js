import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const searchBeers = async () => {
    if (!query.trim()) {
      setError('Please enter a search term');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      // Use relative URL with proxy in development
      const response = await axios.get(`/api/search?q=${encodeURIComponent(query)}`);
      setResults(response.data.results);
      
      if (response.data.results.length === 0) {
        setError('No beers found matching your search');
      }
    } catch (error) {
      console.error('Error searching beers:', error);
      setError('An error occurred while searching. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Chicago Beer Finder</h1>
        <p>Find your favorite beers in the Windy City</p>
      </header>
      
      <div className="search-container">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search for beers by name or type..."
          onKeyPress={(e) => e.key === 'Enter' && searchBeers()}
        />
        <button onClick={searchBeers} disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>
      
      {error && <p className="error">{error}</p>}
      
      <div className="results">
        {results.map((beer, index) => (
          <div className="beer-card" key={index}>
            <h3>{beer.beer}</h3>
            <div className="beer-details">
              <p><strong>Type:</strong> {beer.type}</p>
              <p><strong>ABV:</strong> {beer.abv}%</p>
              <p><strong>Description:</strong> {beer.description}</p>
            </div>
            <div className="location-details">
              <h4>Available at: {beer.brewery}</h4>
              <p>{beer.address}</p>
              <p>{beer.city}, {beer.state}</p>
              {beer.website && <a href={beer.website} target="_blank" rel="noopener noreferrer">Visit Website</a>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
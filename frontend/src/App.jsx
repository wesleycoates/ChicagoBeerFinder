import { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import AgeVerification from './AgeVerification';

function App() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isVerified, setIsVerified] = useState(false);
  
  // Filter states
  const [showFilters, setShowFilters] = useState(false);
  const [filterOptions, setFilterOptions] = useState({
    types: [],
    abv_range: { min: 0, max: 15 },
    breweries: []
  });
  const [selectedFilters, setSelectedFilters] = useState({
    type: '',
    min_abv: '',
    max_abv: '',
    brewery: ''
  });

  // Fetch filter options when component mounts
  useEffect(() => {
    const fetchFilterOptions = async () => {
      try {
        const response = await axios.get('/api/filters');
        setFilterOptions(response.data);
      } catch (error) {
        console.error('Error fetching filter options:', error);
      }
    };
    
    if (isVerified) {
      fetchFilterOptions();
    }
  }, [isVerified]);

  const searchBeers = async () => {
    if (!query.trim() && !selectedFilters.type && !selectedFilters.min_abv && 
        !selectedFilters.max_abv && !selectedFilters.brewery) {
      setError('Please enter a search term or select filters');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      // Build query parameters including filters
      const params = new URLSearchParams();
      if (query.trim()) params.append('q', query);
      if (selectedFilters.type) params.append('type', selectedFilters.type);
      if (selectedFilters.min_abv) params.append('min_abv', selectedFilters.min_abv);
      if (selectedFilters.max_abv) params.append('max_abv', selectedFilters.max_abv);
      if (selectedFilters.brewery) params.append('brewery', selectedFilters.brewery);
      
      const response = await axios.get(`/api/search?${params.toString()}`);
      
      if (response.data.results && response.data.results.length > 0) {
        setResults(response.data.results);
        setError('');
      } else {
        setResults([]);
        setError('No beers found matching your criteria');
      }
    } catch (error) {
      console.error('Error searching beers:', error);
      setResults([]);
      setError('An error occurred while searching. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (filter, value) => {
    setSelectedFilters(prev => ({
      ...prev,
      [filter]: value
    }));
  };

  const clearFilters = () => {
    setSelectedFilters({
      type: '',
      min_abv: '',
      max_abv: '',
      brewery: ''
    });
  };

  return (
    <div className="App">
      <AgeVerification onVerified={() => setIsVerified(true)} />
      
      {isVerified && (
        <>
          <header className="App-header">
            <h1>Chicago Beer Finder</h1>
            <p>Find your favorite beers in the Windy City</p>
          </header>
          
          <div className="search-container">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search for beers by name..."
              onKeyDown={(e) => e.key === 'Enter' && searchBeers()}
            />
            <button onClick={searchBeers} disabled={loading}>
              {loading ? 'Searching...' : 'Search'}
            </button>
            <button 
              className="filter-toggle" 
              onClick={() => setShowFilters(!showFilters)}
            >
              {showFilters ? 'Hide Filters' : 'Show Filters'}
            </button>
          </div>
          
          {showFilters && (
            <div className="filters-container">
              <div className="filter-group">
                <label>Beer Type</label>
                <select 
                  value={selectedFilters.type}
                  onChange={(e) => handleFilterChange('type', e.target.value)}
                >
                  <option value="">Any Type</option>
                  {filterOptions.types.map((type, index) => (
                    <option key={index} value={type}>{type}</option>
                  ))}
                </select>
              </div>
              
              <div className="filter-group">
                <label>ABV Range</label>
                <div className="abv-range">
                  <input
                    type="number"
                    min={filterOptions.abv_range.min}
                    max={filterOptions.abv_range.max}
                    step="0.1"
                    placeholder="Min"
                    value={selectedFilters.min_abv}
                    onChange={(e) => handleFilterChange('min_abv', e.target.value)}
                  />
                  <span>to</span>
                  <input
                    type="number"
                    min={filterOptions.abv_range.min}
                    max={filterOptions.abv_range.max}
                    step="0.1"
                    placeholder="Max"
                    value={selectedFilters.max_abv}
                    onChange={(e) => handleFilterChange('max_abv', e.target.value)}
                  />
                </div>
              </div>
              
              <div className="filter-group">
                <label>Brewery</label>
                <select
                  value={selectedFilters.brewery}
                  onChange={(e) => handleFilterChange('brewery', e.target.value)}
                >
                  <option value="">Any Brewery</option>
                  {filterOptions.breweries.map((brewery, index) => (
                    <option key={index} value={brewery}>{brewery}</option>
                  ))}
                </select>
              </div>
              
              <div className="filter-buttons">
                <button onClick={searchBeers}>Apply Filters</button>
                <button onClick={clearFilters}>Clear Filters</button>
              </div>
            </div>
          )}
          
          {error && <p className="error">{error}</p>}
          
          <div className="results">
            {results.map((beer, index) => (
              <div className="beer-card" key={index}>
                <h3>{beer.beer}</h3>
                <div className="beer-details">
                  <p><strong>Type:</strong> {beer.type}</p>
                  <p><strong>ABV:</strong> {beer.abv}%</p>
                  {beer.description && <p><strong>Description:</strong> {beer.description}</p>}
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
        </>
      )}
    </div>
  );
}

export default App;
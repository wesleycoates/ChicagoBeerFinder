import { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import AgeVerification from './AgeVerification';
import BeerDetail from './BeerDetail';
import { useRef } from 'react';
import OfflineDetection from './OfflineDetection';
import LeafletMap from './LeafletMap';

function App() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isVerified, setIsVerified] = useState(false);
  const [selectedBeer, setSelectedBeer] = useState(null);
  const [viewMode, setViewMode] = useState('list'); // 'list' or 'map' or 'breweries'
  const [breweryData, setBreweryData] = useState([]);
  const [breweries, setBreweries] = useState([]);
  
  // Filter states
  const [showFilters, setShowFilters] = useState(false);
  const [filterOptions, setFilterOptions] = useState({
    types: [],
    abv_range: { min: 0, max: 30 },
    breweries: [],
    categories: [] // New addition for categories
  });
  const [selectedFilters, setSelectedFilters] = useState({
    type: '',
    min_abv: '',
    max_abv: '',
    brewery: '',
    category_id: '' // New addition for category filter
  });
  
  const filtersRef = useRef(null);

  // Fetch filter options when component mounts
  useEffect(() => {
    const fetchData = async () => {
      try {
        const filtersResponse = await axios.get('/api/filters');
        setFilterOptions(filtersResponse.data);

        const breweriesResponse = await axios.get('/api/breweries');
        setBreweries(breweriesResponse.data.breweries);

      } catch (error) {
        console.error('Error fetching filter options:', error);
      }
    };
    
    if (isVerified) {
      fetchData();
    }
  }, [isVerified]);

  // Add this useEffect for scrolling to filters when they're shown
  useEffect(() => {
    if (showFilters && filtersRef.current) {
      // Small delay to ensure DOM is updated
      setTimeout(() => {
        filtersRef.current.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    }
  }, [showFilters]);

  const searchBeers = async () => {
    if (!query.trim() && !selectedFilters.type && !selectedFilters.min_abv && 
        !selectedFilters.max_abv && !selectedFilters.brewery && !selectedFilters.category_id) {
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
      if (selectedFilters.category_id) params.append('category_id', selectedFilters.category_id);
      
      const response = await axios.get(`/api/search?${params.toString()}`);
      
      if (response.data.results && response.data.results.length > 0) {
        setResults(response.data.results);
        
        // Process results for map view
        // Group beers by brewery
        const breweriesMap = {};
        response.data.results.forEach(beer => {
          if (!breweriesMap[beer.brewery]) {
            breweriesMap[beer.brewery] = {
              name: beer.brewery,
              address: beer.address,
              city: beer.city,
              state: beer.state,
              website: beer.website,
              lat: beer.lat || 41.8781, // Default to Chicago's latitude if missing
              lng: beer.lng || -87.6298, // Default to Chicago's longitude if missing
              beers: []
            };
          }
          
          breweriesMap[beer.brewery].beers.push({
            name: beer.beer,
            type: beer.type,
            abv: beer.abv,
            description: beer.description,
            category: beer.category,
            parent_category: beer.parent_category
          });
        });
        
        // Convert to array for the map
        setBreweryData(Object.values(breweriesMap));
        setError('');
      } else {
        setResults([]);
        setBreweryData([]);
        setError('No beers found matching your criteria');
      }
    } catch (error) {
      console.error('Error searching beers:', error);
      setResults([]);
      setBreweryData([]);
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
      brewery: '',
      category_id: ''
    });
  };

  const handleBeerClick = async (beer) => {
    if (beer.beer_id) {
      try {
        const response = await axios.get(`/api/beer/${beer.beer_id}`);
        if (response.data && response.data.length > 0) {
          setSelectedBeer(response.data[0]);
        } else {
          setSelectedBeer(beer);
        }
      } catch (error) {
        console.error('Error fetching beer details:', error);
        setSelectedBeer(beer);
      }
    } else {
      setSelectedBeer(beer);
    }
  };

  // function to close the detail modal
  const closeModal = () => {
    setSelectedBeer(null);
  };
  
  const getUniqueBreweries = () => {
    if (!results || results.length === 0) return [];
    
    const uniqueBreweries = [];
    const breweryIds = new Set();
    
    results.forEach(beer => {
      const breweryKey = `${beer.brewery}-${beer.address}`;
      if (!breweryIds.has(breweryKey)) {
        breweryIds.add(breweryKey);
        uniqueBreweries.push({
          brewery: beer.brewery,
          address: beer.address,
          city: beer.city,
          state: beer.state,
          website: beer.website,
          coordinates: beer.coordinates // Use coordinates from backend
        });
      }
    });
    
    return uniqueBreweries;
  };
  
  // Helper function to render category options with proper indentation
  const renderCategoryOptions = () => {
    const options = [];
    
    // Add a default "Any Category" option
    options.push(
      <option key="any" value="">Any Category</option>
    );
    
    // Add parent categories and their children
    if (filterOptions.categories && filterOptions.categories.length > 0) {
      filterOptions.categories.forEach(category => {
        // Add parent category
        options.push(
          <option key={category.id} value={category.id}>{category.name}</option>
        );
        
        // Add subcategories with indentation
        if (category.subcategories && category.subcategories.length > 0) {
          category.subcategories.forEach(subcategory => {
            options.push(
              <option key={subcategory.id} value={subcategory.id}>
                &nbsp;&nbsp;— {subcategory.name}
              </option>
            );
          });
        }
      });
    }
    
    return options;
  };
  
  return (
    <div className="App">
      <OfflineDetection />
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
              placeholder="Search for beers..."
              onKeyDown={(e) => e.key === 'Enter' && searchBeers()}
              aria-label="Search for beers"
            />
            <button onClick={searchBeers} disabled={loading} aria-label="Search">
              {loading ? 'Searching...' : 'Search'}
            </button>
            <button 
              className="filter-toggle" 
              onClick={() => setShowFilters(!showFilters)}
              aria-expanded={showFilters}
              aria-controls="filter-panel"
            >
              {showFilters ? 'Hide Filters' : 'Show Filters'}
            </button>
          </div>
          
          {showFilters && (
            <div 
              className="filters-container"
              ref={filtersRef}
              id="filter-panel" 
              aria-label="Filter options"
            >
              {/* New Beer Category Filter */}
              <div className="filter-group">
                <label htmlFor="beer-category">Beer Category</label>
                <select 
                  id="beer-category"
                  value={selectedFilters.category_id}
                  onChange={(e) => handleFilterChange('category_id', e.target.value)}
                >
                  {renderCategoryOptions()}
                </select>
              </div>
              
              <div className="filter-group">
                <label htmlFor="beer-type">Beer Type</label>
                <select 
                  id="beer-type"
                  value={selectedFilters.type}
                  onChange={(e) => handleFilterChange('type', e.target.value)}
                >
                  <option value="">Any Type</option>
                  {filterOptions.types && filterOptions.types.map((type, index) => (
                    <option key={index} value={type}>{type}</option>
                  ))}
                </select>
              </div>
              
              <div className="filter-group">
                <label>ABV Range</label>
                <div className="abv-range">
                  <input
                    type="number"
                    min={filterOptions.abv_range?.min || 0}
                    max={filterOptions.abv_range?.max || 30}
                    step="0.1"
                    placeholder="Min"
                    value={selectedFilters.min_abv}
                    onChange={(e) => handleFilterChange('min_abv', e.target.value)}
                    aria-label="Minimum ABV"
                    id="min-abv"
                  />
                  <span>to</span>
                  <input
                    type="number"
                    min={filterOptions.abv_range?.min || 0}
                    max={filterOptions.abv_range?.max || 30}
                    step="0.1"
                    placeholder="Max"
                    value={selectedFilters.max_abv}
                    onChange={(e) => handleFilterChange('max_abv', e.target.value)}
                    aria-label="Maximum ABV"
                    id="max-abv"
                  />
                </div>
              </div>
              
              <div className="filter-group">
                <label htmlFor="brewery">Brewery</label>
                <select
                  id="brewery"
                  value={selectedFilters.brewery}
                  onChange={(e) => handleFilterChange('brewery', e.target.value)}
                >
                  <option value="">Any Brewery</option>
                  {filterOptions.breweries && filterOptions.breweries.map((brewery, index) => (
                    <option key={index} value={brewery}>{brewery}</option>
                  ))}
                </select>
              </div>
              
              <div className="filter-buttons">
                <button
                  onClick={searchBeers}
                  aria-label="Apply filters"
                >
                  Apply Filters
                </button>
                <button
                  onClick={clearFilters}
                  aria-label="Clear all filters"
                >
                  Clear Filters
                </button>
              </div>
            </div>
          )}
          
          {error && <p className="error" role="alert">{error}</p>}
          
          {/* View Mode Toggle Buttons */}
          <div className="view-toggle">
            <button 
              className={viewMode === 'list' ? 'active' : ''} 
              onClick={() => setViewMode('list')}
              aria-pressed={viewMode === 'list'}
            >
              List View
            </button>
            <button 
              className={viewMode === 'map' ? 'active' : ''}
              onClick={() => setViewMode('map')}
              aria-pressed={viewMode === 'map'}
            >
              Map View
            </button>
            <button 
              className={viewMode === 'breweries' ? 'active' : ''}
              onClick={() => setViewMode('breweries')}
              aria-pressed={viewMode === 'breweries'}
            >
              All Breweries
            </button>
          </div>

          {/* Conditionally render either map or list view */}
          {viewMode === 'map' ? (
            breweryData.length > 0 ? (
              <LeafletMap breweries={breweryData} />
            ) : (
              <p>No brewery data available. Try searching for beers first.</p>
            )
          ) : viewMode === 'breweries' && breweries.length > 0 ? (
            <div>
              <h2>All Breweries in Chicago</h2>
              <LeafletMap breweries={breweries} />
            </div>
          ) : (
            <div className="results" aria-live="polite">
              {results.length > 0 && (
                <h2 className="visually-hidden">Search Results</h2>
              )}  
              
              {results.map((beer, index) => (
                <div 
                  className="beer-card" 
                  key={index}
                  tabIndex="0"
                  onClick={() => handleBeerClick(beer)}
                >
                  <h3>{beer.beer}</h3>
                  <div className="beer-details">
                    {/* Display beer category info if available */}
                    {(beer.category || beer.parent_category) && (
                      <p>
                        <strong>Category:</strong> {' '}
                        {beer.parent_category && (
                          <span className="category-badge parent-category">{beer.parent_category}</span>
                        )}
                        {beer.parent_category && beer.category && ' → '}
                        {beer.category && (
                          <span className="category-badge">{beer.category}</span>
                        )}
                      </p>
                    )}
                    <p><strong>Type:</strong> {beer.type}</p>
                    <p><strong>ABV:</strong> {beer.abv}%</p>
                    {beer.description && <p><strong>Description:</strong> {beer.description}</p>}
                  </div>
                  <div className="location-details">
                    <h4>Available at: {beer.brewery}</h4>
                    <p>{beer.address}</p>
                    <p>{beer.city}, {beer.state}</p>
                    {beer.website && (
                      <a 
                        href={beer.website} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        aria-label={`Visit ${beer.brewery} website`}
                      >
                        Visit Website
                      </a>
                    )}
                  </div>
                </div>
              ))}

              {results.length === 0 && !loading && !error && (
                <p>Search for beers to see results here</p>
              )}
            </div>
          )}
          
          {/* Beer Detail Modal */}
          {selectedBeer && (
            <BeerDetail beer={selectedBeer} onClose={closeModal} />
          )}
        </>
      )}
    </div>
  );
}

export default App;
import sqlite3
import os

# Cache for geocoding results
geocoding_cache = {}

def init_geocoding_table():
    """Initialize a geocoding cache table in the database"""
    db_path = os.path.join(os.path.dirname(__file__), 'beers.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS geocoding_cache (
        address TEXT PRIMARY KEY,
        lat REAL,
        lng REAL,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

def get_cached_coordinates(address):
    """Get coordinates from cache if available"""
    # Check in-memory cache first
    if address in geocoding_cache:
        return geocoding_cache[address]
    
    # Check database cache
    db_path = os.path.join(os.path.dirname(__file__), 'beers.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT lat, lng FROM geocoding_cache WHERE address = ?", 
        (address,)
    )
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        # Store in memory cache and return
        coords = {"lat": result[0], "lng": result[1]}
        geocoding_cache[address] = coords
        return coords
    
    return None

def save_coordinates_to_cache(address, lat, lng):
    """Save coordinates to cache"""
    # Save to in-memory cache
    geocoding_cache[address] = {"lat": lat, "lng": lng}
    
    # Save to database cache
    db_path = os.path.join(os.path.dirname(__file__), 'beers.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute(
        """
        INSERT OR REPLACE INTO geocoding_cache (address, lat, lng)
        VALUES (?, ?, ?)
        """,
        (address, lat, lng)
    )
    
    conn.commit()
    conn.close()

def geocode_address(address):
    """
    Geocode an address to get latitude and longitude
    
    For development, this generates deterministic coordinates without API calls
    """
    # Check cache first
    cached = get_cached_coordinates(address)
    if cached:
        return cached
    
    # Generate a hash from the address
    address_hash = sum(ord(c) for c in address)
    
    # Small variation around Chicago
    lat = 41.8781 + ((address_hash % 1000) - 500) / 10000
    lng = -87.6298 + ((address_hash // 1000 % 1000) - 500) / 10000
    
    # Cache the result
    save_coordinates_to_cache(address, lat, lng)
    
    return {"lat": lat, "lng": lng}

# Initialize the table when module is imported
init_geocoding_table()
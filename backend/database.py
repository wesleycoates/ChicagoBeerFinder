import sqlite3
import os

def init_db():
    # Ensure we're creating the database in the right location
    db_path = os.path.join(os.path.dirname(__file__), 'beers.db')
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables with enhanced schema
    cursor.executescript('''
    CREATE TABLE IF NOT EXISTS breweries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        address TEXT,
        city TEXT,
        state TEXT,
        zip_code TEXT,
        latitude REAL,       -- Added for mapping
        longitude REAL,      -- Added for mapping
        phone TEXT,          -- Added for contact info
        website TEXT,
        hours TEXT,          -- Added for visitor info
        has_taproom INTEGER DEFAULT 0,  -- Added to indicate if brewery has a taproom
        description TEXT     -- Added for brewery description
    );

    CREATE TABLE IF NOT EXISTS beers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT,
        abv REAL,
        ibu REAL,            -- Added for beer bitterness
        description TEXT,
        image_url TEXT,      -- Added for beer image
        untappd_id TEXT,     -- Added for Untappd integration
        rating_score REAL,   -- Added for average rating
        seasonal INTEGER DEFAULT 0  -- Added to indicate seasonal availability
    );

    CREATE TABLE IF NOT EXISTS beer_locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        beer_id INTEGER,
        brewery_id INTEGER,
        is_available INTEGER DEFAULT 1,
        price TEXT,           -- Added for price information
        serving_types TEXT,   -- Added for available serving types (draft, bottle, can)
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (beer_id) REFERENCES beers (id),
        FOREIGN KEY (brewery_id) REFERENCES breweries (id)
    );
    ''')
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("Enhanced database initialized successfully. Created at:", db_path)

if __name__ == '__main__':
    init_db()

import sqlite3
import os

def init_db():
    print("Starting database initialization...")
    
    # Ensure we're creating the database in the right location
    db_path = os.path.join(os.path.dirname(__file__), 'beers.db')
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        print(f"Removing existing database at {db_path}")
        os.remove(db_path)
    
    print(f"Creating new database at {db_path}")
    
    # Connect to the database (this will create it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    print("Creating database tables...")
    cursor.executescript('''
    CREATE TABLE IF NOT EXISTS breweries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        address TEXT,
        city TEXT,
        state TEXT,
        website TEXT,
        logo_url TEXT,
        founded_year INTEGER
    );

    CREATE TABLE IF NOT EXISTS beers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT,
        abv REAL,
        description TEXT,
        ibu REAL,
        image_url TEXT,
        seasonal INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS beer_locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        beer_id INTEGER,
        brewery_id INTEGER,
        is_available INTEGER DEFAULT 1,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (beer_id) REFERENCES beers (id),
        FOREIGN KEY (brewery_id) REFERENCES breweries (id)
    );
    
    CREATE TABLE IF NOT EXISTS beer_ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        beer_id INTEGER,
        rating REAL,
        num_ratings INTEGER DEFAULT 0,
        FOREIGN KEY (beer_id) REFERENCES beers (id)
    );
    ''')
    
    # Insert sample data
    print("Adding sample data...")
    
    # Add Revolution Brewing
    cursor.execute('''
    INSERT INTO breweries (name, address, city, state, website)
    VALUES ('Revolution Brewing', '2323 N Milwaukee Ave', 'Chicago', 'IL', 'https://revbrew.com')
    ''')
    revolution_id = cursor.lastrowid
    
    # Add Half Acre Beer Company
    cursor.execute('''
    INSERT INTO breweries (name, address, city, state, website)
    VALUES ('Half Acre Beer Company', '4257 N Lincoln Ave', 'Chicago', 'IL', 'https://halfacrebeer.com')
    ''')
    half_acre_id = cursor.lastrowid
    
    # Add beers for Revolution Brewing
    cursor.execute('''
    INSERT INTO beers (name, type, abv, description)
    VALUES ('Anti-Hero IPA', 'IPA', 6.7, 'Iconic Chicago IPA with citrus and pine notes')
    ''')
    anti_hero_id = cursor.lastrowid
    
    cursor.execute('''
    INSERT INTO beers (name, type, abv, description)
    VALUES ('Freedom of Speech', 'West Coast IPA', 7.2, 'A West Coast-style IPA with bright notes of grapefruit, pine, and tropical fruit')
    ''')
    freedom_id = cursor.lastrowid
    
    # Add beers for Half Acre
    cursor.execute('''
    INSERT INTO beers (name, type, abv, description)
    VALUES ('Daisy Cutter', 'Pale Ale', 5.2, 'Flagship pale ale with citrus and floral notes')
    ''')
    daisy_cutter_id = cursor.lastrowid
    
    cursor.execute('''
    INSERT INTO beers (name, type, abv, description)
    VALUES ('Pony Pilsner', 'Pilsner', 5.8, 'A crisp, clean Czech-style Pilsner with a floral hop profile')
    ''')
    pony_id = cursor.lastrowid
    
    # Link beers to breweries
    cursor.execute('''
    INSERT INTO beer_locations (beer_id, brewery_id) VALUES (?, ?)
    ''', (anti_hero_id, revolution_id))
    
    cursor.execute('''
    INSERT INTO beer_locations (beer_id, brewery_id) VALUES (?, ?)
    ''', (freedom_id, revolution_id))
    
    cursor.execute('''
    INSERT INTO beer_locations (beer_id, brewery_id) VALUES (?, ?)
    ''', (daisy_cutter_id, half_acre_id))
    
    cursor.execute('''
    INSERT INTO beer_locations (beer_id, brewery_id) VALUES (?, ?)
    ''', (pony_id, half_acre_id))
    
    # Add ratings for beers
    cursor.execute('''
    INSERT INTO beer_ratings (beer_id, rating, num_ratings)
    VALUES (?, ?, ?)
    ''', (anti_hero_id, 4.5, 120))
    
    cursor.execute('''
    INSERT INTO beer_ratings (beer_id, rating, num_ratings)
    VALUES (?, ?, ?)
    ''', (daisy_cutter_id, 4.7, 95))
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("Database initialized successfully!")

if __name__ == '__main__':
    init_db()
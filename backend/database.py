import sqlite3
import os

def init_db():
    # Ensure we're creating the database in the right location
    db_path = os.path.join(os.path.dirname(__file__), 'beers.db')
    
    # Connect to the database (this will create it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.executescript('''
    CREATE TABLE IF NOT EXISTS breweries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        address TEXT,
        city TEXT,
        state TEXT,
        website TEXT
    );

    CREATE TABLE IF NOT EXISTS beers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT,
        abv REAL,
        description TEXT
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
    ''')
    
    # Insert some sample data
    cursor.execute('''
    INSERT INTO breweries (name, address, city, state, website)
    VALUES ('Revolution Brewing', '2323 N Milwaukee Ave', 'Chicago', 'IL', 'https://revbrew.com')
    ''')
    
    cursor.execute('''
    INSERT INTO beers (name, type, abv, description)
    VALUES ('Anti-Hero IPA', 'IPA', 6.7, 'Iconic Chicago IPA with citrus and pine notes')
    ''')
    
    brewery_id = cursor.lastrowid
    
    cursor.execute('''
    INSERT INTO beer_locations (beer_id, brewery_id)
    VALUES (1, 1)
    ''')
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("Database initialized successfully. Created at:", db_path)

if __name__ == '__main__':
    init_db()
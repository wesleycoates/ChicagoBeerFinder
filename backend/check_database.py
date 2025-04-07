import sqlite3
import os

def check_database():
    # Connect to the database
    db_path = os.path.join(os.path.dirname(__file__), 'beers.db')
    print(f"Looking for database at: {db_path}")
    
    # Check if the database file exists
    if not os.path.exists(db_path):
        print(f"ERROR: Database file not found at {db_path}")
        return
    
    print(f"Database file found at {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # This allows us to access columns by name
    cursor = conn.cursor()
    
    # List all tables in the database
    print("\n===== TABLES IN DATABASE =====")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table in tables:
        print(f"Table: {table['name']}")
    
    # Now try to query each expected table
    try:
        print("\n===== BREWERIES =====")
        cursor.execute("SELECT * FROM breweries")
        breweries = cursor.fetchall()
        for brewery in breweries:
            print(f"ID: {brewery['id']}, Name: {brewery['name']}")
    except sqlite3.OperationalError as e:
        print(f"Error accessing breweries table: {e}")
    
    try:
        print("\n===== BEERS =====")
        cursor.execute("SELECT * FROM beers")
        beers = cursor.fetchall()
        for beer in beers:
            print(f"ID: {beer['id']}, Name: {beer['name']}, Type: {beer['type']}, ABV: {beer['abv']}")
    except sqlite3.OperationalError as e:
        print(f"Error accessing beers table: {e}")
    
    try:
        print("\n===== BEER LOCATIONS =====")
        cursor.execute("SELECT * FROM beer_locations")
        locations = cursor.fetchall()
        for loc in locations:
            print(f"ID: {loc['id']}, Beer ID: {loc['beer_id']}, Brewery ID: {loc['brewery_id']}")
    except sqlite3.OperationalError as e:
        print(f"Error accessing beer_locations table: {e}")
    
    conn.close()

if __name__ == '__main__':
    check_database()
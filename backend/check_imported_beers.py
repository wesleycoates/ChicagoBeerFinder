import sqlite3
import os

def check_imported_beers():
    # Connect to the database
    db_path = os.path.join(os.path.dirname(__file__), 'beers.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check for our newly imported beers
    sample_beers = ["Anti-Hero IPA", "Freedom of Speech", "Fist City", "Daisy Cutter", "Pony Pilsner"]
    
    print("Checking for sample beers:")
    for beer_name in sample_beers:
        cursor.execute("SELECT id, name, type, abv FROM beers WHERE name = ?", (beer_name,))
        beer = cursor.fetchone()
        
        if beer:
            print(f"✓ Found: {beer['name']} (Type: {beer['type']}, ABV: {beer['abv']})")
        else:
            print(f"✗ Not found: {beer_name}")
    
    # Check the beer_locations table for these beers
    print("\nChecking brewery associations:")
    cursor.execute("""
        SELECT b.name as beer_name, br.name as brewery_name
        FROM beer_locations bl
        JOIN beers b ON b.id = bl.beer_id
        JOIN breweries br ON br.id = bl.brewery_id
        WHERE b.name IN (?, ?, ?, ?, ?)
    """, sample_beers)
    
    associations = cursor.fetchall()
    for assoc in associations:
        print(f"Beer '{assoc['beer_name']}' is available at '{assoc['brewery_name']}'")
    
    conn.close()

if __name__ == '__main__':
    check_imported_beers()
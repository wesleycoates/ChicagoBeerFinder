import sqlite3

def query_database(db_path='beers.db'):
    """Query the database to show summaries of the data."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print(f"Connected to database at {db_path}")
    
    # Count breweries
    cursor.execute("SELECT COUNT(*) as count FROM breweries")
    brewery_count = cursor.fetchone()['count']
    print(f"\nTotal breweries: {brewery_count}")
    
    # List breweries
    cursor.execute("SELECT id, name, location FROM breweries ORDER BY name LIMIT 10")
    breweries = cursor.fetchall()
    print("\nFirst 10 breweries:")
    for brewery in breweries:
        print(f"  - {brewery['name']} ({brewery['location'] or 'No location'})")
    
    # Count beers
    cursor.execute("SELECT COUNT(*) as count FROM beers")
    beer_count = cursor.fetchone()['count']
    print(f"\nTotal beers: {beer_count}")
    
    # Count beers by category
    cursor.execute("""
        SELECT c.name as category, COUNT(b.id) as count
        FROM beers b
        JOIN beer_categories c ON b.category_id = c.id
        GROUP BY c.name
        ORDER BY count DESC
    """)
    categories = cursor.fetchall()
    print("\nBeers by category:")
    for category in categories:
        print(f"  - {category['category']}: {category['count']} beers")
    
    # Sample of beers with their categories and breweries
    cursor.execute("""
        SELECT b.name as beer_name, b.type, b.abv, 
               c.name as category, br.name as brewery
        FROM beers b
        JOIN beer_categories c ON b.category_id = c.id
        JOIN breweries br ON b.brewery_id = br.id
        ORDER BY RANDOM()
        LIMIT 10
    """)
    sample_beers = cursor.fetchall()
    print("\nRandom sample of 10 beers:")
    for beer in sample_beers:
        abv_info = f"ABV: {beer['abv']}%" if beer['abv'] else "ABV: unknown"
        print(f"  - {beer['beer_name']} - {beer['type'] or 'No type'} - {abv_info}")
        print(f"    Brewery: {beer['brewery']}, Category: {beer['category']}")
    
    # Close the connection
    conn.close()

if __name__ == "__main__":
    query_database()

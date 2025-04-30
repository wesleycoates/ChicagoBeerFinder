import sqlite3

# Connect to the database
conn = sqlite3.connect("beers.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check beer-brewery connections
print("=== Beer-Brewery Connections ===")
cursor.execute("""
    SELECT 
        b.id as beer_id, 
        b.name as beer_name, 
        bl.brewery_id,
        br.name as brewery_name,
        br.city,
        br.state
    FROM beers b
    JOIN beer_locations bl ON b.id = bl.beer_id
    JOIN breweries br ON bl.brewery_id = br.id
    ORDER BY br.id;
""")
connections = cursor.fetchall()
for conn_row in connections:
    print(f"Beer: {conn_row['beer_name']} -> Brewery: {conn_row['brewery_name']} (ID: {conn_row['brewery_id']})")
    print(f"  Location: {conn_row['city']}, {conn_row['state']}")
    print()

# Now check what's being returned by the actual search endpoint
print("\n=== Sample Search Query ===")
cursor.execute("""
    SELECT b.name, b.type, b.abv, b.description, br.name as brewery, 
           br.address, br.city, br.state, br.website
    FROM beers b
    JOIN beer_locations bl ON b.id = bl.beer_id
    JOIN breweries br ON bl.brewery_id = br.id
    WHERE bl.is_available = 1
    LIMIT 10;
""")
results = cursor.fetchall()
for result in results:
    print(f"Beer: {result['name']}")
    print(f"  Brewery: {result['brewery']}")
    print(f"  Location: {result['city']}, {result['state']}")
    print(f"  Address: {result['address']}")
    print(f"  Website: {result['website']}")
    print()

# Close connection
conn.close()
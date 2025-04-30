import sqlite3

# Connect to the database
conn = sqlite3.connect("beers.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Display all breweries
print("=== All Breweries ===")
cursor.execute("SELECT * FROM breweries ORDER BY id;")
breweries = cursor.fetchall()
for brewery in breweries:
    print(f"ID: {brewery['id']}")
    print(f"  Name: {brewery['name']}")
    print(f"  Address: {brewery['address']}")
    print(f"  City: {brewery['city']}")
    print(f"  State: {brewery['state']}")
    print(f"  Website: {brewery['website']}")
    print()

# Close connection
conn.close()
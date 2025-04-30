import sqlite3

# Connect to the database
conn = sqlite3.connect("beers.db")
conn.row_factory = sqlite3.Row  # This allows accessing columns by name
cursor = conn.cursor()

# Print all tables in the database
print("=== Tables in the database ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for table in tables:
    print(table['name'])

# Let's look at the breweries table
print("\n=== Breweries Table ===")
cursor.execute("PRAGMA table_info(breweries);")
columns = cursor.fetchall()
print("Columns:")
for column in columns:
    print(f"  {column['name']} ({column['type']})")

# Show actual brewery data
print("\nBrewery Records:")
cursor.execute("SELECT * FROM breweries LIMIT 10;")
breweries = cursor.fetchall()
for brewery in breweries:
    print(f"ID: {brewery['id']}, Name: {brewery['name']}, City: {brewery['city']}")

# Close the connection
conn.close()
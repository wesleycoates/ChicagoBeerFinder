import sqlite3
import os

def enhance_schema():
    print("Starting database schema enhancement...")
    
    # Get the absolute path to the beers.db file
    # We'll look in the current directory and one level up
    possible_paths = [
        os.path.join(os.getcwd(), 'beers.db'),                # Current directory
        os.path.join(os.path.dirname(os.getcwd()), 'beers.db'),  # Parent directory
        '/workspaces/ChicagoBeerFinder/backend/beers.db'      # Absolute path
    ]
    
    db_path = None
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            print(f"Found database at: {db_path}")
            break
    
    if not db_path:
        print(f"ERROR: Could not find the database file. Searched in:")
        for path in possible_paths:
            print(f"  - {path}")
        return
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # List all tables in the database to check what's available
        print("\nTables in the database:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        for table in tables:
            print(f"  - {table[0]}")
        
        # Now try to enhance the schema
        if 'breweries' in [t[0] for t in tables]:
            # Check if columns already exist before trying to add them
            cursor.execute("PRAGMA table_info(breweries)")
            brewery_columns = [column[1] for column in cursor.fetchall()]
            
            if 'logo_url' not in brewery_columns:
                cursor.execute("ALTER TABLE breweries ADD COLUMN logo_url TEXT")
                print("Added logo_url column to breweries table")
            
            if 'founded_year' not in brewery_columns:
                cursor.execute("ALTER TABLE breweries ADD COLUMN founded_year INTEGER")
                print("Added founded_year column to breweries table")
        else:
            print("ERROR: breweries table not found")
        
        if 'beers' in [t[0] for t in tables]:
            # For the beers table
            cursor.execute("PRAGMA table_info(beers)")
            beer_columns = [column[1] for column in cursor.fetchall()]
            
            if 'ibu' not in beer_columns:
                cursor.execute("ALTER TABLE beers ADD COLUMN ibu REAL")
                print("Added ibu column to beers table")
            
            if 'image_url' not in beer_columns:
                cursor.execute("ALTER TABLE beers ADD COLUMN image_url TEXT")
                print("Added image_url column to beers table")
            
            if 'seasonal' not in beer_columns:
                cursor.execute("ALTER TABLE beers ADD COLUMN seasonal INTEGER DEFAULT 0")
                print("Added seasonal column to beers table")
        else:
            print("ERROR: beers table not found")
        
        # Add a ratings table if it doesn't exist
        if 'beer_ratings' not in [t[0] for t in tables]:
            cursor.execute('''
            CREATE TABLE beer_ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                beer_id INTEGER,
                rating REAL,
                num_ratings INTEGER DEFAULT 0,
                FOREIGN KEY (beer_id) REFERENCES beers (id)
            )
            ''')
            print("Created beer_ratings table")
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        print("\nDatabase schema enhancement completed successfully")
    
    except Exception as e:
        print(f"ERROR: {e}")
        return

if __name__ == '__main__':
    enhance_schema()
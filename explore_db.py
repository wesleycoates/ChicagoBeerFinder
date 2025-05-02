import sqlite3

def explore_database(db_path='beers.db'):
    """
    Explore the structure of the SQLite database and print out table information.
    """
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print(f"Connected to database at {db_path}")
        
        # Get list of all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"Found {len(tables)} tables in the database:")
        
        # For each table, get column information and sample data
        for table in tables:
            table_name = table['name']
            print(f"\n=== Table: {table_name} ===")
            
            # Get column info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print("Columns:")
            for col in columns:
                print(f"  - {col['name']} ({col['type']})" + 
                      (f" PRIMARY KEY" if col['pk'] else "") + 
                      (f" NOT NULL" if col['notnull'] else ""))
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            row_count = cursor.fetchone()['count']
            print(f"Total rows: {row_count}")
            
            # Get sample data (first 5 rows)
            if row_count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                rows = cursor.fetchall()
                
                print("Sample data (up to 5 rows):")
                for row in rows:
                    print(f"  - {dict(row)}")
            
            # If this is the beer_categories table, show the hierarchy
            if table_name == 'beer_categories':
                print("\nCategory Hierarchy:")
                cursor.execute("""
                    WITH RECURSIVE category_tree AS (
                        SELECT id, name, parent_id, 0 AS level, name AS path
                        FROM beer_categories 
                        WHERE parent_id IS NULL
                        
                        UNION ALL
                        
                        SELECT c.id, c.name, c.parent_id, ct.level + 1, 
                               ct.path || ' > ' || c.name
                        FROM beer_categories c
                        JOIN category_tree ct ON c.parent_id = ct.id
                    )
                    SELECT id, name, parent_id, level, path
                    FROM category_tree
                    ORDER BY path;
                """)
                
                hierarchy = cursor.fetchall()
                for cat in hierarchy:
                    indent = "  " * cat['level']
                    print(f"{indent}- {cat['name']} (ID: {cat['id']})")
        
        # Close the connection
        conn.close()
        
    except Exception as e:
        print(f"Error exploring database: {e}")

if __name__ == '__main__':
    explore_database()

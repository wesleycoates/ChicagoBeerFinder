import os
import sqlite3

def find_databases():
    print("Searching for SQLite databases in the project...")
    
    # Start from the project root
    root_dir = "/workspaces/ChicagoBeerFinder"
    
    found_dbs = []
    
    # Walk through all directories and files
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.db'):
                db_path = os.path.join(root, file)
                found_dbs.append(db_path)
                
                # Try to open each database and list its tables
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    table_names = [t[0] for t in tables]
                    conn.close()
                    
                    print(f"\nFound database: {db_path}")
                    print(f"Tables: {', '.join(table_names)}")
                except Exception as e:
                    print(f"\nFound database but couldn't open: {db_path}")
                    print(f"Error: {e}")
    
    if not found_dbs:
        print("No SQLite database files found in the project.")
    else:
        print(f"\nFound {len(found_dbs)} database file(s) in total.")

if __name__ == '__main__':
    find_databases()
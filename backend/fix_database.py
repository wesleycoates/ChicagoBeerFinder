import sqlite3
import os
import re
from datetime import datetime

def backup_database(db_path):
    """Create a backup of the database"""
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    with open(db_path, 'rb') as src, open(backup_path, 'wb') as dst:
        dst.write(src.read())
    print(f"Created backup at {backup_path}")

def fix_database():
    """Fix brewery and beer data issues"""
    db_path = "beers.db"
    
    # Create backup first
    backup_database(db_path)
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Fix problematic brewery entries
    print("\n=== Finding problematic brewery entries ===")
    cursor.execute("SELECT id, name FROM breweries WHERE city IS NULL OR name LIKE '%20250%';")
    problematic_breweries = cursor.fetchall()
    
    if problematic_breweries:
        print(f"Found {len(problematic_breweries)} problematic brewery entries")
        
        # For each problematic brewery, we'll either update it or mark it for deletion
        for brewery in problematic_breweries:
            brewery_id = brewery['id']
            current_name = brewery['name']
            
            # Extract the actual brewery name (remove date/time stamps)
            real_name = re.sub(r'\s+\d{8}\s+\d{6}$', '', current_name)
            real_name = real_name.strip()
            
            # Convert underscores to spaces
            real_name = real_name.replace('_', ' ')
            
            # Proper case the name
            real_name = ' '.join(word.capitalize() for word in real_name.split())
            
            print(f"ID {brewery_id}: '{current_name}' -> '{real_name}'")
            
            # For names like "hop butcher beers", convert to proper brewery names
            if real_name.lower() == "hop butcher beers":
                real_name = "Hop Butcher For The World"
            elif real_name.lower() == "midwest coast":
                real_name = "Midwest Coast Brewing Company"
            elif real_name.lower() == "hopewell":
                real_name = "Hopewell Brewing Company"
            
            # Update the brewery with a proper name and some basic location info
            cursor.execute("""
                UPDATE breweries
                SET name = ?, city = 'Chicago', state = 'IL'
                WHERE id = ?
            """, (real_name, brewery_id))
    
    # 2. Delete metadata entries that were incorrectly added as beers
    print("\n=== Finding beer entries that are actually metadata ===")
    cursor.execute("""
        SELECT id, name FROM beers 
        WHERE name LIKE 'Style:%' OR name LIKE 'ABV:%' OR name LIKE 'Hops:%' 
        OR name LIKE 'Last Canned:%' OR name LIKE 'Formats:%' OR name LIKE 'Flavors:%'
        OR name LIKE 'Label Artwork:%';
    """)
    metadata_beers = cursor.fetchall()
    
    if metadata_beers:
        print(f"Found {len(metadata_beers)} beer entries that are actually metadata")
        
        # Get beer IDs to delete
        metadata_ids = [beer['id'] for beer in metadata_beers]
        
        # Delete related entries in beer_locations first (foreign key constraint)
        for beer_id in metadata_ids:
            cursor.execute("DELETE FROM beer_locations WHERE beer_id = ?", (beer_id,))
        
        # Then delete the beer entries
        for beer_id in metadata_ids:
            cursor.execute("DELETE FROM beers WHERE id = ?", (beer_id,))
            print(f"Deleted beer ID {beer_id}: {next((b['name'] for b in metadata_beers if b['id'] == beer_id), '')}")
    
    # Commit changes
    conn.commit()
    print("\nChanges committed to the database")
    
    # Print summary of changes
    print("\n=== Database Cleanup Summary ===")
    cursor.execute("SELECT COUNT(*) as count FROM breweries;")
    brewery_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM beers;")
    beer_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM beer_locations;")
    location_count = cursor.fetchone()['count']
    
    print(f"Total breweries: {brewery_count}")
    print(f"Total beers: {beer_count}")
    print(f"Total beer locations: {location_count}")
    
    # Close connection
    conn.close()
    print("\nDatabase cleanup complete!")

if __name__ == "__main__":
    # Ask for confirmation before proceeding
    response = input("This will modify your database. A backup will be created. Proceed? (y/n): ")
    if response.lower() == 'y':
        fix_database()
    else:
        print("Operation cancelled.")
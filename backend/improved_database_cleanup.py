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
    """Fix brewery and beer data issues with improved naming cleanup"""
    db_path = "beers.db"
    
    # Create backup first
    backup_database(db_path)
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Fix problematic brewery entries - more comprehensive pattern matching
    print("\n=== Finding problematic brewery entries ===")
    cursor.execute("SELECT id, name, city, state FROM breweries;")
    breweries = cursor.fetchall()
    
    # Define mapping of common brewery names for normalization
    brewery_name_map = {
        'hop butcher beers': 'Hop Butcher For The World',
        'hop butcher': 'Hop Butcher For The World',
        'midwest coast': 'Midwest Coast Brewing Company',
        'hopewell': 'Hopewell Brewing Company',
        'revolution brewing': 'Revolution Brewing',
        'revolution': 'Revolution Brewing',
        'half acre beer co': 'Half Acre Beer Company',
        'half acre': 'Half Acre Beer Company',
        'goose island': 'Goose Island Beer Company',
        'forbidden root': 'Forbidden Root Brewery',
        'maplewood brewing co': 'Maplewood Brewery & Distillery',
        'maplewood': 'Maplewood Brewery & Distillery',
        'off color brewing': 'Off Color Brewing',
        'off color': 'Off Color Brewing',
        'begyle': 'Begyle Brewing',
        'dovetail': 'Dovetail Brewery',
        'on tour brewing': 'On Tour Brewing Company',
        'on tour': 'On Tour Brewing Company',
        'pilot project': 'Pilot Project Brewing',
        'oldirving': 'Old Irving Brewing Co.',
        'suncatcher': 'Suncatcher Brewing'
    }
    
    # Track how many breweries were fixed
    fixed_count = 0
    
    for brewery in breweries:
        brewery_id = brewery['id']
        current_name = brewery['name']
        
        # Get city value safely
        city = brewery['city'] if 'city' in brewery and brewery['city'] is not None else ""
        
        # Skip if the brewery already has a city (likely properly formatted)
        # and doesn't have a date pattern in the name
        if city and not any(date_pattern in current_name for date_pattern in ['2025', '20250']):
            continue
            
        # Flag as needing update
        needs_update = False
        
        # Extract the actual brewery name - more comprehensive pattern matching
        cleaned_name = current_name.strip()
        
        # Remove all date/timestamp patterns
        # Format: 20250402, 2025-04-02, etc.
        cleaned_name = re.sub(r'\s+\d{8}\s+\d{6}$', '', cleaned_name)  # 20250407 131029
        cleaned_name = re.sub(r'\s+\d{8}$', '', cleaned_name)  # 20250402
        cleaned_name = re.sub(r'\s+\d{4}-\d{2}-\d{2}$', '', cleaned_name)  # 2025-04-02
        
        # Convert underscores to spaces
        cleaned_name = cleaned_name.replace('_', ' ')
        
        # If the name changed, mark for update
        if cleaned_name != current_name:
            needs_update = True
        
        # Normalize to proper brewery names from our mapping
        cleaned_name_lower = cleaned_name.lower()
        for key, proper_name in brewery_name_map.items():
            if key in cleaned_name_lower:
                cleaned_name = proper_name
                needs_update = True
                break
        
        # Update the brewery if needed
        if needs_update:
            print(f"ID {brewery_id}: '{current_name}' -> '{cleaned_name}'")
            
            cursor.execute("""
                UPDATE breweries
                SET name = ?, city = ?, state = ?
                WHERE id = ?
            """, (cleaned_name, 'Chicago', 'IL', brewery_id))
            
            fixed_count += 1
    
    print(f"Fixed {fixed_count} brewery entries")
    
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
    
    # 3. Add website/address data to popular breweries if missing
    print("\n=== Adding missing website/address data ===")
    
    brewery_data = [
        ('Hop Butcher For The World', 'Chicago', 'IL', '4710 W Arthington St', 'https://www.hopbutcher.com'),
        ('Half Acre Beer Company', 'Chicago', 'IL', '4257 N Lincoln Ave', 'https://halfacrebeer.com'),
        ('Revolution Brewing', 'Chicago', 'IL', '2323 N Milwaukee Ave', 'https://revbrew.com'),
        ('Goose Island Beer Company', 'Chicago', 'IL', '1800 W Fulton St', 'https://www.gooseisland.com'),
        ('Maplewood Brewery & Distillery', 'Chicago', 'IL', '2717 N Maplewood Ave', 'https://www.maplewoodbrew.com'),
        ('Off Color Brewing', 'Chicago', 'IL', '1460 N Kingsbury St', 'https://www.offcolorbrewing.com'),
        ('Hopewell Brewing Company', 'Chicago', 'IL', '2760 N Milwaukee Ave', 'https://www.hopewellbrewing.com'),
        ('Dovetail Brewery', 'Chicago', 'IL', '1800 W Belle Plaine Ave', 'https://dovetailbrewery.com'),
        ('Begyle Brewing', 'Chicago', 'IL', '1800 W Cuyler Ave', 'https://www.begylebrewing.com'),
        ('Old Irving Brewing Co.', 'Chicago', 'IL', '4419 W Montrose Ave', 'https://www.oldirvingbrewing.com'),
        ('On Tour Brewing Company', 'Chicago', 'IL', '1725 W Hubbard St', 'https://ontourbrewing.com'),
        ('Midwest Coast Brewing Company', 'Chicago', 'IL', '2137 W Walnut St', 'https://midwestcoastbrewing.com'),
        ('Forbidden Root Brewery', 'Chicago', 'IL', '1746 W Chicago Ave', 'https://www.forbiddenroot.com'),
        ('Pilot Project Brewing', 'Chicago', 'IL', '2140 N Milwaukee Ave', 'https://www.pilotprojectbrewing.com')
    ]
    
    for brewery_info in brewery_data:
        name, city, state, address, website = brewery_info
        
        # Update website and address if missing
        cursor.execute("""
            UPDATE breweries 
            SET website = CASE WHEN (website IS NULL OR website = '') THEN ? ELSE website END,
                address = CASE WHEN (address IS NULL OR address = '') THEN ? ELSE address END
            WHERE name = ?
        """, (website, address, name))
    
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
    
    # Let's list the first 10 breweries to verify
    print("\n=== Sample of brewery records ===")
    cursor.execute("SELECT id, name, city, state, website FROM breweries ORDER BY id LIMIT 10;")
    sample_breweries = cursor.fetchall()
    for brewery in sample_breweries:
        print(f"ID {brewery['id']}: {brewery['name']} ({brewery['city']}, {brewery['state']})")
    
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
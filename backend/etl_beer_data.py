import json
import os
import sqlite3
import glob
import traceback

def etl_beer_data():
    print("Starting Beer Data ETL Process...")
    
    # Connect to the database
    db_path = os.path.join(os.path.dirname(__file__), 'beers.db')
    
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at {db_path}")
        return
    
    print(f"Connected to database at: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get the path to JSON files - updated to the correct location
    json_dir = os.path.join(os.path.dirname(__file__), 'scraper/breweries/scraped_data')
    if not os.path.exists(json_dir):
        print(f"ERROR: Directory {json_dir} does not exist.")
        return
    
    print(f"Looking for JSON files in: {json_dir}")
    
    # Get all JSON files
    json_files = glob.glob(os.path.join(json_dir, '*.json'))
    json_files += glob.glob(os.path.join(json_dir, '*/*.json'))  # Include subdirectories
    
    print(f"Found {len(json_files)} JSON files to process")
    
    # Statistics for reporting
    stats = {
        'breweries_added': 0,
        'breweries_updated': 0,
        'beers_added': 0,
        'beers_updated': 0,
        'beer_locations_added': 0
    }
    
    # Process each JSON file
    for json_file in json_files:
        # Get brewery name from filename (remove path and extension)
        brewery_name = os.path.basename(json_file).split('.')[0].replace('_', ' ')
        print(f"\nProcessing brewery: {brewery_name}")
        
        try:
            # Load JSON data
            with open(json_file, 'r') as f:
                beers_data = json.load(f)
            
            if isinstance(beers_data, dict) and 'beers' in beers_data:
                # Handle case where data is in a 'beers' key
                beers_data = beers_data['beers']
            
            print(f"Loaded {len(beers_data)} beers from {json_file}")
            
            # Check if brewery exists in database
            cursor.execute('SELECT id FROM breweries WHERE name = ?', (brewery_name,))
            brewery_result = cursor.fetchone()
            
            if brewery_result:
                brewery_id = brewery_result[0]
                print(f"Found existing brewery with ID: {brewery_id}")
                stats['breweries_updated'] += 1
            else:
                # Add brewery to database
                cursor.execute('''
                INSERT INTO breweries (name) VALUES (?)
                ''', (brewery_name,))
                brewery_id = cursor.lastrowid
                print(f"Added new brewery with ID: {brewery_id}")
                stats['breweries_added'] += 1
            
            # Process each beer in the file
            for beer_data in beers_data:
                try:
                    # Handle different formats of beer data
                    if isinstance(beer_data, str):
                        # If it's just a string, use it as the name
                        name = beer_data.strip()
                        beer_type = ""
                        abv = 0.0
                        description = ""
                    else:
                        # Extract and normalize beer data
                        name = beer_data.get('name', '').strip()
                        if not name:
                            print("WARNING: Skipping beer with no name")
                            continue
                        
                        # Handle different field names for beer type
                        beer_type = beer_data.get('type', '')
                        if not beer_type:
                            beer_type = beer_data.get('style', '')
                        beer_type = beer_type.strip() if beer_type else ""
                        
                        # Clean up ABV value
                        abv_raw = beer_data.get('abv', 0)
                        abv = 0.0
                        
                        if isinstance(abv_raw, str):
                            abv_str = abv_raw.replace('%', '').strip()
                            try:
                                abv = float(abv_str)
                            except ValueError:
                                print(f"WARNING: Invalid ABV value '{abv_raw}' for beer '{name}', using 0.0")
                        elif isinstance(abv_raw, (int, float)):
                            abv = float(abv_raw)
                        
                        # Get description
                        description = beer_data.get('description', '').strip()
                    
                    print(f"Processing beer: {name}, Type: {beer_type}, ABV: {abv}")
                    
                    # Check if beer already exists
                    cursor.execute('''
                    SELECT id FROM beers WHERE name = ?
                    ''', (name,))
                    
                    beer_result = cursor.fetchone()
                    if beer_result:
                        beer_id = beer_result[0]
                        print(f"Updating existing beer with ID: {beer_id}")
                        
                        # Update beer data - only if we have valid data
                        if beer_type or abv > 0 or description:
                            cursor.execute('''
                            UPDATE beers 
                            SET type = COALESCE(NULLIF(?, ''), type),
                                abv = CASE WHEN ? > 0 THEN ? ELSE abv END,
                                description = COALESCE(NULLIF(?, ''), description)
                            WHERE id = ?
                            ''', (beer_type, abv, abv, description, beer_id))
                        
                        stats['beers_updated'] += 1
                    else:
                        # Add beer to database
                        cursor.execute('''
                        INSERT INTO beers (name, type, abv, description)
                        VALUES (?, ?, ?, ?)
                        ''', (name, beer_type, abv, description))
                        
                        beer_id = cursor.lastrowid
                        print(f"Added new beer with ID: {beer_id}")
                        stats['beers_added'] += 1
                    
                    # Check if beer is already available at this brewery
                    cursor.execute('''
                    SELECT id FROM beer_locations 
                    WHERE beer_id = ? AND brewery_id = ?
                    ''', (beer_id, brewery_id))
                    
                    location_result = cursor.fetchone()
                    if not location_result:
                        # Link beer to brewery
                        cursor.execute('''
                        INSERT INTO beer_locations (beer_id, brewery_id, is_available)
                        VALUES (?, ?, 1)
                        ''', (beer_id, brewery_id))
                        
                        print(f"Linked beer '{name}' to brewery '{brewery_name}'")
                        stats['beer_locations_added'] += 1
                
                except Exception as e:
                    print(f"ERROR processing beer {beer_data if isinstance(beer_data, str) else beer_data.get('name', 'unknown')}: {str(e)}")
                    traceback.print_exc()
        
        except json.JSONDecodeError:
            print(f"ERROR: {json_file} is not a valid JSON file")
        except Exception as e:
            print(f"ERROR processing {json_file}: {str(e)}")
            traceback.print_exc()
    
    # Commit changes and close connection
    conn.commit()
    
    # Check how many beers we have now
    cursor.execute("SELECT COUNT(*) FROM beers")
    beer_count = cursor.fetchone()[0]
    print(f"\nTotal beers in database after import: {beer_count}")
    
    # Check the latest beers added
    cursor.execute("""
        SELECT b.id, b.name, b.type, b.abv, br.name as brewery
        FROM beers b
        JOIN beer_locations bl ON b.id = bl.beer_id
        JOIN breweries br ON bl.brewery_id = br.id
        ORDER BY b.id DESC
        LIMIT 10
    """)
    latest_beers = cursor.fetchall()
    print("\nLatest beers in database:")
    for beer in latest_beers:
        print(f"ID: {beer['id']}, Name: {beer['name']}, Type: {beer['type'] or 'Unknown'}, ABV: {beer['abv']}, Brewery: {beer['brewery']}")
    
    conn.close()
    
    # Print summary statistics
    print("\n=== ETL Process Summary ===")
    print(f"Breweries added: {stats['breweries_added']}")
    print(f"Breweries updated: {stats['breweries_updated']}")
    print(f"Beers added: {stats['beers_added']}")
    print(f"Beers updated: {stats['beers_updated']}")
    print(f"Beer-brewery relationships added: {stats['beer_locations_added']}")
    print("ETL process completed successfully!")

if __name__ == '__main__':
    etl_beer_data()
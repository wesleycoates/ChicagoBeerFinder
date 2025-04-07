import json
import os
import sqlite3

def import_beer_data():
    print("Starting beer data import process...")
    
    # Step 1: Connect to the database
    db_path = os.path.join(os.path.dirname(__file__), 'beers.db')
    print(f"Connecting to database at: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Step 2: Set the path to your JSON files (create this folder if it doesn't exist)
    json_dir = os.path.join(os.path.dirname(__file__), 'brewery_data')
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)
        print(f"Created directory for JSON files at: {json_dir}")
    
    # Step 3: Find all JSON files
    json_files = []
    for file in os.listdir(json_dir):
        if file.endswith('.json'):
            json_files.append(os.path.join(json_dir, file))
    
    print(f"Found {len(json_files)} JSON files to process")
    
    # Count how many beers we import successfully
    total_imported = 0
    
    # Step 4: Process each JSON file
    for json_file in json_files:
        brewery_name = os.path.basename(json_file).split('.')[0]
        print(f"Processing brewery: {brewery_name}")
        
        # Load JSON data
        try:
            with open(json_file, 'r') as f:
                beers = json.load(f)
                
            # Check if brewery exists in database
            cursor.execute('SELECT id FROM breweries WHERE name = ?', (brewery_name,))
            brewery_result = cursor.fetchone()
            
            if brewery_result:
                brewery_id = brewery_result[0]
                print(f"Found existing brewery with ID: {brewery_id}")
            else:
                # Add brewery to database
                cursor.execute('''
                INSERT INTO breweries (name) VALUES (?)
                ''', (brewery_name,))
                brewery_id = cursor.lastrowid
                print(f"Added new brewery with ID: {brewery_id}")
            
            # Process each beer
            for beer in beers:
                # Get beer details from JSON
                beer_name = beer.get('name', '')
                
                # Handle different field names for beer type
                beer_type = beer.get('type', '')
                if not beer_type:
                    beer_type = beer.get('style', '')
                
                # Clean up ABV value
                abv_str = beer.get('abv', '0')
                if isinstance(abv_str, str):
                    abv_str = abv_str.replace('%', '')
                    try:
                        abv = float(abv_str)
                    except ValueError:
                        abv = 0.0
                else:
                    abv = float(abv_str) if abv_str else 0.0
                
                description = beer.get('description', '')
                
                # Check if beer already exists
                cursor.execute('''
                SELECT id FROM beers WHERE name = ? AND type = ?
                ''', (beer_name, beer_type))
                
                beer_result = cursor.fetchone()
                if beer_result:
                    beer_id = beer_result[0]
                    print(f"Found existing beer: {beer_name}")
                else:
                    # Add beer to database
                    cursor.execute('''
                    INSERT INTO beers (name, type, abv, description)
                    VALUES (?, ?, ?, ?)
                    ''', (beer_name, beer_type, abv, description))
                    beer_id = cursor.lastrowid
                    print(f"Added new beer: {beer_name}")
                
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
                    print(f"Linked beer {beer_name} to brewery {brewery_name}")
                    total_imported += 1
                
        except json.JSONDecodeError:
            print(f"Error: {json_file} is not a valid JSON file")
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
    
    # Commit all changes and close connection
    conn.commit()
    conn.close()
    
    print(f"Successfully imported {total_imported} beers from {len(json_files)} breweries")
    print("Import process completed!")

if __name__ == '__main__':
    import_beer_data()
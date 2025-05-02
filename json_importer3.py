import json
import sqlite3
import os
import re

def clean_text(text):
    """Clean and normalize text data."""
    if not text:
        return None
    
    # Remove excess whitespace and normalize
    if isinstance(text, str):
        return re.sub(r'\s+', ' ', text).strip()
    return text

def categorize_beer(conn, name, beer_type, description):
    """Determine the most likely beer category based on name, type and description."""
    search_text = ""
    if name:
        search_text += str(name).lower() + " "
    if beer_type:
        search_text += str(beer_type).lower() + " "
    if description:
        search_text += str(description).lower()
    
    search_text = search_text.strip()
    
    cursor = conn.cursor()
    
    # Get all categories
    cursor.execute("SELECT id, name FROM beer_categories")
    categories = cursor.fetchall()
    
    # Build a mapping of category names to IDs
    category_map = {cat[1]: cat[0] for cat in categories}
    
    # Mapping of regex patterns to category names
    category_patterns = {
        r'ipa|india pale ale|imperial ipa|double ipa|dipa|triple ipa|tipa|hazy': 'IPA',
        r'pale ale|blonde ale|golden ale': 'Pale Ale',
        r'amber|red ale|irish red': 'Amber/Red Ale',
        r'brown ale|brown|nut brown': 'Brown Ale',
        r'porter|coffee porter|vanilla porter|chocolate porter': 'Porter',
        r'stout|imperial stout|milk stout|oatmeal stout|coffee stout': 'Stout',
        r'wheat|hefeweizen|witbier|white ale|weiss|weisse': 'Wheat Beer',
        r'sour|gose|berliner|lambic|flanders|wild ale': 'Sour',
        r'pilsner|pils|pilsener': 'Pilsner',
        r'lager|vienna lager|munich lager|dortmunder': 'Lager',
        r'light lager|american light|lite': 'Light Lager',
        r'belgian|abbey|trappist|dubbel|tripel|quad|quadrupel|saison': 'Belgian',
        r'barleywine|barley wine': 'Barleywine',
        r'scotch ale|scottish ale|wee heavy': 'Scotch/Scottish Ale',
        r'kolsch|kölsch': 'Kölsch',
        r'bock|doppelbock|maibock|eisbock': 'Bock',
        r'farmhouse|saison|biere de garde': 'Farmhouse',
        r'wild|brett|brettanomyces': 'Wild/Spontaneous'
    }
    
    # First, check for main category
    for pattern, category in category_patterns.items():
        if re.search(pattern, search_text):
            return category_map.get(category, category_map.get('Other'))
    
    # Default to "Other" if no category matches
    return category_map.get('Other')

def process_brewery_beer_format(conn, data, filename):
    """Process JSON data in {brewery: {...}, beers: [...]} format."""
    cursor = conn.cursor()
    
    # Extract brewery data
    brewery_data = data.get('brewery', {})
    brewery_name = clean_text(brewery_data.get('name'))
    
    if not brewery_name:
        print(f"Skipping {filename} - No brewery name found")
        return 0
    
    # Check if brewery already exists
    cursor.execute("SELECT id FROM breweries WHERE name = ?", (brewery_name,))
    brewery_result = cursor.fetchone()
    
    if brewery_result:
        brewery_id = brewery_result[0]
        print(f"Found existing brewery: {brewery_name} (ID: {brewery_id})")
    else:
        # Insert new brewery
        cursor.execute(
            """
            INSERT INTO breweries (name, location, description, website, image_url)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                brewery_name,
                clean_text(brewery_data.get('location')),
                clean_text(brewery_data.get('description')),
                clean_text(brewery_data.get('website')),
                clean_text(brewery_data.get('image_url'))
            )
        )
        brewery_id = cursor.lastrowid
        print(f"Added new brewery: {brewery_name} (ID: {brewery_id})")
    
    # Process beers
    beers_added = 0
    beers_data = data.get('beers', [])
    for beer_data in beers_data:
        beer_name = clean_text(beer_data.get('name'))
        if not beer_name:
            continue
        
        # Check if beer already exists for this brewery
        cursor.execute(
            "SELECT id FROM beers WHERE name = ? AND brewery_id = ?",
            (beer_name, brewery_id)
        )
        beer_result = cursor.fetchone()
        
        if beer_result:
            print(f"Beer already exists: {beer_name} - skipping")
            continue
        
        beer_type = clean_text(beer_data.get('type'))
        beer_description = clean_text(beer_data.get('description', ''))
        
        # Get ABV and IBU
        abv = beer_data.get('abv')
        ibu = beer_data.get('ibu')
        
        # Determine beer category
        category_id = categorize_beer(conn, beer_name, beer_type, beer_description)
        
        # Insert beer
        cursor.execute(
            """
            INSERT INTO beers (
                name, brewery_id, type, abv, ibu, 
                description, category_id, image_url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                beer_name,
                brewery_id,
                beer_type,
                abv,
                ibu,
                beer_description,
                category_id,
                clean_text(beer_data.get('image_url'))
            )
        )
        beers_added += 1
        
        # Get the category name for this beer
        if category_id:
            cursor.execute("SELECT name FROM beer_categories WHERE id = ?", (category_id,))
            category_result = cursor.fetchone()
            category_name = category_result[0] if category_result else "Unknown"
        else:
            category_name = "Other"
        
        print(f"Added beer: {beer_name} (Category: {category_name})")
    
    return beers_added

def process_list_format(conn, data, filename):
    """Process JSON data in list format [beer1, beer2, ...] or [brewery1, brewery2, ...]."""
    cursor = conn.cursor()
    beers_added = 0
    
    # Check what kind of list we have
    if not data:
        return 0
    
    # If it's a list of beers
    for item in data:
        # Check if the item has a brewery field
        brewery_name = clean_text(item.get('brewery'))
        beer_name = clean_text(item.get('name'))
        
        if not beer_name:
            continue
        
        if brewery_name:
            # Check if brewery exists
            cursor.execute("SELECT id FROM breweries WHERE name = ?", (brewery_name,))
            brewery_result = cursor.fetchone()
            
            if brewery_result:
                brewery_id = brewery_result[0]
            else:
                # Insert new brewery with minimal info
                cursor.execute(
                    "INSERT INTO breweries (name, location) VALUES (?, ?)",
                    (brewery_name, clean_text(item.get('location')))
                )
                brewery_id = cursor.lastrowid
                print(f"Added new brewery: {brewery_name} (ID: {brewery_id})")
            
            # Check if beer already exists
            cursor.execute(
                "SELECT id FROM beers WHERE name = ? AND brewery_id = ?",
                (beer_name, brewery_id)
            )
            beer_result = cursor.fetchone()
            
            if beer_result:
                print(f"Beer already exists: {beer_name} - skipping")
                continue
            
            beer_type = clean_text(item.get('type') or item.get('style'))
            beer_description = clean_text(item.get('description', ''))
            
            # Get ABV and IBU
            abv = item.get('abv')
            ibu = item.get('ibu')
            
            # Determine beer category
            category_id = categorize_beer(conn, beer_name, beer_type, beer_description)
            
            # Insert beer
            cursor.execute(
                """
                INSERT INTO beers (
                    name, brewery_id, type, abv, ibu, 
                    description, category_id, image_url
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    beer_name,
                    brewery_id,
                    beer_type,
                    abv,
                    ibu,
                    beer_description,
                    category_id,
                    clean_text(item.get('image_url'))
                )
            )
            beers_added += 1
            
            # Get the category name for this beer
            if category_id:
                cursor.execute("SELECT name FROM beer_categories WHERE id = ?", (category_id,))
                category_result = cursor.fetchone()
                category_name = category_result[0] if category_result else "Unknown"
            else:
                category_name = "Other"
            
            print(f"Added beer: {beer_name} (Category: {category_name})")
    
    return beers_added

def import_json_data(json_directory, db_path='beers.db'):
    """
    Import beer data from JSON files into the database.
    Handles multiple JSON formats.
    """
    # Connect to the database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Process each JSON file in the directory
        json_files = [f for f in os.listdir(json_directory) if f.endswith('.json')]
        
        if not json_files:
            print(f"No JSON files found in {json_directory}")
            return
            
        print(f"Found {len(json_files)} JSON files to process")
        
        total_beers_added = 0
        successful_files = 0
        
        for filename in json_files:
            file_path = os.path.join(json_directory, filename)
            print(f"Processing {file_path}...")
            
            try:
                with open(file_path, 'r') as file:
                    data = json.load(file)
                
                beers_added = 0
                
                # Determine the format and process accordingly
                if isinstance(data, dict) and 'brewery' in data and 'beers' in data:
                    # Standard format with brewery and beers
                    beers_added = process_brewery_beer_format(conn, data, filename)
                elif isinstance(data, list):
                    # List format
                    beers_added = process_list_format(conn, data, filename)
                else:
                    print(f"Unknown JSON format in {filename} - skipping")
                    continue
                
                conn.commit()
                total_beers_added += beers_added
                successful_files += 1
                print(f"Finished processing {filename} - Added {beers_added} beers")
                
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON in {filename}: {e}")
            except Exception as e:
                conn.rollback()
                print(f"Error processing {filename}: {e}")
        
        print(f"Import complete! Processed {successful_files} of {len(json_files)} files.")
        print(f"Added {total_beers_added} beers to the database.")
        
    except Exception as e:
        conn.rollback()
        print(f"Error importing data: {e}")
    finally:
        cursor.close()
        conn.close()

# Usage example
if __name__ == "__main__":
    # You'll need to specify the correct path to your JSON files
    json_directory = "./beer_json_files"
    import_json_data(json_directory)

import sqlite3
import re

def assign_categories_to_beers():
    """
    Script to assign categories to existing beers based on their beer type and name.
    This helps migrate existing data to use the new hierarchical category structure.
    """
    # Path to the database - we're already in the backend folder
    db_path = 'beers.db'
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print(f"Connected to database at {db_path}")
    
    # First, let's check if the beers table has a category_id column
    try:
        cursor.execute("SELECT category_id FROM beers LIMIT 1")
    except sqlite3.OperationalError:
        print("Adding category_id column to beers table...")
        cursor.execute("ALTER TABLE beers ADD COLUMN category_id INTEGER REFERENCES beer_categories(id)")
    
    # Get all beers that don't have a category assigned
    cursor.execute("""
        SELECT b.id, b.name, b.type, b.description
        FROM beers b
        WHERE b.category_id IS NULL OR b.category_id = 0
    """)
    
    beers_without_category = cursor.fetchall()
    print(f"Found {len(beers_without_category)} beers without a category assigned")
    
    # Get all categories
    cursor.execute("SELECT id, name, parent_id FROM beer_categories")
    categories = cursor.fetchall()
    
    # Build a mapping of category names to IDs
    category_map = {cat['name']: cat['id'] for cat in categories}
    
    # Mapping of beer types/terms to categories
    type_to_category_mapping = {
        # IPAs
        r'IPA|India Pale Ale|Imperial IPA|Double IPA|DIPA|Triple IPA|TIPA': category_map.get('IPA'),
        
        # Pale Ales
        r'Pale Ale|Blonde Ale|Golden Ale': category_map.get('Pale Ale'),
        
        # Amber/Red Ales
        r'Amber|Red Ale|Irish Red': category_map.get('Amber/Red Ale'),
        
        # Brown Ales
        r'Brown Ale|Brown|Nut Brown': category_map.get('Brown Ale'),
        
        # Porters
        r'Porter|Coffee Porter|Vanilla Porter|Chocolate Porter': category_map.get('Porter'),
        
        # Stouts
        r'Stout|Imperial Stout|Milk Stout|Oatmeal Stout|Coffee Stout': category_map.get('Stout'),
        
        # Wheat Beers
        r'Wheat|Hefeweizen|Witbier|White Ale|Weiss|Weisse': category_map.get('Wheat Beer'),
        
        # Sours
        r'Sour|Gose|Berliner|Lambic|Flanders|Wild Ale': category_map.get('Sour'),
        
        # Pilsners
        r'Pilsner|Pils|Pilsener': category_map.get('Pilsner'),
        
        # Lagers
        r'Lager|Vienna Lager|Munich Lager|Dortmunder': category_map.get('Lager'),
        
        # Light Lagers
        r'Light Lager|American Light|Lite': category_map.get('Light Lager'),
        
        # Belgian
        r'Belgian|Abbey|Trappist|Dubbel|Tripel|Quad|Quadrupel|Saison': category_map.get('Belgian'),
        
        # Barleywine
        r'Barleywine|Barley Wine': category_map.get('Barleywine'),
        
        # Scotch/Scottish Ale
        r'Scotch Ale|Scottish Ale|Wee Heavy': category_map.get('Scotch/Scottish Ale'),
        
        # Fruit/Vegetable Beer
        r'Fruit|Berry|Cherry|Apricot|Peach|Mango|Pumpkin|Watermelon': category_map.get('Fruit/Vegetable Beer'),
        
        # Spice/Herb/Specialty
        r'Spice|Herb|Chai|Ginger|Pepper|Chocolate|Coffee|Vanilla': category_map.get('Spice/Herb/Specialty'),
        
        # Smoked Beer
        r'Smoked|Rauch|Smoke': category_map.get('Smoked Beer'),
        
        # Strong Ale
        r'Strong Ale|Old Ale': category_map.get('Strong Ale'),
        
        # Kölsch
        r'Kölsch|Kolsch': category_map.get('Kölsch'),
        
        # Bock
        r'Bock|Doppelbock|Maibock|Eisbock': category_map.get('Bock'),
        
        # Farmhouse
        r'Farmhouse|Saison|Biere de Garde': category_map.get('Farmhouse'),
        
        # Hybrid
        r'Hybrid|California Common|Steam Beer|Cream Ale|Altbier': category_map.get('Hybrid'),
        
        # Wild/Spontaneous
        r'Wild|Brett|Brettanomyces': category_map.get('Wild/Spontaneous'),
        
        # Session
        r'Session': category_map.get('Session')
    }
    
    # Track stats
    categorized_count = 0
    uncategorized_count = 0
    
    # Process each beer
    for beer in beers_without_category:
        beer_id = beer['id']
        beer_name = beer['name'] or ''
        beer_type = beer['type'] or ''
        beer_desc = beer['description'] or ''
        
        # Combine fields for searching
        search_text = f"{beer_name} {beer_type} {beer_desc}".lower()
        
        category_id = None
        matched_pattern = None
        
        # Try to match a category based on the type_to_category_mapping
        for pattern, cat_id in type_to_category_mapping.items():
            if cat_id and re.search(pattern.lower(), search_text):
                category_id = cat_id
                matched_pattern = pattern
                break
        
        # If no match found, assign to "Other"
        if category_id is None and 'Other' in category_map:
            category_id = category_map['Other']
            matched_pattern = "Other (default)"
        
        # Update the beer's category
        if category_id:
            cursor.execute(
                "UPDATE beers SET category_id = ? WHERE id = ?",
                (category_id, beer_id)
            )
            categorized_count += 1
            
            # Get the category name
            cursor.execute(
                "SELECT name FROM beer_categories WHERE id = ?", 
                (category_id,)
            )
            category_result = cursor.fetchone()
            if category_result:
                category_name = category_result['name']
                print(f"Assigned category '{category_name}' to beer: {beer_name} (matched: {matched_pattern})")
            else:
                print(f"Assigned category ID {category_id} to beer: {beer_name} (matched: {matched_pattern})")
        else:
            uncategorized_count += 1
            print(f"Could not categorize beer: {beer_name}")
    
    # Commit the changes
    conn.commit()
    
    # Print summary
    print("\nCategory assignment complete!")
    print(f"Categorized {categorized_count} beers")
    print(f"Could not categorize {uncategorized_count} beers")
    
    # Check all beers have categories now
    cursor.execute("SELECT COUNT(*) as count FROM beers WHERE category_id IS NULL OR category_id = 0")
    result = cursor.fetchone()
    if result and result['count'] > 0:
        print(f"Warning: {result['count']} beers still don't have a category assigned")
    else:
        print("All beers have been assigned to a category")
    
    # Close the connection
    conn.close()

if __name__ == '__main__':
    assign_categories_to_beers()
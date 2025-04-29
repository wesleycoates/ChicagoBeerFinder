import sqlite3
import os

def organize_beer_categories():
    """
    Organize existing beer categories into a hierarchy by setting up parent-child relationships.
    """
    # Path to the database - simpler path since we're already in backend folder
    db_path = 'beers.db'
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Connected to database at {db_path}")
    
    # Define the main categories that will serve as parents
    main_categories = {
        "Ales": ["IPA", "Pale Ale", "Amber/Red Ale", "Brown Ale", "Stout", "Porter", 
                "Wheat Beer", "Sour", "Belgian", "Barleywine", "Scotch/Scottish Ale", 
                "Strong Ale", "Kölsch", "Wild/Spontaneous", "Session"],
        "Lagers": ["Pilsner", "Lager", "Light Lager", "Bock"],
        "Specialty": ["Fruit/Vegetable Beer", "Spice/Herb/Specialty", "Smoked Beer", 
                     "Farmhouse", "Hybrid", "Other"]
    }
    
    # First, create the parent categories
    for parent_name in main_categories.keys():
        # Check if the parent category already exists
        cursor.execute("SELECT id FROM beer_categories WHERE name = ?", (parent_name,))
        result = cursor.fetchone()
        
        if result:
            print(f"Parent category '{parent_name}' already exists with ID {result[0]}")
        else:
            cursor.execute("INSERT INTO beer_categories (name, parent_id) VALUES (?, NULL)", (parent_name,))
            print(f"Created parent category '{parent_name}'")
    
    # Now, assign parent IDs to existing categories
    for parent_name, child_categories in main_categories.items():
        # Get the parent ID
        cursor.execute("SELECT id FROM beer_categories WHERE name = ?", (parent_name,))
        parent_result = cursor.fetchone()
        
        if parent_result:
            parent_id = parent_result[0]
            
            # Update the child categories
            for child_name in child_categories:
                cursor.execute("UPDATE beer_categories SET parent_id = ? WHERE name = ?", 
                              (parent_id, child_name))
                # Use a different approach to check for changes
                cursor.execute("SELECT changes()")
                changes = cursor.fetchone()[0]
                if changes > 0:
                    print(f"Set parent for '{child_name}' to '{parent_name}'")
                else:
                    print(f"Warning: Category '{child_name}' not found")
    
    # Make sure we haven't missed any categories
    cursor.execute("""
        SELECT id, name 
        FROM beer_categories 
        WHERE parent_id IS NULL 
        AND name NOT IN ('Ales', 'Lagers', 'Specialty')
    """)
    orphans = cursor.fetchall()
    
    if orphans:
        print("\nWarning: Found categories without parents:")
        for orphan_id, orphan_name in orphans:
            # Skip the main categories which should have NULL parent_id
            if orphan_name in main_categories:
                continue
            print(f"ID: {orphan_id}, Name: {orphan_name}")
            # Default these to the "Other" category
            cursor.execute("SELECT id FROM beer_categories WHERE name = 'Specialty'")
            other_result = cursor.fetchone()
            if other_result:
                cursor.execute("UPDATE beer_categories SET parent_id = ? WHERE id = ?", 
                              (other_result[0], orphan_id))
                print(f"  - Set parent for '{orphan_name}' to 'Specialty'")
    
    # Commit changes and close connection
    conn.commit()
    print("\nSummary of categories after organization:")
    cursor.execute("""
    SELECT p.name as parent, c.name as child 
    FROM beer_categories c
    LEFT JOIN beer_categories p ON c.parent_id = p.id
    ORDER BY p.name, c.name
    """)
    
    results = cursor.fetchall()
    current_parent = None
    for parent, child in results:
        if parent != current_parent:
            current_parent = parent
            print(f"\n{parent or 'Top-level categories'}:")
        print(f"  - {child}")
    
    conn.close()
    print("\nCategory organization completed successfully.")

if __name__ == '__main__':
    organize_beer_categories()
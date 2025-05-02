import sqlite3
import os

def setup_database(db_path='beers.db'):
    """
    Set up the SQLite database with the required tables for the beer app.
    """
    # Create database directory if it doesn't exist
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
    # Connect to the database (creates it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Connected to database at {db_path}")
    
    # Create beer_categories table with hierarchical structure
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS beer_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        parent_id INTEGER,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (parent_id) REFERENCES beer_categories(id)
    );
    """)
    
    # Create breweries table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS breweries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        location TEXT,
        description TEXT,
        website TEXT,
        image_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Create beers table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS beers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        brewery_id INTEGER,
        type TEXT,
        abv REAL,
        ibu INTEGER,
        description TEXT,
        category_id INTEGER,
        image_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (brewery_id) REFERENCES breweries(id),
        FOREIGN KEY (category_id) REFERENCES beer_categories(id)
    );
    """)
    
    # Create indexes for faster queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_beers_category_id ON beers(category_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_beers_brewery_id ON beers(brewery_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_beer_categories_parent_id ON beer_categories(parent_id);")
    
    print("Database tables and indexes created successfully!")
    
    # Populate beer categories if the table is empty
    cursor.execute("SELECT COUNT(*) FROM beer_categories")
    if cursor.fetchone()[0] == 0:
        print("Populating beer categories...")
        create_beer_hierarchy(conn)
    
    conn.close()

def create_beer_hierarchy(conn):
    """Create a hierarchical structure of beer categories."""
    cursor = conn.cursor()
    
    # First, let's define our top-level categories
    top_level_categories = [
        {"name": "Ales", "description": "Beers fermented with top-fermenting yeast at warmer temperatures."},
        {"name": "Lagers", "description": "Beers fermented with bottom-fermenting yeast at cooler temperatures."},
        {"name": "Mixed Fermentation", "description": "Beers that use multiple fermentation methods or wild yeasts."}
    ]
    
    # Sub-categories organized by parent
    sub_categories = {
        "Ales": [
            {"name": "IPA", "description": "India Pale Ales, characterized by hoppy flavor and aroma."},
            {"name": "Pale Ale", "description": "Light to amber colored ales with balanced hop and malt."},
            {"name": "Amber/Red Ale", "description": "Amber to red colored ales with caramel flavors."},
            {"name": "Brown Ale", "description": "Brown colored ales with nutty, toffee flavors."},
            {"name": "Porter", "description": "Dark ale with roasted malt flavors."},
            {"name": "Stout", "description": "Very dark ales with roasted barley flavors."},
            {"name": "Wheat Beer", "description": "Ales brewed with significant proportion of wheat."},
            {"name": "Belgian", "description": "Belgian-style ales with fruity, spicy characteristics."},
            {"name": "Barleywine", "description": "Strong ales with intense malt flavors."},
            {"name": "Scotch/Scottish Ale", "description": "Malty, caramel-forward ales from Scotland."},
            {"name": "Strong Ale", "description": "Higher alcohol ales with rich flavors."}
        ],
        "Lagers": [
            {"name": "Pilsner", "description": "Pale lagers with crisp hop bitterness."},
            {"name": "Lager", "description": "Clean, crisp beers with subtle flavors."},
            {"name": "Light Lager", "description": "Very pale, light-bodied lagers."},
            {"name": "Bock", "description": "Strong lagers with rich malt flavors."},
            {"name": "Kölsch", "description": "Hybrid ale/lager style, light and crisp."}
        ],
        "Mixed Fermentation": [
            {"name": "Sour", "description": "Tart, acidic beers."},
            {"name": "Wild/Spontaneous", "description": "Beers fermented with wild yeasts like Brettanomyces."},
            {"name": "Farmhouse", "description": "Rustic styles including Saison and Biere de Garde."}
        ]
    }
    
    # Third level categories (IPA types, etc.)
    third_level_categories = {
        "IPA": [
            {"name": "American IPA", "description": "Bold hop flavors with citrus and pine notes."},
            {"name": "English IPA", "description": "More balanced, with earthy hop character."},
            {"name": "Double/Imperial IPA", "description": "Stronger, more intense IPAs."},
            {"name": "Triple IPA", "description": "Very high alcohol and hop intensity."},
            {"name": "Session IPA", "description": "Lower alcohol IPAs with hop character."},
            {"name": "New England IPA", "description": "Hazy, juicy IPAs with low bitterness."}
        ],
        "Stout": [
            {"name": "Dry Stout", "description": "Dry, roasted stouts like Guinness."},
            {"name": "Imperial Stout", "description": "Strong, intense stouts."},
            {"name": "Milk Stout", "description": "Sweet stouts brewed with lactose."},
            {"name": "Oatmeal Stout", "description": "Smooth stouts brewed with oats."},
            {"name": "Coffee Stout", "description": "Stouts with coffee flavor."}
        ]
    }
    
    # Insert top-level categories
    parent_ids = {}
    for category in top_level_categories:
        cursor.execute(
            "INSERT INTO beer_categories (name, description) VALUES (?, ?)",
            (category["name"], category["description"])
        )
        parent_ids[category["name"]] = cursor.lastrowid
        print(f"Added top-level category: {category['name']}")
    
    # Insert sub-categories
    sub_category_ids = {}
    for parent_name, subcategories in sub_categories.items():
        parent_id = parent_ids.get(parent_name)
        if parent_id:
            for subcategory in subcategories:
                cursor.execute(
                    "INSERT INTO beer_categories (name, description, parent_id) VALUES (?, ?, ?)",
                    (subcategory["name"], subcategory["description"], parent_id)
                )
                sub_category_ids[subcategory["name"]] = cursor.lastrowid
                print(f"Added sub-category: {subcategory['name']} under {parent_name}")
    
    # Insert third-level categories
    for parent_name, subcategories in third_level_categories.items():
        parent_id = sub_category_ids.get(parent_name)
        if parent_id:
            for subcategory in subcategories:
                cursor.execute(
                    "INSERT INTO beer_categories (name, description, parent_id) VALUES (?, ?, ?)",
                    (subcategory["name"], subcategory["description"], parent_id)
                )
                print(f"Added third-level category: {subcategory['name']} under {parent_name}")
    
    # Add a special "Other" category for beers that don't fit elsewhere
    cursor.execute(
        "INSERT INTO beer_categories (name, description) VALUES (?, ?)",
        ("Other", "Beers that don't fit into standard categories.")
    )
    print("Added 'Other' category")
    
    conn.commit()
    print("Beer category hierarchy created successfully!")

if __name__ == "__main__":
    # You can specify a different path if needed
    setup_database()

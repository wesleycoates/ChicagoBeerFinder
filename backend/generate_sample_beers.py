import sqlite3
import random

# Connect to the database
conn = sqlite3.connect('/workspaces/ChicagoBeerFinder/backend/beers.db')
cursor = conn.cursor()

# Beer types
beer_types = [
    "IPA", "Double IPA", "Pale Ale", "Stout", "Porter", "Lager", 
    "Pilsner", "Wheat Beer", "Sour", "Saison", "Brown Ale", "Amber Ale",
    "Blonde Ale", "Hefeweizen", "Kölsch", "Belgian Tripel", "Barleywine"
]

# Beer name prefixes
name_prefixes = [
    "Windy City", "Lake Effect", "Michigan Ave", "Loop", "Magnificent Mile",
    "Wrigley", "Sox", "Cubs", "Bears", "Bulls", "Blackhawks", "El Train",
    "South Side", "North Side", "West Loop", "Wicker Park", "Logan Square",
    "Bucktown", "Gold Coast", "River North", "Pilsen", "Lakeview"
]

# Beer name suffixes
name_suffixes = [
    "IPA", "Pale Ale", "Lager", "Stout", "Porter", "Wheat", "Ale",
    "Pilsner", "Saison", "Sour", "Hazy", "Brew", "Craft", "Special", 
    "Reserve", "Limited", "Seasonal", "Session", "Imperial", "Double"
]

# Beer description templates
description_templates = [
    "A {strength} {beer_type} with notes of {flavor1} and {flavor2}.",
    "This {beer_type} offers a {mouthfeel} mouthfeel with {flavor1} undertones.",
    "A {location} twist on a classic {beer_type}, featuring {flavor1} and {flavor2}.",
    "Brewed with {ingredient} hops, this {beer_type} delivers {flavor1} flavors.",
    "A {season} favorite, this {beer_type} balances {flavor1} and {flavor2}."
]

# Flavor profiles
flavors = [
    "citrus", "pine", "tropical fruit", "grapefruit", "mango", "peach", 
    "coffee", "chocolate", "caramel", "toffee", "vanilla", "oak", 
    "honey", "floral", "spicy", "earthy", "grassy", "herbal", "berry", 
    "stone fruit", "melon", "biscuit", "bread", "toast", "nutty"
]

# Beer characteristics
strengths = ["light", "refreshing", "bold", "robust", "strong", "sessionable", "malty", "hoppy"]
mouthfeels = ["smooth", "creamy", "full", "light", "rich", "velvety", "silky"]
locations = ["Chicago", "Midwestern", "American", "traditional", "modern", "craft"]
seasons = ["summer", "winter", "spring", "fall", "year-round"]
ingredients = ["Citra", "Mosaic", "Cascade", "Centennial", "Amarillo", "Galaxy", "Simcoe", "local"]

# Get all breweries
cursor.execute("SELECT id, name FROM breweries")
breweries = cursor.fetchall()

beer_count = 0
# For each brewery, add 2-5 beers
for brewery_id, brewery_name in breweries:
    # Check if brewery already has beers
    cursor.execute("SELECT COUNT(*) FROM beer_locations WHERE brewery_id = ?", (brewery_id,))
    existing_beers = cursor.fetchone()[0]
    
    if existing_beers > 0:
        print(f"Brewery {brewery_name} already has {existing_beers} beers. Skipping.")
        continue
    
    # Add 2-5 random beers
    num_beers = random.randint(2, 5)
    print(f"Adding {num_beers} beers to {brewery_name}...")
    
    for _ in range(num_beers):
        # Generate beer name
        prefix = random.choice(name_prefixes)
        suffix = random.choice(name_suffixes)
        beer_name = f"{prefix} {suffix}"
        
        # Generate beer type
        beer_type = random.choice(beer_types)
        
        # Generate ABV (3.5% to 9.5%)
        abv = round(random.uniform(3.5, 9.5), 1)
        
        # Generate IBU (10 to 100)
        ibu = random.randint(10, 100)
        
        # Generate rating (3.2 to 4.8)
        rating = round(random.uniform(3.2, 4.8), 1)
        
        # Generate description
        template = random.choice(description_templates)
        flavor1 = random.choice(flavors)
        flavor2 = random.choice([f for f in flavors if f != flavor1])
        
        description = template.format(
            beer_type=beer_type.lower(),
            strength=random.choice(strengths),
            flavor1=flavor1,
            flavor2=flavor2,
            mouthfeel=random.choice(mouthfeels),
            location=random.choice(locations),
            season=random.choice(seasons),
            ingredient=random.choice(ingredients)
        )
        
        # Add beer to database
        try:
            cursor.execute('''
                INSERT INTO beers (name, type, abv, ibu, description, rating_score)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (beer_name, beer_type, abv, ibu, description, rating))
            
            beer_id = cursor.lastrowid
            
            # Link beer to brewery
            cursor.execute('''
                INSERT INTO beer_locations (beer_id, brewery_id)
                VALUES (?, ?)
            ''', (beer_id, brewery_id))
            
            beer_count += 1
            
        except sqlite3.Error as e:
            print(f"Error adding beer {beer_name}: {e}")

# Commit changes
conn.commit()
conn.close()

print(f"Added {beer_count} sample beers to the database")

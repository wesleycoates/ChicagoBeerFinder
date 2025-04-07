import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import datetime

class DemoBrewingScraper:
    def __init__(self):
        self.brewery_name = "Demo Brewing"
        self.brewery_url = "https://www.demobrewery.com/menu"  # Replace with actual URL
        self.brewery_address = "1763 Berteau Ave"  # Replace with actual address
        self.brewery_city = "Chicago"
        self.brewery_state = "IL"
        self.brewery_website = "https://demobrewing.com"  # Replace with actual website
        
        # Full HTML content
        self.html_content = """<div class="MuiBox-root css-1s2y5gw"><div class="MuiBox-root css-157mcdf"><div class="MuiBox-root css-u4p24i"><div class="MuiBox-root css-7lq03x"></div><div class="MuiBox-root css-0"><h3 class="MuiTypography-root MuiTypography-h3 css-5s5015">Our Beers</h3></div><div class="MuiBox-root css-7lq03x"></div></div><div class="MuiGrid-root MuiGrid-container MuiGrid-spacing-xs-4 css-1df6gfj"><div class="MuiGrid-root MuiGrid-item MuiGrid-grid-mobile-12 MuiGrid-grid-tablet-6 css-rvmsug"><p class="MuiTypography-root MuiTypography-body1 css-7qoyso">Tidal Flex</p><p class="MuiTypography-root MuiTypography-body1 css-70kg74">Breakfast Stout - 5% ABV</p><p class="MuiTypography-root MuiTypography-body1 css-1mztlj7">Brewed in collaboration with Dark Matter Coffee, "Tidal Flex" is a rich, smooth brew delivering bold notes of coffee and subtle chocolate undertones, featuring their "Agua" single-origin roast. At 5% ABV, it's a perfectly balanced and sessionable way to start your day—or any time you need a cozy pick-me-up.</p><div class="MuiBox-root css-1yuhvjn"><div class="MuiBox-root css-k008qs"><p class="MuiTypography-root MuiTypography-body1 css-of3ws9">10oz English Pub Glass</p><p class="MuiTypography-root MuiTypography-body1 css-1vj3ocr">$5.50</p></div><div class="MuiBox-root css-k008qs"><p class="MuiTypography-root MuiTypography-body1 css-of3ws9">16oz Mug</p><p class="MuiTypography-root MuiTypography-body1 css-1vj3ocr">$7.50</p></div></div></div><div class="MuiGrid-root MuiGrid-item MuiGrid-grid-mobile-12 MuiGrid-grid-tablet-6 css-rvmsug"><p class="MuiTypography-root MuiTypography-body1 css-7qoyso">Wheat Your Heart Out</p><p class="MuiTypography-root MuiTypography-body1 css-70kg74">American Wheat Beer - 5% ABV</p><p class="MuiTypography-root MuiTypography-body1 css-1mztlj7">Wheat Your Heart Out is a smooth and refreshing American Wheat Ale with forward malt character, complemented by a touch of coriander and orange zest for a bright, citrusy finish.

Garnish with an orange and 🌾 🫵 💛 👉</p><div class="MuiBox-root css-1yuhvjn"><div class="MuiBox-root css-k008qs"><p class="MuiTypography-root MuiTypography-body1 css-of3ws9">10oz English Pub Glass</p><p class="MuiTypography-root MuiTypography-body1 css-1vj3ocr">$5</p></div><div class="MuiBox-root css-k008qs"><p class="MuiTypography-root MuiTypography-body1 css-of3ws9">16oz Aspen</p><p class="MuiTypography-root MuiTypography-body1 css-1vj3ocr">$7</p></div></div></div><div class="MuiGrid-root MuiGrid-item MuiGrid-grid-mobile-12 MuiGrid-grid-tablet-6 css-rvmsug"><p class="MuiTypography-root MuiTypography-body1 css-7qoyso">Czech Yo Self</p><p class="MuiTypography-root MuiTypography-body1 css-70kg74">Dark Czech Lager - 5.4% ABV</p><p class="MuiTypography-root MuiTypography-body1 css-1mztlj7">Rich malt-forward profile, offering notes of toasted bread and subtle caramel sweetness. Balanced with the delicate herbal aroma of Hallertauer and Saaz hops, it finishes smooth and satisfying, making it the perfect winter lager.</p><div class="MuiBox-root css-1yuhvjn"><div class="MuiBox-root css-k008qs"><p class="MuiTypography-root MuiTypography-body1 css-of3ws9">10oz English Pub Glass</p><p class="MuiTypography-root MuiTypography-body1 css-1vj3ocr">$5.50</p></div><div class="MuiBox-root css-k008qs"><p class="MuiTypography-root MuiTypography-body1 css-of3ws9">16oz Mug</p><p class="MuiTypography-root MuiTypography-body1 css-1vj3ocr">$7.50</p></div></div></div><div class="MuiGrid-root MuiGrid-item MuiGrid-grid-mobile-12 MuiGrid-grid-tablet-6 css-rvmsug"><p class="MuiTypography-root MuiTypography-body1 css-7qoyso">Cold Pizza</p><p class="MuiTypography-root MuiTypography-body1 css-70kg74">American Amber Ale - 5.9% ABV</p><p class="MuiTypography-root MuiTypography-body1 css-1mztlj7">This amber ale was made with a huge assortment of base and specialty grains that give it a balanced malt backbone, followed up with columbus and mosaic hops for a floral finish. So many different malts contributed to the grain bill that it's almost as if we used the leftovers from other brews... 🤔</p><div class="MuiBox-root css-1yuhvjn"><div class="MuiBox-root css-k008qs"><p class="MuiTypography-root MuiTypography-body1 css-of3ws9">10oz English Pub Glass</p><p class="MuiTypography-root MuiTypography-body1 css-1vj3ocr">$5.50</p></div><div class="MuiBox-root css-k008qs"><p class="MuiTypography-root MuiTypography-body1 css-of3ws9">16oz Imperial Pint</p><p class="MuiTypography-root MuiTypography-body1 css-1vj3ocr">$7.50</p></div></div></div><div class="MuiGrid-root MuiGrid-item MuiGrid-grid-mobile-12 MuiGrid-grid-tablet-6 css-rvmsug"><p class="MuiTypography-root MuiTypography-body1 css-7qoyso">Voyager to Europa</p><p class="MuiTypography-root MuiTypography-body1 css-70kg74">Imperial Breakfast Stout - 8% ABV</p><p class="MuiTypography-root MuiTypography-body1 css-1mztlj7">Imperial breakfast stout made with a double dose of coffee and cold brew coffee, maple syrup, and oatmeal. In addition to the pours in the taproom, this was bottled and is for same in 22oz bottles to-go.</p><div class="MuiBox-root css-1yuhvjn"><div class="MuiBox-root css-k008qs"><p class="MuiTypography-root MuiTypography-body1 css-of3ws9">22oz Bomber</p><p class="MuiTypography-root MuiTypography-body1 css-1vj3ocr">$14</p></div></div></div><div class="MuiGrid-root MuiGrid-item MuiGrid-grid-mobile-12 MuiGrid-grid-tablet-6 css-rvmsug"><p class="MuiTypography-root MuiTypography-body1 css-7qoyso">Ambrosia</p><p class="MuiTypography-root MuiTypography-body1 css-70kg74">Double NEIPA - 9.3% ABV</p><p class="MuiTypography-root MuiTypography-body1 css-1mztlj7">Huge 9.3% Hazy Double IPA hopped with Nectaron, Citra, and Galaxy hops, offering juicy notes of nectarine and sweet orange.</p><div class="MuiBox-root css-1yuhvjn"><div class="MuiBox-root css-k008qs"><p class="MuiTypography-root MuiTypography-body1 css-of3ws9">10oz English Pub Glass</p><p class="MuiTypography-root MuiTypography-body1 css-1vj3ocr">$6.25</p></div><div class="MuiBox-root css-k008qs"><p class="MuiTypography-root MuiTypography-body1 css-of3ws9">16oz Footed Tear Drop</p><p class="MuiTypography-root MuiTypography-body1 css-1vj3ocr">$8.50</p></div></div></div></div></div></div>"""

    def scrape(self):
        # Parse the HTML
        soup = BeautifulSoup(self.html_content, 'html.parser')
        
        # Find beer elements
        beer_elements = soup.find_all('div', class_='MuiGrid-root MuiGrid-item MuiGrid-grid-mobile-12 MuiGrid-grid-tablet-6 css-rvmsug')
        
        beers = []
        
        for beer_element in beer_elements:
            try:
                # Extract beer name
                name_element = beer_element.find('p', class_='MuiTypography-root MuiTypography-body1 css-7qoyso')
                beer_name = name_element.text.strip() if name_element else "Unknown Beer"
                
                # Extract type and ABV
                type_abv_element = beer_element.find('p', class_='MuiTypography-root MuiTypography-body1 css-70kg74')
                type_abv_text = type_abv_element.text.strip() if type_abv_element else ""
                
                # Extract description
                description_element = beer_element.find('p', class_='MuiTypography-root MuiTypography-body1 css-1mztlj7')
                description = description_element.text.strip() if description_element else ""
                
                # Parse type and ABV using regex
                type_abv_match = re.match(r'(.+?)\s*-\s*(\d+(?:\.\d+)?)%\s*ABV', type_abv_text, re.IGNORECASE)
                
                if type_abv_match:
                    beer_type = type_abv_match.group(1).strip()
                    abv = float(type_abv_match.group(2))
                else:
                    # Fallback parsing
                    parts = type_abv_text.split('-')
                    beer_type = parts[0].strip()
                    abv_match = re.search(r'(\d+(?:\.\d+)?)%', type_abv_text, re.IGNORECASE)
                    abv = float(abv_match.group(1)) if abv_match else None
                
                # Construct beer dictionary
                beer = {
                    'name': beer_name,
                    'type': beer_type,
                    'abv': abv,
                    'description': description,
                    'brewery': self.brewery_name,
                    'address': self.brewery_address,
                    'city': self.brewery_city,
                    'state': self.brewery_state,
                    'website': self.brewery_website
                }
                
                # Add to beers list if not already present
                if not any(b['name'] == beer_name for b in beers):
                    beers.append(beer)
                    print(f"Added {beer_name}")
            
            except Exception as e:
                print(f"Error processing beer: {e}")
        
        print(f"Total beers found: {len(beers)}")
        return beers
    
    def save_to_json(self):
        beers = self.scrape()
        
        if not beers:
            print(f"No beers found for {self.brewery_name}")
            return
        
        # Create the output directory if it doesn't exist
        output_dir = "scraped_data"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate a filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(output_dir, f"{self.brewery_name.replace(' ', '_')}_{timestamp}.json")
        
        # Write the beers to a JSON file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(beers, f, indent=4)
        
        print(f"Saved {len(beers)} beers to {filename}")
        return filename

# When running the file directly
if __name__ == "__main__":
    scraper = DemoBrewingScraper()
    output_file = scraper.save_to_json()
    
    # Print the first few beers to verify
    if output_file:
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print("\nSample of beers scraped:")
            for i, beer in enumerate(data):  # Show all beers
                print(f"\nBeer {i+1}: {beer['name']}")
                print(f"Type: {beer['type']}")
                print(f"ABV: {beer['abv']}%")
                print(f"Description: {beer['description'][:100]}...")
import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

def parse_begyle_beers(html_content):
    """
    Parse Begyle Brewing beers from the provided HTML content
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    beers = []
    
    # Find all beer item wrappers
    beer_items = soup.find_all('div', class_='item-wrapper')
    
    for beer_item in beer_items:
        # Skip non-Begyle beers (like Go Brewing or Liquid Death)
        brewery_location = beer_item.find('span', class_='item-producer-location')
        if not brewery_location or brewery_location.text.strip() != 'Chicago, IL':
            continue
        
        # Extract beer name
        name_elem = beer_item.find('h3', class_='item-name')
        name = name_elem.text.strip() if name_elem else 'Unknown Beer'
        
        # Extract beer type/style
        type_elem = beer_item.find('span', class_='item-style')
        beer_type = type_elem.text.strip() if type_elem else 'Unknown'
        
        # Extract ABV
        abv_elem = beer_item.find('span', class_='item-abv')
        abv_str = abv_elem.text.strip().rstrip('%') if abv_elem else None
        abv = float(abv_str) if abv_str else None
        
        # Extract description
        desc_elem = beer_item.find('div', class_='item-description')
        description = desc_elem.text.strip() if desc_elem else ''
        
        # Extract serving details
        serving_elem = beer_item.find('p', class_='item-serving')
        serving_details = {}
        if serving_elem:
            serving_size = serving_elem.find('span', class_='serving-size')
            serving_type = serving_elem.find('span', class_='serving-type')
            serving_price = serving_elem.find('span', class_='serving-price')
            
            serving_details = {
                'size': serving_size.text.strip() if serving_size else '',
                'type': serving_type.text.strip() if serving_type else '',
                'price': serving_price.text.strip() if serving_price else ''
            }
        
        beers.append({
            'name': name,
            'type': beer_type,
            'abv': abv,
            'description': description,
            'brewery': 'Begyle Brewing',
            'address': '1800 W Cuyler Ave',
            'city': 'Chicago',
            'state': 'IL',
            'website': 'https://begylebrewing.com',
            'serving': serving_details
        })
    
    return beers

def save_to_json(beers):
    """
    Save scraped beers to a JSON file in the scraped_data directory
    """
    # Ensure scraped_data directory exists
    output_dir = 'scraped_data'
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'begyle_beers_{timestamp}.json'
    filepath = os.path.join(output_dir, filename)
    
    try:
        # Save to JSON file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(beers, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully saved {len(beers)} Begyle Brewing beers to {filepath}")
        return filepath
    
    except Exception as e:
        print(f"Error saving JSON file: {e}")
        return None

def main():
    """
    Main function to parse and save Begyle Brewing beers from a local file
    """
    # Read the HTML file
    with open('begylepaste.txt', 'r', encoding='utf-8') as file:
        html_content = file.read()
    
    # Parse beers
    beers = parse_begyle_beers(html_content)
    
    # Save to JSON
    if beers:
        saved_file = save_to_json(beers)
        
        # Print out the beers for verification
        if saved_file:
            for beer in beers:
                print(f"Beer: {beer['name']}")
                print(f"Type: {beer['type']}")
                print(f"ABV: {beer['abv']}%")
                print(f"Description: {beer['description'][:100]}...")
                print(f"Serving: {beer['serving']}")
                print("---")

if __name__ == '__main__':
    main()
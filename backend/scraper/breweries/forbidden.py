import os
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup

def scrape_forbidden_root_from_html(html_file=None, html_content=None):
    """
    Scrape Forbidden Root beer information from either an HTML file or HTML content.
    
    Args:
        html_file (str, optional): Path to HTML file containing beer info
        html_content (str, optional): HTML content string containing beer info
    
    Returns:
        list: List of dictionaries with beer information
    """
    print("Starting Forbidden Root HTML parser...")
    
    # Create a list to store beer information
    beers = []
    
    try:
        # Load HTML content from file or use provided content
        if html_file and os.path.exists(html_file):
            print(f"Reading HTML from file: {html_file}")
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
        elif not html_content:
            print("No HTML content provided.")
            return beers
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all beer container items
        beer_items = soup.select('div.jet-listing-grid__item')
        print(f"Found {len(beer_items)} potential beer containers")
        
        # Process each beer item
        for item in beer_items:
            try:
                # Find the beer container
                beer_container = item.select_one('div.kc-beer-cont')
                if not beer_container:
                    continue
                
                # Extract category
                category_elem = item.select_one('h2.elementor-heading-title')
                category = category_elem.text.strip() if category_elem else "Unknown"
                
                # Extract beer name
                name_elem = beer_container.select_one('div.e-con-inner h2.elementor-heading-title')
                if not name_elem:
                    continue
                name = name_elem.text.strip()
                
                # Extract ABV
                abv = "N/A"
                abv_elements = beer_container.select('div.elementor-heading-title')
                for elem in abv_elements:
                    if "%" in elem.text:
                        abv = elem.text.strip()
                        break
                
                # Extract beer style
                style = "N/A"
                style_elem = beer_container.select_one('h2.kc-beer-name')
                if style_elem:
                    style = style_elem.text.strip()
                
                # Create beer info dictionary
                beer_info = {
                    "name": name,
                    "abv": abv,
                    "style": style,
                    "category": category,
                    "brewery": "Forbidden Root",
                    "scrape_date": datetime.now().strftime("%Y-%m-%d")
                }
                
                beers.append(beer_info)
                print(f"Extracted beer: {name} - ABV: {abv} - Style: {style} - Category: {category}")
                
            except Exception as e:
                print(f"Error processing beer item: {e}")
        
        print(f"Total beers scraped: {len(beers)}")
        
        # Create directory for scraped data if it doesn't exist
        if not os.path.exists("scraped_data"):
            os.makedirs("scraped_data")
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scraped_data/forbidden_root_{timestamp}.json"
        
        # Save the data to a JSON file
        with open(filename, "w") as f:
            json.dump(beers, f, indent=4)
        
        print(f"Data saved to {filename}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    
    return beers

def main():
    # Save the HTML content to a file first
    html_content = """
    [PASTE THE HTML CONTENT HERE]
    """
    
    # Or use a file path if you've saved the HTML
    html_file = "forbiddenpaste.txt"  # Update with your file path if needed
    
    # Run the scraper
    scrape_forbidden_root_from_html(html_file=html_file)

if __name__ == "__main__":
    main()
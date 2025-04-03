import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import datetime

class DovetailScraper:
    def __init__(self):
        self.url = "https://www.dovetailbrewery.com/beers"
        self.brewery_name = "Dovetail Brewery"
        self.output_dir = "scraped_data"
        
    def scrape(self):
        # Make the request to the brewery website
        print(f"Scraping {self.brewery_name}...")
        response = requests.get(self.url)
        
        # Check if the request was successful
        if response.status_code != 200:
            print(f"Failed to retrieve data from {self.url}")
            return None
            
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all beer entries
        beers = []
        
        # Looking for h4 elements (beer names)
        beer_headers = soup.find_all('h4', style="white-space:pre-wrap;")
        
        for header in beer_headers:
            beer_name = header.text.strip()
            
            # Get the description from the next paragraph element
            desc_elem = header.find_next('p', style="white-space:pre-wrap;")
            if desc_elem:
                description = desc_elem.text.strip()
                
                # Extract ABV using regex - look for patterns like "4.8% ABV" or "ABV 7%"
                abv_match = re.search(r'(\d+\.?\d*)%\s+ABV|ABV\s+(\d+\.?\d*)%', description)
                if abv_match:
                    # Get whichever group matched (either the first or second pattern)
                    abv_value = abv_match.group(1) or abv_match.group(2)
                    abv = float(abv_value)
                    # Remove the ABV portion from the description
                    description = re.sub(r'\s*\d+\.?\d*%\s+ABV\s*|\s*ABV\s+\d+\.?\d*%\s*', '', description).strip()
                else:
                    abv = None
                
                # For Dovetail, the beer type is the same as the name
                beer_type = beer_name
                
                # Skip beers that are only release announcements
                if description.startswith("RELEASED IN") and len(description) < 50:
                    # Either skip completely or add a note that it's a seasonal release
                    description = f"Seasonal release: {description}"
                
                beers.append({
                    "name": beer_name,
                    "type": beer_type,
                    "abv": abv,
                    "description": description,
                    "brewery": self.brewery_name
                })
        
        # Get current timestamp
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        
        # Return both beers and timestamp
        return beers, timestamp
        
    def save_to_json(self, beers, timestamp):
        if not beers:
            print("No beers to save!")
            return
            
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        # Use timestamp for filename
        filename = f"{self.output_dir}/dovetail_{timestamp}.json"
        
        # Create data structure with metadata
        data = {
            "metadata": {
                "brewery": self.brewery_name,
                "scraped_at": timestamp,
                "url": self.url
            },
            "beers": beers
        }
        
        # Save the beers to a JSON file with proper encoding for special characters
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        print(f"Saved {len(beers)} beers to {filename}")
        
    def run(self):
        result = self.scrape()
        if result:
            beers, timestamp = result
            self.save_to_json(beers, timestamp)
            return beers
        return None

# If running this file directly
if __name__ == "__main__":
    scraper = DovetailScraper()
    scraper.run()
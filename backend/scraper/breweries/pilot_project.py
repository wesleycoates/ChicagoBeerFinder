# pilot_project_scraper.py
import requests
from bs4 import BeautifulSoup
import json
import os
import datetime
import re

class PilotProjectScraper:
    def __init__(self):
        self.brewery_name = "Pilot Project Brewing"
        self.brewery_location = "Logan Square, Chicago, IL"
        self.brewery_url = "https://www.pilotprojectbrewing.com"
        self.beer_url = "https://www.pilotprojectbrewing.com/logansquarebeer"
        self.output_dir = "scraped_data"
    
    def scrape(self):
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # Get current timestamp for filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{self.output_dir}/pilot_project_{timestamp}.json"
        
        # Fetch the beer page
        print(f"Fetching beer information from {self.beer_url}...")
        response = requests.get(self.beer_url)
        
        if response.status_code != 200:
            print(f"Failed to retrieve page: {response.status_code}")
            return None
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all beer descriptions (based on the HTML structure you provided)
        beer_paragraphs = soup.find_all('p', style='white-space:pre-wrap;')
        
        beers = []
        for paragraph in beer_paragraphs:
            # Skip paragraphs that don't contain beer information
            if not paragraph.strong:
                continue
                
            # Extract beer information
            beer_info = paragraph.strong.text.strip()
            
            # Example beer_info: "Serpente - Brewer's Kitchen // Italian Pilsner // 4.8%"
            # Let's split it and parse more carefully
            
            try:
                # First try to split by '//' to separate the beer name, style, and ABV sections
                parts = beer_info.split('//')
                
                if len(parts) >= 3:  # We have at least three parts
                    # First part contains beer name, might have a dash or not
                    beer_name = parts[0].strip()
                    if '-' in beer_name:
                        beer_name = beer_name.split('-')[0].strip()
                    
                    # Second part is the beer style
                    beer_style = parts[1].strip()
                    
                    # Third part has the ABV, need to extract just the number
                    abv_part = parts[2].strip()
                    # Extract just the number using regex
                    abv_match = re.search(r'(\d+\.?\d*)%?', abv_part)
                    if abv_match:
                        beer_abv = float(abv_match.group(1))
                    else:
                        beer_abv = None
                else:
                    # If we can't parse it properly, just use the whole thing as the name
                    beer_name = beer_info
                    beer_style = "Unknown"
                    beer_abv = None
                
                # Extract description from the <em> tag if it exists
                description = ""
                if paragraph.em:
                    description = paragraph.em.text.strip()
                
                # Extract pricing information if available
                pricing = ""
                if "For Here:" in paragraph.text:
                    pricing_text = paragraph.text.split("For Here:")[1].strip()
                    pricing = pricing_text
                
                beer_data = {
                    "name": beer_name,
                    "style": beer_style,
                    "abv": beer_abv,
                    "description": description,
                    "pricing": pricing,
                    "brewery": self.brewery_name,
                    "location": self.brewery_location,
                    "brewery_url": self.brewery_url
                }
                
                beers.append(beer_data)
                
            except Exception as e:
                print(f"Error processing beer: {beer_info}")
                print(f"Error details: {str(e)}")
                continue
        
        # Create final data structure
        brewery_data = {
            "brewery": self.brewery_name,
            "location": self.brewery_location,
            "url": self.brewery_url,
            "beers": beers,
            "scraped_date": datetime.datetime.now().isoformat()
        }
        
        # Save to JSON file
        with open(output_file, 'w') as f:
            json.dump(brewery_data, f, indent=2)
        
        print(f"Scraped {len(beers)} beers from {self.brewery_name}")
        print(f"Data saved to {output_file}")
        
        return brewery_data

if __name__ == "__main__":
    scraper = PilotProjectScraper()
    scraper.scrape()
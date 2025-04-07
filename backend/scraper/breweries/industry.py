import os
import json
import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup

class IndustryAlesScraper:
    def __init__(self):
        self.brewery_name = "Industry Ales"
        self.brewery_location = "Chicago, IL"
        self.brewery_website = "https://www.industryales.com"
        self.brewery_address = "213 S Wabash Ave, Chicago, IL 60604"
        self.beer_list_url = "https://www.industryales.com/beerlist"
    
    def fetch_beer_list(self):
        """Fetch the beer list page from the brewery website"""
        try:
            response = requests.get(self.beer_list_url)
            response.raise_for_status()  # Raise an exception for 4XX/5XX status codes
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching beer list: {e}")
            return None
    
    def scrape_beers(self):
        """Scrape beer information from the brewery website"""
        html_content = self.fetch_beer_list()
        if not html_content:
            return []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        beers = []
        
        # Find all beer menu items
        menu_items = soup.select('.menu-item')
        
        for item in menu_items:
            # Extract beer name
            title_elem = item.select_one('.menu-item-title')
            if not title_elem:
                continue
            
            title_text = title_elem.text.strip()
            
            # Skip section headers like "--CAN OFFERINGS--"
            if title_text.startswith('--'):
                continue
            
            # Extract beer type and ABV
            description_elem = item.select_one('.menu-item-description')
            if not description_elem:
                continue
            
            description_text = description_elem.text.strip()
            
            # Parse beer type and ABV
            beer_type = None
            abv = None
            
            if ',' in description_text:
                parts = description_text.split(',')
                beer_type = parts[0].strip()
                
                # Extract ABV
                abv_match = re.search(r'(\d+\.\d+|\d+)%', description_text)
                if abv_match:
                    abv = float(abv_match.group(1))
            
            # Extract beer description
            details_elem = item.select_one('.menu-item-price-bottom')
            detailed_description = details_elem.text.strip() if details_elem else None
            
            # Handle non-alcoholic beers
            is_non_alcoholic = False
            if title_text.lower().startswith('non alcoholic:'):
                is_non_alcoholic = True
                title_text = title_text.replace('Non Alcoholic:', '').strip()
            
            # Handle can offerings
            is_can = False
            if '(Can)' in title_text or '(16oz. Can)' in title_text or '(12oz. Can)' in title_text:
                is_can = True
                title_text = title_text.split('(')[0].strip()
            
            # Check for collaborations
            brewery_name = self.brewery_name
            if 'Collaboration' in description_text:
                collaboration_match = re.search(r'([\w\s/]+)Collaboration', description_text)
                if collaboration_match:
                    brewery_name = f"{self.brewery_name} & {collaboration_match.group(1).strip()}"
            
            beer = {
                "name": title_text,
                "type": beer_type,
                "abv": abv,
                "description": detailed_description,
                "brewery": brewery_name,
                "location": self.brewery_location,
                "address": self.brewery_address,
                "website": self.brewery_website,
                "is_can": is_can,
                "is_non_alcoholic": is_non_alcoholic,
                "scraped_date": datetime.now().strftime("%Y-%m-%d")
            }
            
            beers.append(beer)
        
        return beers
    
    def save_to_json(self, output_dir="scraped_data"):
        """Save scraped beer data to a JSON file"""
        beers = self.scrape_beers()
        
        if not beers:
            print(f"No beers found for {self.brewery_name}")
            return None
        
        # Create directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/industry_ales_{timestamp}.json"
        
        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(beers, f, indent=4)
        
        print(f"Scraped {len(beers)} beers from {self.brewery_name}")
        print(f"Data saved to {filename}")
        
        return filename

# For direct testing from terminal
if __name__ == "__main__":
    scraper = IndustryAlesScraper()
    scraper.save_to_json()
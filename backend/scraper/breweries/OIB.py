import requests
from bs4 import BeautifulSoup
import json
import os
import time
from datetime import datetime
import random

class OldIrvingBreweryScraper:
    def __init__(self):
        self.base_url = "https://oldirvingbrewing.com"
        self.beer_list_url = f"{self.base_url}/beer/"
        self.output_dir = "scraped_data"
        
        # User agent to mimic a browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://oldirvingbrewing.com/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def make_request(self, url, retry_count=3):
        """Make a request with retries and random delays"""
        for attempt in range(retry_count):
            try:
                # Random delay between 2-5 seconds to avoid triggering rate limits
                if attempt > 0:
                    delay = 2 + random.random() * 3
                    print(f"  Retrying in {delay:.1f} seconds (attempt {attempt+1}/{retry_count})")
                    time.sleep(delay)
                
                response = requests.get(url, headers=self.headers, timeout=10)
                
                if response.status_code == 200:
                    return response
                
                print(f"  Request failed with status code: {response.status_code}")
                
                # If we get a 403 or 429, we need to wait longer
                if response.status_code in [403, 429]:
                    delay = 5 + random.random() * 5
                    print(f"  Rate limited. Waiting {delay:.1f} seconds")
                    time.sleep(delay)
            
            except Exception as e:
                print(f"  Request error: {str(e)}")
        
        return None
    
    def scrape(self):
        # Get the main beer page
        print(f"Fetching beer list from {self.beer_list_url}")
        response = self.make_request(self.beer_list_url)
        
        if not response:
            print("Failed to fetch beer list after multiple attempts")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all beer buttons on the main page
        beer_buttons = soup.find_all('span', class_='elementor-button-text')
        
        beers_data = []
        for button in beer_buttons:
            beer_name = button.text.strip()
            if not beer_name:  # Skip empty buttons
                continue
                
            print(f"Found beer: {beer_name}")
            
            # Look for the beer type in the next div
            beer_info_container = button.find_parent('div').find_parent('div').find_parent('div').find_next_sibling('div')
            beer_type = "Unknown"
            if beer_info_container:
                type_element = beer_info_container.find('p')
                if type_element:
                    beer_type = type_element.text.strip()
            
            # Find the link to the beer detail page
            link_element = button.find_parent('a')
            if not link_element:
                print(f"  Could not find link for {beer_name}, skipping")
                continue
                
            beer_url = link_element.get('href')
            if not beer_url:
                print(f"  Empty URL for {beer_name}, skipping")
                continue
                
            if not beer_url.startswith('http'):
                beer_url = f"{self.base_url}{beer_url}"
            
            # Get beer details
            beer_details = self.get_beer_details(beer_url, beer_name, beer_type)
            if beer_details:
                beers_data.append(beer_details)
            
            # Be nice to the server
            time.sleep(2 + random.random() * 2)
        
        # Save the data
        self.save_data(beers_data)
        return beers_data
    
    def get_beer_details(self, beer_url, beer_name, beer_type):
        print(f"  Fetching details from {beer_url}")
        try:
            response = self.make_request(beer_url)
            if not response:
                print(f"  Failed to fetch beer details after multiple attempts")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract beer description
            description = ""
            desc_element = soup.find('span', style="white-space: pre-wrap;")
            if desc_element:
                description = desc_element.text.strip()
            
            # Extract ABV, IBU, SRM
            abv = "Unknown"
            ibu = "Unknown"
            srm = "Unknown"
            
            icon_list_items = soup.find_all('span', class_='elementor-icon-list-text')
            for item in icon_list_items:
                text = item.text.strip()
                if text.startswith('ABV:'):
                    abv = text.replace('ABV:', '').strip()
                elif text.startswith('IBU:'):
                    ibu = text.replace('IBU:', '').strip()
                elif text.startswith('SRM:'):
                    srm = text.replace('SRM:', '').strip()
            
            # Convert ABV to number for consistency with other scrapers
            try:
                abv_value = float(abv.replace('%', ''))
            except (ValueError, AttributeError):
                abv_value = None
            
            # Get current timestamp
            timestamp = datetime.now().isoformat()
            
            return {
                'name': beer_name,
                'type': beer_type,
                'abv': abv_value,
                'abv_text': abv,
                'ibu': ibu,
                'srm': srm,
                'description': description,
                'brewery': 'Old Irving Brewing',
                'url': beer_url,
                'scraped_date': datetime.now().strftime('%Y-%m-%d'),
                'timestamp': timestamp
            }
        except Exception as e:
            print(f"  Error getting details for {beer_name}: {str(e)}")
            return None
    
    def save_data(self, beers_data):
        if not beers_data:
            print("No beer data to save")
            return
        
        # Format filename with date
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = os.path.join(self.output_dir, f"oldirving_{date_str}.json")
        
        print(f"Saving {len(beers_data)} beers to {filename}")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(beers_data, f, indent=2)

# Run the scraper if this file is executed directly
if __name__ == "__main__":
    print("Starting Old Irving Brewery scraper...")
    scraper = OldIrvingBreweryScraper()
    beers = scraper.scrape()
    print(f"Finished scraping {len(beers) if beers else 0} beers")
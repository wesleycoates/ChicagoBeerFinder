import requests
import sqlite3
import os
import time
import json
import re
from bs4 import BeautifulSoup
from random import randint
from urllib.parse import urljoin
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='scraper.log'
)

class ChicagoBeerScraper:
    def __init__(self, db_path=None):
        """Initialize the scraper with database connection"""
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'beers.db')
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def __del__(self):
        """Close database connection on object destruction"""
        if hasattr(self, 'conn'):
            self.conn.close()
    
    def _get_soup(self, url):
        """Get BeautifulSoup object from URL with error handling and rate limiting"""
        try:
            # Add random delay to avoid hitting rate limits
            time.sleep(randint(1, 3))
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            logging.error(f"Error fetching {url}: {e}")
            return None
    
    def scrape_chicago_brewery_list(self):
        """Scrape a list of Chicago breweries from Beer Advocate"""
        # Beer Advocate's Chicago brewery list
        url = "https://www.beeradvocate.com/place/city/18/"
        soup = self._get_soup(url)
        
        breweries = []
        if not soup:
            return breweries
        
        # Find brewery listings
        brewery_listings = soup.select('#ba-content table tr')
        for row in brewery_listings[1:]:  # Skip header row
            cols = row.find_all('td')
            if len(cols) >= 2:
                brewery_name = cols[0].text.strip()
                brewery_url = urljoin("https://www.beeradvocate.com", cols[0].find('a')['href']) if cols[0].find('a') else None
                
                breweries.append({
                    'name': brewery_name,
                    'url': brewery_url
                })
        
        logging.info(f"Found {len(breweries)} breweries on Beer Advocate")
        return breweries
    
    def scrape_brewery_details(self, brewery_info):
        """Scrape details about a brewery from its page"""
        if not brewery_info.get('url'):
            return brewery_info
        
        soup = self._get_soup(brewery_info['url'])
        if not soup:
            return brewery_info
        
        # Extract address information
        address_section = soup.select_one('#info_box')
        if address_section:
            address_text = address_section.get_text()
            
            # Extract address components using regex
            address_match = re.search(r'Address:\s+(.*?)(?=\n|$)', address_text)
            if address_match:
                brewery_info['address'] = address_match.group(1).strip()
            
            # Extract phone
            phone_match = re.search(r'Phone:\s+(.*?)(?=\n|$)', address_text)
            if phone_match:
                brewery_info['phone'] = phone_match.group(1).strip()
            
            # Extract website
            website_match = re.search(r'Website:\s+(.*?)(?=\n|$)', address_text)
            if website_match:
                brewery_info['website'] = website_match.group(1).strip()
            
            # Parse city and state from address
            if brewery_info.get('address'):
                city_state_match = re.search(r'Chicago,\s+IL\s+(\d{5})', brewery_info.get('address', ''))
                if city_state_match:
                    brewery_info['city'] = 'Chicago'
                    brewery_info['state'] = 'IL'
                    brewery_info['zip_code'] = city_state_match.group(1)
        
        # Extract description
        description_section = soup.select_one('#ba-content .break')
        if description_section:
            brewery_info['description'] = description_section.get_text().strip()
        
        # Extract beer listings if available
        beer_listings = soup.select('#ba-content table tr')
        beers = []
        
        for row in beer_listings[1:]:  # Skip header row
            cols = row.find_all('td')
            if len(cols) >= 2:
                beer_name = cols[0].text.strip()
                beer_url = urljoin("https://www.beeradvocate.com", cols[0].find('a')['href']) if cols[0].find('a') else None
                beer_style = cols[1].text.strip() if len(cols) > 1 else None
                beer_abv = cols[2].text.strip() if len(cols) > 2 else None
                
                if beer_abv and beer_abv.endswith('%'):
                    try:
                        beer_abv = float(beer_abv[:-1])
                    except ValueError:
                        beer_abv = None
                
                beers.append({
                    'name': beer_name,
                    'url': beer_url,
                    'type': beer_style,
                    'abv': beer_abv
                })
        
        brewery_info['beers'] = beers
        
        logging.info(f"Scraped details for {brewery_info['name']}, found {len(beers)} beers")
        return brewery_info
    
    def save_brewery_to_db(self, brewery):
        """Save brewery data to database"""
        try:
            # Insert brewery
            self.cursor.execute('''
                INSERT INTO breweries (
                    name, address, city, state, zip_code, phone, website, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                brewery.get('name'),
                brewery.get('address'),
                brewery.get('city'),
                brewery.get('state'),
                brewery.get('zip_code'),
                brewery.get('phone'),
                brewery.get('website'),
                brewery.get('description')
            ))
            
            brewery_id = self.cursor.lastrowid
            
            # Insert beers if present
            for beer in brewery.get('beers', []):
                self.cursor.execute('''
                    INSERT INTO beers (
                        name, type, abv, description
                    ) VALUES (?, ?, ?, ?)
                ''', (
                    beer.get('name'),
                    beer.get('type'),
                    beer.get('abv'),
                    beer.get('description')
                ))
                
                beer_id = self.cursor.lastrowid
                
                # Link beer to brewery
                self.cursor.execute('''
                    INSERT INTO beer_locations (
                        beer_id, brewery_id
                    ) VALUES (?, ?)
                ''', (beer_id, brewery_id))
            
            self.conn.commit()
            logging.info(f"Saved brewery {brewery['name']} to database with {len(brewery.get('beers', []))} beers")
            return True
        
        except sqlite3.Error as e:
            logging.error(f"Database error while saving {brewery.get('name')}: {e}")
            self.conn.rollback()
            return False
    
    def run(self):
        """Run the complete scraping process"""
        logging.info("Starting Chicago beer scraping process")
        
        # Get list of breweries
        breweries = self.scrape_chicago_brewery_list()
        
        # Scrape details for each brewery
        for i, brewery in enumerate(breweries):
            logging.info(f"Processing brewery {i+1} of {len(breweries)}: {brewery['name']}")
            
            # Skip if we've already processed this brewery
            self.cursor.execute("SELECT id FROM breweries WHERE name = ?", (brewery['name'],))
            if self.cursor.fetchone():
                logging.info(f"Brewery {brewery['name']} already exists in database, skipping")
                continue
            
            # Get detailed information
            brewery_details = self.scrape_brewery_details(brewery)
            
            # Save to database
            self.save_brewery_to_db(brewery_details)
            
            # Save after each brewery in case of interruption
            self.conn.commit()
        
        logging.info("Completed Chicago beer scraping process")

if __name__ == "__main__":
    scraper = ChicagoBeerScraper()
    scraper.run()

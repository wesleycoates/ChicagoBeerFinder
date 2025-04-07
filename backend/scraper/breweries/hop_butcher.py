import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import traceback
import re
import time
from urllib.parse import urljoin

class HopButcherScraper:
    def __init__(self):
        # Configure logging
        self.setup_logging()
        
        # Base URL for the brewery
        self.base_url = 'https://www.hopbutcher.com'
        
        # Ensure scraped_data directory exists
        self.output_dir = 'scraped_data'
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Headers to mimic a browser request
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def setup_logging(self):
        """
        Set up logging to capture detailed error information
        """
        # Create logs directory if it doesn't exist
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        
        # Configure logging
        log_file = os.path.join(log_dir, 'hop_butcher_scraper.log')
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def scrape_beers(self):
        """
        Main method to scrape beers from Hop Butcher
        """
        try:
            # Get beer links from the main page
            beer_links = self.get_beer_links()
            
            if not beer_links:
                self.logger.error("No beer links found")
                return []
            
            self.logger.info(f"Found {len(beer_links)} beer links")
            
            # Scrape details for each beer
            all_beers = []
            for name, link in beer_links:
                try:
                    beer_details = self.scrape_beer_page(name, link)
                    if beer_details:
                        all_beers.append(beer_details)
                    
                    # Be nice to the server
                    time.sleep(1)
                except Exception as e:
                    self.logger.error(f"Error scraping beer {name}: {e}")
            
            self.logger.info(f"Successfully scraped {len(all_beers)} beers")
            return all_beers
            
        except Exception as e:
            self.logger.error(f"Critical error in scrape_beers: {e}")
            self.logger.error(traceback.format_exc())
            return []

    def get_beer_links(self):
        """
        Get links to individual beer pages from the main page
        
        Returns:
            list: List of tuples (beer_name, beer_url)
        """
        self.logger.info(f"Fetching content from {self.base_url}")
        
        try:
            # Fetch the main page
            response = requests.get(self.base_url, headers=self.headers)
            self.logger.info(f"Response status code: {response.status_code}")
            
            # Save raw HTML for debugging
            self.save_debug_html(response.text)
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all beer links
            beer_links = []
            
            # Try to find gallery items that contain links to beer pages
            gallery_items = soup.select('.sqs-gallery-design-autocolumns-slide')
            self.logger.info(f"Found {len(gallery_items)} gallery items")
            
            if gallery_items:
                for item in gallery_items:
                    link_element = item.select_one('a')
                    name_element = item.select_one('.project-title h2')
                    
                    if link_element and name_element:
                        beer_name = name_element.text.strip()
                        beer_link = link_element.get('href')
                        
                        if beer_link:
                            full_url = urljoin(self.base_url, beer_link)
                            beer_links.append((beer_name, full_url))
            
            # If we didn't find gallery items, try alternative selectors
            if not beer_links:
                # Try more general selectors to find links
                all_links = soup.select('a[href]')
                pattern = re.compile(r'/([\w-]+)/$')  # Pattern for beer URLs
                
                for link in all_links:
                    href = link.get('href', '')
                    
                    # Check if this link appears to be a beer page
                    match = pattern.match(href)
                    if match:
                        # Try to find the beer name
                        name_element = link.select_one('h1, h2, h3') or link
                        beer_name = name_element.text.strip()
                        
                        if beer_name and href:
                            full_url = urljoin(self.base_url, href)
                            beer_links.append((beer_name, full_url))
            
            return beer_links
        
        except Exception as e:
            self.logger.error(f"Error getting beer links: {e}")
            self.logger.error(traceback.format_exc())
            return []

    def scrape_beer_page(self, beer_name, url):
        """
        Scrape details from an individual beer page
        
        Args:
            beer_name (str): The beer name
            url (str): URL of the beer page
            
        Returns:
            dict: Dictionary with beer details
        """
        self.logger.info(f"Scraping beer page: {beer_name} - {url}")
        
        try:
            # Fetch the beer page
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                self.logger.error(f"Error fetching {url}: status code {response.status_code}")
                return None
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Initialize beer details
            beer = {
                'name': beer_name,
                'brewery': 'Hop Butcher for the World',
                'source_url': url
            }
            
            # Find the paragraphs containing beer details
            paragraphs = soup.select('p[data-rte-preserve-empty="true"][style*="white-space:pre-wrap"]')
            
            # Extract details from paragraphs
            for p in paragraphs:
                text = p.get_text(strip=True)
                if ':' in text:
                    # Split the text into key and value
                    parts = text.split(':', 1)
                    if len(parts) == 2:
                        key, value = parts
                        
                        # Clean and normalize the key
                        key = key.strip().lower()
                        
                        # Fix common keys
                        if 'style' in key:
                            key = 'style'
                        elif 'abv' in key:
                            key = 'abv'
                        elif 'hop' in key:
                            key = 'hops'
                        elif 'last canned' in key:
                            key = 'last_canned'
                        elif 'label artwork' in key:
                            key = 'label_artwork'
                        else:
                            # Convert spaces to underscores for other keys
                            key = key.replace(' ', '_')
                        
                        # Clean the value
                        value = value.strip()
                        
                        # Store in beer dictionary
                        beer[key] = value
            
            return beer
        
        except Exception as e:
            self.logger.error(f"Error scraping beer page {url}: {e}")
            self.logger.error(traceback.format_exc())
            return None

    def save_debug_html(self, html_content):
        """
        Save the HTML content for debugging
        
        Args:
            html_content (str): HTML content to save
        """
        try:
            debug_dir = 'debug'
            os.makedirs(debug_dir, exist_ok=True)
            filename = os.path.join(debug_dir, 'hop_butcher_page_source.html')
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"Saved page source to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving page source: {e}")

    def save_to_json(self, beers):
        """
        Save scraped beers to a JSON file with timestamp
        
        Args:
            beers (list): List of beer dictionaries
        """
        # Create timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") 
        filename = f"{self.output_dir}/hop_butcher_beers_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(beers, f, indent=4, ensure_ascii=False)
            
            self.logger.info(f"Saved {len(beers)} beers to {filename}")
        
        except Exception as e:
            self.logger.error(f"Error saving JSON: {e}")
            self.logger.error(traceback.format_exc())

def main():
    # Create scraper instance
    scraper = HopButcherScraper()
    
    # Scrape beers
    beers = scraper.scrape_beers()
    
    # Save to JSON
    scraper.save_to_json(beers)

if __name__ == '__main__':
    main()
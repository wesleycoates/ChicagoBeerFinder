import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import traceback
import re

class HopButcherScraper:
    def __init__(self):
        # Configure logging
        self.setup_logging()
        
        # Base URL for the brewery
        self.base_url = 'https://www.hopbutcher.com'
        
        # Ensure scraped_data directory exists
        self.output_dir = 'scraped_data'
        os.makedirs(self.output_dir, exist_ok=True)

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
        Scrape beer details from Hop Butcher website
        
        Returns:
            list: A list of dictionaries containing beer details
        """
        beers = []
        try:
            # Send request to the website
            self.logger.info(f"Fetching content from {self.base_url}")
            
            # Headers to mimic a browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Fetch the page
            response = requests.get(self.base_url, headers=headers)
            
            # Log response details
            self.logger.info(f"Response status code: {response.status_code}")
            self.logger.info(f"Response content length: {len(response.text)} characters")
            
            # Save raw HTML for debugging
            self.save_debug_html(response.text)
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try different strategies to find beers
            beers = self.find_beers_multiple_strategies(soup)
            
            self.logger.info(f"Successfully scraped {len(beers)} beers")
            return beers
        
        except Exception as e:
            self.logger.error(f"Critical error in scrape_beers: {e}")
            self.logger.error(traceback.format_exc())
            return beers

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

    def find_beers_multiple_strategies(self, soup):
        """
        Try multiple strategies to find beer details
        
        Args:
            soup (BeautifulSoup): Parsed HTML
        
        Returns:
            list: List of found beers
        """
        beers = []
        
        # Strategies to find beers
        strategies = [
            self.find_beers_by_name_and_details,
            self.find_beers_by_detailed_paragraphs,
            self.find_beers_by_project_items
        ]
        
        for strategy in strategies:
            try:
                found_beers = strategy(soup)
                if found_beers:
                    beers.extend(found_beers)
                    break
            except Exception as e:
                self.logger.error(f"Error with strategy {strategy.__name__}: {e}")
        
        return beers

    def find_beers_by_name_and_details(self, soup):
        """
        Find beers by matching names with their details
        
        Args:
            soup (BeautifulSoup): Parsed HTML
        
        Returns:
            list: List of found beers
        """
        beers = []
        
        # Find beer names (try multiple selectors)
        name_selectors = [
            'h1[data-shrink-original-size="42"]',
            'h1.beer-name',
            'h1.project-title'
        ]
        
        for selector in name_selectors:
            try:
                name_elements = soup.select(selector)
                self.logger.info(f"Name selector '{selector}' found {len(name_elements)} elements")
                
                for name_elem in name_elements:
                    # Find the container (usually a parent or nearby div)
                    container = name_elem.find_parent('div') or name_elem.find_next('div')
                    
                    if container:
                        # Look for detail paragraphs
                        detail_paragraphs = container.select('p[data-rte-preserve-empty="true"][style="white-space:pre-wrap;"]')
                        
                        # Extract details
                        beer_details = self.extract_details_from_paragraphs(name_elem.get_text(strip=True), detail_paragraphs)
                        
                        if beer_details:
                            beers.append(beer_details)
            except Exception as e:
                self.logger.error(f"Error with name selector {selector}: {e}")
        
        return beers

    def find_beers_by_detailed_paragraphs(self, soup):
        """
        Find beers by looking for paragraphs with detailed information
        
        Args:
            soup (BeautifulSoup): Parsed HTML
        
        Returns:
            list: List of found beers
        """
        beers = []
        
        # Find paragraphs that might contain beer details
        paragraphs = soup.select('p[data-rte-preserve-empty="true"][style="white-space:pre-wrap;"]')
        
        self.logger.info(f"Found {len(paragraphs)} paragraphs with preserve-empty attribute")
        
        # Group paragraphs that might belong to the same beer
        current_beer = None
        for p in paragraphs:
            text = p.get_text(strip=True)
            
            # Check if this is a new beer name
            if re.match(r'^[A-Z]', text):
                # If we had a previous beer, add it
                if current_beer:
                    beers.append(current_beer)
                
                # Start a new beer
                current_beer = {'name': text, 'source_url': self.base_url}
            
            # Extract details if current beer exists
            elif current_beer:
                if ':' in text:
                    key, value = text.split(':', 1)
                    key = key.strip().lower().replace(' ', '_')
                    value = value.strip()

                    if key and value:
                        current_beer[key] = value
        
        # Add the last beer if exists
        if current_beer:
            beers.append(current_beer)
        
        return beers

    def find_beers_by_project_items(self, soup):
        """
        Find beers by looking for project/item classes
        
        Args:
            soup (BeautifulSoup): Parsed HTML
        
        Returns:
            list: List of found beers
        """
        beers = []
        
        # Find project/beer items
        project_selectors = [
            '.project-item',
            '.item[data-type="image"]',
            '.gallery-item'
        ]
        
        for selector in project_selectors:
            try:
                items = soup.select(selector)
                self.logger.info(f"Selector '{selector}' found {len(items)} items")
                
                for item in items:
                    # Try to find name and details
                    name_elem = item.select_one('h1, h2, h3')
                    if name_elem:
                        name = name_elem.get_text(strip=True)
                        
                        # Find detail paragraphs
                        detail_paragraphs = item.select('p[data-rte-preserve-empty="true"][style="white-space:pre-wrap;"]')
                        
                        # Extract details
                        beer_details = self.extract_details_from_paragraphs(name, detail_paragraphs)
                        
                        if beer_details:
                            beers.append(beer_details)
            except Exception as e:
                self.logger.error(f"Error with project selector {selector}: {e}")
        
        return beers

    def extract_details_from_paragraphs(self, name, paragraphs):
        """
        Extract beer details from a list of paragraphs
        
        Args:
            name (str): Beer name
            paragraphs (list): List of BeautifulSoup paragraph elements
        
        Returns:
            dict: Beer details dictionary
        """
        beer = {
            'name': name,
            'source_url': self.base_url
        }
        
        for p in paragraphs:
            text = p.get_text(strip=True)
            if ':' in text:
                key, value = text.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                value = value.strip()

                if key and value:
                    beer[key] = value
        
        return beer if len(beer) > 2 else None

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
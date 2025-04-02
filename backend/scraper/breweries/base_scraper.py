# base_scraper.py
import requests
from bs4 import BeautifulSoup
import json
import re

class BreweryScraper:
    def __init__(self, brewery_name, website_url, location="Chicago, IL"):
        self.brewery_name = brewery_name
        self.website_url = website_url
        self.location = location
        self.beer_url = website_url  # Default to main URL, can be overridden
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        
    def get_page_content(self, url=None):
        """Get the HTML content of the specified URL or the brewery's beer page"""
        if url is None:
            url = self.beer_url
            
        print(f"Retrieving content from {url}...")
        response = requests.get(url, headers=self.headers)
        return response.text
    
    def parse_html(self, html):
        """Parse HTML with BeautifulSoup"""
        soup = BeautifulSoup(html, 'html.parser')
        # Remove scripts and styles for cleaner text
        for script in soup(["script", "style"]):
            script.extract()
        return soup
    
    def clean_text(self, text):
        """Clean up text content"""
        if not text:
            return ""
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', text).strip()
        return cleaned
    
    def extract_beer_type(self, text):
        """Extract beer type from text"""
        text = text.lower()
        beer_types = {
            "ipa": "IPA",
            "pale ale": "Pale Ale", 
            "lager": "Lager",
            "pilsner": "Pilsner",
            "stout": "Stout",
            "porter": "Porter",
            "wheat": "Wheat Beer",
            "amber": "Amber Ale",
            "golden": "Golden Ale",
            "saison": "Saison",
            "farmhouse": "Farmhouse Ale",
            "gose": "Gose",
            "belgian": "Belgian",
            "sour": "Sour",
            "wild ale": "Wild Ale",
            "kottbusser": "Kottbusser"
        }
        
        for type_key, type_name in beer_types.items():
            if type_key in text:
                return type_name
        return "Unknown"
    
    def extract_abv(self, text):
        """Extract ABV from text"""
        if not text:
            return "Unknown"
            
        abv_pattern = re.compile(r'(\d+\.?\d*)%(\s*ABV)?', re.IGNORECASE)
        match = abv_pattern.search(text)
        if match:
            return match.group(0)
        return "Unknown"
    
    def scrape(self):
        """Main scraping method to be implemented by subclasses"""
        raise NotImplementedError("Each brewery scraper must implement the scrape method")
    
    def save_to_json(self, data, filename=None):
        """Save data to a JSON file"""
        if not filename:
            filename = f"{self.brewery_name.lower().replace(' ', '_')}_beers.json"
        
        with open(filename, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=4)
        
        print(f"Data saved to {filename}")
        return filename
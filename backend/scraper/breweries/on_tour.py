#!/usr/bin/env python3
"""
Scraper for On Tour Brewing
This script scrapes beer information from On Tour Brewing's website.
"""

import os
import json
import time
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

class OnTourBrewingScraper:
    """Scraper for On Tour Brewing website."""
    
    def __init__(self):
        """Initialize the scraper with the URL and other settings."""
        self.url = "https://ontourbrewing.com/menu/"
        self.brewery_name = "On Tour Brewing"
        self.brewery_location = "Chicago, IL"
        self.brewery_url = "https://ontourbrewing.com"
        # Output directory for scraped data
        self.output_dir = "scraped_data"
        # Ensure the output directory exists
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def setup_driver(self):
        """Set up and return a Chrome WebDriver instance."""
        print("Setting up Chrome WebDriver...")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36")
        
        # Initialize the Chrome driver
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    
    def extract_beer_info_from_html_content(self, html_content):
        """Extract beer information directly from HTML content using specific selectors."""
        print("Extracting beer information from HTML content...")
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all item-details elements
        beer_items = soup.find_all('div', class_='item-details')
        if not beer_items:
            print("No item-details elements found")
            return []
        
        print(f"Found {len(beer_items)} beer items")
        beers = []
        
        for item in beer_items:
            try:
                # Extract beer name from id attribute
                name_element = item.find('span', id=True)
                if not name_element:
                    # Try to find any name-like element
                    name_element = item.find('h4', class_='item-name')
                    if name_element:
                        name_element = name_element.find('span')
                
                if not name_element or not name_element.text.strip():
                    print("Could not find beer name, skipping item")
                    continue
                
                beer_name = name_element.text.strip()
                
                # Extract beer style
                style_element = item.find('span', class_='item-category')
                beer_style = style_element.text.strip() if style_element else "N/A"
                
                # Make sure beer style is not the same as beer name
                if beer_style == beer_name:
                    beer_style = "N/A"
                
                # Extract ABV
                abv = None
                abv_element = item.find('span', class_='item-abv')
                if abv_element and abv_element.text:
                    abv_text = abv_element.text.strip()
                    # Use regex to match the decimal number
                    abv_match = re.search(r'(\d+\.?\d*)', abv_text)
                    if abv_match:
                        abv = float(abv_match.group(1))
                
                # Extract IBU
                ibu = None
                ibu_element = item.find('span', class_='item-ibu')
                if ibu_element and ibu_element.text:
                    ibu_text = ibu_element.text.strip()
                    # Use regex to match the integer
                    ibu_match = re.search(r'(\d+)', ibu_text)
                    if ibu_match:
                        ibu = int(ibu_match.group(1))
                
                # Extract brewing location
                brewing_location = self.brewery_location
                location_element = item.find('span', class_='item-brewery-location')
                if location_element and location_element.text.strip():
                    brewing_location = location_element.text.strip()
                
                # Extract description
                description = "No description available."
                # Try to find the description based on the beer name id
                desc_id = f"{name_element.get('id')}_description" if name_element.get('id') else None
                if desc_id:
                    desc_element = item.find('p', id=desc_id)
                    if desc_element:
                        description = desc_element.text.strip()
                else:
                    # Try alternate methods
                    desc_element = item.find('p', class_='show-less')
                    if desc_element:
                        description = desc_element.text.strip()
                    else:
                        # Try looking for any paragraph
                        desc_element = item.find('p')
                        if desc_element:
                            description = desc_element.text.strip()
                
                # Create beer data dictionary
                beer_data = {
                    "name": beer_name,
                    "style": beer_style,
                    "abv": abv,
                    "ibu": ibu,
                    "brewing_location": brewing_location,
                    "description": description,
                    "brewery": self.brewery_name,
                    "brewery_location": self.brewery_location,
                    "source_url": self.url,
                    "scraped_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # Print debug info
                print(f"Beer: {beer_name}, Style: {beer_style}, ABV: {abv}, IBU: {ibu}")
                
                beers.append(beer_data)
                
            except Exception as e:
                print(f"Error processing a beer item: {str(e)}")
                continue
        
        return beers
    
    def check_html_for_beer_pattern(self, html_content):
        """Check for common patterns that might indicate beer information."""
        # Look for specific patterns that indicate beer data
        patterns = [
            r'span class="item-abv">\s*(\d+\.?\d*%)',
            r'span class="item-ibu">\s*(\d+)',
            r'span class="item-brewery-location">([^<]+)',
            r'<span class="item-category">([^<]+)',
        ]
        
        matches = []
        for pattern in patterns:
            if re.search(pattern, html_content):
                matches.append(pattern)
        
        return len(matches) > 0
    
    def scrape(self):
        """Scrape the website and return the data."""
        print(f"Scraping {self.brewery_name} using Selenium...")
        
        driver = self.setup_driver()
        
        try:
            # Navigate to the page
            print(f"Loading {self.url}...")
            driver.get(self.url)
            
            # Wait for the page to load
            print("Waiting for page to load completely...")
            time.sleep(10)  # Wait longer to ensure JS execution completes
            
            # Get the page source
            page_source = driver.page_source
            
            # Save the page source for debugging
            with open("ontour_page_source.html", "w", encoding="utf-8") as f:
                f.write(page_source)
            print("Saved page source to ontour_page_source.html")
            
            # Take a screenshot for visual inspection
            driver.save_screenshot("ontour_page.png")
            print("Saved screenshot to ontour_page.png")
            
            # Check if the HTML contains beer information
            if self.check_html_for_beer_pattern(page_source):
                print("Found beer-related patterns in HTML")
                beers = self.extract_beer_info_from_html_content(page_source)
                if beers:
                    print(f"Successfully extracted {len(beers)} beers")
                    return beers
            
            # If no beers found, try alternative URLs
            alternative_urls = [
                "https://ontourbrewing.com/beers/",
                "https://ontourbrewing.com/taproom/",
                "https://ontourbrewing.com/our-beers/",
                "https://ontourbrewing.com/"
            ]
            
            for alt_url in alternative_urls:
                print(f"Trying alternative URL: {alt_url}")
                driver.get(alt_url)
                time.sleep(8)
                
                # Take a screenshot
                driver.save_screenshot(f"ontour_{alt_url.split('/')[-2] or 'home'}.png")
                
                alt_page_source = driver.page_source
                
                # Check if this page has beer information
                if self.check_html_for_beer_pattern(alt_page_source):
                    print(f"Found beer-related patterns at {alt_url}")
                    
                    # Save this page source
                    with open(f"ontour_{alt_url.split('/')[-2] or 'home'}.html", "w", encoding="utf-8") as f:
                        f.write(alt_page_source)
                    
                    # Try to extract beer info
                    beers = self.extract_beer_info_from_html_content(alt_page_source)
                    if beers:
                        print(f"Successfully extracted {len(beers)} beers from {alt_url}")
                        self.url = alt_url  # Update URL to the successful one
                        return beers
            
            print("No beer information found on any page.")
            return None
            
        except Exception as e:
            print(f"Error during scraping: {str(e)}")
            return None
            
        finally:
            driver.quit()
    
    def save_data(self, data):
        """Save the scraped data to a JSON file."""
        if not data:
            print("No data to save.")
            return None
        
        # Create a filename with a timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/on_tour_brewing_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"Data saved to {filename}")
            return filename
        except Exception as e:
            print(f"Error saving data to {filename}: {e}")
            return None
    
    def run(self):
        """Run the scraper and save the data."""
        data = self.scrape()
        if data:
            return self.save_data(data)
        return None

if __name__ == "__main__":
    try:
        print("Starting On Tour Brewing scraper...")
        scraper = OnTourBrewingScraper()
        result = scraper.run()
        if result:
            print(f"Scraping completed successfully. Data saved to {result}")
        else:
            print("Scraping failed to extract any beer information.")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
import requests
from bs4 import BeautifulSoup
import json
import os
import time
from datetime import datetime
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

class GooseIslandScraper:
    def __init__(self, output_dir="scraped_data"):
        self.brewery_name = "Goose Island"
        self.brewery_url = "https://www.gooseisland.com"
        self.beer_page_url = "https://www.gooseisland.com/our-beers"
        self.brewery_location = "Chicago, IL"
        self.output_dir = output_dir
        self.today = datetime.now().strftime("%Y-%m-%d")
        
        # Make sure output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def scrape(self):
        # Set up Selenium with headless Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            # Go to the website
            driver.get(self.beer_page_url)
            
            # Check for age verification
            try:
                # Wait for age verification form to appear
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "age-gate-form"))
                )
                
                # Find the date inputs (month, day, year)
                month_input = driver.find_element(By.ID, "month")
                day_input = driver.find_element(By.ID, "day")
                year_input = driver.find_element(By.ID, "year")
                
                # Input a date that's definitely over 21
                month_input.send_keys("01")
                day_input.send_keys("01")
                year_input.send_keys("1980")
                
                # Find and click the submit button
                submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                submit_button.click()
                
                # Wait for page to load after verification
                time.sleep(3)
            except Exception as e:
                print(f"No age verification found or error: {str(e)}")
            
            # Wait for the beer list to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".beer-card, .beer-item, .product-item"))
            )
            
            # Get the page source and parse with BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Find all beer elements (adjust selector based on actual page structure)
            beer_elements = soup.select(".beer-card, .beer-item, .product-item")
            
            beers = []
            for beer in beer_elements:
                try:
                    # Adjust these selectors based on the actual HTML structure
                    name_elem = beer.select_one(".beer-name, .product-title, h3, h4")
                    style_elem = beer.select_one(".beer-style, .product-style, .beer-type")
                    abv_elem = beer.select_one(".beer-abv, .product-abv, .abv")
                    description_elem = beer.select_one(".beer-description, .product-description, p")
                    
                    # Extract data or provide defaults
                    name = name_elem.get_text(strip=True) if name_elem else "Unknown"
                    
                    # For style, try to extract or parse from description if needed
                    beer_style = ""
                    if style_elem:
                        beer_style = style_elem.get_text(strip=True)
                    
                    # Extract ABV, handling different formats
                    abv = ""
                    if abv_elem:
                        abv_text = abv_elem.get_text(strip=True)
                        abv_match = re.search(r'(\d+\.?\d*)%', abv_text)
                        if abv_match:
                            abv = abv_match.group(1)
                    
                    # Get description if available
                    description = ""
                    if description_elem:
                        description = description_elem.get_text(strip=True)
                    
                    # Add to our list
                    beers.append({
                        "name": name,
                        "type": beer_style,
                        "abv": abv,
                        "description": description,
                        "brewery": self.brewery_name,
                        "location": self.brewery_location,
                        "url": self.brewery_url
                    })
                except Exception as e:
                    print(f"Error processing a beer: {str(e)}")
            
            # Output results to JSON
            self._save_to_json(beers)
            
            return beers
            
        except Exception as e:
            print(f"Error scraping {self.brewery_name}: {str(e)}")
            return []
        finally:
            driver.quit()
    
    def _save_to_json(self, beers):
        """Save the beer data to a JSON file"""
        filename = f"{self.output_dir}/{self.brewery_name.lower().replace(' ', '_')}_{self.today}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(beers, f, indent=4)
        
        print(f"Saved {len(beers)} beers from {self.brewery_name} to {filename}")


if __name__ == "__main__":
    scraper = GooseIslandScraper()
    scraper.scrape()
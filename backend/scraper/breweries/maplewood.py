import requests
from bs4 import BeautifulSoup
import re
import json
import time
import os
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

class MaplewoodScraper:
    def __init__(self):
        self.brewery_name = "Maplewood Brewing Co."
        self.output_dir = "scraped_data"
        self.debug_dir = "debug_screenshots"
        
        # Create output and debug directories if they don't exist
        for dir_path in [self.output_dir, self.debug_dir]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)

    def _take_screenshot(self, driver, name):
        """Take a screenshot and save it to debug directory"""
        try:
            screenshot_path = os.path.join(self.debug_dir, f"{name}.png")
            driver.save_screenshot(screenshot_path)
            print(f"Screenshot saved: {screenshot_path}")
        except Exception as e:
            print(f"Failed to take screenshot: {e}")

    def _setup_chrome_options(self):
        """Setup Chrome options for Selenium"""
        options = Options()
        
        # Headless mode and other compatibility options
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        # Window size
        options.add_argument("--window-size=1920,1080")
        
        # User agent
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        return options

    def scrape(self):
        """Scrape beers from Maplewood website"""
        print(f"Scraping {self.brewery_name}...")
        
        # Combine current and archived beers
        current_beers = self._get_maplewood_beers_with_selenium(
            "https://maplewoodbrew.com/beer/calendar", is_current=True
        )
        archived_beers = self._get_maplewood_beers_with_selenium(
            "https://maplewoodbrew.com/beer/archive", is_current=False
        )
        
        # Combine and deduplicate beers
        all_beers = self._deduplicate_beers(current_beers + archived_beers)
        
        return {
            "brewery": self.brewery_name,
            "beers": all_beers
        }

    def save_to_json(self, data):
        """Save scraped data to a JSON file"""
        filename = os.path.join(self.output_dir, f"{self.brewery_name.lower().replace(' ', '_')}_beers.json")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"Saved {len(data['beers'])} beers to {filename}")
        return filename

    def _deduplicate_beers(self, beers):
        """Remove duplicate beers based on name"""
        unique_beers = []
        seen_names = set()
        
        for beer in beers:
            # Normalize name for comparison
            normalized_name = beer['name'].lower().strip()
            
            if normalized_name not in seen_names:
                unique_beers.append(beer)
                seen_names.add(normalized_name)
        
        return unique_beers

    def _get_maplewood_beers_with_selenium(self, url, is_current=True):
        """Use Selenium to extract beers from Maplewood's website while handling age verification"""
        print(f"\n===== Setting up Selenium for {url} =====")
        
        driver = None
        beers = []
        
        try:
            # Setup Chrome options
            options = self._setup_chrome_options()
            
            # Setup Chrome WebDriver
            service = Service(ChromeDriverManager().install())
            
            print("Initializing WebDriver...")
            driver = webdriver.Chrome(service=service, options=options)
            
            # Configure wait
            wait = WebDriverWait(driver, 15)
            
            # Navigate to the beer page
            print(f"Navigating to {url}")
            driver.get(url)
            
            # Take initial screenshot
            self._take_screenshot(driver, f"initial_page_{is_current}")
            
            # Debug initial page
            print(f"Page Title: {driver.title}")
            print(f"Current URL: {driver.current_url}")
            
            # Age Verification Strategies
            verification_strategies = [
                # Strategy 1: JavaScript to find and click 'Yes' link
                lambda: driver.execute_script("""
                    const links = document.querySelectorAll('a.verify__link');
                    const yesLink = Array.from(links).find(link => 
                        link.textContent.trim().toLowerCase() === 'yes'
                    );
                    if (yesLink) {
                        console.log('Found YES link via JS');
                        yesLink.click();
                    }
                """),
                
                # Strategy 2: Direct Selenium click on 'Yes' link
                lambda: wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'verify__link') and contains(text(), 'Yes')]"))
                ).click(),
                
                # Strategy 3: Action Chains click
                lambda: ActionChains(driver).move_to_element(
                    driver.find_element(By.XPATH, "//a[contains(@class, 'verify__link') and contains(text(), 'Yes')]")
                ).click().perform()
            ]
            
            # Try verification strategies
            verification_successful = False
            for i, strategy in enumerate(verification_strategies, 1):
                try:
                    print(f"Attempting verification strategy {i}")
                    strategy()
                    
                    # Wait for potential page load
                    time.sleep(3)
                    print(f"Current URL after verification: {driver.current_url}")
                    
                    # Take screenshot after verification
                    self._take_screenshot(driver, f"verification_attempt_{i}_{is_current}")
                    
                    # Verify we've moved past age verification
                    if 'verify' not in driver.current_url.lower():
                        verification_successful = True
                        break
                    
                except Exception as e:
                    print(f"Verification strategy {i} failed: {e}")
            
            # Final verification screenshot
            self._take_screenshot(driver, f"after_verification_{is_current}")
            
            # If verification failed, print detailed debug info
            if not verification_successful:
                print("ALL VERIFICATION STRATEGIES FAILED!")
                print("Page Source:")
                print(driver.page_source[:5000])  # Print first 5000 characters
                
                # Additional debugging
                print("\nAvailable Links:")
                links = driver.find_elements(By.TAG_NAME, 'a')
                for link in links:
                    try:
                        print(f"Link text: '{link.text}', Class: '{link.get_attribute('class')}'")
                    except:
                        pass
                
                return []
            
            # Wait for page to load
            time.sleep(5)
            
            # Scroll to load all elements on archive page
            if is_current == False:  # Only do this for archive page
                print("Scrolling to load all archive beers...")
                last_height = driver.execute_script("return document.body.scrollHeight")
                
                while True:
                    # Scroll down to bottom
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    
                    # Wait to load page
                    time.sleep(2)
                    
                    # Calculate new scroll height and compare with last scroll height
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    
                    # If heights are the same, it means we've reached the bottom
                    if new_height == last_height:
                        break
                    
                    last_height = new_height
                
                # Take a screenshot after scrolling
                self._take_screenshot(driver, f"after_scrolling_{is_current}")
            
            # Find beer elements after potential scrolling
            beer_elements = driver.find_elements(By.CSS_SELECTOR, ".archive-list__item")
            print(f"Total beer elements found after scrolling: {len(beer_elements)}")
            
            # Process beer elements
            for element in beer_elements:
                try:
                    # Extract name
                    name_elem = element.find_element(By.CSS_SELECTOR, ".archive-list__name")
                    name = name_elem.text.strip()
                    
                    # Skip empty names
                    if not name:
                        continue
                    
                    # Extract beer type
                    try:
                        type_elem = element.find_element(By.CSS_SELECTOR, ".archive-list__style")
                        beer_type = type_elem.text.strip()
                    except:
                        beer_type = "Unknown"
                    
                    # Extract description
                    try:
                        desc_elem = element.find_element(By.CSS_SELECTOR, ".archive-list__description p")
                        description = desc_elem.text.strip()
                    except:
                        description = ""
                    
                    # Extract ABV
                    try:
                        abv_elem = element.find_element(By.CSS_SELECTOR, ".archive-list__detail")
                        abv_match = re.search(r'(\d+\.\d+)%', abv_elem.text)
                        abv = float(abv_match.group(1)) if abv_match else 0.0
                    except:
                        abv = 0.0
                    
                    # Create beer entry
                    beer_entry = {
                        'name': name,
                        'type': beer_type,
                        'abv': abv,
                        'description': description,
                        'brewery': self.brewery_name,
                        'status': 'Current' if is_current else 'Archived'
                    }
                    
                    beers.append(beer_entry)
                    print(f"Added beer: {name} ({beer_type}, {abv}% ABV)")
                
                except Exception as e:
                    print(f"Error processing individual beer: {e}")
        
        except Exception as e:
            print(f"CRITICAL ERROR scraping {url}: {str(e)}")
            print(traceback.format_exc())
        
        finally:
            # Clean up
            if driver:
                try:
                    driver.quit()
                except:
                    pass
        
        return beers

# For direct script testing
def main():
    scraper = MaplewoodScraper()
    data = scraper.scrape()
    scraper.save_to_json(data)

if __name__ == "__main__":
    main()
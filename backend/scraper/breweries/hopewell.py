#!/usr/bin/env python3
"""
Hopewell Brewery Scraper - Standalone scraper for Hopewell Brewing's website
"""

import requests
import json
import os
import re
import logging
import time
from datetime import datetime
from bs4 import BeautifulSoup

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Warning: Selenium not available. Web scraping mode will not work.")

class HopewellScraper:
    """
    Scraper for Hopewell Brewing's website.
    Extracts beer information and handles newsletter popup.
    """
    def __init__(self, output_directory="scraped_data"):
        self.brewery_name = "Hopewell Brewing"
        self.brewery_url = "https://www.hopewellbrewing.com"
        self.output_directory = output_directory
        self.beers = []
        self.logger = self._setup_logger()
        
        # Brewery metadata
        self.brewery_info = {
            "name": self.brewery_name,
            "address": "2760 N Milwaukee Ave",
            "city": "Chicago",
            "state": "IL",
            "website": self.brewery_url
        }
        
    def _setup_logger(self):
        """Set up logging for the scraper"""
        logger = logging.getLogger(f"{self.brewery_name}Scraper")
        logger.setLevel(logging.INFO)
        
        # Create handlers
        c_handler = logging.StreamHandler()
        c_handler.setLevel(logging.INFO)
        
        # Create formatters and add to handlers
        c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        c_handler.setFormatter(c_format)
        
        # Add handlers to the logger
        logger.addHandler(c_handler)
        
        return logger
    
    def _setup_webdriver(self):
        """Set up Chrome webdriver with headless option"""
        if not SELENIUM_AVAILABLE:
            self.logger.error("Selenium not available. Cannot set up webdriver.")
            return None
            
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Initialize browser
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    
    def _handle_popup(self, driver):
        """Close the newsletter popup if it appears"""
        if not SELENIUM_AVAILABLE:
            return
            
        try:
            # Wait for popup to appear (up to 5 seconds)
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button.mc-closeModal[data-action='close-mc-modal']"))
            )
            
            # Close the popup
            close_button = driver.find_element(By.CSS_SELECTOR, "button.mc-closeModal[data-action='close-mc-modal']")
            driver.execute_script("arguments[0].click();", close_button)  # Use JavaScript click for more reliability
            self.logger.info("Newsletter popup closed")
        except TimeoutException:
            self.logger.info("No newsletter popup detected")
        except NoSuchElementException:
            self.logger.warning("Could not find close button for popup")
        except Exception as e:
            self.logger.warning(f"Error handling popup: {str(e)}")
            # Try alternative method if the first fails
            try:
                # Sometimes we need to use more generic selectors
                popups = driver.find_elements(By.CSS_SELECTOR, ".modal-container button[aria-label='Close']")
                if popups:
                    driver.execute_script("arguments[0].click();", popups[0])
                    self.logger.info("Newsletter popup closed using alternative method")
            except Exception:
                self.logger.warning("Failed to close popup with alternative method")
    
    def scrape(self):
        """Main method to scrape the Hopewell website"""
        self.logger.info(f"Starting scrape of {self.brewery_name}")
        
        if not SELENIUM_AVAILABLE:
            self.logger.error("Cannot scrape website: Selenium not available")
            return self.beers
        
        driver = self._setup_webdriver()
        if not driver:
            return self.beers
        
        try:
            # Visit the main page
            self.logger.info(f"Navigating to {self.brewery_url}")
            driver.get(self.brewery_url)
            
            # Handle popup if it appears
            self._handle_popup(driver)
            
            # Add debug info
            self.logger.info("Waiting for beer content to load...")
            
            # Get the current page URL (in case of redirects)
            current_url = driver.current_url
            self.logger.info(f"Current page URL: {current_url}")
            
            # The beer page might be on a different URL/path
            # Let's try to find a link to the beer page if we're not already there
            if "/beers" not in current_url.lower() and "/our-beer" not in current_url.lower():
                try:
                    # Look for links to a beer page
                    beer_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'beer') or contains(text(), 'Beer') or contains(text(), 'beer')]")
                    if beer_links:
                        self.logger.info(f"Found beer link: {beer_links[0].get_attribute('href')}")
                        beer_links[0].click()
                        self.logger.info("Navigated to beer page")
                    else:
                        self.logger.warning("No beer links found on homepage")
                except Exception as e:
                    self.logger.warning(f"Error finding beer links: {str(e)}")
            
            # Give the page time to load
            time.sleep(2)
            
            # Wait for beer elements with a more flexible approach
            try:
                # Try different possible selectors for beer elements
                for selector in [".beer-thumbnails__thumbs", ".beer-thumbnail", ".beers-container", ".beer-list"]:
                    try:
                        WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        self.logger.info(f"Found beer elements with selector: {selector}")
                        break
                    except Exception:
                        continue
            except Exception as e:
                self.logger.warning(f"Could not find beer elements with standard selectors: {str(e)}")
            
            # Save page source for debugging
            page_source = driver.page_source
            self.logger.info(f"Page source length: {len(page_source)} characters")
            
            # Parse the page with BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Try multiple selectors to find beer elements
            beer_elements = []
            for selector in [".beer-thumbnail", ".beer-item", ".beer-card", "[class*='beer']"]:
                found_elements = soup.select(selector)
                if found_elements:
                    beer_elements = found_elements
                    self.logger.info(f"Found {len(beer_elements)} beer elements with selector: {selector}")
                    break
            
            if not beer_elements:
                self.logger.warning("No beer elements found with any selector")
            
            for beer_element in beer_elements:
                try:
                    # Extract name
                    name_element = beer_element.select_one(".beer-thumbnail__title")
                    if not name_element:
                        continue
                    
                    name = name_element.text.strip()
                    
                    # Extract beer type directly from the HTML structure
                    style_element = beer_element.select_one(".beer-thumbnail__style")
                    beer_type = style_element.text.strip() if style_element else "Unknown"
                    
                    # Extract ABV directly from the HTML structure
                    abv_element = beer_element.select_one(".beer-thumbnail__abv")
                    abv_text = abv_element.text.strip() if abv_element else ""
                    abv_match = re.search(r'(\d+(?:\.\d+)?)%', abv_text)
                    abv = float(abv_match.group(1)) if abv_match else None
                    
                    # Extract description
                    description_element = beer_element.select_one(".beer-thumbnail__description .type-body--small")
                    description = description_element.text.strip() if description_element else ""
                    
                    # Create beer object
                    beer = {
                        "name": name,
                        "type": beer_type,
                        "abv": abv,
                        "description": description,
                        "brewery": self.brewery_info["name"]
                    }
                    
                    self.beers.append(beer)
                    self.logger.info(f"Added beer: {name}")
                    
                except Exception as e:
                    self.logger.error(f"Error processing beer element: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error scraping {self.brewery_name}: {e}")
        finally:
            driver.quit()
            
        self.logger.info(f"Completed scrape of {self.brewery_name}. Found {len(self.beers)} beers.")
        return self.beers
    
    def process_html_directly(self, html_content):
        """
        Process beer data directly from provided HTML content
        Useful for debugging or when web scraping encounters issues
        
        Args:
            html_content (str): Raw HTML content containing beer information
            
        Returns:
            list: List of beer dictionaries extracted from the HTML
        """
        self.logger.info("Processing HTML content directly")
        self.beers = []
        
        try:
            # Parse the HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find beer elements
            beer_elements = soup.select(".beer-thumbnail")
            self.logger.info(f"Found {len(beer_elements)} beer elements in provided HTML")
            
            for beer_element in beer_elements:
                try:
                    # Extract name
                    name_element = beer_element.select_one(".beer-thumbnail__title")
                    if not name_element:
                        continue
                    
                    name = name_element.text.strip()
                    
                    # Extract beer type
                    style_element = beer_element.select_one(".beer-thumbnail__style")
                    beer_type = style_element.text.strip() if style_element else "Unknown"
                    
                    # Extract ABV
                    abv_element = beer_element.select_one(".beer-thumbnail__abv")
                    abv_text = abv_element.text.strip() if abv_element else ""
                    abv_match = re.search(r'(\d+(?:\.\d+)?)%', abv_text)
                    abv = float(abv_match.group(1)) if abv_match else None
                    
                    # Extract description
                    description_element = beer_element.select_one(".beer-thumbnail__description .type-body--small")
                    description = description_element.text.strip() if description_element else ""
                    
                    # Create beer object
                    beer = {
                        "name": name,
                        "type": beer_type,
                        "abv": abv,
                        "description": description,
                        "brewery": self.brewery_info["name"]
                    }
                    
                    self.beers.append(beer)
                    self.logger.info(f"Added beer: {name}")
                    
                except Exception as e:
                    self.logger.error(f"Error processing beer element: {e}")
            
            self.logger.info(f"Processed {len(self.beers)} beers from provided HTML")
            
        except Exception as e:
            self.logger.error(f"Error processing HTML: {e}")
        
        return self.beers
    
    def save_data(self):
        """Save scraped data to JSON file"""
        if not self.beers:
            self.logger.warning("No beers to save. Run scrape() or process_html_directly() first.")
            return None
            
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_directory):
            os.makedirs(self.output_directory)
            
        # Create filename with date
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"{self.output_directory}/hopewell_{date_str}.json"
        
        # Prepare data for saving
        data = {
            "brewery": self.brewery_info,
            "beers": self.beers,
            "scrape_date": datetime.now().isoformat()
        }
        
        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            
        self.logger.info(f"Saved {len(self.beers)} beers to {filename}")
        return filename
        
    def run(self, html_content=None):
        """
        Run the full scrape process
        
        Args:
            html_content (str, optional): HTML content to process instead of scraping
            
        Returns:
            str: Path to the saved JSON file
        """
        if html_content:
            self.process_html_directly(html_content)
        else:
            self.scrape()
            
        return self.save_data()

def main():
    """Main function to run when executed as a script"""
    # Initialize the scraper
    scraper = HopewellScraper(output_directory="scraped_data")
    
    # Check if HTML content is provided via file
    html_file = "hopewell_beers.html"
    if os.path.exists(html_file):
        print(f"Found HTML file: {html_file}")
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        output_file = scraper.run(html_content)
    else:
        # Otherwise, use the manual HTML content
        html_content = """
<div class="beer-thumbnails__thumbs">
      <div class="beer-thumbnail beer-thumbnail--text">
      <div class="beer-thumbnail__details">
        <div class="beer-thumbnail__title type-condensed">Pils</div>
        <div class="beer-thumbnail__meta">
                      <div class="beer-thumbnail__style type-skinny">Pilsner</div>
                                <div class="beer-thumbnail__abv type-skinny">5.1% ABV</div>
                  </div>
        <div class="beer-thumbnail__description">
          <div class="type-body--small"><p>Hopewell Pils is a&nbsp;crystal clear, hop-forward Pilsner inspired by the Northern German brewing tradition. Lightly bready malt is met with the floral zip of classic German noble hops, followed by a&nbsp;crispy clean, drying finish. A&nbsp;very precious Pilsner for very precious&nbsp;people.</p> 
<p><br></p></div>
        </div>
      </div>
    </div>
      <div class="beer-thumbnail beer-thumbnail--text">
      <div class="beer-thumbnail__details">
        <div class="beer-thumbnail__title type-condensed">Tankbeer</div>
        <div class="beer-thumbnail__meta">
                      <div class="beer-thumbnail__style type-skinny">Lager</div>
                                <div class="beer-thumbnail__abv type-skinny">4.4% ABV</div>
                  </div>
        <div class="beer-thumbnail__description">
          <div class="type-body--small"><p>Tankbeer is an unfiltered, naturally carbonated Lager inspired by the rich traditions of Czech Republic bar culture. With notes of fresh dough, fragrant noble hop spice and a&nbsp;pleasantly pillowy body, this beer transports you to the brewer's cellar, where the beer is always&nbsp;fresh.</p></div>
        </div>
      </div>
    </div>
      <div class="beer-thumbnail beer-thumbnail--text">
      <div class="beer-thumbnail__details">
        <div class="beer-thumbnail__title type-condensed">Ride or Die</div>
        <div class="beer-thumbnail__meta">
                      <div class="beer-thumbnail__style type-skinny">Pale Ale</div>
                                <div class="beer-thumbnail__abv type-skinny">5.5% ABV</div>
                  </div>
        <div class="beer-thumbnail__description">
          <div class="type-body--small"><p>A Pale Ale you can depend on — a bona fide fridge staple. Bright neon flavors of grapefruit and pine give way to a&nbsp;pleasantly soft malt base and a&nbsp;quick slice of balancing bitterness. Reliably tasty without&nbsp;a&nbsp;fuss.</p></div>
        </div>
      </div>
    </div>
      <div class="beer-thumbnail beer-thumbnail--text">
      <div class="beer-thumbnail__details">
        <div class="beer-thumbnail__title type-condensed">Going Places</div>
        <div class="beer-thumbnail__meta">
                      <div class="beer-thumbnail__style type-skinny">IPA</div>
                                <div class="beer-thumbnail__abv type-skinny">6.8% ABV</div>
                  </div>
        <div class="beer-thumbnail__description">
          <div class="type-body--small"><p>An <span class="caps">IPA</span> for those on the up-and-up. A&nbsp;vibrant combo of new-wave hops offers fresh citrus, tropical fruit and sticky pine with a&nbsp;prickly finish, putting this hoppy bev on the path ahead. Let's&nbsp;get&nbsp;it.</p>
<p><br></p></div>
        </div>
      </div>
    </div>
      <div class="beer-thumbnail beer-thumbnail--text">
      <div class="beer-thumbnail__details">
        <div class="beer-thumbnail__title type-condensed">Lightbeam</div>
        <div class="beer-thumbnail__meta">
                      <div class="beer-thumbnail__style type-skinny">Hazy IPA</div>
                                <div class="beer-thumbnail__abv type-skinny">6.3% ABV</div>
                  </div>
        <div class="beer-thumbnail__description">
          <div class="type-body--small"><p>A Hazy <span class="caps">IPA</span> that radiates the full spectrum of modern hop eccentricities. An initial burst swells with the essence of ripe mango, papaya and apricot, while reverberant threads of green grass and prickly pine tether its final form. Here's to a&nbsp;bright spot.</p></div>
        </div>
      </div>
    </div>
      <div class="beer-thumbnail beer-thumbnail--text">
      <div class="beer-thumbnail__details">
        <div class="beer-thumbnail__title type-condensed">Outside Voice</div>
        <div class="beer-thumbnail__meta">
                      <div class="beer-thumbnail__style type-skinny">XPA</div>
                                <div class="beer-thumbnail__abv type-skinny">4.8% ABV</div>
                  </div>
        <div class="beer-thumbnail__description">
          <div class="type-body--small"><p>An Extra Pale Ale (<span class="caps">XPA</span>) fashioned for warm, sunny days and the cookouts that coincide. Notes of dank tropical fruit lead the way, followed by an undercurrent of citrus zest and piney bitterness.</p></div>
        </div>
      </div>
    </div>
      <div class="beer-thumbnail beer-thumbnail--text">
      <div class="beer-thumbnail__details">
        <div class="beer-thumbnail__title type-condensed">Plain English</div>
        <div class="beer-thumbnail__meta">
                      <div class="beer-thumbnail__style type-skinny">London-style Brown Ale</div>
                                <div class="beer-thumbnail__abv type-skinny">4.2% ABV</div>
                  </div>
        <div class="beer-thumbnail__description">
          <div class="type-body--small"><p>A malty yet sessionable Brown Ale modeled after the traditional examples found in London and the southern half of England at large. Notes of toffee, caramel and light chocolate fill out this full-bodied brew, but its low <span class="caps">ABV</span> and dry finish make it an everyday&nbsp;drinker.</p></div>
        </div>
      </div>
    </div>
      <div class="beer-thumbnail beer-thumbnail--text">
      <div class="beer-thumbnail__details">
        <div class="beer-thumbnail__title type-condensed">Shaker</div>
        <div class="beer-thumbnail__meta">
                      <div class="beer-thumbnail__style type-skinny">'90s Brewpub-style Amber Ale</div>
                                <div class="beer-thumbnail__abv type-skinny">5.9% ABV</div>
                  </div>
        <div class="beer-thumbnail__description">
          <div class="type-body--small"><p>A hopped up amber ale that conjures the classics of the <span class="push-single"></span>​<span class="pull-single">'</span>90s brewpub boom. Hopped thoroughly with tried-and-true varieties that dominated the era, bringing notes ofpine sap, grapefruit, fresh grass and resin. This one's forthe old&nbsp;heads.</p></div>
        </div>
      </div>
    </div>
      <div class="beer-thumbnail beer-thumbnail--text">
      <div class="beer-thumbnail__details">
        <div class="beer-thumbnail__title type-condensed">Soup</div>
        <div class="beer-thumbnail__meta">
                      <div class="beer-thumbnail__style type-skinny">Belgian-style Dubbel</div>
                                <div class="beer-thumbnail__abv type-skinny">7.0% ABV</div>
                  </div>
        <div class="beer-thumbnail__description">
          <div class="type-body--small"><p>A complex, red-hued Belgian ale with notes of gingersnap, clove, light toffee and&nbsp;banana.</p></div>
        </div>
      </div>
    </div>
      <div class="beer-thumbnail beer-thumbnail--text">
      <div class="beer-thumbnail__details">
        <div class="beer-thumbnail__title type-condensed">Olde Duck</div>
        <div class="beer-thumbnail__meta">
                      <div class="beer-thumbnail__style type-skinny">Barrel-aged Barleywine</div>
                                <div class="beer-thumbnail__abv type-skinny">12.4% ABV</div>
                  </div>
        <div class="beer-thumbnail__description">
          <div class="type-body--small"><p>An English-style Barleywine aged 18 months in third use Bourbon barrels that previously held Deluxe Imperial Stout, and Heaven Hill before that. Rich and malty with notes of toffee, caramel, raisin, vanilla and light&nbsp;oak.</p></div>
        </div>
      </div>
    </div>
  </div>
"""
        print("Using built-in HTML content")
        output_file = scraper.run(html_content)
    
    # Print results
    if output_file:
        print(f"\nSuccessfully extracted {len(scraper.beers)} beers from Hopewell Brewing!")
        print(f"Data saved to: {output_file}")
        
        # Print a summary of the beers
        print("\nBeers extracted:")
        for i, beer in enumerate(scraper.beers, 1):
            print(f"{i}. {beer['name']} - {beer['type']} ({beer['abv']}% ABV)")
    else:
        print("\nNo beers were extracted. Check logs for errors.")

if __name__ == "__main__":
    main()
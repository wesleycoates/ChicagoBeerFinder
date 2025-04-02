import os
import sys
import time
import csv
import shutil
import tempfile
import subprocess
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def kill_chrome_processes():
    """
    Attempt to kill existing Chrome and ChromeDriver processes
    """
    try:
        # Kill Chrome processes
        subprocess.run(['pkill', '-f', 'google-chrome'], stderr=subprocess.DEVNULL)
        subprocess.run(['pkill', '-f', 'chromedriver'], stderr=subprocess.DEVNULL)
        
        # Wait a moment for processes to terminate
        time.sleep(2)
    except Exception as e:
        print(f"Error killing Chrome processes: {e}")

def setup_chrome_driver():
    """
    Set up Chrome WebDriver with comprehensive process management
    """
    # Kill existing Chrome processes
    kill_chrome_processes()
    
    # Create a unique temporary directory for Chrome user data
    user_data_dir = tempfile.mkdtemp()
    
    chrome_options = Options()
    
    # Explicitly set the Chrome binary location
    chrome_options.binary_location = "/usr/bin/google-chrome"
    
    # Set unique user data directory
    chrome_options.add_argument(f"user-data-dir={user_data_dir}")
    
    # Add additional options for debugging and stability
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--headless")  # Run in headless mode
    
    # Detailed logging
    chrome_options.add_argument("--enable-logging")
    chrome_options.add_argument("--v=1")
    
    # User agent to mimic a real browser
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36")
    
    try:
        # Alternative method to get ChromeDriver
        service = Service(ChromeDriverManager().install())
        
        # Create and return the driver
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Set a default page load timeout
        driver.set_page_load_timeout(30)
        
        return driver, user_data_dir
    
    except Exception as e:
        print(f"Error setting up WebDriver: {e}")
        import traceback
        traceback.print_exc()
        
        # Additional diagnostic information
        try:
            chrome_version = subprocess.check_output(["/usr/bin/google-chrome", "--version"]).decode().strip()
            print(f"Chrome version: {chrome_version}")
        except Exception as version_error:
            print(f"Could not retrieve Chrome version: {version_error}")
        
        raise

def handle_age_verification(driver):
    """
    Attempt to handle age verification popup
    """
    try:
        # Wait for potential age verification modal
        wait = WebDriverWait(driver, 10)
        
        # Try multiple potential age verification button selectors
        age_verification_selectors = [
            "//button[contains(text(), 'Yes, I am 21 or older')]",
            "//button[contains(text(), 'Yes')]",
            "//button[contains(text(), 'Enter')]",
            "#age-verification-submit",
            ".age-verify-yes"
        ]
        
        for selector in age_verification_selectors:
            try:
                # Try to find and click the age verification button
                if selector.startswith('//'):
                    age_button = wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                else:
                    age_button = wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                
                # Scroll into view and click
                driver.execute_script("arguments[0].scrollIntoView(true);", age_button)
                time.sleep(1)  # Brief pause
                age_button.click()
                
                print(f"Clicked age verification button: {selector}")
                
                # Wait for page to potentially load
                time.sleep(2)
                return True
            
            except TimeoutException:
                # If this selector doesn't work, continue to next
                continue
        
        print("No age verification button found with standard selectors")
        return False
    
    except Exception as e:
        print(f"Error handling age verification: {e}")
        return False

def scrape_revolution_beers():
    """
    Scrape beers from Revolution Brewing website
    """
    # Set up driver with unique user data directory
    driver, user_data_dir = setup_chrome_driver()
    beers = []
    
    try:
        # Navigate to the website
        driver.get('https://revbrew.com/visit/brewery/tap-room-dl')
        
        # Attempt to handle age verification
        handle_age_verification(driver)
        
        # Wait and find beer elements
        wait = WebDriverWait(driver, 10)
        
        # Beer list selectors to try
        beer_selectors = [
            '.untapped-beer-capsule',
            '.beer-list__col',
            'li.beer-list__col',
            '.beer-item',
            'div[class*="beer"]'
        ]
        
        beer_elements = None
        for selector in beer_selectors:
            try:
                beer_elements = wait.until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                )
                print(f"Found {len(beer_elements)} elements using selector: {selector}")
                
                if beer_elements:
                    break
            except TimeoutException:
                print(f"No elements found with selector: {selector}")
        
        if not beer_elements:
            print("No beer elements found")
            return beers
        
        for beer_elem in beer_elements:
            try:
                # Safe text extraction function
                def safe_find_text(element, selector, default='Unknown'):
                    try:
                        return element.find_element(By.CSS_SELECTOR, selector).text.strip()
                    except NoSuchElementException:
                        return default
                
                # Extract beer details
                name = safe_find_text(beer_elem, '.untapped-beer-capsule__name, h2.beer-name')
                style = safe_find_text(beer_elem, '.untapped-beer-capsule__style, .beer-style')
                abv = safe_find_text(beer_elem, '.untapped-beer-capsule__abv, .beer-abv')
                ibu = safe_find_text(beer_elem, '.untapped-beer-capsule__ibu, .beer-ibu')
                
                # Clean up ABV
                if abv and '%' in abv:
                    abv = abv.rstrip('%')
                
                beer_info = {
                    'name': name,
                    'style': style,
                    'abv': abv,
                    'ibu': ibu,
                    'brewery': 'Revolution Brewing',
                    'scraped_date': datetime.now().isoformat()
                }
                
                beers.append(beer_info)
                
            except Exception as beer_extract_error:
                print(f"Error extracting individual beer: {beer_extract_error}")
        
    except Exception as e:
        print(f"Error scraping Revolution Brewing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Always quit the driver and clean up temp directory
        driver.quit()
        try:
            shutil.rmtree(user_data_dir)
        except Exception as cleanup_error:
            print(f"Error cleaning up temp directory: {cleanup_error}")
    
    return beers

def save_to_csv(beers, filename='revolution_beers.csv'):
    """
    Save scraped beer information to a CSV file
    """
    if not beers:
        print("No beers to save.")
        return
    
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)
        
        # Specify the fieldnames based on the keys in the first beer dictionary
        fieldnames = beers[0].keys()
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write the header
            writer.writeheader()
            
            # Write each beer's information
            for beer in beers:
                writer.writerow(beer)
        
        print(f"Successfully saved {len(beers)} beers to {filename}")
    
    except Exception as e:
        print(f"Error saving to CSV: {e}")

def main():
    # Scrape Revolution Brewing
    print("Scraping Revolution Brewing...")
    revolution_beers = scrape_revolution_beers()
    
    if revolution_beers:
        print(f"Found {len(revolution_beers)} beers from Revolution Brewing")
        save_to_csv(revolution_beers, 'revolution_beers.csv')
    else:
        print("No beers found or scraping failed")

if __name__ == '__main__':
    main()
import os
import sys
import time
import csv
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def setup_chrome_driver():
    """
    Set up Chrome WebDriver with specific Chrome binary path and comprehensive options
    """
    chrome_options = Options()
    
    # Explicitly set the Chrome binary location
    chrome_options.binary_location = "/usr/bin/google-chrome"
    
    # Add additional options for headless and stability
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--headless")
    
    # User agent to mimic a real browser
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36")
    
    try:
        # Use WebDriver Manager to handle driver installation
        service = Service(ChromeDriverManager().install())
        
        # Create and return the driver
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Set a default page load timeout
        driver.set_page_load_timeout(30)
        
        return driver
    
    except Exception as e:
        print(f"Error setting up WebDriver: {e}")
        import traceback
        traceback.print_exc()
        raise

def scrape_revolution_brewing():
    """
    Scrape beers from Revolution Brewing website
    """
    driver = setup_chrome_driver()
    beers = []
    
    try:
        # Navigate to the website
        driver.get('https://revbrew.com/visit/brewery/tap-room-dl')
        
        # Wait for potential age verification
        try:
            # Wait for and click age verification button
            wait = WebDriverWait(driver, 10)
            age_verify_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Yes, I am 21 or older')]"))
            )
            age_verify_button.click()
            
            # Wait a moment for page to load
            time.sleep(2)
        except Exception as age_verify_error:
            print(f"Age verification may have been skipped or failed: {age_verify_error}")
        
        # Scroll to load all content (if needed)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Find beer elements
        # Note: You'll need to inspect the actual page to get the correct selectors
        beer_elements = driver.find_elements(By.CSS_SELECTOR, '.beer-item')
        
        for beer_elem in beer_elements:
            try:
                # Extract beer details
                name = beer_elem.find_element(By.CSS_SELECTOR, '.beer-name').text.strip()
                
                # Try to extract additional details if available
                try:
                    beer_type = beer_elem.find_element(By.CSS_SELECTOR, '.beer-style').text.strip()
                except:
                    beer_type = 'Unknown'
                
                try:
                    description = beer_elem.find_element(By.CSS_SELECTOR, '.beer-description').text.strip()
                except:
                    description = ''
                
                beer_info = {
                    'name': name,
                    'type': beer_type,
                    'description': description,
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
        # Always quit the driver to free up resources
        driver.quit()
    
    return beers

def save_to_csv(beers, filename='brewery_beers.csv'):
    """
    Save scraped beer information to a CSV file
    """
    if not beers:
        print("No beers to save.")
        return
    
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
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
    revolution_beers = scrape_revolution_brewing()
    
    if revolution_beers:
        print(f"Found {len(revolution_beers)} beers from Revolution Brewing")
        save_to_csv(revolution_beers, 'revolution_beers.csv')
    else:
        print("No beers found or scraping failed")

if __name__ == '__main__':
    main()
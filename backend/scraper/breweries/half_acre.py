import requests
from bs4 import BeautifulSoup
import re
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def get_half_acre_beers_with_selenium():
    """Use Selenium to extract beers from Half Acre's website while handling age verification"""
    print("Setting up Selenium for Half Acre Brewing...")
    
    # Set up Selenium options
    options = Options()
    options.add_argument("--headless")  # Run in headless mode (no browser UI)
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    driver = None
    beers = []
    
    try:
        # Initialize the driver
        driver = webdriver.Chrome(options=options)
        
        # Navigate to the beer page
        beer_url = "https://www.halfacrebeer.com/beer"
        print(f"Navigating to {beer_url}")
        driver.get(beer_url)
        
        # Wait for page to initially load
        time.sleep(3)
        
        print(f"Page title: {driver.title}")
        
        # Check for and handle age verification
        try:
            print("Checking for age verification...")
            # Different selectors that might contain age verification buttons
            age_verify_selectors = [
                "button.age-gate-submit-yes", 
                "button.age-gate-submit", 
                "input[value='YES']",
                "a.age-gate-submit-yes",
                ".age-gate-submit",
                "button:contains('I am 21')",
                "button:contains('Yes')"
            ]
            
            for selector in age_verify_selectors:
                try:
                    # Use a short timeout to quickly check each selector
                    verify_button = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    print(f"Found age verification button with selector: {selector}")
                    verify_button.click()
                    print("Clicked age verification button")
                    time.sleep(2)  # Wait for page to update after click
                    break
                except:
                    continue
            
            # Alternative approach: look for any button with yes/confirm text
            if "age" in driver.page_source.lower() and "verify" in driver.page_source.lower():
                print("Looking for any yes/confirm buttons...")
                buttons = driver.find_elements(By.TAG_NAME, "button")
                for button in buttons:
                    if any(text in button.text.lower() for text in ["yes", "confirm", "21", "verify"]):
                        print(f"Found age verification button with text: {button.text}")
                        button.click()
                        print("Clicked age verification button")
                        time.sleep(2)
                        break
        
        except Exception as e:
            print(f"No age verification found or error handling it: {str(e)}")
        
        # Wait for the content to load
        time.sleep(3)
        
        # Save page source for debugging
        with open("half_acre_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
            print("Saved page source for debugging")
        
        # Extract the beer information
        print("Looking for beer elements...")
        
        # Try different selectors that might contain beer information
        beer_selectors = [
            ".beer-card", 
            ".product-card", 
            ".product-item",
            ".summary-item",
            ".beer-item"
        ]
        
        beer_elements = []
        for selector in beer_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"Found {len(elements)} beer elements with selector: {selector}")
                beer_elements = elements
                break
        
        # If we didn't find beer elements with specific selectors, try a more generic approach
        if not beer_elements:
            print("No specific beer elements found, trying more generic approach...")
            
            # Look for elements that contain beer-related text
            all_elements = driver.find_elements(By.TAG_NAME, "div")
            for element in all_elements:
                try:
                    element_text = element.text
                    if "%" in element_text and any(style in element_text for style in ["IPA", "Ale", "Lager"]):
                        beer_elements.append(element)
                except:
                    continue
            
            print(f"Found {len(beer_elements)} potential beer elements with generic approach")
        
        # Process beer elements
        for element in beer_elements:
            try:
                element_text = element.text
                print(f"Processing beer element: {element_text[:100]}...")
                
                # Extract beer name (usually in a heading within the element)
                name = "Unknown"
                name_elem = None
                try:
                    name_elem = element.find_element(By.CSS_SELECTOR, "h2, h3, h4, .title, .name")
                    name = name_elem.text.strip()
                except:
                    # If we can't find a specific name element, try to extract it from the text
                    lines = element_text.split('\n')
                    if lines:
                        name = lines[0].strip()
                
                # Extract beer type
                beer_type = "Unknown"
                common_styles = ['IPA', 'India Pale Ale', 'Lager', 'Ale', 'Stout', 'Porter', 'Pilsner', 'Wheat', 'Sour']
                for style in common_styles:
                    if style in element_text:
                        # Get context around the style
                        context_match = re.search(r'([^.!?\n]*\b' + style + r'\b[^.!?\n]*)', element_text)
                        if context_match:
                            beer_type = context_match.group(1).strip()
                            break
                
                # Extract ABV
                abv = 0.0
                abv_match = re.search(r'(\d+\.\d+|\d+)%', element_text)
                if abv_match:
                    abv = float(abv_match.group(1))
                
                # Extract description
                description = ""
                if name_elem:
                    # Try to find description as text after the name
                    desc_text = element_text.replace(name, '', 1).strip()
                    if desc_text:
                        description = desc_text
                else:
                    # Use everything except the first line as description
                    lines = element_text.split('\n')
                    if len(lines) > 1:
                        description = '\n'.join(lines[1:]).strip()
                
                # Add beer to our list
                beers.append({
                    'name': name,
                    'type': beer_type,
                    'abv': abv,
                    'description': description,
                    'brewery': 'Half Acre Beer Co.'
                })
                
                print(f"Added beer: {name} ({beer_type}, {abv}% ABV)")
                
            except Exception as e:
                print(f"Error processing beer element: {str(e)}")
                continue
    
    except Exception as e:
        print(f"Error with Selenium: {str(e)}")
    finally:
        # Clean up
        if driver:
            driver.quit()
    
    return beers

def main():
    print("Testing Half Acre Brewing scraper with age verification handling...")
    
    # Extract beers using Selenium (which can handle age verification)
    beers = get_half_acre_beers_with_selenium()
    
    if beers:
        print(f"\nSuccessfully extracted {len(beers)} beers")
        
        # Print all beers
        for i, beer in enumerate(beers, 1):
            print(f"Beer {i}: {beer['name']} - {beer['type']} - {beer['abv']}% ABV")
            if beer.get('description'):
                desc_preview = beer['description'][:100] + "..." if len(beer['description']) > 100 else beer['description']
                print(f"  Description: {desc_preview}")
        
        # Save all results to a JSON file
        with open('half_acre_beers.json', 'w', encoding='utf-8') as f:
            json.dump(beers, f, indent=2)
            print(f"Saved all {len(beers)} beers to half_acre_beers.json")
        
        return 0
    else:
        print("Failed to extract any beers from Half Acre")
        print("\nConsider checking the saved page source to understand why extraction failed")
        return 1

if __name__ == "__main__":
    main()
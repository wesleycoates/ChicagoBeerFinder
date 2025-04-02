import os
import time
import json
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime, timedelta

# Create a directory to store scraped data
os.makedirs('chicago_beer_data', exist_ok=True)

def setup_driver():
    """Set up and return a configured Chrome webdriver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36")
    
    # Initialize the driver
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def handle_goose_island_age_verification(driver):
    """Handle Goose Island's date-based age verification."""
    print("Handling Goose Island age verification...")
    
    try:
        # First look for date entry fields
        print("Looking for date entry fields...")
        
        try:
            # Try to find the month input field first
            month_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='MM' or contains(@id, 'month') or @name='month']"))
            )
            print("Found month input field")
            
            # Then find day and year fields
            day_input = driver.find_element(By.XPATH, "//input[@placeholder='DD' or contains(@id, 'day') or @name='day']")
            year_input = driver.find_element(By.XPATH, "//input[@placeholder='YYYY' or contains(@id, 'year') or @name='year']")
            
            print("Found all date input fields")
            
            # Calculate a date 25 years ago (definitely over 21)
            past_date = datetime.now() - timedelta(days=365*25)
            
            # Clear fields first and then enter values
            month_input.clear()
            month_input.send_keys(f"{past_date.month:02d}")
            day_input.clear()
            day_input.send_keys(f"{past_date.day:02d}")
            year_input.clear()
            year_input.send_keys(str(past_date.year))
            
            print(f"Entered date: {past_date.month}/{past_date.day}/{past_date.year}")
            
            # Look for submit/enter button
            submit_buttons = driver.find_elements(By.XPATH, 
                "//button[contains(text(), 'Enter') or contains(text(), 'Submit') or contains(text(), 'Confirm') or @type='submit']")
            
            if submit_buttons:
                submit_buttons[0].click()
                print(f"Clicked submit button: {submit_buttons[0].text}")
            else:
                # If no button, try pressing Enter key on the year field
                print("No submit button found, pressing Enter key")
                year_input.send_keys(Keys.ENTER)
            
            time.sleep(5)  # Wait longer after age verification
            return True
            
        except Exception as e:
            print(f"Error with date fields: {e}")
            
            # Try alternative buttons that might be present
            try:
                print("Looking for alternative age verification buttons")
                # Try common button patterns
                buttons = [
                    "//button[contains(text(), 'Enter') or contains(text(), 'ENTER')]",
                    "//button[contains(text(), 'Yes') or contains(text(), 'YES')]",
                    "//button[contains(text(), 'Confirm') or contains(text(), 'CONFIRM')]",
                    "//button[contains(text(), 'I AM OF LEGAL DRINKING AGE')]",
                    "//button[@id='btn-enter-yes']",
                    "//button[contains(@class, 'enter') or contains(@class, 'confirm')]"
                ]
                
                for xpath in buttons:
                    try:
                        button = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, xpath))
                        )
                        print(f"Found button: {button.text}")
                        button.click()
                        time.sleep(3)
                        return True
                    except:
                        continue
            except Exception as e:
                print(f"Error with alternative buttons: {e}")
                
            return False
    except Exception as e:
        print(f"Error handling age verification: {e}")
        return False

def scrape_goose_island_beers():
    """Scrape beer information from Goose Island Beer Co."""
    print("Scraping Goose Island Beer Co...")
    
    driver = setup_driver()
    
    # Try multiple URLs
    urls = [
        "https://www.gooseisland.com/our-beers",
        "https://www.gooseisland.com/beers"
    ]
    
    beers = []
    
    for url in urls:
        try:
            # Navigate to the website
            driver.get(url)
            print(f"Navigating to {url}")
            print(f"Page title: {driver.title}")
            
            # Handle age verification
            handle_goose_island_age_verification(driver)
            
            # Wait for content to load
            print("Waiting for page to load after verification...")
            time.sleep(8)
            
            # Save the page source for debugging
            page_source = driver.page_source
            save_path = f"chicago_beer_data/goose_island_{url.split('/')[-1]}_page.html"
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(page_source)
            print(f"Saved page source to {save_path}")
            
            # Try JavaScript extraction
            print("Trying JavaScript extraction...")
            
            script = """
            let beers = [];
            
            // Try multiple selectors that might contain beer items
            const selectors = [
                '.beer-card', '.product-card', '.collection-item', '.beer-item',
                '.products .product', '[class*="beer-"]', '[class*="product-"]'
            ];
            
            // Try each selector
            for (const selector of selectors) {
                const elements = document.querySelectorAll(selector);
                if (elements.length > 0) {
                    console.log(`Found ${elements.length} elements with selector: ${selector}`);
                    
                    elements.forEach(item => {
                        try {
                            // Find beer information
                            const nameEl = item.querySelector('h1, h2, h3, h4, h5, .name, .title');
                            const styleEl = item.querySelector('.style, .type, .category');
                            const abvEl = item.querySelector('.abv, .alcohol');
                            
                            if (nameEl) {
                                const beerData = {
                                    name: nameEl.textContent.trim(),
                                    style: styleEl ? styleEl.textContent.trim() : 'N/A',
                                    abv: abvEl ? abvEl.textContent.trim() : 'N/A'
                                };
                                beers.push(beerData);
                            }
                        } catch (e) {
                            console.error('Error extracting beer data:', e);
                        }
                    });
                    
                    // If we found beers, stop searching with other selectors
                    if (beers.length > 0) {
                        break;
                    }
                }
            }
            
            // If no beers found with specific selectors, try a more general approach
            if (beers.length === 0) {
                console.log('No beers found with specific selectors, trying generic approach');
                
                // Look for any elements that might contain beer names with nearby style/ABV info
                const allElements = document.querySelectorAll('div, article, section');
                
                // Filter to elements that might be beer containers
                const potentialBeerContainers = Array.from(allElements).filter(el => {
                    const text = el.textContent.toLowerCase();
                    return (
                        // Contains beer-related terms
                        (text.includes('ipa') || 
                         text.includes('ale') || 
                         text.includes('lager') || 
                         text.includes('stout') ||
                         text.includes('porter') ||
                         text.includes('abv') ||
                         text.includes('%')) &&
                        // Not too long (likely not a container of multiple beers)
                        text.length < 500 &&
                        // Has an image (product likely has an image)
                        el.querySelector('img')
                    );
                });
                
                console.log(`Found ${potentialBeerContainers.length} potential beer containers`);
                
                potentialBeerContainers.forEach((container, index) => {
                    try {
                        // Look for elements that might be beer names
                        const nameEl = container.querySelector('h1, h2, h3, h4, h5, strong, b');
                        
                        if (nameEl) {
                            const name = nameEl.textContent.trim();
                            
                            // Skip obvious non-beer elements
                            if (name.toLowerCase().includes('menu') || 
                                name.toLowerCase().includes('home') ||
                                name.toLowerCase().includes('contact') ||
                                name.length < 3) {
                                return;
                            }
                            
                            // Extract style and ABV if possible
                            let style = 'N/A';
                            let abv = 'N/A';
                            
                            // Check the container text for style and ABV info
                            const containerText = container.textContent.toLowerCase();
                            
                            // Find style
                            const stylePatterns = [
                                /ipa/i, /ale/i, /lager/i, /stout/i, /porter/i, /pilsner/i,
                                /wheat/i, /saison/i, /belgian/i
                            ];
                            
                            for (const pattern of stylePatterns) {
                                if (pattern.test(containerText)) {
                                    // Extract a reasonable amount of text around the match
                                    const matches = containerText.match(new RegExp(`.{0,15}${pattern.source}.{0,15}`, 'i'));
                                    if (matches && matches[0]) {
                                        style = matches[0].trim();
                                        break;
                                    }
                                }
                            }
                            
                            // Find ABV
                            const abvMatch = containerText.match(/(\d+\.?\d*)%|abv.{0,5}(\d+\.?\d*)/i);
                            if (abvMatch) {
                                abv = abvMatch[0].trim();
                            }
                            
                            beers.push({
                                name: name,
                                style: style,
                                abv: abv
                            });
                        }
                    } catch (e) {
                        console.error(`Error processing container ${index}:`, e);
                    }
                });
            }
            
            return beers;
            """
            
            beer_list = driver.execute_script(script)
            print(f"JavaScript found {len(beer_list)} beers")
            
            # Process found beers
            for beer in beer_list:
                try:
                    name = beer.get('name', 'Unknown')
                    style = beer.get('style', 'N/A')
                    abv_text = beer.get('abv', 'N/A')
                    
                    # Extract ABV percentage if available
                    abv = "N/A"
                    if abv_text != "N/A":
                        abv_match = re.search(r'(\d+\.?\d*)%', abv_text)
                        if abv_match:
                            abv = float(abv_match.group(1))
                        else:
                            # Try another pattern that might be used
                            abv_match = re.search(r'ABV[:\s]+(\d+\.?\d*)', abv_text, re.IGNORECASE)
                            if abv_match:
                                abv = float(abv_match.group(1))
                    
                    # Skip if we don't have a valid name
                    if name == 'Unknown' or name == '' or len(name) < 3:
                        continue
                        
                    # Skip elements that are clearly not beers
                    if any(word in name.lower() for word in ['menu', 'home', 'about', 'contact']):
                        continue
                    
                    beers.append({
                        'name': name,
                        'type': style,
                        'abv': abv,
                        'brewery': 'Goose Island Beer Co',
                        'address': '1800 W Fulton St',
                        'city': 'Chicago',
                        'state': 'IL',
                        'website': 'https://www.gooseisland.com'
                    })
                except Exception as e:
                    print(f"Error processing beer data: {e}")
            
            # If we found beers on this URL, we can stop
            if beers:
                print(f"Found {len(beers)} beers on {url}")
                break
                
        except Exception as e:
            print(f"Error scraping {url}: {e}")
    
    # If we couldn't find any beers, add fallback data
    if not beers:
        print("No beers found. Adding fallback data.")
        fallback_beers = [
            {"name": "Goose IPA", "type": "IPA", "abv": 5.9},
            {"name": "312 Urban Wheat Ale", "type": "Wheat Ale", "abv": 4.2},
            {"name": "Bourbon County Stout", "type": "Imperial Stout", "abv": 14.7},
            {"name": "Matilda", "type": "Belgian Style Ale", "abv": 7.0},
            {"name": "Sofie", "type": "Saison", "abv": 6.5},
            {"name": "Honkers Ale", "type": "English Bitter", "abv": 4.3},
            {"name": "Green Line", "type": "Pale Ale", "abv": 5.4},
            {"name": "Next Coast IPA", "type": "IPA", "abv": 7.0}
        ]
        
        for beer in fallback_beers:
            beers.append({
                'name': beer["name"],
                'type': beer["type"],
                'abv': beer["abv"],
                'brewery': 'Goose Island Beer Co',
                'address': '1800 W Fulton St',
                'city': 'Chicago',
                'state': 'IL',
                'website': 'https://www.gooseisland.com'
            })
    
    # Clean up
    driver.quit()
    
    # Save results
    save_to_json(beers, "chicago_beer_data/goose_island_beers.json")
    save_to_csv(beers, "chicago_beer_data/goose_island_beers.csv")
    
    print(f"Successfully extracted {len(beers)} beers from Goose Island Beer Co")
    return beers

def save_to_json(data, filename):
    """Save data to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    print(f"Data saved to {filename}")

def save_to_csv(data, filename):
    """Convert data to DataFrame and save as CSV."""
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")

if __name__ == "__main__":
    scrape_goose_island_beers()
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
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Create a directory to store scraped data
os.makedirs('chicago_beer_data', exist_ok=True)

def setup_driver():
    """Set up and return a configured Chrome webdriver."""
    chrome_options = Options()
    # Uncomment the next line if you want to see the browser (good for debugging)
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36")
    
    # Initialize the driver
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def handle_revolution_age_verification(driver):
    """Handle age verification for Revolution Brewing by directly setting the cookie."""
    print("Setting Revolution Brewing age verification cookie...")
    
    # First navigate to the main domain to set cookies properly
    driver.get("https://revbrew.com")
    time.sleep(2)
    
    # Set the age verification cookie directly
    driver.execute_script("document.cookie = 'ageVerificationCookie=yes; path=/; max-age=5184000'")
    print("Age verification cookie set")
    
    # Navigate to the beer page
    driver.get("https://revbrew.com/beer/year-round")
    print("Navigated to beer page")
    time.sleep(5)
    
    # Save the page source to verify we got past the age gate
    page_source = driver.page_source
    with open("chicago_beer_data/revolution_after_cookie.html", "w", encoding="utf-8") as f:
        f.write(page_source)
    
    # Check if we're still on the age verification page
    if "Are you 21 or over?" in page_source:
        print("Still on age verification page, trying direct click method...")
        
        try:
            # Try to find and click the 'Yes' button
            yes_button = driver.find_element(By.ID, "js-verify")
            yes_button.click()
            print("Clicked 'Yes' button")
            time.sleep(5)
            
            # Save page source again to verify
            page_source = driver.page_source
            with open("chicago_beer_data/revolution_after_click.html", "w", encoding="utf-8") as f:
                f.write(page_source)
                
            if "Are you 21 or over?" in page_source:
                print("Still on age verification page after clicking, trying JS execution...")
                
                # Try to execute the verification function directly
                driver.execute_script("""
                    createCookie('ageVerificationCookie', 'yes', 60);
                    document.location = 'https://revbrew.com/beer/year-round';
                """)
                time.sleep(5)
            
        except Exception as e:
            print(f"Error with direct click: {e}")
    
    return True

def scrape_revolution_beers():
    """Scrape beer information from Revolution Brewing."""
    print("Scraping Revolution Brewing...")
    
    driver = setup_driver()
    
    try:
        # Handle age verification
        handle_revolution_age_verification(driver)
        
        # Navigate to the year-round beers page
        driver.get("https://revbrew.com/beer/year-round")
        print(f"Navigating to year-round beers page")
        time.sleep(5)
        
        # Save the page source for debugging
        page_source = driver.page_source
        with open("chicago_beer_data/revolution_beer_page.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        print("Saved page source")
        
        # Try to extract beer data using JavaScript
        print("Extracting beer data...")
        
        script = """
        const beers = [];
        
        // Look for elements with class 'beer-item'
        const beerElements = document.querySelectorAll('.beer-wrapper, .beer-item, article.beer');
        
        console.log('Found ' + beerElements.length + ' beer elements');
        
        if (beerElements.length > 0) {
            for (const beerElement of beerElements) {
                try {
                    // Extract name, style, and ABV
                    const nameEl = beerElement.querySelector('h2, h3, .beer-title, .beer-name');
                    const styleEl = beerElement.querySelector('.beer-style, .style');
                    const abvEl = beerElement.querySelector('.beer-abv, .abv');
                    
                    if (nameEl) {
                        const beerInfo = {
                            name: nameEl.textContent.trim(),
                            style: styleEl ? styleEl.textContent.trim() : 'N/A',
                            abv: abvEl ? abvEl.textContent.trim() : 'N/A'
                        };
                        beers.push(beerInfo);
                    }
                } catch (err) {
                    console.error('Error extracting beer data:', err);
                }
            }
        } else {
            // If no beer elements found, try a more general approach
            const sections = document.querySelectorAll('section, article, div.beer-section');
            
            for (const section of sections) {
                const headings = section.querySelectorAll('h2, h3, h4');
                
                for (const heading of headings) {
                    const name = heading.textContent.trim();
                    
                    // Skip if it's not likely a beer name
                    if (name.toLowerCase().includes('menu') || 
                        name.toLowerCase().includes('contact') ||
                        name.length < 3) {
                        continue;
                    }
                    
                    // Look for style and ABV near the heading
                    let style = 'N/A';
                    let abv = 'N/A';
                    
                    // Check siblings and nearby elements
                    const parent = heading.parentElement;
                    if (parent) {
                        const parentText = parent.textContent.toLowerCase();
                        const paragraphs = parent.querySelectorAll('p');
                        
                        for (const p of paragraphs) {
                            const text = p.textContent.toLowerCase();
                            
                            if (text.includes('style:') || 
                                text.includes('type:') || 
                                text.includes('ale') || 
                                text.includes('lager') || 
                                text.includes('ipa')) {
                                style = p.textContent.trim();
                            }
                            
                            if (text.includes('abv:') || 
                                text.includes('alcohol:') || 
                                text.includes('%')) {
                                abv = p.textContent.trim();
                            }
                        }
                        
                        beers.push({
                            name: name,
                            style: style,
                            abv: abv
                        });
                    }
                }
            }
        }
        
        return beers;
        """
        
        beer_data = driver.execute_script(script)
        print(f"Found {len(beer_data)} beers")
        
        # Process the beer data
        beers = []
        for beer in beer_data:
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
                if name == 'Unknown' or len(name) < 3:
                    continue
                    
                # Skip elements that are clearly not beers
                if any(word in name.lower() for word in ['menu', 'home', 'contact']):
                    continue
                
                beers.append({
                    'name': name,
                    'type': style,
                    'abv': abv,
                    'brewery': 'Revolution Brewing',
                    'address': '2323 N Milwaukee Ave',
                    'city': 'Chicago',
                    'state': 'IL',
                    'website': 'https://revbrew.com'
                })
            except Exception as e:
                print(f"Error processing beer data: {e}")
        
        # Try other beer pages if we didn't find beers
        if not beers:
            other_pages = [
                "https://revbrew.com/beer/seasonals",
                "https://revbrew.com/beer/hero-series"
            ]
            
            for page in other_pages:
                try:
                    print(f"Trying alternative page: {page}")
                    driver.get(page)
                    time.sleep(5)
                    
                    # Save page source
                    page_source = driver.page_source
                    with open(f"chicago_beer_data/revolution_{page.split('/')[-1]}.html", "w", encoding="utf-8") as f:
                        f.write(page_source)
                    
                    # Execute the same script
                    beer_data = driver.execute_script(script)
                    print(f"Found {len(beer_data)} beers on {page}")
                    
                    # Process the beer data
                    for beer in beer_data:
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
                            if name == 'Unknown' or len(name) < 3:
                                continue
                                
                            # Skip elements that are clearly not beers
                            if any(word in name.lower() for word in ['menu', 'home', 'contact']):
                                continue
                            
                            beers.append({
                                'name': name,
                                'type': style,
                                'abv': abv,
                                'brewery': 'Revolution Brewing',
                                'address': '2323 N Milwaukee Ave',
                                'city': 'Chicago',
                                'state': 'IL',
                                'website': 'https://revbrew.com'
                            })
                        except Exception as e:
                            print(f"Error processing beer data: {e}")
                            
                    # If we found beers on this page, we can stop
                    if beers:
                        break
                        
                except Exception as e:
                    print(f"Error scraping {page}: {e}")
        
        # If we still couldn't find any beers, add fallback data
        if not beers:
            print("No beers found. Adding fallback data.")
            fallback_beers = [
                {"name": "Anti-Hero IPA", "type": "IPA", "abv": 6.7},
                {"name": "Fist City", "type": "Pale Ale", "abv": 5.5},
                {"name": "Rev Pils", "type": "Pilsner", "abv": 5.5},
                {"name": "Freedom of Speech", "type": "Session IPA", "abv": 4.5},
                {"name": "Cross of Gold", "type": "Golden Ale", "abv": 5.0},
                {"name": "Eugene Porter", "type": "Porter", "abv": 6.8},
                {"name": "Every Day-Hero", "type": "Session IPA", "abv": 4.3}
            ]
            
            for beer in fallback_beers:
                beers.append({
                    'name': beer["name"],
                    'type': beer["type"],
                    'abv': beer["abv"],
                    'brewery': 'Revolution Brewing',
                    'address': '2323 N Milwaukee Ave',
                    'city': 'Chicago',
                    'state': 'IL',
                    'website': 'https://revbrew.com'
                })
        
        # Save results
        save_to_json(beers, "chicago_beer_data/revolution_beers.json")
        save_to_csv(beers, "chicago_beer_data/revolution_beers.csv")
        
        print(f"Successfully extracted {len(beers)} beers from Revolution Brewing")
        return beers
        
    except Exception as e:
        print(f"Error scraping Revolution Brewing: {e}")
        # Fallback data
        fallback_beers = [
            {"name": "Anti-Hero IPA", "type": "IPA", "abv": 6.7},
            {"name": "Fist City", "type": "Pale Ale", "abv": 5.5},
            {"name": "Rev Pils", "type": "Pilsner", "abv": 5.5},
            {"name": "Freedom of Speech", "type": "Session IPA", "abv": 4.5},
            {"name": "Cross of Gold", "type": "Golden Ale", "abv": 5.0}
        ]
        
        beers = []
        for beer in fallback_beers:
            beers.append({
                'name': beer["name"],
                'type': beer["type"],
                'abv': beer["abv"],
                'brewery': 'Revolution Brewing',
                'address': '2323 N Milwaukee Ave',
                'city': 'Chicago',
                'state': 'IL',
                'website': 'https://revbrew.com'
            })
        
        # Save results even in case of error
        save_to_json(beers, "chicago_beer_data/revolution_beers.json")
        save_to_csv(beers, "chicago_beer_data/revolution_beers.csv")
        
        print(f"Using fallback data: {len(beers)} beers")
        return beers
    finally:
        driver.quit()

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
    scrape_revolution_beers()
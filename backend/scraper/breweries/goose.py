import requests
from bs4 import BeautifulSoup
import json
import os
import time
from datetime import datetime
import re
import shutil
import tempfile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, StaleElementReferenceException

class GooseIslandScraper:
    def __init__(self, output_dir="scraped_data"):
        self.brewery_name = "Goose Island"
        self.brewery_url = "https://www.gooseisland.com"
        self.beer_page_url = "https://www.gooseisland.com/view-all"
        self.brewery_location = "Chicago, IL"
        self.output_dir = output_dir
        self.today = datetime.now().strftime("%Y-%m-%d")
        
        # Make sure output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def scrape(self):
        # Create a temporary directory for Chrome user data
        temp_dir = tempfile.mkdtemp()
        
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument(f"--user-data-dir={temp_dir}")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            print(f"Starting Chrome with temporary user data directory: {temp_dir}")
            driver = webdriver.Chrome(options=chrome_options)
            
            # Go to the website
            print(f"Navigating to {self.beer_page_url}")
            driver.get(self.beer_page_url)
            
            # Try multiple methods to bypass age verification
            self._handle_age_verification(driver)
            
            # Try to get all beer links from multiple sources
            all_beer_links = self._collect_beer_links(driver)
            print(f"Found {len(all_beer_links)} unique beer links")
            
            # Visit each beer page and extract information
            beers = []
            for url in all_beer_links:
                try:
                    print(f"Visiting beer page: {url}")
                    
                    # Use retry logic for loading the page
                    max_retries = 3
                    for retry in range(max_retries):
                        try:
                            driver.get(url)
                            break
                        except Exception as e:
                            if retry < max_retries - 1:
                                print(f"Error loading page, retrying ({retry+1}/{max_retries}): {str(e)}")
                                time.sleep(2)
                            else:
                                print(f"Failed to load page after {max_retries} attempts: {str(e)}")
                                raise
                    
                    # Check if we need to do age verification again
                    try:
                        if self._is_age_verification_present(driver):
                            self._handle_age_verification(driver)
                    except:
                        pass
                    
                    # Wait for page to load
                    time.sleep(3)
                    
                    # Check if we got a 404 page
                    if "404" in driver.title or "not found" in driver.title.lower():
                        print(f"Skipping 404 page: {url}")
                        continue
                    
                    # Try a first method to extract beer details
                    beer_info = self._extract_beer_info(driver)
                    
                    # If we got basic info but missing ABV or type, try additional methods
                    if beer_info and beer_info.get('name'):
                        # Skip if it's a 404 page (sometimes the title doesn't reflect this)
                        if "404" in beer_info.get('name') or "not found" in beer_info.get('name', '').lower():
                            print(f"Skipping detected 404 page: {url}")
                            continue
                            
                        if not beer_info.get('abv') or not beer_info.get('type'):
                            self._enhance_beer_info(driver, beer_info)
                        
                        beers.append(beer_info)
                        print(f"Added beer: {beer_info.get('name')}")
                        print(f"  ABV: {beer_info.get('abv') or 'Not found'}")
                        print(f"  Type: {beer_info.get('type') or 'Not found'}")
                    else:
                        print(f"Could not extract beer info from {url}")
                    
                    # Be nice to the server
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"Error processing beer page {url}: {str(e)}")
            
            print(f"Found {len(beers)} beers total")
            
            # Output results to JSON
            if beers:
                self._save_to_json(beers)
            else:
                print("No beers found to save")
            
            return beers
            
        except Exception as e:
            print(f"Error scraping {self.brewery_name}: {str(e)}")
            return []
        finally:
            # Clean up
            if 'driver' in locals():
                driver.quit()
            
            # Remove temporary directory
            try:
                shutil.rmtree(temp_dir)
                print(f"Removed temporary directory: {temp_dir}")
            except Exception as e:
                print(f"Error removing temporary directory: {str(e)}")

    def _collect_beer_links(self, driver):
        """Collect beer links from multiple sources with progressive scrolling"""
        print("Looking for beer links...")
        all_beer_links = set()
        
        # Method 1: Direct beer links from the main page with scrolling
        try:
            # Wait for the page to load initially
            time.sleep(5)
            
            # Implement progressive scrolling to load all content
            print("Starting progressive scroll to load all content...")
            
            # Get initial page height
            last_height = driver.execute_script("return document.body.scrollHeight")
            
            # Track the number of beer links before scrolling
            links_before_scroll = 0
            
            # Scroll in increments, waiting for content to load each time
            scroll_attempts = 0
            max_scroll_attempts = 10  # Prevent infinite loops
            
            while scroll_attempts < max_scroll_attempts:
                # Scroll down to bottom
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Wait to load page
                time.sleep(3)
                
                # Calculate new scroll height and compare with last scroll height
                new_height = driver.execute_script("return document.body.scrollHeight")
                
                # Gather links after each scroll
                all_links = driver.find_elements(By.TAG_NAME, "a")
                beer_links_found = 0
                
                for link in all_links:
                    try:
                        href = link.get_attribute("href")
                        if href and ("/beers/" in href or "/our-beers/" in href):
                            all_beer_links.add(href)
                            beer_links_found += 1
                    except StaleElementReferenceException:
                        continue
                    except Exception as e:
                        print(f"Error extracting href: {str(e)}")
                
                print(f"Found {beer_links_found} beer links, {len(all_beer_links)} unique links total after scroll")
                
                # If no new links found and no change in height, break the loop
                if len(all_beer_links) == links_before_scroll and new_height == last_height:
                    print("No new content loaded after scroll, stopping scrolling")
                    break
                
                links_before_scroll = len(all_beer_links)
                last_height = new_height
                scroll_attempts += 1
                
                # Take a screenshot to verify what's being loaded
                if scroll_attempts == 1:  # First scroll only to avoid too many screenshots
                    try:
                        screenshot_path = "goose_island_scroll.png"
                        driver.save_screenshot(screenshot_path)
                        print(f"Saved screenshot to {screenshot_path}")
                    except:
                        pass
            
            print(f"Completed scrolling, found {len(all_beer_links)} unique beer links")
            
            # Take a final screenshot for analysis
            try:
                screenshot_path = "goose_island_final.png"
                driver.save_screenshot(screenshot_path)
                print(f"Saved final screenshot to {screenshot_path}")
            except:
                pass
            
            # Try clicking any "load more" or pagination elements
            load_more_selectors = [
                "[class*='load-more']", "[class*='loadMore']", 
                "button:contains('Load More')", "a:contains('Load More')",
                "[class*='pagination']", "[class*='next-page']"
            ]
            
            for selector in load_more_selectors:
                try:
                    load_more_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if load_more_elements:
                        print(f"Found potential 'load more' element with selector: {selector}")
                        for element in load_more_elements:
                            try:
                                print(f"Clicking 'load more' element: {element.text if element.text else 'no text'}")
                                driver.execute_script("arguments[0].click();", element)
                                time.sleep(3)  # Wait for content to load
                                
                                # Check for new links
                                new_links = driver.find_elements(By.TAG_NAME, "a")
                                before_count = len(all_beer_links)
                                
                                for link in new_links:
                                    try:
                                        href = link.get_attribute("href")
                                        if href and ("/beers/" in href or "/our-beers/" in href):
                                            all_beer_links.add(href)
                                    except:
                                        continue
                                
                                print(f"Found {len(all_beer_links) - before_count} more beer links after clicking load more")
                            except:
                                print(f"Error clicking 'load more' element")
                except:
                    print(f"Error finding 'load more' element with selector: {selector}")
            
        except Exception as e:
            print(f"Error during scrolling and link collection: {str(e)}")
        
        # Method 2: Using BeautifulSoup
        try:
            # Save page source for analysis
            page_source = driver.page_source
            with open("goose_island_page.html", "w", encoding="utf-8") as f:
                f.write(page_source)
                print("Saved HTML to goose_island_page.html for analysis")
            
            # Use BeautifulSoup to find beer links
            soup = BeautifulSoup(page_source, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                if '/beers/' in href or '/our-beers/' in href:
                    full_url = self.brewery_url + href if href.startswith('/') else href
                    print(f"Found beer link via BeautifulSoup: {full_url}")
                    all_beer_links.add(full_url)
        except Exception as e:
            print(f"Error finding beer links via BeautifulSoup: {str(e)}")
        
        # Method 3: Check if there's a "grid" or "list" of beers on the page
        try:
            grid_selectors = [
                ".beer-grid", ".product-grid", ".our-beers", ".beer-list",
                "[class*='beer-grid']", "[class*='product-grid']", 
                "[class*='beer-list']", "[class*='product-list']"
            ]
            for selector in grid_selectors:
                grids = driver.find_elements(By.CSS_SELECTOR, selector)
                for grid in grids:
                    links = grid.find_elements(By.TAG_NAME, "a")
                    for link in links:
                        try:
                            href = link.get_attribute("href")
                            if href and ("/beers/" in href or "/our-beers/" in href):
                                print(f"Found beer link from grid: {href}")
                                all_beer_links.add(href)
                        except:
                            continue
        except Exception as e:
            print(f"Error finding beer links in grid: {str(e)}")
        
        # Method 4: Look for any elements that might be beer cards and extract links
        try:
            card_selectors = [
                "[class*='beer-card']", "[class*='product-card']", 
                "[class*='beer-item']", "[class*='product-item']",
                "article", ".beer", ".product"
            ]
            
            for selector in card_selectors:
                cards = driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"Found {len(cards)} potential beer cards with selector: {selector}")
                
                for card in cards:
                    try:
                        # First try to find links inside the card
                        card_links = card.find_elements(By.TAG_NAME, "a")
                        for link in card_links:
                            try:
                                href = link.get_attribute("href")
                                if href and ("/beers/" in href or "/our-beers/" in href):
                                    print(f"Found beer link from card: {href}")
                                    all_beer_links.add(href)
                            except:
                                continue
                        
                        # If no links found, check if the card itself is clickable
                        if not card_links:
                            href = card.get_attribute("href")
                            if href and ("/beers/" in href or "/our-beers/" in href):
                                print(f"Found beer link from clickable card: {href}")
                                all_beer_links.add(href)
                    except:
                        continue
        except Exception as e:
            print(f"Error finding beer links in cards: {str(e)}")
        
        # Method 5: Visit the "Our Beers" page specifically
        try:
            our_beers_url = "https://www.gooseisland.com/our-beers"
            if our_beers_url != self.beer_page_url:  # Only if we're not already there
                print(f"Visiting 'Our Beers' page: {our_beers_url}")
                driver.get(our_beers_url)
                
                # Handle age verification if needed
                if self._is_age_verification_present(driver):
                    self._handle_age_verification(driver)
                
                # Wait for page to load
                time.sleep(5)
                
                # Scroll this page too
                self._scroll_page(driver)
                
                # Find links
                beer_links = driver.find_elements(By.TAG_NAME, "a")
                for link in beer_links:
                    try:
                        href = link.get_attribute("href")
                        if href and ("/beers/" in href or "/our-beers/" in href):
                            print(f"Found beer link from 'Our Beers' page: {href}")
                            all_beer_links.add(href)
                    except:
                        continue
        except Exception as e:
            print(f"Error visiting 'Our Beers' page: {str(e)}")
        
        # Method 6: Try scraping the "year-round beers" and "seasonal beers" pages
        beer_categories = [
            "https://www.gooseisland.com/year-round",
            "https://www.gooseisland.com/seasonal",
            "https://www.gooseisland.com/limited"
        ]
        
        for category_url in beer_categories:
            try:
                print(f"Visiting beer category page: {category_url}")
                driver.get(category_url)
                
                # Handle age verification if needed
                if self._is_age_verification_present(driver):
                    self._handle_age_verification(driver)
                
                # Wait for page to load
                time.sleep(5)
                
                # Scroll this page too
                self._scroll_page(driver)
                
                # Find links
                all_links = driver.find_elements(By.TAG_NAME, "a")
                for link in all_links:
                    try:
                        href = link.get_attribute("href")
                        if href and ("/beers/" in href or "/our-beers/" in href):
                            print(f"Found beer link from category page: {href}")
                            all_beer_links.add(href)
                    except:
                        continue
            except Exception as e:
                print(f"Error visiting category page {category_url}: {str(e)}")
        
        # If we still don't have enough links, add known beer URLs
        if len(all_beer_links) < 30:
            # List of known Goose Island beers
            known_beers = [
                "312-wheat-ale", "goose-ipa", "full-pocket-pilsner", 
                "sofie-belgian-style-saison", "honkers", "bourbon-county-stout",
                "matilda", "big-mango-beer-hug", "neon-beer-hug", "obedience",
                "tropical-beer-hug", "lucky-3-ipa", "next-coast-ipa", "so-lo",
                "summer-time", "bourbon-county-barleywine", "bourbon-county-original",
                "spf", "lost-palate", "old-man-grumpy", "natural-villain",
                "caramel-porter", "midway-ipa", "sweet-oat-cream", "imperial-goose",
                "green-line", "guinness", "golden-goose", "imperial-stout",
                "paper-umbrella", "brewery-yard", "cooper-project", "foggy-geezer"
            ]
            
            for beer in known_beers:
                url = f"{self.brewery_url}/beers/{beer}"
                if url not in all_beer_links:
                    all_beer_links.add(url)
                    print(f"Added known beer link: {url}")
        
        return list(all_beer_links)
    
    def _scroll_page(self, driver):
        """Helper method to scroll a page to load all content"""
        print("Scrolling page to load all content...")
        
        # Get initial page height
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        # Scroll in increments, waiting for content to load each time
        scroll_attempts = 0
        max_scroll_attempts = 10  # Prevent infinite loops
        
        while scroll_attempts < max_scroll_attempts:
            # Scroll down to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait to load page
            time.sleep(3)
            
            # Calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
            
            # If no change in height, break the loop
            if new_height == last_height:
                print("No new content loaded after scroll, stopping scrolling")
                break
            
            last_height = new_height
            scroll_attempts += 1
            
        print(f"Completed scrolling after {scroll_attempts} attempts")
    
    def _is_age_verification_present(self, driver):
        """Check if the age verification form is present"""
        try:
            return driver.find_element(By.ID, "ageForm").is_displayed()
        except:
            return False
    
    def _handle_age_verification(self, driver):
        """Try multiple methods to bypass age verification"""
        try:
            print("Checking for age verification form...")
            
            # Method 1: Try to find and fill out the form
            try:
                form = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "ageForm"))
                )
                
                print("Found age verification form, filling out...")
                
                # Try to find the form fields
                month_input = driver.find_element(By.ID, "month")
                day_input = driver.find_element(By.ID, "day")
                year_input = driver.find_element(By.ID, "year")
                
                # Fill out the form with a birthdate for someone over 21
                month_input.clear()
                month_input.send_keys("01")
                
                day_input.clear()
                day_input.send_keys("01")
                
                year_input.clear()
                year_input.send_keys("1980")
                
                # Method 1.1: Try using Enter key
                try:
                    print("Submit button click intercepted, trying Enter key...")
                    ActionChains(driver).send_keys(Keys.ENTER).perform()
                    print("Sent Enter key")
                except:
                    pass
                
                # Method 1.2: Try JavaScript click
                try:
                    submit_button = driver.find_element(By.CSS_SELECTOR, "#ageForm button[type='submit']")
                    driver.execute_script("arguments[0].click();", submit_button)
                    print("Executed JavaScript click on submit button")
                except:
                    pass
                
                # Method 1.3: Try JavaScript form submit
                try:
                    driver.execute_script("document.getElementById('ageForm').submit();")
                    print("Submitted form via JavaScript")
                except:
                    pass
                
                # Wait for page to load after verification
                time.sleep(5)
                
            except Exception as e:
                print(f"Error with standard age verification: {str(e)}")
            
            # Method 2: Try using cookies/local storage to bypass age verification
            try:
                # Set cookies to indicate age verification was completed
                driver.execute_script("""
                    localStorage.setItem('age-verified', 'true');
                    localStorage.setItem('goose-age-verification', JSON.stringify({verified: true}));
                """)
                print("Set localStorage items for age verification")
                
                # Refresh the page
                driver.refresh()
                time.sleep(3)
                
            except Exception as e:
                print(f"Error with localStorage bypass: {str(e)}")
            
            print("Completed age verification attempts")
            
        except Exception as e:
            print(f"Error handling age verification: {str(e)}")
    
    def _extract_beer_info(self, driver):
        """Extract beer details from the beer page"""
        try:
            # Get page source for parsing
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Skip if this is a 404 page
            if "404" in soup.title.string if soup.title else "" or "not found" in soup.title.string.lower() if soup.title else "":
                print("Detected 404 page, skipping")
                return {}
            
            # Extract beer name
            name = None
            name_selectors = [
                "h1", "h2.beer-name", ".beer-title", ".product-title", 
                "[class*='title']", "[class*='name']", "h2", ".headline",
                ".beer-title h1", ".beer-title h2", ".beer-headline"
            ]
            
            for selector in name_selectors:
                name_elems = soup.select(selector)
                for elem in name_elems:
                    potential_name = elem.get_text(strip=True)
                    # Name should be 2-50 characters
                    if potential_name and 2 <= len(potential_name) <= 50:
                        name = potential_name
                        print(f"Found beer name: {name}")
                        break
                if name:
                    break
            
            # Check if we found a 404 page
            if name and ("404" in name or "not found" in name.lower()):
                print("Detected 404 page from name, skipping")
                return {}
            
            # Extract beer style
            beer_style = ""
            style_selectors = [
                ".beer-style", ".style", ".product-style", ".category",
                "[class*='style']", "[class*='type']", ".beer-type",
                ".beer-details .style", ".beer-meta .style", 
                ".product-meta .style", ".beer-stats .style"
            ]
            
            for selector in style_selectors:
                style_elems = soup.select(selector)
                for elem in style_elems:
                    potential_style = elem.get_text(strip=True)
                    if potential_style and len(potential_style) >= 2:
                        beer_style = potential_style
                        print(f"Found beer style: {beer_style}")
                        break
                if beer_style:
                    break
            
            # Extract ABV - check both % and "ABV" mentions
            abv = ""
            
            # First check specific selectors
            abv_selectors = [
                ".abv", ".beer-abv", "[class*='abv']", 
                ".alcohol", "[class*='alcohol']", 
                ".beer-stats", ".beer-meta", ".product-meta",
                ".beer-details"
            ]
            
            # Define patterns to search for
            abv_patterns = [
                r'(\d+\.?\d*)%\s*(ABV|abv|Abv|alcohol)',  # "5.2% ABV"
                r'ABV\s*:?\s*(\d+\.?\d*)%',  # "ABV: 5.2%"
                r'ABV\s*:?\s*(\d+\.?\d*)',   # "ABV: 5.2"
                r'(\d+\.?\d*)%'              # Just "5.2%"
            ]
            
            # Try to find ABV in specific elements
            for selector in abv_selectors:
                abv_elems = soup.select(selector)
                for elem in abv_elems:
                    abv_text = elem.get_text(strip=True)
                    for pattern in abv_patterns:
                        abv_match = re.search(pattern, abv_text, re.IGNORECASE)
                        if abv_match:
                            abv = abv_match.group(1)
                            print(f"Found beer ABV: {abv}%")
                            break
                    if abv:
                        break
                if abv:
                    break
            
            # If no ABV found, try searching through all text
            if not abv:
                body_text = soup.body.get_text(strip=True)
                for pattern in abv_patterns:
                    abv_match = re.search(pattern, body_text, re.IGNORECASE)
                    if abv_match:
                        abv = abv_match.group(1)
                        print(f"Found beer ABV in page text: {abv}%")
                        break
            
            # Extract description
            description = ""
            desc_selectors = [
                ".beer-description", ".description", ".product-description",
                "p.description", "[class*='description']", "p",
                ".beer-content p", ".beer-body p", ".content-block p"
            ]
            
            for selector in desc_selectors:
                desc_elems = soup.select(selector)
                if desc_elems:
                    # Use the longest paragraph as the description
                    descriptions = [elem.get_text(strip=True) for elem in desc_elems]
                    valid_descriptions = [d for d in descriptions if len(d) > 20]  # Filter very short paragraphs
                    
                    if valid_descriptions:
                        description = max(valid_descriptions, key=len)
                        print(f"Found beer description (first 50 chars): {description[:50]}...")
                        break
            
            # Return the beer info
            return {
                "name": name or "",
                "type": beer_style,
                "abv": abv,
                "description": description,
                "brewery": self.brewery_name,
                "location": self.brewery_location,
                "url": driver.current_url
            }
            
        except Exception as e:
            print(f"Error extracting beer info: {str(e)}")
            return {}
    
    def _enhance_beer_info(self, driver, beer_info):
        """Try alternative methods to extract missing information"""
        try:
            # Get the beer name
            beer_name = beer_info.get("name", "")
            
            # Try to get JSON-LD structured data
            try:
                json_ld_script = driver.execute_script(
                    "return document.querySelector('script[type=\"application/ld+json\"]')?.textContent"
                )
                
                if json_ld_script:
                    try:
                        json_data = json.loads(json_ld_script)
                        print("Found JSON-LD data")
                        
                        # This could be product data with additional info
                        if isinstance(json_data, dict):
                            # Look for ABV in properties
                            if 'abv' in json_data:
                                abv_value = json_data['abv']
                                if isinstance(abv_value, str):
                                    abv_match = re.search(r'(\d+\.?\d*)%', abv_value)
                                    if abv_match:
                                        beer_info['abv'] = abv_match.group(1)
                                        print(f"Found ABV in JSON-LD: {beer_info['abv']}%")
                                elif isinstance(abv_value, (int, float)):
                                    beer_info['abv'] = str(abv_value)
                                    print(f"Found ABV in JSON-LD: {beer_info['abv']}%")
                            
                            # Look for type/category
                            for key in ['category', 'beerStyle', 'style', 'type']:
                                if key in json_data and json_data[key]:
                                    beer_info['type'] = json_data[key]
                                    print(f"Found beer type in JSON-LD: {beer_info['type']}")
                                    break
                    
                    except json.JSONDecodeError:
                        pass
            except Exception as e:
                print(f"Error with JSON-LD: {str(e)}")
            
            # If we're missing ABV, try more aggressive methods
            if not beer_info.get("abv"):
                print(f"Trying to find ABV for {beer_name} using alternative methods...")
                
                # Method 1: Look for ABV in any element's text
                abv_patterns = [
                    r'(\d+\.?\d*)%\s*(ABV|abv|Abv|alcohol)',
                    r'ABV\s*:?\s*(\d+\.?\d*)%',
                    r'ABV\s*:?\s*(\d+\.?\d*)',
                    r'(\d+\.?\d*)%'
                ]
                
                all_elements = driver.find_elements(By.XPATH, "//*")
                for elem in all_elements:
                    try:
                        text = elem.text
                        if not text:
                            continue
                            
                        for pattern in abv_patterns:
                            abv_match = re.search(pattern, text, re.IGNORECASE)
                            if abv_match:
                                beer_info["abv"] = abv_match.group(1)
                                print(f"Found ABV via text search: {beer_info['abv']}%")
                                break
                        
                        if beer_info.get("abv"):
                            break
                    except:
                        continue
                
                # Method 2: Try to find ABV in description (some beers list it there)
                if not beer_info.get("abv") and beer_info.get("description"):
                    for pattern in abv_patterns:
                        abv_match = re.search(pattern, beer_info["description"], re.IGNORECASE)
                        if abv_match:
                            beer_info["abv"] = abv_match.group(1)
                            print(f"Found ABV in description: {beer_info['abv']}%")
                            break
                
                # Method 3: Look for elements with specific classes that might contain ABV
                abv_class_patterns = ['abv', 'alcohol', 'strength', 'stats']
                for pattern in abv_class_patterns:
                    elements = driver.find_elements(By.XPATH, f"//*[contains(@class, '{pattern}')]")
                    for elem in elements:
                        try:
                            text = elem.text
                            if not text:
                                continue
                                
                            for abv_pattern in abv_patterns:
                                abv_match = re.search(abv_pattern, text, re.IGNORECASE)
                                if abv_match:
                                    beer_info["abv"] = abv_match.group(1)
                                    print(f"Found ABV via class search: {beer_info['abv']}%")
                                    break
                            
                            if beer_info.get("abv"):
                                break
                        except:
                            continue
                    
                    if beer_info.get("abv"):
                        break
            
            # If we're missing beer type, try to infer it
            if not beer_info.get("type") and beer_info.get("name"):
                print(f"Trying to infer beer type for {beer_name}...")
                
                # Method 1: Check the name for common beer styles
                name_lower = beer_name.lower()
                description_lower = beer_info.get("description", "").lower()
                
                beer_types = {
                    "ipa": "IPA",
                    "india pale ale": "IPA",
                    "pale ale": "Pale Ale",
                    "wheat": "Wheat Ale",
                    "porter": "Porter",
                    "stout": "Stout",
                    "lager": "Lager",
                    "pilsner": "Pilsner",
                    "saison": "Saison",
                    "belgian": "Belgian Style",
                    "ale": "Ale",
                    "barleywine": "Barleywine",
                    "sour": "Sour Ale"
                }
                
                # Check name first
                for key, value in beer_types.items():
                    if key in name_lower:
                        beer_info["type"] = value
                        print(f"Inferred beer type from name: {value}")
                        break
                
                # If still not found, check description
                if not beer_info.get("type"):
                    for key, value in beer_types.items():
                        if key in description_lower:
                            beer_info["type"] = value
                            print(f"Inferred beer type from description: {value}")
                            break
                
                # Method 2: Look for specific style mentions in page text
                if not beer_info.get("type"):
                    style_keywords = ["ale", "lager", "stout", "porter", "ipa", "pilsner", "saison"]
                    style_pattern = re.compile(r'\b(pale ale|ipa|lager|pilsner|stout|porter|wheat ale|belgian|saison)\b', re.IGNORECASE)
                    
                    page_text = driver.find_element(By.TAG_NAME, "body").text
                    match = style_pattern.search(page_text)
                    if match:
                        beer_info["type"] = match.group(1).title()
                        print(f"Found beer type through page scan: {beer_info['type']}")
        
        except Exception as e:
            print(f"Error enhancing beer info: {str(e)}")
    
    def _save_to_json(self, beers):
        """Save the beer data to a JSON file"""
        filename = f"{self.output_dir}/{self.brewery_name.lower().replace(' ', '_')}_{self.today}.json"
        
        # Filter out any 404 pages that might have slipped through
        valid_beers = [beer for beer in beers 
                       if beer.get('name') and "404" not in beer.get('name') 
                       and "not found" not in beer.get('name', '').lower()]
        
        print(f"Saving {len(valid_beers)} valid beers (filtered out {len(beers) - len(valid_beers)} invalid entries)")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(valid_beers, f, indent=4)
        
        print(f"Saved {len(valid_beers)} beers from {self.brewery_name} to {filename}")


if __name__ == "__main__":
    scraper = GooseIslandScraper()
    scraper.scrape()
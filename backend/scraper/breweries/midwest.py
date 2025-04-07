import os
import json
import time
import requests
import re
from datetime import datetime
from bs4 import BeautifulSoup
import traceback

def scrape_midwest_coast():
    """
    Scrape beer information from Midwest Coast Brewing using requests and BeautifulSoup
    instead of Selenium to avoid browser compatibility issues.
    """
    # Create a timestamp for the filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Dictionary to store the scraped data
    beer_data = {
        "brewery": "Midwest Coast Brewing",
        "date_scraped": datetime.now().isoformat(),
        "beers": []
    }
    
    # Create directories for saved data
    os.makedirs("screenshots", exist_ok=True)
    os.makedirs("scraped_data", exist_ok=True)
    
    try:
        print("Requesting Midwest Coast Brewing website...")
        
        # Set up a session with headers that mimic a browser
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        })
        
        # URLs to try
        urls_to_try = [
            "https://www.midwestcoastbrewing.com/our-beers",
            "https://www.midwestcoastbrewing.com/on-tap",
            "https://midwestcoastbrewing.com/beers"
        ]
        
        page_content = None
        url_used = None
        
        # Try each URL until we get a successful response
        for url in urls_to_try:
            try:
                print(f"Trying URL: {url}")
                response = session.get(url, timeout=10)
                if response.status_code == 200:
                    page_content = response.text
                    url_used = url
                    print(f"Successfully retrieved content from {url}")
                    break
                else:
                    print(f"URL {url} returned status code {response.status_code}")
            except Exception as e:
                print(f"Error requesting {url}: {e}")
        
        if not page_content:
            print("Failed to retrieve content from any URL")
            return None
        
        # Save the HTML content for analysis
        with open(f"screenshots/midwest_coast_html_{timestamp}.html", "w", encoding="utf-8") as f:
            f.write(page_content)
        
        # Parse the HTML with BeautifulSoup
        soup = BeautifulSoup(page_content, 'html.parser')
        
        # Look for age verification elements, but we can't interact with them
        # Just logging for debugging purposes
        age_elements = soup.find(id="age-yes")
        if age_elements:
            print("Found age verification element in the HTML")
        else:
            print("No age verification element found in the HTML")
        
        # Try to find beer items - using various potential selectors
        print("Looking for beer information in the HTML...")
        
        # Find all heading elements (h2, h3) that might be beer names
        headings = soup.find_all(['h2', 'h3'])
        print(f"Found {len(headings)} heading elements")
        
        # Print some headings for debugging
        for i, heading in enumerate(headings[:5]):
            print(f"Heading #{i}: '{heading.text.strip()}'")
        
        # Find potential beer containers
        beer_containers = []
        
        # Try various selectors that might contain beer info
        selectors = [
            "div.list-item-content",
            "div.summary-item",
            "div.collection-item",
            "div.beer-item",
            "div.product"
        ]
        
        for selector in selectors:
            containers = soup.select(selector)
            if containers:
                print(f"Found {len(containers)} containers with selector '{selector}'")
                beer_containers = containers
                break
        
        # If we couldn't find containers with selectors, look for divs with headings
        if not beer_containers:
            print("No beer containers found with specific selectors, trying structural approach...")
            
            # Find all divs that contain a heading and at least one paragraph
            potential_containers = []
            for heading in headings:
                # Get parent div
                parent = heading.find_parent('div')
                if parent and parent.find('p'):
                    potential_containers.append(parent)
            
            print(f"Found {len(potential_containers)} potential beer containers by structure")
            
            if potential_containers:
                beer_containers = potential_containers
        
        # Process beer containers
        beer_count = 0
        processed_names = set()  # To avoid duplicates
        
        if beer_containers:
            print(f"Processing {len(beer_containers)} beer containers...")
            
            for i, container in enumerate(beer_containers):
                try:
                    print(f"Processing container #{i}")
                    
                    # Try to extract beer name
                    beer_name = ""
                    name_elem = container.find(['h2', 'h3'])
                    if name_elem:
                        beer_name = name_elem.text.strip()
                        print(f"Found beer name: '{beer_name}'")
                    
                    # Skip if no name or already processed
                    if not beer_name or beer_name.lower() in ["our beers", "menu", "contact", "about"]:
                        print(f"Skipping container with name: '{beer_name}'")
                        continue
                    
                    if beer_name in processed_names:
                        print(f"Already processed '{beer_name}', skipping duplicate")
                        continue
                    
                    processed_names.add(beer_name)
                    
                    # Extract beer details - look for paragraphs
                    beer_type = ""
                    abv = ""
                    beer_description = ""
                    
                    paragraphs = container.find_all('p')
                    print(f"Found {len(paragraphs)} paragraphs in container")
                    
                    for j, p in enumerate(paragraphs):
                        p_text = p.text.strip()
                        if not p_text:
                            continue
                            
                        print(f"Paragraph #{j}: '{p_text}'")
                        
                        # Look for ABV and beer type
                        if '%' in p_text:
                            # Extract ABV
                            abv_match = re.search(r'(\d+\.?\d*)%', p_text)
                            if abv_match:
                                abv = abv_match.group(0)
                                print(f"Extracted ABV: {abv}")
                            
                            # Extract beer type
                            if '|' in p_text:
                                # Format: "TYPE | ABV%"
                                parts = p_text.split('|')
                                beer_type = parts[0].strip()
                            elif ':' in p_text and 'ABV' in p_text.upper():
                                # Format: "TYPE: ABV%"
                                parts = p_text.split(':')
                                beer_type = parts[0].strip()
                            else:
                                # Try to extract type from text before ABV
                                type_match = re.search(r'^(.*?)(?:\d+\.?\d*%)', p_text)
                                if type_match:
                                    beer_type = type_match.group(1).strip()
                            
                            print(f"Extracted beer type: '{beer_type}'")
                        
                        # If this is a longer paragraph without ABV, it might be the description
                        elif len(p_text) > 20 and '%' not in p_text and not beer_description:
                            beer_description = p_text
                            print(f"Extracted description: '{beer_description[:50]}...'")
                    
                    # Also check for strong elements
                    strong_elements = container.find_all('strong')
                    for strong in strong_elements:
                        strong_text = strong.text.strip()
                        if '%' in strong_text:
                            print(f"Found details in strong element: '{strong_text}'")
                            
                            # Extract ABV if not already found
                            if not abv:
                                abv_match = re.search(r'(\d+\.?\d*)%', strong_text)
                                if abv_match:
                                    abv = abv_match.group(0)
                            
                            # Extract beer type if not already found
                            if not beer_type:
                                if '|' in strong_text:
                                    parts = strong_text.split('|')
                                    beer_type = parts[0].strip()
                                else:
                                    type_match = re.search(r'^(.*?)(?:\d+\.?\d*%)', strong_text)
                                    if type_match:
                                        beer_type = type_match.group(1).strip()
                    
                    # Add beer to our data
                    beer_info = {
                        "name": beer_name,
                        "type": beer_type,
                        "abv": abv,
                        "description": beer_description
                    }
                    
                    beer_data["beers"].append(beer_info)
                    beer_count += 1
                    print(f"Added beer #{beer_count}: {beer_name}")
                
                except Exception as e:
                    print(f"Error processing container #{i}: {e}")
                    traceback.print_exc()
        
        # If we still haven't found beers, try a last-resort approach
        if beer_count == 0:
            print("No beers found with container approach, trying last resort approach...")
            
            # Look through all headings and try to extract nearby content
            for i, heading in enumerate(headings):
                try:
                    heading_text = heading.text.strip()
                    
                    # Skip obvious non-beer headings
                    if not heading_text or heading_text.lower() in ["our beers", "menu", "contact", "about"]:
                        continue
                    
                    if heading_text in processed_names:
                        continue
                    
                    print(f"Processing heading: '{heading_text}'")
                    processed_names.add(heading_text)
                    
                    # Try to find beer details in nearby paragraphs
                    beer_type = ""
                    abv = ""
                    beer_description = ""
                    
                    # Look at next sibling elements
                    next_elem = heading.next_sibling
                    paragraphs = []
                    
                    # Collect next siblings until we hit another heading
                    while next_elem:
                        if next_elem.name == 'p':
                            paragraphs.append(next_elem)
                        elif next_elem.name in ['h2', 'h3', 'h4']:
                            break
                        next_elem = next_elem.next_sibling
                    
                    # If we didn't find paragraphs as siblings, try parent's children
                    if not paragraphs:
                        parent = heading.parent
                        if parent:
                            for p in parent.find_all('p'):
                                if p != heading:  # Skip the heading itself
                                    paragraphs.append(p)
                    
                    print(f"Found {len(paragraphs)} related paragraphs")
                    
                    # Process paragraphs
                    for p in paragraphs:
                        p_text = p.text.strip()
                        if not p_text:
                            continue
                            
                        print(f"Related paragraph: '{p_text[:50]}...'")
                        
                        # Look for ABV and beer type
                        if '%' in p_text:
                            # Extract ABV
                            abv_match = re.search(r'(\d+\.?\d*)%', p_text)
                            if abv_match:
                                abv = abv_match.group(0)
                            
                            # Extract beer type
                            if '|' in p_text:
                                parts = p_text.split('|')
                                beer_type = parts[0].strip()
                            elif ':' in p_text:
                                parts = p_text.split(':')
                                beer_type = parts[0].strip()
                        elif len(p_text) > 20 and not beer_description:
                            beer_description = p_text
                    
                    # Add beer to our data
                    beer_info = {
                        "name": heading_text,
                        "type": beer_type,
                        "abv": abv,
                        "description": beer_description
                    }
                    
                    beer_data["beers"].append(beer_info)
                    beer_count += 1
                    print(f"Added beer from last resort approach: {heading_text}")
                
                except Exception as e:
                    print(f"Error processing heading #{i}: {e}")
            
        # Save the scraped data to a JSON file
        output_file = f"scraped_data/midwest_coast_{timestamp}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(beer_data, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully scraped {beer_count} beers from Midwest Coast Brewing")
        print(f"Data saved to {output_file}")
        
        return beer_data
    
    except Exception as e:
        print(f"An error occurred during scraping: {e}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("Starting Midwest Coast Brewing scraper...")
    result = scrape_midwest_coast()
    if result:
        print(f"Scraping completed. Found {len(result['beers'])} beers.")
    else:
        print("Scraping failed.")
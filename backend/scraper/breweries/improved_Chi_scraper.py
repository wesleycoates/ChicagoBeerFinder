import requests
from bs4 import BeautifulSoup
import re
import json
import time

def get_page(url):
    """Get a webpage and parse it with BeautifulSoup"""
    print(f"Fetching {url}")
    
    try:
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml',
            'Accept-Language': 'en-US,en;q=0.9',
        }, timeout=30)
        
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"Error fetching {url}: {str(e)}")
        return None

def extract_begyle_beers():
    """Extract beers from Begyle Brewing website"""
    # Try their landing page
    url = "https://www.begylebrewing.com/"
    
    soup = get_page(url)
    if not soup:
        return []
    
    beers = []
    
    # Print page title to verify we're on the right page
    if soup.title:
        print(f"Page title: {soup.title.text.strip()}")
    
    # For debugging, save the HTML to examine later
    with open('begyle_page.html', 'w', encoding='utf-8') as f:
        f.write(str(soup))
        print("Saved page HTML for inspection")
    
    # Find all blocks of text that might contain beer information
    print("Looking for text blocks that might contain beer info...")
    
    # Look for paragraphs with beer-related content
    all_paragraphs = soup.find_all('p')
    print(f"Found {len(all_paragraphs)} paragraphs on the page")
    
    beer_paragraphs = []
    for p in all_paragraphs:
        text = p.get_text()
        # Look for indicators of beer descriptions (ABV, beer styles)
        if '%' in text and any(style in text for style in ['IPA', 'Ale', 'Lager', 'Stout', 'Porter']):
            beer_paragraphs.append(p)
    
    print(f"Found {len(beer_paragraphs)} paragraphs that might contain beer info")
    
    # Also look for headings that might be beer names
    beer_headings = []
    for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5']):
        if len(heading.get_text().strip()) > 0 and len(heading.get_text().strip()) < 50:
            next_elem = heading.find_next_sibling()
            if next_elem and next_elem.name == 'p' and '%' in next_elem.get_text():
                beer_headings.append((heading, next_elem))
    
    print(f"Found {len(beer_headings)} potential beer headings with descriptions")
    
    # Process beer headings and descriptions
    for heading, description in beer_headings:
        try:
            name = heading.get_text().strip()
            desc_text = description.get_text().strip()
            
            # Extract ABV
            abv = 0.0
            abv_match = re.search(r'(\d+\.\d+|\d+)%', desc_text)
            if abv_match:
                abv = float(abv_match.group(1))
            
            # Extract beer style
            beer_type = "Unknown"
            common_styles = ['IPA', 'India Pale Ale', 'Lager', 'Ale', 'Stout', 'Porter', 'Pilsner', 'Wheat', 'Sour']
            for style in common_styles:
                if style in desc_text:
                    context_match = re.search(r'([^.!?\n]*\b' + style + r'\b[^.!?\n]*)', desc_text)
                    if context_match:
                        beer_type = context_match.group(1).strip()
                        break
            
            beers.append({
                'name': name,
                'type': beer_type,
                'abv': abv,
                'description': desc_text,
                'brewery': 'Begyle Brewing'
            })
            
            print(f"Added beer: {name} ({beer_type}, {abv}% ABV)")
            
        except Exception as e:
            print(f"Error processing beer entry: {str(e)}")
            continue
    
    # If we didn't find any beer headings, try processing the paragraphs directly
    if not beers and beer_paragraphs:
        for paragraph in beer_paragraphs:
            try:
                text = paragraph.get_text().strip()
                
                # Try to extract beer name from the beginning of the paragraph
                # Often the format is "Beer Name: Description..."
                name_match = re.match(r'^([^:]+):', text)
                if name_match:
                    name = name_match.group(1).strip()
                    # Remove name from description
                    description = text[len(name)+1:].strip()
                else:
                    # Try to find the first sentence as name
                    sentences = re.split(r'[.!?]', text)
                    if sentences:
                        name = sentences[0].strip()
                        # Remove name from description
                        description = text[len(name):].strip()
                    else:
                        continue  # Skip if we can't identify a name
                
                # Extract ABV
                abv = 0.0
                abv_match = re.search(r'(\d+\.\d+|\d+)%', text)
                if abv_match:
                    abv = float(abv_match.group(1))
                
                # Extract beer style
                beer_type = "Unknown"
                common_styles = ['IPA', 'India Pale Ale', 'Lager', 'Ale', 'Stout', 'Porter', 'Pilsner', 'Wheat', 'Sour']
                for style in common_styles:
                    if style in text:
                        context_match = re.search(r'([^.!?\n]*\b' + style + r'\b[^.!?\n]*)', text)
                        if context_match:
                            beer_type = context_match.group(1).strip()
                            break
                
                beers.append({
                    'name': name,
                    'type': beer_type,
                    'abv': abv,
                    'description': description,
                    'brewery': 'Begyle Brewing'
                })
                
                print(f"Added beer from paragraph: {name} ({beer_type}, {abv}% ABV)")
                
            except Exception as e:
                print(f"Error processing beer paragraph: {str(e)}")
                continue
    
    return beers

def main():
    print("Testing improved Begyle Brewing scraper...")
    
    # Extract beers
    beers = extract_begyle_beers()
    
    if beers:
        print(f"\nSuccessfully extracted {len(beers)} beers")
        
        # Print all beers
        for i, beer in enumerate(beers, 1):
            print(f"Beer {i}: {beer['name']} - {beer['type']} - {beer['abv']}% ABV")
            if beer.get('description'):
                desc_preview = beer['description'][:100] + "..." if len(beer['description']) > 100 else beer['description']
                print(f"  Description: {desc_preview}")
        
        # Save all results to a JSON file
        with open('begyle_beers.json', 'w') as f:
            json.dump(beers, f, indent=2)
            print(f"Saved all {len(beers)} beers to begyle_beers.json")
        
        return 0
    else:
        print("Failed to extract any beers from Begyle")
        print("\nLet's try an even simpler approach - Metropolitan Brewing")
        
        try_metropolitan()
        
        return 1

def try_metropolitan():
    """Try scraping Metropolitan Brewing as an alternative"""
    print("\nTrying Metropolitan Brewing instead...")
    url = "https://metrobrewing.com/our-beer/"
    
    soup = get_page(url)
    if not soup:
        return []
    
    beers = []
    
    # Print page title to verify we're on the right page
    if soup.title:
        print(f"Page title: {soup.title.text.strip()}")
    
    # For debugging
    with open('metropolitan_page.html', 'w', encoding='utf-8') as f:
        f.write(str(soup))
        print("Saved page HTML for inspection")
    
    # Look for beer sections
    beer_sections = soup.select('.beer-item') or soup.select('.beer') or soup.select('.beer-section')
    print(f"Found {len(beer_sections)} beer sections")
    
    # If we can't find specific beer containers, look for headings with descriptions
    if not beer_sections:
        beer_headings = []
        headings = soup.find_all(['h2', 'h3', 'h4'])
        
        for heading in headings:
            # Check if this might be a beer name
            if len(heading.text.strip()) < 50:
                # Look for a following paragraph that might be a description
                next_elem = heading.find_next_sibling()
                if next_elem and next_elem.name == 'p':
                    beer_headings.append((heading, next_elem))
        
        print(f"Found {len(beer_headings)} potential beer headings with descriptions")
        
        # Process these heading-description pairs
        for heading, description in beer_headings:
            try:
                name = heading.text.strip()
                desc_text = description.text.strip()
                
                # Extract ABV
                abv = 0.0
                abv_match = re.search(r'(\d+\.\d+|\d+)%', desc_text)
                if abv_match:
                    abv = float(abv_match.group(1))
                
                # Extract beer style
                beer_type = "Unknown"
                common_styles = ['IPA', 'India Pale Ale', 'Lager', 'Ale', 'Stout', 'Porter', 'Pilsner', 'Wheat', 'Sour']
                for style in common_styles:
                    if style in desc_text:
                        context_match = re.search(r'([^.!?\n]*\b' + style + r'\b[^.!?\n]*)', desc_text)
                        if context_match:
                            beer_type = context_match.group(1).strip()
                            break
                
                beers.append({
                    'name': name,
                    'type': beer_type,
                    'abv': abv,
                    'description': desc_text,
                    'brewery': 'Metropolitan Brewing'
                })
                
                print(f"Added Metropolitan beer: {name} ({beer_type}, {abv}% ABV)")
                
            except Exception as e:
                print(f"Error processing Metropolitan beer: {str(e)}")
                continue
    
        # Save results if we found any
        if beers:
            with open('metropolitan_beers.json', 'w') as f:
                json.dump(beers, f, indent=2)
                print(f"Saved {len(beers)} Metropolitan beers to metropolitan_beers.json")

if __name__ == "__main__":
    main()
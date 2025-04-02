import json
import requests
from bs4 import BeautifulSoup
import re

def scrape_suncatcher():
    """
    Scrape beer data from Suncatcher Brewing website.
    Returns a list of beer dictionaries with well-formatted information.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }
    
    # Get the site content
    print("Retrieving website content...")
    response = requests.get("https://suncatcherbrewing.com/beer", headers=headers)
    
    # Create BeautifulSoup object
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Remove scripts and styles to get clean text
    for script in soup(["script", "style"]):
        script.extract()
    
    # Get text and split into paragraphs
    text_content = soup.get_text(separator="\n")
    paragraphs = [p.strip() for p in text_content.split("\n") if p.strip()]
    
    # Store beer-related paragraphs
    beer_paragraphs = []
    
    # Store brewery information
    brewery_info = {
        "name": "Suncatcher Brewing",
        "location": "Chicago, IL",
        "website": "https://suncatcherbrewing.com/beer",
        "service_info": ""
    }
    
    # Look for paragraphs that might describe beer
    for p in paragraphs:
        # Skip very short paragraphs or navigation elements
        if len(p) < 10 or p in ["Home", "About", "Contact", "Menu"]:
            continue
            
        # Skip the age verification text or very common elements
        if "21+" in p or "Copyright" in p or "Powered by" in p:
            continue
        
        # Check if this is the "Suncatcher Drafts" information paragraph
        if "suncatcher drafts" in p.lower() or "imperial pints" in p.lower():
            brewery_info["service_info"] = p
            print(f"Found brewery service info: {p}")
            continue
            
        # Check if it might be beer-related
        beer_keywords = ["lager", "ipa", "ale", "stout", "pilsner", "porter", "wheat", "hops", "malt", "brew", "beer", "abv"]
        is_beer_related = any(keyword in p.lower() for keyword in beer_keywords)
        
        if is_beer_related:
            beer_paragraphs.append(p)
            print(f"Found beer-related paragraph: {p[:100]}...")
    
    # Initialize beers list
    beers = []
    
    # Process beer paragraphs to extract structured beer information
    # First pass: Look for beer names with ABV
    i = 0
    while i < len(beer_paragraphs):
        p = beer_paragraphs[i]
        
        # Handle the special case with SOLD OUT
        sold_out_pattern = re.compile(r'(.*?)\s+(\d+\.?\d*%\s*ABV)\s*-\s*SOLD OUT', re.IGNORECASE)
        sold_out_match = sold_out_pattern.search(p)
        
        if sold_out_match:
            name = sold_out_match.group(1).strip()
            abv = sold_out_match.group(2).strip()
            
            # Create a new beer entry
            new_beer = {
                "name": name,
                "abv": abv,
                "brewery": "Suncatcher Brewing",
                "type": "Unknown",
                "status": "SOLD OUT",
                "location": "Chicago, IL",
                "website": "https://suncatcherbrewing.com/beer"
            }
            
            # Determine beer type from name
            beer_types = {
                "ipa": "IPA",
                "pale ale": "Pale Ale", 
                "san diego pale": "Pale Ale",
                "lager": "Lager",
                "pilsner": "Pilsner",
                "stout": "Stout",
                "porter": "Porter",
                "wheat": "Wheat Beer",
                "amber": "Amber Ale",
                "golden": "Golden Ale"
            }
            
            for type_key, type_name in beer_types.items():
                if type_key.lower() in name.lower():
                    new_beer["type"] = type_name
                    break
            
            # Look for description in the next paragraph
            if i + 1 < len(beer_paragraphs):
                next_p = beer_paragraphs[i + 1]
                # Check if next paragraph is likely a description (no ABV pattern)
                if not re.search(r'\d+\.?\d*%\s*ABV', next_p) and len(next_p) > 20:
                    new_beer["description"] = next_p
                    i += 1  # Skip the next paragraph since we've used it
            
            beers.append(new_beer)
            i += 1
            continue
        
        # Regular pattern for "Beer Name X.X% ABV"
        abv_pattern = re.compile(r'(.*?)\s+(\d+\.?\d*%\s*ABV)', re.IGNORECASE)
        match = abv_pattern.search(p)
        
        if match:
            name = match.group(1).strip()
            abv = match.group(2).strip()
            
            # Check if this is a beer name (exclude descriptions that happen to have ABV in them)
            if len(name) < 50 and "%" not in name:
                # Create a new beer entry
                new_beer = {
                    "name": name,
                    "abv": abv,
                    "brewery": "Suncatcher Brewing",
                    "type": "Unknown",
                    "location": "Chicago, IL",
                    "website": "https://suncatcherbrewing.com/beer"
                }
                
                # Determine beer type from name
                beer_types = {
                    "ipa": "IPA",
                    "pale ale": "Pale Ale",
                    "lager": "Lager",
                    "pilsner": "Pilsner",
                    "stout": "Stout",
                    "porter": "Porter",
                    "wheat": "Wheat Beer",
                    "amber": "Amber Ale",
                    "golden": "Golden Ale"
                }
                
                for type_key, type_name in beer_types.items():
                    if type_key.lower() in name.lower():
                        new_beer["type"] = type_name
                        break
                
                # Look for description in the next paragraph
                if i + 1 < len(beer_paragraphs):
                    next_p = beer_paragraphs[i + 1]
                    # Check if next paragraph is likely a description (no ABV pattern)
                    if not re.search(r'\d+\.?\d*%\s*ABV', next_p) and len(next_p) > 20:
                        # Exclude poetic quotes and non-beer content
                        if "//" not in next_p and not next_p.startswith('"') and not next_p.startswith("'"):
                            new_beer["description"] = next_p
                            i += 1  # Skip the next paragraph since we've used it
                
                beers.append(new_beer)
        
        i += 1
    
    # Filter out invalid entries
    valid_beers = []
    for beer in beers:
        # Skip guest beers, coffee, etc.
        skip_keywords = ["medella", "coors", "coffee"]
        if any(keyword in beer["name"].lower() for keyword in skip_keywords):
            continue
        
        # Skip entries with poetic quotes in description
        if "description" in beer and "//" in beer["description"]:
            continue
            
        valid_beers.append(beer)
    
    # For beers that have description but no type, try to extract type from description
    for beer in valid_beers:
        if beer["type"] == "Unknown" and "description" in beer:
            desc = beer["description"].lower()
            beer_types = {
                "ipa": "IPA",
                "pale ale": "Pale Ale", 
                "lager": "Lager",
                "pilsner": "Pilsner",
                "stout": "Stout",
                "porter": "Porter",
                "wheat": "Wheat Beer",
                "amber": "Amber Ale",
                "golden": "Golden Ale"
            }
            
            for type_key, type_name in beer_types.items():
                if type_key in desc:
                    beer["type"] = type_name
                    break
    
    # Verify we have all 5 expected beers (not including Suncatcher Drafts info)
    expected_beers = [
        "Rye Lager",
        "MI Pale Ale",
        "IPA",
        "Amber Ale",
        "San Diego Pale Ale"
    ]
    
    # Check if any expected beers are missing
    found_beer_names = [beer["name"] for beer in valid_beers]
    for expected in expected_beers:
        found = False
        for beer_name in found_beer_names:
            if expected.lower() in beer_name.lower():
                found = True
                break
        
        if not found:
            print(f"Missing expected beer: {expected}")
    
    # Create the final output structure
    output = {
        "brewery": brewery_info,
        "beers": valid_beers
    }
    
    # Save the data to a JSON file
    with open('suncatcher_beers.json', 'w', encoding='utf-8') as json_file:
        json.dump(output, json_file, indent=4)
    
    print(f"Found {len(valid_beers)} valid beer entries")
    print("Data saved to suncatcher_beers.json")
    
    return output

if __name__ == "__main__":
    scrape_suncatcher()
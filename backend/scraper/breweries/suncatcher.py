from base_scraper import BreweryScraper
import requests
from bs4 import BeautifulSoup
import re
import json

class SuncatcherScraper(BreweryScraper):
    def __init__(self):
        super().__init__(
            brewery_name="Suncatcher Brewing", 
            website_url="https://suncatcherbrewing.com/",
            location="Chicago, IL"
        )
        self.beer_url = "https://suncatcherbrewing.com/beer"
        
    def scrape(self):
        """Scrape Suncatcher Brewing website for beer information"""
        # Initialize the brewery info
        brewery_info = {
            "name": self.brewery_name,
            "location": self.location,
            "website": self.website_url,
            "description": "Suncatcher Brewing is a craft brewery in Chicago."
        }
        
        html = self.get_page_content()
        soup = self.parse_html(html)
        
        # Extract brewery info
        service_info = ""
        for p in soup.find_all('p'):
            if "imperial pints" in p.text.lower() or "suncatcher drafts" in p.text.lower():
                service_info = p.text.strip()
                break
                
        if service_info:
            brewery_info["service_info"] = service_info
        
        # Extract beer information
        beer_entries = {}  # Use a dictionary to prevent duplicates
        
        # Store beer-related paragraphs - use a set to remove duplicates
        beer_paragraphs = set()
        
        # Look for paragraphs that might describe beer
        for p in soup.find_all(['p', 'div']):
            # Skip very short paragraphs or navigation elements
            if len(p.text.strip()) < 10:
                continue
                
            # Skip common non-beer paragraphs
            if "21+" in p.text or "Copyright" in p.text or "Powered by" in p.text:
                continue
                
            # Skip navigation elements
            if p.text.strip().startswith("HOME") or p.text.strip().startswith("BEER") or "Account" in p.text:
                continue
                
            # Check if it might be beer-related
            beer_keywords = ["lager", "ipa", "ale", "stout", "pilsner", "hops", "malt", "brew", "beer", "abv"]
            is_beer_related = any(keyword in p.text.lower() for keyword in beer_keywords)
            
            if is_beer_related:
                beer_paragraphs.add(p.text.strip())
                print(f"Found beer-related paragraph: {p.text.strip()[:100]}...")
        
        # Convert set back to list for processing
        beer_paragraphs = list(beer_paragraphs)
        
        # Process beer paragraphs to extract beer information
        i = 0
        while i < len(beer_paragraphs):
            p = beer_paragraphs[i]
            
            # Handle the special case with SOLD OUT
            sold_out_pattern = re.compile(r'(.*?)\s+(\d+\.?\d*%\s*ABV)\s*-\s*SOLD OUT', re.IGNORECASE)
            sold_out_match = sold_out_pattern.search(p)
            
            if sold_out_match:
                name = sold_out_match.group(1).strip()
                abv = sold_out_match.group(2).strip()
                
                # Skip price information if present
                if "$" in name:
                    name = name.split("$")[0].strip()
                
                # Create a new beer entry
                if name not in beer_entries:
                    beer_entries[name] = {
                        "name": name,
                        "abv": abv,
                        "brewery": self.brewery_name,
                        "type": self.extract_beer_type(name + " " + p),
                        "status": "SOLD OUT",
                        "location": self.location,
                        "website": self.beer_url
                    }
                
                # Look for description in the next paragraph
                if i + 1 < len(beer_paragraphs):
                    next_p = beer_paragraphs[i + 1]
                    # Check if next paragraph is likely a description (no ABV pattern and no price)
                    if not re.search(r'\d+\.?\d*%\s*ABV', next_p) and "$" not in next_p and len(next_p) > 20:
                        # Exclude poetic quotes
                        if "//" not in next_p:
                            beer_entries[name]["description"] = next_p
                            i += 1  # Skip the next paragraph since we've used it
                
                i += 1
                continue
            
            # Regular pattern for "Beer Name X.X% ABV"
            abv_pattern = re.compile(r'(.*?)\s+(\d+\.?\d*%\s*ABV)', re.IGNORECASE)
            match = abv_pattern.search(p)
            
            if match:
                name = match.group(1).strip()
                abv = match.group(2).strip()
                
                # Skip price information if present
                if "$" in name:
                    name = name.split("$")[0].strip()
                
                # Check if this is a beer name (exclude descriptions that happen to have ABV in them)
                if len(name) < 50 and "%" not in name:
                    # Create a new beer entry if we don't have it yet
                    if name not in beer_entries:
                        beer_entries[name] = {
                            "name": name,
                            "abv": abv,
                            "brewery": self.brewery_name,
                            "type": self.extract_beer_type(name + " " + p),
                            "location": self.location,
                            "website": self.beer_url
                        }
                    
                    # Look for description in the next paragraph
                    if i + 1 < len(beer_paragraphs):
                        next_p = beer_paragraphs[i + 1]
                        # Check if next paragraph is likely a description (no ABV pattern and no price)
                        if not re.search(r'\d+\.?\d*%\s*ABV', next_p) and "$" not in next_p and len(next_p) > 20:
                            # Exclude poetic quotes and non-beer content
                            if "//" not in next_p:
                                beer_entries[name]["description"] = next_p
                                i += 1  # Skip the next paragraph since we've used it
            
            i += 1
        
        # Skip certain beers that aren't Suncatcher's own
        skip_beers = ["Medella Light", "Coors Banquet", "La Chouffe", "Dark Matter Coffee"]
        
        # Convert dictionary to list
        beers = [beer for name, beer in beer_entries.items() 
                if not any(skip in name for skip in skip_beers)]
        
        # Also filter out any entries that appear to be coffee or other beverages
        beers = [beer for beer in beers 
                if not ("coffee" in beer["name"].lower() or 
                       "pellegrino" in beer["name"].lower())]
        
        print(f"Found {len(beers)} valid beers")
        
        # Return brewery info and beers
        return {
            "brewery": brewery_info,
            "beers": beers
        }
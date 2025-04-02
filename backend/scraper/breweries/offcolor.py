from base_scraper import BreweryScraper
import requests
from bs4 import BeautifulSoup
import re
import json


class OffColorScraper(BreweryScraper):
    def __init__(self):
        super().__init__(
            brewery_name="Off Color Brewing", 
            website_url="https://www.offcolorbrewing.com/",
            location="Chicago, IL"
        )
        self.beer_url = "https://www.offcolorbrewing.com/current-beer"
        self.beermenu_url = "https://www.beermenus.com/places/48519-off-color-brewing-mousetrap"
        
    def scrape(self):
        """Scrape Off Color Brewing website for beer information"""
        # Initialize the brewery info
        brewery_info = {
            "name": self.brewery_name,
            "location": self.location,
            "website": self.website_url,
            "description": "Off Color Brewing specializes in forgotten and experimental beer styles, particularly those made in Germany before Reinheitsgebot was proclaimed in the late 15th century."
        }
        
        beers = []
        
        # First try to get beers from the official website
        print(f"Retrieving content from {self.beer_url}...")
        official_beers = self._scrape_official_site()
        if official_beers:
            beers.extend(official_beers)
            
        # Then supplement with BeerMenus data
        print(f"Retrieving content from BeerMenus...")
        beermenu_beers = self._scrape_beer_menus()
        
        # Merge beer data
        beers = self._merge_beer_data(beers, beermenu_beers)
        
        # Remove duplicates
        unique_beers = self._remove_duplicates(beers)
        
        print(f"Found {len(unique_beers)} unique beers")
        
        return {
            "brewery": brewery_info,
            "beers": unique_beers
        }
    
    def _scrape_official_site(self):
        """Scrape beer information from the official Off Color website"""
        beers = []
        try:
            response = requests.get(self.beer_url, headers=self.headers)
            soup = self.parse_html(response.text)
            
            # Off Color website has basic beer names but links to individual beer pages
            # Try to find beer links or names
            beer_links = soup.find_all('a', href=lambda href: href and ('/apex' in href or '/beer' in href))
            
            # If no links found, try to find beer names in the page
            if not beer_links:
                # Look for a list of beer names on the page
                beer_elements = soup.find_all(['div', 'span', 'li'], text=lambda t: t and ('Apex' in t or 'Beer for' in t or 'DinoS\'mores' in t))
                
                for element in beer_elements:
                    beer_name = element.text.strip()
                    if beer_name and beer_name != "" and not any(b["name"] == beer_name for b in beers):
                        beers.append({
                            "name": beer_name,
                            "brewery": self.brewery_name,
                            "type": "Unknown",
                            "abv": "Unknown",
                            "description": "",
                            "source": "official_site"
                        })
                
            else:
                # Process beer links
                for link in beer_links:
                    beer_name = link.text.strip()
                    beer_url = link.get('href')
                    if not beer_url.startswith('http'):
                        beer_url = self.website_url + beer_url.lstrip('/')
                    
                    # Skip if this is not a beer-specific page
                    if beer_name == "" or beer_name.lower() in ["home", "about", "contact"]:
                        continue
                    
                    # Check if we already have this beer
                    if any(b["name"] == beer_name for b in beers):
                        continue
                    
                    # Create a basic beer entry
                    beer_entry = {
                        "name": beer_name,
                        "brewery": self.brewery_name,
                        "type": "Unknown",
                        "abv": "Unknown",
                        "description": "",
                        "url": beer_url,
                        "source": "official_site"
                    }
                    
                    # Try to get more details from the beer-specific page
                    try:
                        beer_details = self._get_beer_details(beer_url)
                        if beer_details:
                            beer_entry.update(beer_details)
                    except Exception as e:
                        print(f"Error getting details for {beer_name}: {e}")
                    
                    beers.append(beer_entry)
                    
            # Check if we found any beers
            if not beers:
                # Fallback: check if there's a specific beer list on the page
                beer_list = soup.find_all(['div', 'ul', 'section'], class_=lambda c: c and ('beer-list' in c.lower() or 'beer-grid' in c.lower()))
                
                if beer_list:
                    for section in beer_list:
                        items = section.find_all(['li', 'div', 'a'])
                        for item in items:
                            beer_name = item.text.strip()
                            if beer_name and beer_name != "" and not any(b["name"] == beer_name for b in beers):
                                beers.append({
                                    "name": beer_name,
                                    "brewery": self.brewery_name,
                                    "type": "Unknown", 
                                    "abv": "Unknown",
                                    "description": "",
                                    "source": "official_site"
                                })
            
            return beers
            
        except Exception as e:
            print(f"Error scraping official site: {e}")
            return []
    
    def _get_beer_details(self, beer_url):
        """Get detailed information about a specific beer"""
        try:
            response = requests.get(beer_url, headers=self.headers)
            soup = self.parse_html(response.text)
            
            beer_details = {}
            
            # Look for beer description
            description_elements = soup.find_all(['p', 'div'], class_=lambda c: c and ('description' in c.lower() or 'beer-info' in c.lower()))
            if not description_elements:
                # Try more generic paragraph elements
                description_elements = soup.find_all('p', limit=3)
            
            if description_elements:
                description = description_elements[0].text.strip()
                beer_details["description"] = description
                
                # Try to extract ABV from description
                abv_match = re.search(r'(\d+\.?\d*)%', description)
                if abv_match:
                    beer_details["abv"] = abv_match.group(0)
                
                # Try to extract beer type from description
                beer_details["type"] = self.extract_beer_type(description)
            
            return beer_details
            
        except Exception as e:
            print(f"Error getting beer details from {beer_url}: {e}")
            return {}
    
    def _scrape_beer_menus(self):
        """Scrape beer information from BeerMenus"""
        beers = []
        try:
            response = requests.get(self.beermenu_url, headers=self.headers)
            soup = self.parse_html(response.text)
            
            # BeerMenus typically has a structured format with beer items
            beer_items = soup.find_all(['div', 'li'], class_=lambda c: c and ('beer-item' in c.lower() or 'menu-item' in c.lower()))
            
            if not beer_items:
                # Try alternative selectors
                beer_items = soup.find_all(['div', 'tr'], class_=lambda c: c and ('item' in c.lower() or 'beer' in c.lower()))
            
            for item in beer_items:
                try:
                    # Extract beer name
                    name_element = item.find(['h3', 'a', 'span', 'div'], class_=lambda c: c and ('name' in c.lower() or 'title' in c.lower()))
                    if not name_element:
                        continue
                        
                    beer_name = name_element.text.strip()
                    
                    # Check if this is an Off Color beer (they might list guest beers too)
                    if "Off Color" not in item.text and not any(keyword in beer_name for keyword in ["Apex", "Troublesome", "Scurry", "DinoS'mores"]):
                        # Try to find brewery info
                        brewery_element = item.find(['span', 'div'], class_=lambda c: c and 'brewery' in c.lower())
                        if brewery_element and "Off Color" not in brewery_element.text:
                            continue  # Skip non-Off Color beers
                    
                    # Extract beer type
                    beer_type = "Unknown"
                    type_element = item.find(['span', 'div'], class_=lambda c: c and ('style' in c.lower() or 'type' in c.lower()))
                    if type_element:
                        beer_type = type_element.text.strip()
                    
                    # Extract ABV
                    abv = "Unknown"
                    abv_element = item.find(['span', 'div'], string=lambda s: s and '%' in s)
                    if abv_element:
                        abv_match = re.search(r'(\d+\.?\d*)%', abv_element.text)
                        if abv_match:
                            abv = abv_match.group(0)
                    
                    # Extract description
                    description = ""
                    desc_element = item.find(['p', 'div'], class_=lambda c: c and ('description' in c.lower() or 'notes' in c.lower()))
                    if desc_element:
                        description = desc_element.text.strip()
                    
                    beers.append({
                        "name": beer_name,
                        "brewery": self.brewery_name,
                        "type": beer_type,
                        "abv": abv,
                        "description": description,
                        "source": "beermenu"
                    })
                
                except Exception as e:
                    print(f"Error processing beer item: {e}")
            
            return beers
            
        except Exception as e:
            print(f"Error scraping BeerMenus: {e}")
            return []
    
    def _merge_beer_data(self, official_beers, beermenu_beers):
        """Merge data from official site and BeerMenus"""
        merged_beers = official_beers.copy()
        
        for beermenu_beer in beermenu_beers:
            # Check if this beer exists in the official beers
            match_found = False
            for i, official_beer in enumerate(merged_beers):
                # Compare names (allowing for some variation)
                if self._compare_beer_names(official_beer["name"], beermenu_beer["name"]):
                    # Update official beer with any missing information
                    if official_beer["type"] == "Unknown" and beermenu_beer["type"] != "Unknown":
                        merged_beers[i]["type"] = beermenu_beer["type"]
                        
                    if official_beer["abv"] == "Unknown" and beermenu_beer["abv"] != "Unknown":
                        merged_beers[i]["abv"] = beermenu_beer["abv"]
                        
                    if not official_beer["description"] and beermenu_beer["description"]:
                        merged_beers[i]["description"] = beermenu_beer["description"]
                        
                    merged_beers[i]["sources"] = list(set(
                        merged_beers[i].get("sources", []) + 
                        [merged_beers[i]["source"], beermenu_beer["source"]]
                    ))
                    if "source" in merged_beers[i]:
                        del merged_beers[i]["source"]
                        
                    match_found = True
                    break
            
            # If no match found, add this beer to the list
            if not match_found:
                beermenu_beer["sources"] = [beermenu_beer["source"]]
                del beermenu_beer["source"]
                merged_beers.append(beermenu_beer)
        
        return merged_beers
    
    def _compare_beer_names(self, name1, name2):
        """Compare beer names, allowing for small variations"""
        name1 = name1.lower()
        name2 = name2.lower()
        
        # Direct match
        if name1 == name2:
            return True
            
        # One name contains the other
        if name1 in name2 or name2 in name1:
            return True
            
        # Special cases for Off Color beers
        if ("apex" in name1 and "predator" in name1) and ("apex" in name2 and "predator" in name2):
            return True
            
        if "dinos'mores" in name1 and "dinos'mores" in name2:
            return True
            
        if "beer for" in name1 and "beer for" in name2 and name1.split("beer for")[1].strip() == name2.split("beer for")[1].strip():
            return True
        
        return False
    
    def _remove_duplicates(self, beers):
        """Remove duplicate beers based on name"""
        unique_beers = []
        seen_names = set()
        
        for beer in beers:
            normalized_name = beer["name"].lower()
            
            # Check for similar names we've already seen
            is_duplicate = False
            for seen_name in seen_names:
                if self._compare_beer_names(normalized_name, seen_name):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_names.add(normalized_name)
                
                # Clean up the beer entry
                if "source" in beer:
                    beer["sources"] = [beer["source"]]
                    del beer["source"]
                    
                unique_beers.append(beer)
        
        return unique_beers
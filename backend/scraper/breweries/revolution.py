from scraper.base import BaseScraper
from typing import List, Dict, Any
import re

class RevolutionScraper(BaseScraper):
    """Scraper for Revolution Brewing"""
    
    def __init__(self, brewery_id: int, db_path: str = None):
        super().__init__(
            brewery_id=brewery_id,
            name="Revolution Brewing",
            url="https://revbrew.com/visit/brewery/tap-room-dl",
            db_path=db_path
        )
    
    def extract_beers(self) -> List[Dict[str, Any]]:
        """Extract beers from Revolution Brewing website"""
        soup = self.get_page()
        if not soup:
            return []
        
        beers = []
        
        # Find all beer containers - adjust selectors based on actual website structure
        beer_containers = soup.select('div.beer-item')
        
        for container in beer_containers:
            try:
                # Extract beer name
                name_elem = container.select_one('h3.beer-name')
                if not name_elem:
                    continue
                
                name = name_elem.text.strip()
                
                # Extract beer style/type
                style_elem = container.select_one('div.beer-style')
                beer_type = style_elem.text.strip() if style_elem else "Unknown"
                
                # Extract ABV
                abv_elem = container.select_one('div.beer-abv')
                abv = 0.0
                
                if abv_elem:
                    abv_text = abv_elem.text.strip()
                    abv_match = re.search(r'(\d+\.\d+|\d+)%', abv_text)
                    if abv_match:
                        abv = float(abv_match.group(1))
                
                # Extract description
                desc_elem = container.select_one('div.beer-desc')
                description = desc_elem.text.strip() if desc_elem else ""
                
                beers.append({
                    'name': name,
                    'type': beer_type,
                    'abv': abv,
                    'description': description
                })
                
            except Exception as e:
                self.logger.error(f"Error extracting beer: {str(e)}")
                continue
        
        return beers
import json
import os
import random
import logging

logger = logging.getLogger(__name__)

class LocalBeerClient:
    """Client for accessing beer data from a local JSON file."""
    
    def __init__(self, data_file=None):
        """Initialize the local beer data client.
        
        Args:
            data_file (str): Path to the beer data JSON file
        """
        self.beers = []
        
        # If no file provided, use default sample data
        if not data_file:
            self.load_sample_data()
        else:
            self.load_data(data_file)
            
        logger.info(f"Loaded {len(self.beers)} beers into local client")
    
    def load_sample_data(self):
        """Load sample beer data."""
        # Sample data with a few beers
        self.beers = [
            {
                "id": 1,
                "name": "Buzz",
                "tagline": "A Real Bitter Experience.",
                "first_brewed": "09/2007",
                "description": "A light, crisp and bitter IPA brewed with English and American hops. A small batch brewed only once.",
                "image_url": "https://images.punkapi.com/v2/keg.png",
                "abv": 4.5,
                "ibu": 60,
                "target_fg": 1010,
                "target_og": 1044,
                "ebc": 20,
                "srm": 10,
                "ph": 4.4,
                "attenuation_level": 75,
                "volume": {
                    "value": 20,
                    "unit": "litres"
                },
                "food_pairing": [
                    "Spicy chicken tikka masala",
                    "Grilled chicken quesadilla",
                    "Caramel toffee cake"
                ],
                "brewers_tips": "The earthy and floral aromas from the hops can be overpowering. Drop a little Cascade in at the end of the boil to lift the profile with a bit of citrus.",
                "contributed_by": "Sam Mason <samjbmason>"
            },
            {
                "id": 2,
                "name": "Trashy Blonde",
                "tagline": "You Know You Shouldn't",
                "first_brewed": "04/2008",
                "description": "A titillating, neurotic, peroxide punk of a Pale Ale. Combining attitude, style, substance, and a little bit of low self esteem for good measure; what would your mother say? The seductive lure of the sassy passion fruit hop proves too much to resist. All that is even before we get onto the fact that there are no additives, preservatives, pasteurization or strings attached. All wrapped up with the customary BrewDog bite and imaginative twist.",
                "image_url": "https://images.punkapi.com/v2/2.png",
                "abv": 4.1,
                "ibu": 41.5,
                "target_fg": 1010,
                "target_og": 1041.7,
                "ebc": 15,
                "srm": 15,
                "ph": 4.4,
                "attenuation_level": 76,
                "volume": {
                    "value": 20,
                    "unit": "litres"
                },
                "food_pairing": [
                    "Fresh crab with lemon",
                    "Garlic butter dipping sauce",
                    "Goats cheese salad",
                    "Creamy lemon bar doused in powdered sugar"
                ],
                "brewers_tips": "Be careful not to collect too much wort from the mash. Once the sugars are all washed out there are some very unpleasant grainy tasting compounds that can be extracted into the wort.",
                "contributed_by": "Sam Mason <samjbmason>"
            },
            {
                "id": 3,
                "name": "Berliner Weisse With Yuzu - B-Sides",
                "tagline": "Japanese Citrus Berliner Weisse.",
                "first_brewed": "11/2015",
                "description": "Japanese citrus fruit intensifies the sour nature of this German classic.",
                "image_url": "https://images.punkapi.com/v2/keg.png",
                "abv": 4.2,
                "ibu": 8,
                "target_fg": 1007,
                "target_og": 1040,
                "ebc": 8,
                "srm": 4,
                "ph": 3.2,
                "attenuation_level": 83,
                "volume": {
                    "value": 20,
                    "unit": "litres"
                },
                "food_pairing": [
                    "Smoked chicken wings",
                    "Miso ramen",
                    "Yuzu cheesecake"
                ],
                "brewers_tips": "Clean everything twice. All you want is the clean sourness of lactobacillus.",
                "contributed_by": "Sam Mason <samjbmason>"
            },
            {
                "id": 4,
                "name": "Pilsen Lager",
                "tagline": "Unleash the Yeast Series.",
                "first_brewed": "09/2013",
                "description": "Our Unleash the Yeast series was an epic experiment into the differences in aroma and flavour provided by switching up your yeast. We brewed up a wort with a light caramel note and some toasty biscuit flavour, and hopped it with Amarillo and Centennial for a citrusy bitterness. Everything else is down to the yeast. Pilsner yeast ferments with no fruity esters or spicy phenols, although it can add a hint of butterscotch.",
                "image_url": "https://images.punkapi.com/v2/4.png",
                "abv": 6.3,
                "ibu": 55,
                "target_fg": 1012,
                "target_og": 1060,
                "ebc": 30,
                "srm": 15,
                "ph": 4.4,
                "attenuation_level": 80,
                "volume": {
                    "value": 20,
                    "unit": "litres"
                },
                "food_pairing": [
                    "Spicy crab cakes",
                    "Spicy cucumber and carrot Thai salad",
                    "Sweet filled dumplings"
                ],
                "brewers_tips": "Play around with the fermentation temperature to get the best flavour profile from the individual yeasts.",
                "contributed_by": "Ali Skinner <AliSkinner>"
            },
            {
                "id": 5,
                "name": "Avery Brown Dredge",
                "tagline": "Bloggers' Imperial Pilsner.",
                "first_brewed": "02/2011",
                "description": "An Imperial Pilsner in collaboration with beer writers. Tradition. Homage. Revolution. We wanted to showcase the awesome backbone of the Czech brewing tradition, the noble Saaz hop, and also tip our hats to the modern beers that rock our world, and the people who make them.",
                "image_url": "https://images.punkapi.com/v2/5.png",
                "abv": 7.2,
                "ibu": 59,
                "target_fg": 1027,
                "target_og": 1069,
                "ebc": 10,
                "srm": 5,
                "ph": 4.4,
                "attenuation_level": 67,
                "volume": {
                    "value": 20,
                    "unit": "litres"
                },
                "food_pairing": [
                    "Vietnamese squid salad",
                    "Chargrilled corn on the cob with paprika butter",
                    "Strawberry and rhubarb pie"
                ],
                "brewers_tips": "Make sure you have a big enough yeast starter to ferment through the OG and lager successfully.",
                "contributed_by": "Sam Mason <samjbmason>"
            }
        ]
    
    def load_data(self, data_file):
        """Load beer data from a JSON file.
        
        Args:
            data_file (str): Path to the JSON file containing beer data
        """
        try:
            if os.path.exists(data_file):
                with open(data_file, 'r', encoding='utf-8') as f:
                    self.beers = json.load(f)
            else:
                logger.warning(f"Data file {data_file} not found. Loading sample data instead.")
                self.load_sample_data()
        except Exception as e:
            logger.error(f"Error loading beer data: {e}")
            self.load_sample_data()
    
    def get_all_beers(self, page=1, per_page=25):
        """Get all beers with pagination.
        
        Args:
            page (int): Page number
            per_page (int): Number of beers per page
            
        Returns:
            list: Beer results
        """
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        return self.beers[start_idx:end_idx]
    
    def get_beer(self, beer_id):
        """Get a specific beer by ID.
        
        Args:
            beer_id (int): Beer ID
            
        Returns:
            list: Beer details (single item list)
        """
        for beer in self.beers:
            if beer['id'] == int(beer_id):
                return [beer]
        return []
    
    def get_random_beer(self):
        """Get a random beer.
        
        Returns:
            list: Random beer (single item list)
        """
        if self.beers:
            return [random.choice(self.beers)]
        return []
    
    def search_beers_by_name(self, beer_name, page=1, per_page=25):
        """Search for beers by name.
        
        Args:
            beer_name (str): Beer name to search for
            page (int): Page number
            per_page (int): Number of beers per page
            
        Returns:
            list: Matching beers
        """
        results = []
        for beer in self.beers:
            if beer_name.lower() in beer['name'].lower():
                results.append(beer)
        
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        return results[start_idx:end_idx]
    
    def search_beers_by_abv(self, min_abv=None, max_abv=None, page=1, per_page=25):
        """Search for beers by ABV range.
        
        Args:
            min_abv (float): Minimum ABV
            max_abv (float): Maximum ABV
            page (int): Page number
            per_page (int): Number of beers per page
            
        Returns:
            list: Matching beers
        """
        results = []
        for beer in self.beers:
            abv = beer.get('abv', 0)
            
            if (min_abv is None or abv >= min_abv) and (max_abv is None or abv <= max_abv):
                results.append(beer)
        
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        return results[start_idx:end_idx]
    
    def search_beers_by_food(self, food, page=1, per_page=25):
        """Search for beers that pair with a specific food.
        
        Args:
            food (str): Food to pair with
            page (int): Page number
            per_page (int): Number of beers per page
            
        Returns:
            list: Matching beers
        """
        results = []
        for beer in self.beers:
            food_pairings = beer.get('food_pairing', [])
            
            if any(food.lower() in pairing.lower() for pairing in food_pairings):
                results.append(beer)
        
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        return results[start_idx:end_idx]
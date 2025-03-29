import requests
import logging

logger = logging.getLogger(__name__)

class PunkAPIClient:
    """Client for interacting with the Punk API for beer data."""
    
    BASE_URL = "https://api.punkapi.com/v2"
    
    def __init__(self):
        """Initialize the Punk API client."""
        logger.info("Initializing Punk API client")
    
    def _make_request(self, endpoint, params=None):
        """Make a request to the Punk API.
        
        Args:
            endpoint (str): API endpoint to call
            params (dict): Additional query parameters
            
        Returns:
            dict or list: API response data
        """
        if params is None:
            params = {}
            
        # Build URL
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Punk API request failed: {e}")
            return []
    
    def get_all_beers(self, page=1, per_page=25):
        """Get all beers with pagination.
        
        Args:
            page (int): Page number
            per_page (int): Number of beers per page (max 80)
            
        Returns:
            list: Beer results
        """
        params = {
            'page': page,
            'per_page': min(per_page, 80)  # API max is 80
        }
        
        return self._make_request('beers', params)
    
    def get_beer(self, beer_id):
        """Get a specific beer by ID.
        
        Args:
            beer_id (int): Beer ID
            
        Returns:
            list: Beer details (single item list)
        """
        return self._make_request(f'beers/{beer_id}')
    
    def get_random_beer(self):
        """Get a random beer.
        
        Returns:
            list: Random beer (single item list)
        """
        return self._make_request('beers/random')
    
    def search_beers_by_name(self, beer_name, page=1, per_page=25):
        """Search for beers by name.
        
        Args:
            beer_name (str): Beer name to search for
            page (int): Page number
            per_page (int): Number of beers per page (max 80)
            
        Returns:
            list: Matching beers
        """
        params = {
            'beer_name': beer_name,
            'page': page,
            'per_page': min(per_page, 80)
        }
        
        return self._make_request('beers', params)
    
    def search_beers_by_abv(self, min_abv=None, max_abv=None, page=1, per_page=25):
        """Search for beers by ABV range.
        
        Args:
            min_abv (float): Minimum ABV
            max_abv (float): Maximum ABV
            page (int): Page number
            per_page (int): Number of beers per page (max 80)
            
        Returns:
            list: Matching beers
        """
        params = {
            'page': page,
            'per_page': min(per_page, 80)
        }
        
        if min_abv is not None:
            params['abv_gt'] = min_abv
            
        if max_abv is not None:
            params['abv_lt'] = max_abv
        
        return self._make_request('beers', params)
    
    def search_beers_by_ibu(self, min_ibu=None, max_ibu=None, page=1, per_page=25):
        """Search for beers by IBU range.
        
        Args:
            min_ibu (float): Minimum IBU
            max_ibu (float): Maximum IBU
            page (int): Page number
            per_page (int): Number of beers per page (max 80)
            
        Returns:
            list: Matching beers
        """
        params = {
            'page': page,
            'per_page': min(per_page, 80)
        }
        
        if min_ibu is not None:
            params['ibu_gt'] = min_ibu
            
        if max_ibu is not None:
            params['ibu_lt'] = max_ibu
        
        return self._make_request('beers', params)
    
    def search_beers_by_food(self, food, page=1, per_page=25):
        """Search for beers that pair with a specific food.
        
        Args:
            food (str): Food to pair with
            page (int): Page number
            per_page (int): Number of beers per page (max 80)
            
        Returns:
            list: Matching beers
        """
        params = {
            'food': food,
            'page': page,
            'per_page': min(per_page, 80)
        }
        
        return self._make_request('beers', params)
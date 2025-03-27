import requests
import sqlite3
import os
import time
import json
import logging
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='untappd_integration.log'
)

class UntappdAPI:
    def __init__(self, db_path=None):
        """Initialize the Untappd API integration"""
        # Get API credentials from environment variables
        self.client_id = os.getenv('UNTAPPD_CLIENT_ID')
        self.client_secret = os.getenv('UNTAPPD_CLIENT_SECRET')
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Untappd API credentials not found. Please set UNTAPPD_CLIENT_ID and UNTAPPD_CLIENT_SECRET environment variables.")
        
        # Set up database connection
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'beers.db')
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        self.cursor = self.conn.cursor()
        
        # API base URL
        self.base_url = "https://api.untappd.com/v4"
        self.rate_limit_remaining = 100  # Default value
        self.rate_limit_reset = 0
    
    def __del__(self):
        """Close database connection on object destruction"""
        if hasattr(self, 'conn'):
            self.conn.close()
    
    def _make_request(self, endpoint, params=None):
        """Make a request to the Untappd API with rate limiting"""
        if params is None:
            params = {}
        
        # Add authentication to params
        params.update({
            'client_id': self.client_id,
            'client_secret': self.client_secret
        })
        
        # Check if we need to wait for rate limit
        current_time = time.time()
        if self.rate_limit_remaining <= 5 and current_time < self.rate_limit_reset:
            wait_time = self.rate_limit_reset - current_time + 5  # Add 5 seconds buffer
            logging.info(f"Rate limit approaching, waiting {wait_time:.2f} seconds")
            time.sleep(wait_time)
        
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            # Update rate limit info
            if 'X-Ratelimit-Remaining' in response.headers:
                self.rate_limit_remaining = int(response.headers['X-Ratelimit-Remaining'])
            if 'X-Ratelimit-Reset' in response.headers:
                self.rate_limit_reset = int(response.headers['X-Ratelimit-Reset'])
            
            data = response.json()
            
            # Check for API-specific errors
            if data.get('meta', {}).get('code') != 200:
                error_msg = data.get('meta', {}).get('error_detail', 'Unknown API error')
                logging.error(f"API error: {error_msg}")
                return None
            
            # Add a small delay to be nice to the API
            time.sleep(0.5)
            
            return data.get('response')
        
        except requests.RequestException as e:
            logging.error(f"Request error: {e}")
            return None
    
    def search_brewery(self, brewery_name):
        """Search for a brewery on Untappd"""
        endpoint = "search/brewery"
        params = {
            'q': brewery_name,
            'limit': 5
        }
        
        result = self._make_request(endpoint, params)
        if not result:
            return None
        
        breweries = result.get('brewery', {}).get('items', [])
        
        # Filter to find closest match
        for brewery in breweries:
            brewery_data = brewery.get('brewery')
            if brewery_data and 'Chicago' in brewery_data.get('location', {}).get('brewery_city', ''):
                return brewery_data
        
        return breweries[0].get('brewery') if breweries else None
    
    def get_brewery_info(self, brewery_id):
        """Get detailed information about a brewery"""
        endpoint = f"brewery/info/{brewery_id}"
        params = {
            'compact': 'false'
        }
        
        result = self._make_request(endpoint, params)
        if not result:
            return None
        
        return result.get('brewery')
    
    def get_brewery_beers(self, brewery_id):
        """Get beers for a specific brewery"""
        endpoint = f"brewery/beer/{brewery_id}"
        params = {
            'limit': 50
        }
        
        result = self._make_request(endpoint, params)
        if not result:
            return []
        
        return result.get('beers', {}).get('items', [])
    
    def get_beer_info(self, beer_id):
        """Get detailed information about a beer"""
        endpoint = f"beer/info/{beer_id}"
        
        result = self._make_request(endpoint)
        if not result:
            return None
        
        return result.get('beer')
    
    def update_brewery_with_untappd_data(self, local_brewery_id, untappd_brewery_data):
        """Update brewery in database with Untappd data"""
        if not untappd_brewery_data:
            return False
        
        try:
            # Extract location data
            location = untappd_brewery_data.get('location', {})
            
            # Extract brewery information
            brewery_update = {
                'latitude': location.get('brewery_lat'),
                'longitude': location.get('brewery_lng'),
                'description': untappd_brewery_data.get('brewery_description'),
                'website': untappd_brewery_data.get('contact', {}).get('url'),
                'untappd_id': untappd_brewery_data.get('brewery_id')
            }
            
            # Filter out None values
            brewery_update = {k: v for k, v in brewery_update.items() if v is not None}
            
            if not brewery_update:
                return False
            
            # Build SQL update query
            fields = ", ".join([f"{key} = ?" for key in brewery_update.keys()])
            values = list(brewery_update.values())
            values.append(local_brewery_id)
            
            query = f"UPDATE breweries SET {fields} WHERE id = ?"
            self.cursor.execute(query, values)
            self.conn.commit()
            
            logging.info(f"Updated brewery ID {local_brewery_id} with Untappd data")
            return True
        
        except sqlite3.Error as e:
            logging.error(f"Database error while updating brewery {local_brewery_id}: {e}")
            self.conn.rollback()
            return False
    
    def update_beer_with_untappd_data(self, local_beer_id, untappd_beer_data):
        """Update beer in database with Untappd data"""
        if not untappd_beer_data:
            return False
        
        try:
            # Extract beer information
            beer_update = {
                'description': untappd_beer_data.get('beer_description'),
                'ibu': untappd_beer_data.get('beer_ibu'),
                'image_url': untappd_beer_data.get('beer_label'),
                'untappd_id': untappd_beer_data.get('bid'),
                'rating_score': untappd_beer_data.get('rating_score')
            }
            
            # Filter out None values
            beer_update = {k: v for k, v in beer_update.items() if v is not None}
            
            if not beer_update:
                return False
            
            # Build SQL update query
            fields = ", ".join([f"{key} = ?" for key in beer_update.keys()])
            values = list(beer_update.values())
            values.append(local_beer_id)
            
            query = f"UPDATE beers SET {fields} WHERE id = ?"
            self.cursor.execute(query, values)
            self.conn.commit()
            
            logging.info(f"Updated beer ID {local_beer_id} with Untappd data")
            return True
        
        except sqlite3.Error as e:
            logging.error(f"Database error while updating beer {local_beer_id}: {e}")
            self.conn.rollback()
            return False
    
    def enrich_database(self):
        """Enrich database with Untappd data"""
        logging.info("Starting Untappd data enrichment process")
        
        # Get all breweries from database that don't have Untappd IDs
        self.cursor.execute("SELECT id, name FROM breweries WHERE untappd_id IS NULL")
        breweries = self.cursor.fetchall()
        
        for brewery in breweries:
            logging.info(f"Enriching brewery: {brewery['name']}")
            
            # Search for brewery on Untappd
            untappd_brewery = self.search_brewery(brewery['name'])
            if not untappd_brewery:
                logging.warning(f"Could not find Untappd data for brewery: {brewery['name']}")
                continue
            
            # Get detailed brewery info
            untappd_brewery_id = untappd_brewery.get('brewery_id')
            if untappd_brewery_id:
                brewery_details = self.get_brewery_info(untappd_brewery_id)
                if brewery_details:
                    self.update_brewery_with_untappd_data(brewery['id'], brewery_details)
                
                # Get beers for this brewery
                beers = self.get_brewery_beers(untappd_brewery_id)
                
                for beer_item in beers:
                    beer = beer_item.get('beer')
                    if not beer:
                        continue
                    
                    # Try to match with existing beer
                    self.cursor.execute('''
                        SELECT b.id, b.name FROM beers b
                        JOIN beer_locations bl ON b.id = bl.beer_id
                        WHERE bl.brewery_id = ? AND b.name LIKE ?
                    ''', (brewery['id'], f'%{beer.get("beer_name")}%'))
                    
                    local_beer = self.cursor.fetchone()
                    
                    if local_beer:
                        # Update existing beer
                        beer_details = self.get_beer_info(beer.get('bid'))
                        if beer_details:
                            self.update_beer_with_untappd_data(local_beer['id'], beer_details)
                    else:
                        # Add new beer
                        try:
                            self.cursor.execute('''
                                INSERT INTO beers (
                                    name, type, abv, description, image_url, untappd_id, rating_score
                                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                beer.get('beer_name'),
                                beer.get('beer_style'),
                                beer.get('beer_abv'),
                                beer.get('beer_description'),
                                beer.get('beer_label'),
                                beer.get('bid'),
                                beer.get('rating_score')
                            ))
                            
                            beer_id = self.cursor.lastrowid
                            
                            # Link beer to brewery
                            self.cursor.execute('''
                                INSERT INTO beer_locations (
                                    beer_id, brewery_id
                                ) VALUES (?, ?)
                            ''', (beer_id, brewery['id']))
                            
                            self.conn.commit()
                            logging.info(f"Added new beer {beer.get('beer_name')} to brewery {brewery['name']}")
                        
                        except sqlite3.Error as e:
                            logging.error(f"Database error while adding beer {beer.get('beer_name')}: {e}")
                            self.conn.rollback()
            
            # Pause between breweries to respect rate limits
            time.sleep(2)
        
        logging.info("Completed Untappd data enrichment process")

if __name__ == "__main__":
    untappd_api = UntappdAPI()
    untappd_api.enrich_database()

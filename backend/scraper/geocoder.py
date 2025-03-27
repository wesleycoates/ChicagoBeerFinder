import requests
import sqlite3
import os
import time
import logging
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='geocoding.log'
)

class BreweryGeocoder:
    def __init__(self, db_path=None):
        """Initialize the geocoding script"""
        # Get API key from environment variables
        self.api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        
        if not self.api_key:
            raise ValueError("Google Maps API key not found. Please set GOOGLE_MAPS_API_KEY environment variable.")
        
        # Set up database connection
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'beers.db')
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        self.cursor = self.conn.cursor()
        
        # Geocoding API URL
        self.geocoding_url = "https://maps.googleapis.com/maps/api/geocode/json"
    
    def __del__(self):
        """Close database connection on object destruction"""
        if hasattr(self, 'conn'):
            self.conn.close()
    
    def geocode_address(self, address):
        """Geocode an address to get latitude and longitude"""
        params = {
            'address': address,
            'key': self.api_key
        }
        
        try:
            response = requests.get(self.geocoding_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] != 'OK':
                logging.error(f"Geocoding error: {data['status']} - {data.get('error_message', 'Unknown error')}")
                return None
            
            if not data['results']:
                logging.warning(f"No geocoding results found for address: {address}")
                return None
            
            # Get the first result
            location = data['results'][0]['geometry']['location']
            
            return {
                'latitude': location['lat'],
                'longitude': location['lng'],
                'formatted_address': data['results'][0]['formatted_address']
            }
        
        except requests.RequestException as e:
            logging.error(f"Request error: {e}")
            return None
    
    def update_brewery_coordinates(self, brewery_id, geocoding_result):
        """Update brewery with geocoded coordinates"""
        if not geocoding_result:
            return False
        
        try:
            self.cursor.execute('''
                UPDATE breweries
                SET latitude = ?, longitude = ?
                WHERE id = ?
            ''', (
                geocoding_result['latitude'],
                geocoding_result['longitude'],
                brewery_id
            ))
            
            self.conn.commit()
            logging.info(f"Updated coordinates for brewery ID {brewery_id}")
            return True
        
        except sqlite3.Error as e:
            logging.error(f"Database error while updating brewery {brewery_id}: {e}")
            self.conn.rollback()
            return False
    
    def geocode_breweries(self):
        """Geocode all breweries without coordinates"""
        logging.info("Starting brewery geocoding process")
        
        # Get all breweries that need geocoding
        self.cursor.execute('''
            SELECT id, name, address, city, state, zip_code
            FROM breweries
            WHERE (latitude IS NULL OR longitude IS NULL)
              AND address IS NOT NULL
        ''')
        
        breweries = self.cursor.fetchall()
        logging.info(f"Found {len(breweries)} breweries that need geocoding")
        
        for brewery in breweries:
            # Construct full address
            address_parts = [
                brewery['address'],
                brewery['city'] or 'Chicago',
                brewery['state'] or 'IL',
                brewery['zip_code']
            ]
            address = ', '.join(part for part in address_parts if part)
            
            logging.info(f"Geocoding brewery {brewery['name']} with address: {address}")
            
            # Geocode the address
            geocoding_result = self.geocode_address(address)
            
            if geocoding_result:
                self.update_brewery_coordinates(brewery['id'], geocoding_result)
            else:
                logging.warning(f"Failed to geocode address for brewery: {brewery['name']}")
            
            # Add delay between requests to respect API rate limits
            time.sleep(1)
        
        logging.info("Completed brewery geocoding process")

if __name__ == "__main__":
    geocoder = BreweryGeocoder()
    geocoder.geocode_breweries()

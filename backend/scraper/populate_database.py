import os
import sys
import logging
import time
import argparse
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('populate_database.log'),
        logging.StreamHandler()
    ]
)

# Add the parent directory to the path so imports work correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now import using shorter paths
from database import init_db
from scraper.chicago_beer_scraper import ChicagoBeerScraper
from scraper.untappd_api import UntappdAPI
from scraper.geocoder import BreweryGeocoder

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Populate beer database with scraped and API data')
    
    parser.add_argument('--init', action='store_true', help='Initialize a new empty database')
    parser.add_argument('--scrape', action='store_true', help='Scrape beer websites for data')
    parser.add_argument('--untappd', action='store_true', help='Enrich with Untappd API data')
    parser.add_argument('--geocode', action='store_true', help='Geocode brewery addresses')
    parser.add_argument('--all', action='store_true', help='Run all steps')
    
    return parser.parse_args()

def check_env_variables():
    """Check if required environment variables are set"""
    missing_vars = []
    
    # Check for Untappd API credentials
    if not os.getenv('UNTAPPD_CLIENT_ID'):
        missing_vars.append('UNTAPPD_CLIENT_ID')
    if not os.getenv('UNTAPPD_CLIENT_SECRET'):
        missing_vars.append('UNTAPPD_CLIENT_SECRET')
    
    # Check for Google Maps API key
    if not os.getenv('GOOGLE_MAPS_API_KEY'):
        missing_vars.append('GOOGLE_MAPS_API_KEY')
    
    if missing_vars:
        logging.warning(f"Missing environment variables: {', '.join(missing_vars)}")
        logging.warning("Create a .env file with these variables or set them in your environment.")
        return False
    
    return True

def initialize_database():
    """Initialize a new database"""
    logging.info("Initializing database...")
    init_db()
    logging.info("Database initialized.")

def scrape_beer_data():
    """Scrape beer data from websites"""
    logging.info("Starting web scraping for Chicago breweries and beers...")
    
    # Create scraper instance
    scraper = ChicagoBeerScraper()
    
    # Run the scraper
    scraper.run()
    
    logging.info("Web scraping completed.")

def enrich_with_untappd():
    """Enrich database with Untappd API data"""
    logging.info("Starting Untappd API enrichment...")
    
    # Create Untappd API instance
    untappd_api = UntappdAPI()
    
    # Run the enrichment
    untappd_api.enrich_database()
    
    logging.info("Untappd API enrichment completed.")

def geocode_addresses():
    """Geocode brewery addresses"""
    logging.info("Starting geocoding process...")
    
    # Create geocoder instance
    geocoder = BreweryGeocoder()
    
    # Run the geocoder
    geocoder.geocode_breweries()
    
    logging.info("Geocoding completed.")

def main():
    """Main function to run all steps"""
    load_dotenv()  # Load environment variables from .env file
    
    args = parse_args()
    
    # Check if we should run all steps
    if args.all:
        args.init = args.scrape = args.untappd = args.geocode = True
    
    # If no arguments provided, show help
    if not (args.init or args.scrape or args.untappd or args.geocode):
        print("No actions specified. Use --help to see available options.")
        return
    
    # Check environment variables
    if args.untappd or args.geocode:
        if not check_env_variables():
            logging.error("Missing required environment variables. Please set them and try again.")
            return
    
    # Run the requested steps
    if args.init:
        initialize_database()
    
    if args.scrape:
        scrape_beer_data()
    
    if args.untappd:
        enrich_with_untappd()
    
    if args.geocode:
        geocode_addresses()
    
    logging.info("Database population completed successfully.")

if __name__ == "__main__":
    main()

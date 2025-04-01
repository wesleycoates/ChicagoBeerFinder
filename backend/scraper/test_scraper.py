import logging
import sys
import json
from scraper.breweries.revolution import RevolutionScraper

def setup_logging():
    """Set up basic logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

def main():
    """Test the Revolution scraper"""
    setup_logging()
    logger = logging.getLogger("test")
    
    logger.info("Testing Revolution Brewing scraper...")
    
    # Create a scraper instance (use 0 as a placeholder brewery_id)
    scraper = RevolutionScraper(0, None)
    
    # Extract beers without saving to database
    beers = scraper.extract_beers()
    
    if beers:
        logger.info(f"Successfully extracted {len(beers)} beers")
        
        # Print first 3 beers as a sample
        for i, beer in enumerate(beers[:3], 1):
            logger.info(f"Beer {i}: {beer['name']} - {beer['type']} - {beer['abv']}% ABV")
            if beer.get('description'):
                logger.info(f"  Description: {beer['description'][:100]}...")
        
        # Save all results to a JSON file for inspection
        with open('revolution_beers.json', 'w') as f:
            json.dump(beers, f, indent=2)
            logger.info(f"Saved all {len(beers)} beers to revolution_beers.json")
    else:
        logger.error("Failed to extract any beers")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
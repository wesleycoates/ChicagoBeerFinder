import logging
import argparse
import sqlite3
import os
import sys
from typing import Dict

# Import scrapers
from scraper.breweries.revolution import RevolutionScraper

def setup_logging(log_file=None, verbose=False):
    """Set up logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

def get_brewery_id(db_path: str, brewery_name: str) -> int:
    """Get brewery ID from database by name"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM breweries WHERE name = ?", (brewery_name,))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        else:
            raise ValueError(f"Brewery not found: {brewery_name}")
            
    except sqlite3.Error as e:
        raise Exception(f"Database error: {str(e)}")
    finally:
        if conn:
            conn.close()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run brewery scrapers")
    parser.add_argument("--db", help="Path to the SQLite database", 
                        default=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'beers.db'))
    parser.add_argument("--log", help="Path to log file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--brewery", help="Run only for the specified brewery")
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.log, args.verbose)
    logger = logging.getLogger("scraper.main")
    
    # Check if database exists
    if not os.path.exists(args.db):
        logger.error(f"Database not found: {args.db}")
        sys.exit(1)
    
    # Define available scrapers
    scrapers = {
        "Revolution Brewing": RevolutionScraper
    }
    
    if args.brewery:
        # Run a specific scraper
        if args.brewery not in scrapers:
            logger.error(f"No scraper available for: {args.brewery}")
            sys.exit(1)
            
        try:
            brewery_id = get_brewery_id(args.db, args.brewery)
            scraper = scrapers[args.brewery](brewery_id, args.db)
            success = scraper.run()
            sys.exit(0 if success else 1)
        except Exception as e:
            logger.error(f"Error running scraper: {str(e)}")
            sys.exit(1)
    else:
        # Run all available scrapers
        success_count = 0
        fail_count = 0
        
        for name, scraper_class in scrapers.items():
            try:
                brewery_id = get_brewery_id(args.db, name)
                scraper = scraper_class(brewery_id, args.db)
                if scraper.run():
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                logger.error(f"Error running scraper for {name}: {str(e)}")
                fail_count += 1
        
        logger.info(f"Completed: {success_count} succeeded, {fail_count} failed")
        sys.exit(0 if fail_count == 0 else 1)

if __name__ == "__main__":
    main()
import logging
import requests
from bs4 import BeautifulSoup
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

class BaseScraper:
    """Base class for all brewery scrapers"""
    
    def __init__(self, brewery_id: int, name: str, url: str, db_path: str = None):
        self.brewery_id = brewery_id
        self.name = name
        self.url = url
        
        # Set default database path if not provided
        if db_path is None:
            # Go up one level from the scraper folder to the backend folder
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'beers.db')
        self.db_path = db_path
        
        # Set up logging
        self.logger = logging.getLogger(f"scraper.{name.replace(' ', '_').lower()}")
        
    def get_page(self, url: Optional[str] = None) -> Optional[BeautifulSoup]:
        """Fetch a page and return a BeautifulSoup object"""
        try:
            target_url = url or self.url
            self.logger.info(f"Fetching {target_url}")
            
            response = requests.get(target_url, headers={
                'User-Agent': 'ChicagoBeerFinder/1.0 (educational project)',
                'Accept': 'text/html,application/xhtml+xml,application/xml',
                'Accept-Language': 'en-US,en;q=0.9',
            }, timeout=30)
            
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch {url or self.url}: {str(e)}")
            return None
    
    def extract_beers(self) -> List[Dict[str, Any]]:
        """Extract beer information from the brewery website
        
        Override this method in subclasses for specific brewery implementations
        """
        raise NotImplementedError("Subclasses must implement extract_beers()")
    
    def save_beers(self, beers: List[Dict[str, Any]]) -> bool:
        """Save extracted beers to the database"""
        if not beers:
            self.logger.warning("No beers to save")
            return False
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get existing beers for this brewery to compare
            cursor.execute("""
                SELECT b.id, b.name FROM beers b
                JOIN beer_locations bl ON b.id = bl.beer_id
                WHERE bl.brewery_id = ?
            """, (self.brewery_id,))
            
            existing_beers = {name: beer_id for beer_id, name in cursor.fetchall()}
            
            # Count stats for logging
            stats = {
                'added': 0,
                'updated': 0,
                'unchanged': 0
            }
            
            # Process each beer
            for beer in beers:
                beer_name = beer['name']
                
                if beer_name in existing_beers:
                    # Update existing beer
                    beer_id = existing_beers[beer_name]
                    cursor.execute("""
                        UPDATE beers
                        SET type = ?, abv = ?, description = ?
                        WHERE id = ?
                    """, (beer['type'], beer['abv'], beer.get('description', ''), beer_id))
                    
                    if cursor.rowcount > 0:
                        stats['updated'] += 1
                    else:
                        stats['unchanged'] += 1
                else:
                    # Insert new beer
                    cursor.execute("""
                        INSERT INTO beers (name, type, abv, description)
                        VALUES (?, ?, ?, ?)
                    """, (beer_name, beer['type'], beer['abv'], beer.get('description', '')))
                    
                    beer_id = cursor.lastrowid
                    
                    # Create beer_location relationship
                    cursor.execute("""
                        INSERT INTO beer_locations (beer_id, brewery_id, is_available, last_updated)
                        VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                    """, (beer_id, self.brewery_id))
                    
                    stats['added'] += 1
            
            conn.commit()
            self.logger.info(f"Saved {len(beers)} beers: {stats['added']} added, {stats['updated']} updated, {stats['unchanged']} unchanged")
            return True
            
        except sqlite3.Error as e:
            self.logger.error(f"Database error: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def run(self) -> bool:
        """Run the scraper and save results"""
        self.logger.info(f"Running scraper for {self.name}")
        beers = self.extract_beers()
        
        if beers:
            self.logger.info(f"Extracted {len(beers)} beers from {self.name}")
            return self.save_beers(beers)
        else:
            self.logger.warning(f"No beers extracted from {self.name}")
            return False
import requests
import sqlite3
import os
import json
import logging
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='brewery_import.log'
)

class OpenBreweryDBImporter:
    def __init__(self, db_path=None):
        """Initialize the importer with database connection"""
        if db_path is None:
            # Use an absolute path
            db_path = '/workspaces/ChicagoBeerFinder/backend/beers.db'
        
        print(f"Connecting to database at: {db_path}")
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
    def __del__(self):
        """Close database connection on object destruction"""
        if hasattr(self, 'conn'):
            self.conn.close()
    
    def fetch_chicago_breweries(self):
        """Fetch Chicago breweries from Open Brewery DB API"""
        breweries = []
        page = 1
        
        while True:
            print(f"Fetching page {page} of Chicago breweries...")
            url = f"https://api.openbrewerydb.org/breweries?by_city=chicago&per_page=50&page={page}"
            
            try:
                response = requests.get(url)
                response.raise_for_status()
                
                data = response.json()
                
                if not data:  # Empty array means no more results
                    break
                
                breweries.extend(data)
                print(f"Found {len(data)} breweries on page {page}")
                
                # Add delay to be nice to the API
                time.sleep(1)
                page += 1
                
            except requests.RequestException as e:
                print(f"Error fetching breweries: {e}")
                break
        
        print(f"Total breweries found: {len(breweries)}")
        return breweries
    
    def save_brewery_to_db(self, brewery):
        """Save brewery data to database"""
        try:
            # Check if brewery already exists
            self.cursor.execute("SELECT id FROM breweries WHERE name = ?", (brewery.get('name'),))
            existing = self.cursor.fetchone()
            
            if existing:
                print(f"Brewery '{brewery.get('name')}' already exists, skipping.")
                return False
            
            # Build latitude and longitude from coordinates if available
            latitude = None
            longitude = None
            
            if brewery.get('latitude') and brewery.get('longitude'):
                try:
                    latitude = float(brewery['latitude'])
                    longitude = float(brewery['longitude'])
                except (ValueError, TypeError):
                    pass
            
            # Insert brewery
            self.cursor.execute('''
                INSERT INTO breweries (
                    name, address, city, state, zip_code, phone, website, latitude, longitude
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                brewery.get('name'),
                f"{brewery.get('street') or ''}",
                brewery.get('city'),
                brewery.get('state'),
                brewery.get('postal_code'),
                brewery.get('phone'),
                brewery.get('website_url'),
                latitude,
                longitude
            ))
            
            brewery_id = self.cursor.lastrowid
            print(f"Added brewery: {brewery.get('name')}")
            
            return brewery_id
            
        except sqlite3.Error as e:
            print(f"Database error while saving {brewery.get('name')}: {e}")
            self.conn.rollback()
            return False
    
    def run(self):
        """Run the complete import process"""
        print("Starting Chicago brewery import from Open Brewery DB")
        
        # Check if the breweries table exists
        try:
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='breweries'")
            table_exists = self.cursor.fetchone()
            if not table_exists:
                print("ERROR: The 'breweries' table does not exist!")
            
                # Try to show available tables
                print("Available tables:")
                self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = self.cursor.fetchall()
                for table in tables:
                    print(f"- {table[0]}")
            
                return
            else:
                print("The 'breweries' table exists. Continuing...")
                
                # Check the table structure
                self.cursor.execute("PRAGMA table_info(breweries)")
                columns = self.cursor.fetchall()
                print("Table structure:")
                for col in columns:
                    print(f"- {col[1]} ({col[2]})")

            # Get breweries
            breweries = self.fetch_chicago_breweries()
        
            # Save to database
            added_count = 0
            for brewery in breweries:
                if self.save_brewery_to_db(brewery):
                    added_count += 1
        
            # Commit changes
            self.conn.commit()
        
            print(f"Added {added_count} new breweries to the database")

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")

if __name__ == "__main__":
    importer = OpenBreweryDBImporter()
    importer.run()

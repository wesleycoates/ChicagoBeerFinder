import sqlite3
import os
import sys
import json
import logging
import csv
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('manual_data_entry.log'),
        logging.StreamHandler()
    ]
)

class BreweryDataManager:
    def __init__(self, db_path=None):
        """Initialize database connection"""
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'beers.db')
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        self.cursor = self.conn.cursor()
    
    def __del__(self):
        """Close database connection on object destruction"""
        if hasattr(self, 'conn'):
            self.conn.close()
    
    def add_brewery(self, brewery_data):
        """Add a new brewery to the database"""
        try:
            # Check if brewery already exists
            self.cursor.execute("SELECT id FROM breweries WHERE name = ?", (brewery_data.get('name'),))
            existing = self.cursor.fetchone()
            
            if existing:
                logging.warning(f"Brewery '{brewery_data.get('name')}' already exists with ID {existing['id']}")
                return existing['id']
            
            # Insert new brewery
            columns = []
            placeholders = []
            values = []
            
            for key, value in brewery_data.items():
                if value is not None and key in [
                    'name', 'address', 'city', 'state', 'zip_code', 'phone', 
                    'website', 'description', 'latitude', 'longitude', 'hours',
                    'has_taproom'
                ]:
                    columns.append(key)
                    placeholders.append('?')
                    values.append(value)
            
            if not columns:
                logging.error("No valid brewery data provided")
                return None
            
            query = f"INSERT INTO breweries ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            self.cursor.execute(query, values)
            self.conn.commit()
            
            brewery_id = self.cursor.lastrowid
            logging.info(f"Added brewery '{brewery_data.get('name')}' with ID {brewery_id}")
            
            return brewery_id
        
        except sqlite3.Error as e:
            logging.error(f"Database error while adding brewery: {e}")
            self.conn.rollback()
            return None
    
    def add_beer(self, beer_data):
        """Add a new beer to the database"""
        try:
            # Check if beer already exists for the brewery
            if 'brewery_id' in beer_data:
                self.cursor.execute("""
                    SELECT b.id FROM beers b
                    JOIN beer_locations bl ON b.id = bl.beer_id
                    WHERE b.name = ? AND bl.brewery_id = ?
                """, (beer_data.get('name'), beer_data.get('brewery_id')))
                existing = self.cursor.fetchone()
                
                if existing:
                    logging.warning(f"Beer '{beer_data.get('name')}' already exists with ID {existing['id']}")
                    return existing['id']
            
            # Insert new beer
            columns = []
            placeholders = []
            values = []
            
            for key, value in beer_data.items():
                if value is not None and key in [
                    'name', 'type', 'abv', 'ibu', 'description', 
                    'image_url', 'rating_score', 'seasonal'
                ]:
                    columns.append(key)
                    placeholders.append('?')
                    values.append(value)
            
            if not columns:
                logging.error("No valid beer data provided")
                return None
            
            query = f"INSERT INTO beers ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            self.cursor.execute(query, values)
            
            beer_id = self.cursor.lastrowid
            
            # Link beer to brewery if brewery_id is provided
            if 'brewery_id' in beer_data and beer_data['brewery_id'] is not None:
                self.cursor.execute("""
                    INSERT INTO beer_locations (beer_id, brewery_id)
                    VALUES (?, ?)
                """, (beer_id, beer_data['brewery_id']))
            
            self.conn.commit()
            logging.info(f"Added beer '{beer_data.get('name')}' with ID {beer_id}")
            
            return beer_id
        
        except sqlite3.Error as e:
            logging.error(f"Database error while adding beer: {e}")
            self.conn.rollback()
            return None
    
    def import_from_json(self, json_file):
        """Import data from a JSON file"""
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            breweries_added = 0
            beers_added = 0
            
            for brewery_data in data.get('breweries', []):
                brewery_id = self.add_brewery(brewery_data)
                
                if brewery_id:
                    breweries_added += 1
                    
                    # Add beers for this brewery
                    for beer_data in brewery_data.get('beers', []):
                        beer_data['brewery_id'] = brewery_id
                        if self.add_beer(beer_data):
                            beers_added += 1
            
            logging.info(f"Imported {breweries_added} breweries and {beers_added} beers from {json_file}")
            return True
        
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logging.error(f"Error importing from JSON file: {e}")
            return False
    
    def import_from_csv(self, csv_file):
        """Import data from a CSV file"""
        try:
            with open(csv_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            # Determine if this is a brewery or beer CSV
            if 'name' in rows[0] and ('address' in rows[0] or 'city' in rows[0]):
                # Brewery CSV
                breweries_added = 0
                
                for row in rows:
                    # Convert string values to appropriate types
                    if 'latitude' in row:
                        row['latitude'] = float(row['latitude']) if row['latitude'] else None
                    if 'longitude' in row:
                        row['longitude'] = float(row['longitude']) if row['longitude'] else None
                    if 'has_taproom' in row:
                        row['has_taproom'] = int(row['has_taproom']) if row['has_taproom'] else 0
                    
                    if self.add_brewery(row):
                        breweries_added += 1
                
                logging.info(f"Imported {breweries_added} breweries from {csv_file}")
            
            elif 'name' in rows[0] and ('type' in rows[0] or 'abv' in rows[0]):
                # Beer CSV
                beers_added = 0
                
                for row in rows:
                    # Convert string values to appropriate types
                    if 'abv' in row:
                        row['abv'] = float(row['abv']) if row['abv'] else None
                    if 'ibu' in row:
                        row['ibu'] = float(row['ibu']) if row['ibu'] else None
                    if 'rating_score' in row:
                        row['rating_score'] = float(row['rating_score']) if row['rating_score'] else None
                    if 'seasonal' in row:
                        row['seasonal'] = int(row['seasonal']) if row['seasonal'] else 0
                    
                    # If brewery_name is provided, look up the brewery_id
                    if 'brewery_name' in row and row['brewery_name']:
                        self.cursor.execute("SELECT id FROM breweries WHERE name = ?", (row['brewery_name'],))
                        brewery = self.cursor.fetchone()
                        
                        if brewery:
                            row['brewery_id'] = brewery['id']
                        else:
                            logging.warning(f"Brewery '{row['brewery_name']}' not found for beer '{row['name']}'")
                    
                    if self.add_beer(row):
                        beers_added += 1
                
                logging.info(f"Imported {beers_added} beers from {csv_file}")
            
            else:
                logging.error(f"Unknown CSV format in {csv_file}")
                return False
            
            return True
        
        except (csv.Error, FileNotFoundError) as e:
            logging.error(f"Error importing from CSV file: {e}")
            return False
    
    def export_to_json(self, output_file):
        """Export database to JSON file"""
        try:
            # Get all breweries
            self.cursor.execute("""
                SELECT * FROM breweries
            """)
            breweries = [dict(row) for row in self.cursor.fetchall()]
            
            # For each brewery, get its beers
            for brewery in breweries:
                self.cursor.execute("""
                    SELECT b.* FROM beers b
                    JOIN beer_locations bl ON b.id = bl.beer_id
                    WHERE bl.brewery_id = ?
                """, (brewery['id'],))
                
                brewery['beers'] = [dict(row) for row in self.cursor.fetchall()]
            
            # Write to JSON file
            with open(output_file, 'w') as f:
                json.dump({'breweries': breweries}, f, indent=2)
            
            logging.info(f"Exported {len(breweries)} breweries to {output_file}")
            return True
        
        except (sqlite3.Error, IOError) as e:
            logging.error(f"Error exporting to JSON file: {e}")
            return False
    
    def export_brewery_template(self, output_file):
        """Export empty brewery CSV template"""
        fieldnames = [
            'name', 'address', 'city', 'state', 'zip_code', 'phone', 
            'website', 'description', 'latitude', 'longitude', 'hours',
            'has_taproom'
        ]
        
        try:
            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
            
            logging.info(f"Exported brewery template to {output_file}")
            return True
        
        except IOError as e:
            logging.error(f"Error exporting brewery template: {e}")
            return False
    
    def export_beer_template(self, output_file):
        """Export empty beer CSV template"""
        fieldnames = [
            'name', 'brewery_name', 'type', 'abv', 'ibu', 'description', 
            'image_url', 'rating_score', 'seasonal'
        ]
        
        try:
            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
            
            logging.info(f"Exported beer template to {output_file}")
            return True
        
        except IOError as e:
            logging.error(f"Error exporting beer template: {e}")
            return False
    
    def interactive_add_brewery(self):
        """Add a brewery interactively"""
        print("\n=== Add New Brewery ===\n")
        
        brewery_data = {
            'name': input("Brewery Name: ").strip(),
            'address': input("Address: ").strip(),
            'city': input("City [Chicago]: ").strip() or "Chicago",
            'state': input("State [IL]: ").strip() or "IL",
            'zip_code': input("ZIP Code: ").strip(),
            'phone': input("Phone: ").strip(),
            'website': input("Website: ").strip(),
            'description': input("Description: ").strip()
        }
        
        # Optional numeric fields
        lat_input = input("Latitude (optional): ").strip()
        if lat_input:
            try:
                brewery_data['latitude'] = float(lat_input)
            except ValueError:
                print("Invalid latitude, skipping.")
        
        lng_input = input("Longitude (optional): ").strip()
        if lng_input:
            try:
                brewery_data['longitude'] = float(lng_input)
            except ValueError:
                print("Invalid longitude, skipping.")
        
        has_taproom = input("Has Taproom? (y/n): ").strip().lower()
        brewery_data['has_taproom'] = 1 if has_taproom == 'y' else 0
        
        brewery_data['hours'] = input("Hours (e.g., 'Mon-Fri: 12-8pm, Sat-Sun: 10am-10pm'): ").strip()
        
        # Add the brewery
        brewery_id = self.add_brewery(brewery_data)
        
        if brewery_id:
            print(f"\nBrewery '{brewery_data['name']}' added successfully with ID {brewery_id}")
            
            # Ask if want to add beers for this brewery
            add_beers = input("\nDo you want to add beers for this brewery? (y/n): ").strip().lower()
            
            while add_beers == 'y':
                self.interactive_add_beer(brewery_id, brewery_data['name'])
                add_beers = input("\nAdd another beer? (y/n): ").strip().lower()
        
        return brewery_id
    
    def interactive_add_beer(self, brewery_id=None, brewery_name=None):
        """Add a beer interactively"""
        print("\n=== Add New Beer ===\n")
        
        if brewery_id is None:
            # List breweries to choose from
            self.cursor.execute("SELECT id, name FROM breweries ORDER BY name")
            breweries = self.cursor.fetchall()
            
            if not breweries:
                print("No breweries found. Please add a brewery first.")
                return None
            
            print("Available Breweries:")
            for i, brewery in enumerate(breweries):
                print(f"{i+1}. {brewery['name']}")
            
            choice = input("\nSelect brewery (number): ").strip()
            try:
                index = int(choice) - 1
                brewery_id = breweries[index]['id']
                brewery_name = breweries[index]['name']
            except (ValueError, IndexError):
                print("Invalid selection.")
                return None
        
        beer_data = {
            'name': input("Beer Name: ").strip(),
            'type': input("Beer Type/Style: ").strip(),
            'description': input("Description: ").strip(),
            'brewery_id': brewery_id
        }
        
        # Optional numeric fields
        abv_input = input("ABV (optional): ").strip()
        if abv_input:
            try:
                beer_data['abv'] = float(abv_input)
            except ValueError:
                print("Invalid ABV, skipping.")
        
        ibu_input = input("IBU (optional): ").strip()
        if ibu_input:
            try:
                beer_data['ibu'] = float(ibu_input)
            except ValueError:
                print("Invalid IBU, skipping.")
        
        beer_data['image_url'] = input("Image URL (optional): ").strip()
        
        rating_input = input("Rating (1-5, optional): ").strip()
        if rating_input:
            try:
                beer_data['rating_score'] = float(rating_input)
            except ValueError:
                print("Invalid rating, skipping.")
        
        seasonal = input("Seasonal? (y/n): ").strip().lower()
        beer_data['seasonal'] = 1 if seasonal == 'y' else 0
        
        # Add the beer
        beer_id = self.add_beer(beer_data)
        
        if beer_id:
            print(f"\nBeer '{beer_data['name']}' added successfully to '{brewery_name}' with ID {beer_id}")
        
        return beer_id
    
    def browse_breweries(self):
        """Browse breweries in the database"""
        self.cursor.execute("""
            SELECT b.id, b.name, b.city, b.state, COUNT(bl.beer_id) as beer_count
            FROM breweries b
            LEFT JOIN beer_locations bl ON b.id = bl.brewery_id
            GROUP BY b.id
            ORDER BY b.name
        """)
        
        breweries = self.cursor.fetchall()
        
        if not breweries:
            print("No breweries found in the database.")
            return
        
        print(f"\n=== Breweries ({len(breweries)}) ===\n")
        for i, brewery in enumerate(breweries):
            print(f"{i+1}. {brewery['name']} ({brewery['city']}, {brewery['state']}) - {brewery['beer_count']} beers")
        
        choice = input("\nSelect brewery to view details (number), or 0 to go back: ").strip()
        try:
            index = int(choice) - 1
            if index < 0:
                return
            
            brewery_id = breweries[index]['id']
            self.view_brewery(brewery_id)
        except (ValueError, IndexError):
            print("Invalid selection.")
    
    def view_brewery(self, brewery_id):
        """View details of a specific brewery"""
        self.cursor.execute("SELECT * FROM breweries WHERE id = ?", (brewery_id,))
        brewery = self.cursor.fetchone()
        
        if not brewery:
            print(f"Brewery with ID {brewery_id} not found.")
            return
        
        print(f"\n=== {brewery['name']} ===")
        print(f"Address: {brewery['address']}, {brewery['city']}, {brewery['state']} {brewery['zip_code']}")
        if brewery['phone']:
            print(f"Phone: {brewery['phone']}")
        if brewery['website']:
            print(f"Website: {brewery['website']}")
        if brewery['hours']:
            print(f"Hours: {brewery['hours']}")
        if brewery['description']:
            print(f"\nDescription: {brewery['description']}")
        
        print("\nBeers:")
        self.cursor.execute("""
            SELECT b.* FROM beers b
            JOIN beer_locations bl ON b.id = bl.beer_id
            WHERE bl.brewery_id = ?
            ORDER BY b.name
        """, (brewery_id,))
        
        beers = self.cursor.fetchall()
        
        if not beers:
            print("No beers found for this brewery.")
        else:
            for i, beer in enumerate(beers):
                print(f"{i+1}. {beer['name']} - {beer['type']} ({beer['abv']}% ABV)")
        
        print("\nOptions:")
        print("1. Add Beer to this Brewery")
        print("2. Edit Brewery")
        print("3. View Beer Details")
        print("4. Back to Brewery List")
        
        choice = input("\nSelect option: ").strip()
        
        if choice == '1':
            self.interactive_add_beer(brewery_id, brewery['name'])
            self.view_brewery(brewery_id)
        elif choice == '2':
            print("Edit functionality not implemented yet.")
            self.view_brewery(brewery_id)
        elif choice == '3':
            beer_choice = input("Select beer (number): ").strip()
            try:
                beer_index = int(beer_choice) - 1
                beer_id = beers[beer_index]['id']
                self.view_beer(beer_id)
                self.view_brewery(brewery_id)
            except (ValueError, IndexError):
                print("Invalid selection.")
                self.view_brewery(brewery_id)
        elif choice == '4':
            self.browse_breweries()
    
    def view_beer(self, beer_id):
        """View details of a specific beer"""
        self.cursor.execute("""
            SELECT b.*, br.name as brewery_name
            FROM beers b
            JOIN beer_locations bl ON b.id = bl.beer_id
            JOIN breweries br ON bl.brewery_id = br.id
            WHERE b.id = ?
        """, (beer_id,))
        
        beer = self.cursor.fetchone()
        
        if not beer:
            print(f"Beer with ID {beer_id} not found.")
            return
        
        print(f"\n=== {beer['name']} ===")
        print(f"Brewery: {beer['brewery_name']}")
        print(f"Type: {beer['type']}")
        print(f"ABV: {beer['abv']}%")
        
        if beer['ibu']:
            print(f"IBU: {beer['ibu']}")
        
        if beer['seasonal']:
            print("Seasonal: Yes")
        
        if beer['rating_score']:
            print(f"Rating: {beer['rating_score']}")
        
        if beer['description']:
            print(f"\nDescription: {beer['description']}")
        
        input("\nPress Enter to continue...")
    
    def interactive_menu(self):
        """Show interactive menu"""
        while True:
            print("\n=== Chicago Beer Finder - Data Manager ===\n")
            print("1. Add Brewery")
            print("2. Add Beer")
            print("3. Browse Breweries")
            print("4. Import from JSON or CSV")
            print("5. Export Data")
            print("6. Generate Templates")
            print("0. Exit")
            
            choice = input("\nSelect option: ").strip()
            
            if choice == '1':
                self.interactive_add_brewery()
            elif choice == '2':
                self.interactive_add_beer()
            elif choice == '3':
                self.browse_breweries()
            elif choice == '4':
                print("\n=== Import Data ===\n")
                print("1. Import from JSON")
                print("2. Import from CSV")
                print("0. Back")
                
                import_choice = input("\nSelect option: ").strip()
                
                if import_choice == '1':
                    file_path = input("Enter JSON file path: ").strip()
                    self.import_from_json(file_path)
                elif import_choice == '2':
                    file_path = input("Enter CSV file path: ").strip()
                    self.import_from_csv(file_path)
            elif choice == '5':
                print("\n=== Export Data ===\n")
                file_path = input("Enter output JSON file path: ").strip()
                self.export_to_json(file_path)
            elif choice == '6':
                print("\n=== Generate Templates ===\n")
                print("1. Brewery CSV Template")
                print("2. Beer CSV Template")
                print("0. Back")
                
                template_choice = input("\nSelect option: ").strip()
                
                if template_choice == '1':
                    file_path = input("Enter output CSV file path: ").strip()
                    self.export_brewery_template(file_path)
                elif template_choice == '2':
                    file_path = input("Enter output CSV file path: ").strip()
                    self.export_beer_template(file_path)
            elif choice == '0':
                print("Exiting data manager.")
                break
            else:
                print("Invalid choice. Please try again.")

def main():
    """Main function"""
    db_manager = BreweryDataManager()
    db_manager.interactive_menu()

if __name__ == "__main__":
    main()

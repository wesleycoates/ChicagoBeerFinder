#!/usr/bin/env python3
"""
Beer App Setup and Run Script

This script sets up the SQLite database, imports JSON data, and starts the Flask API.
"""

import os
import argparse
import subprocess
import sys
import time

# Import our custom modules
# You'll need to have these files in the same directory
from sqlite_setup import setup_database
from json_importer import import_json_data

def main():
    parser = argparse.ArgumentParser(description='Set up and run the Beer App')
    parser.add_argument('--db', default='beers.db', help='Path to the SQLite database file')
    parser.add_argument('--json-dir', default='./beer_json_files', help='Directory containing JSON files')
    parser.add_argument('--skip-import', action='store_true', help='Skip importing JSON data')
    parser.add_argument('--skip-setup', action='store_true', help='Skip database setup')
    
    args = parser.parse_args()
    
    # Create database directory if it doesn't exist
    db_dir = os.path.dirname(args.db)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
    # Step 1: Set up the database
    if not args.skip_setup:
        print("Setting up the database...")
        try:
            setup_database(args.db)
            print("Database setup complete!")
        except Exception as e:
            print(f"Error setting up database: {e}")
            return 1
    
    # Step 2: Import JSON data
    if not args.skip_import:
        print("\nImporting JSON data...")
        if not os.path.exists(args.json_dir):
            print(f"JSON directory not found: {args.json_dir}")
            json_dir_input = input("Enter path to JSON directory or press Enter to skip: ")
            if json_dir_input:
                args.json_dir = json_dir_input
            else:
                print("Skipping JSON import.")
                args.skip_import = True
        
        if not args.skip_import:
            try:
                import_json_data(args.json_dir, args.db)
                print("JSON import complete!")
            except Exception as e:
                print(f"Error importing JSON data: {e}")
                return 1
    
    # Step 3: Start the Flask API
    print("\nStarting Flask API...")
    try:
        # Check if the api.py file exists
        if not os.path.exists('api.py'):
            print("Error: api.py not found!")
            return 1
        
        # Set the DATABASE_PATH environment variable
        os.environ['DATABASE_PATH'] = os.path.abspath(args.db)
        
        # Start the Flask app
        subprocess.run([sys.executable, 'api.py'])
    except KeyboardInterrupt:
        print("\nAPI server stopped.")
    except Exception as e:
        print(f"Error starting API: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

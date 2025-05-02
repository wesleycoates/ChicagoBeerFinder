#!/bin/bash
# Script to copy all beer JSON files to a common directory

# Create the destination directory if it doesn't exist
mkdir -p beer_json_files

# Copy all JSON files from scraped_data directory
cp ./backend/scraper/breweries/scraped_data/*.json ./beer_json_files/

# Also copy files from chicago_beer_data if they exist
cp ./backend/scraper/chicago_beer_data/*.json ./beer_json_files/ 2>/dev/null || :
cp ./backend/scraper/breweries/chicago_beer_data/*.json ./beer_json_files/ 2>/dev/null || :

# Copy files from brewery_data if they exist
cp ./backend/brewery_data/*.json ./beer_json_files/ 2>/dev/null || :

echo "Copied JSON files to beer_json_files directory"

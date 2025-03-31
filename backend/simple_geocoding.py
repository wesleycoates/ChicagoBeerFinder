# Save this file as backend/simple_geocoding.py

"""
Simple geocoding module for the Chicago Beer Finder app.
This uses hardcoded coordinates for Chicago breweries to avoid requiring external API calls.
In a production app, you would use a real geocoding service.
"""

import json
import os

# Dictionary mapping brewery names to coordinates
BREWERY_COORDINATES = {
    "Revolution Brewing": {"lat": 41.9231, "lng": -87.6965},
    "Half Acre Beer Company": {"lat": 41.9795, "lng": -87.6843},
    "Goose Island Beer Co.": {"lat": 41.8870, "lng": -87.6722},
    "Lagunitas Brewing Company": {"lat": 41.8579, "lng": -87.6683},
    "Hopewell Brewing Company": {"lat": 41.9308, "lng": -87.7070},
    "Marz Community Brewing": {"lat": 41.8376, "lng": -87.6526},
    "Off Color Brewing": {"lat": 41.9134, "lng": -87.6710},
    "Pipeworks Brewing Co.": {"lat": 41.9205, "lng": -87.7321},
    "Moody Tongue Brewing Company": {"lat": 41.8501, "lng": -87.6518},
    "Spiteful Brewing": {"lat": 41.9763, "lng": -87.6893}
}

def get_coordinates_for_brewery(brewery_name):
    """
    Get coordinates for a brewery based on its name.
    
    Args:
        brewery_name (str): Name of the brewery
        
    Returns:
        dict: Dictionary containing lat and lng keys, or default Chicago coordinates
    """
    default_coords = {"lat": 41.8781, "lng": -87.6298}  # Chicago center coordinates
    
    # Try to find the brewery in our dictionary
    return BREWERY_COORDINATES.get(brewery_name, default_coords)

def add_coordinates_to_results(results):
    """
    Add latitude and longitude to search results.
    
    Args:
        results (list): List of dictionaries containing brewery information
        
    Returns:
        list: The same list with lat and lng added to each item
    """
    for item in results:
        brewery_name = item.get('brewery')
        if brewery_name:
            coords = get_coordinates_for_brewery(brewery_name)
            item['lat'] = coords['lat']
            item['lng'] = coords['lng']
    
    return results
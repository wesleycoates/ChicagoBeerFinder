#!/usr/bin/env python
"""Test script for the local beer client."""

from local_beer_client import LocalBeerClient

def test_local_beer_client():
    """Test the local beer client functionality."""
    client = LocalBeerClient()
    
    # Test getting a random beer
    print("Testing get_random_beer():")
    random_beer = client.get_random_beer()
    if random_beer and len(random_beer) > 0:
        beer = random_beer[0]
        print(f"Found beer: {beer['name']} (ABV: {beer['abv']}%)")
        print(f"Description: {beer['description'][:100]}...")
    else:
        print("No random beer found.")
    
    print("\n" + "-"*50 + "\n")
    
    # Test searching for beers by name
    print("Testing search_beers_by_name('IPA'):")
    ipa_beers = client.search_beers_by_name("IPA")
    if ipa_beers and len(ipa_beers) > 0:
        print(f"Found {len(ipa_beers)} IPA beers:")
        for beer in ipa_beers:
            print(f"- {beer['name']} (ABV: {beer['abv']}%)")
    else:
        print("No IPA beers found.")
    
    print("\n" + "-"*50 + "\n")
    
    # Test searching by ABV
    print("Testing search_beers_by_abv(min_abv=6.0):")
    strong_beers = client.search_beers_by_abv(min_abv=6.0)
    if strong_beers and len(strong_beers) > 0:
        print(f"Found {len(strong_beers)} beers with ABV >= 6%:")
        for beer in strong_beers:
            print(f"- {beer['name']} (ABV: {beer['abv']}%)")
    else:
        print("No beers found in the specified ABV range.")

if __name__ == "__main__":
    test_local_beer_client()
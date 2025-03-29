#!/usr/bin/env python
"""Test script for the Punk API client."""

from punk_api_client import PunkAPIClient

def test_punk_api():
    """Test the Punk API client functionality."""
    client = PunkAPIClient()
    
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
    
    # Test searching for IPA beers
    print("Testing search_beers_by_name('IPA'):")
    ipa_beers = client.search_beers_by_name("IPA", per_page=3)
    if ipa_beers and len(ipa_beers) > 0:
        print(f"Found {len(ipa_beers)} IPA beers:")
        for beer in ipa_beers:
            print(f"- {beer['name']} (ABV: {beer['abv']}%)")
    else:
        print("No IPA beers found.")
    
    print("\n" + "-"*50 + "\n")
    
    # Test searching by ABV
    print("Testing search_beers_by_abv(min_abv=7.0, max_abv=8.0):")
    strong_beers = client.search_beers_by_abv(min_abv=7.0, max_abv=8.0, per_page=3)
    if strong_beers and len(strong_beers) > 0:
        print(f"Found {len(strong_beers)} beers with ABV between 7% and 8%:")
        for beer in strong_beers:
            print(f"- {beer['name']} (ABV: {beer['abv']}%)")
    else:
        print("No beers found in the specified ABV range.")

if __name__ == "__main__":
    test_punk_api()
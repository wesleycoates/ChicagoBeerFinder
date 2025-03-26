import requests
from bs4 import BeautifulSoup
import pandas as pd

def scrape_brewery_site(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    beers = []
    # This selector would need to be adjusted for each site
    beer_elements = soup.select('.beer-list .beer-item')
    
    for beer in beer_elements:
        name = beer.select_one('.beer-name').text.strip()
        beer_type = beer.select_one('.beer-style').text.strip()
        abv = beer.select_one('.beer-abv').text.strip()
        
        beers.append({
            'name': name,
            'type': beer_type,
            'abv': abv,
            'brewery': 'Brewery Name',
            'location': 'Address'
        })
    
    return beers
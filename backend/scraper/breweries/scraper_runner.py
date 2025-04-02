# run_scrapers.py
from off_color_scraper import OffColorScraper
from suncatcher_scraper import SuncatcherScraper  # Assuming you've renamed your previous script

def run_scrapers():
    """Run all brewery scrapers"""
    scrapers = [
        SuncatcherScraper(),
        OffColorScraper(),
        # Add more scrapers here as they're developed
    ]
    
    results = {}
    
    for scraper in scrapers:
        try:
            print(f"\n===== Scraping {scraper.brewery_name} =====")
            data = scraper.scrape()
            filename = scraper.save_to_json(data)
            
            results[scraper.brewery_name] = {
                "status": "success",
                "file": filename,
                "beer_count": len(data["beers"])
            }
        except Exception as e:
            print(f"Error scraping {scraper.brewery_name}: {e}")
            results[scraper.brewery_name] = {
                "status": "error",
                "error": str(e)
            }
    
    print("\n===== Scraping Results Summary =====")
    for brewery, result in results.items():
        if result["status"] == "success":
            print(f"✅ {brewery}: {result['beer_count']} beers saved to {result['file']}")
        else:
            print(f"❌ {brewery}: {result['error']}")

if __name__ == "__main__":
    run_scrapers()
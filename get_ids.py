import cloudscraper
import json

# Initialize Scraper to look like a real browser
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'desktop': True})

# Park IDs
parks = {
    "Magic Kingdom": 6,
    "Epcot": 5,
    "Hollywood Studios": 7,
    "Animal Kingdom": 8
}

print("Fetching correct Ride IDs...")
print("-" * 30)

for park_name, park_id in parks.items():
    # We use the JSON API here because it lists all rides cleanly
    url = f"https://queue-times.com/en-US/parks/{park_id}/queue_times.json"
    try:
        response = scraper.get(url)
        if response.status_code == 200:
            data = response.json()
            print(f"\n--- {park_name} (ID: {park_id}) ---")
            for land in data['lands']:
                for ride in land['rides']:
                    # Print in a format you can copy-paste directly into your dictionary
                    print(f'    "{ride["name"]}": {ride["id"]},')
        else:
            print(f"Error fetching {park_name}: Status {response.status_code}")
    except Exception as e:
        print(f"Error fetching {park_name}: {e}")

input("\nPress Enter to close...")
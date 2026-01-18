import cloudscraper
import json

scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'desktop': True})

# Target: Seven Dwarfs Mine Train, Jan 13, 2025
base_url = "https://queue-times.com/parks/6/rides/129/wait_times.json"
date_param = "2025-01-13"

# The "Secret Handshake" Headers
headers = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'X-Requested-With': 'XMLHttpRequest',  # <--- Tells server we are a script/app
    'Referer': 'https://queue-times.com/parks/6/rides/129'
}

print(f"🕵️ Trying XHR Probe on: {base_url}...")
try:
    # We pass the date as a query parameter
    url = f"{base_url}?date={date_param}"
    
    response = scraper.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    
    try:
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            print("\n✅ SUCCESS! We found the Hidden API!")
            print(f"Data Snippet: {str(data)[:100]}...")
            print("\n--> STOP EVERYTHING. I can rewrite the scraper to use this instantly.")
        else:
            print(f"❌ JSON found but empty/weird: {data}")
            print(f"Response Text: {response.text[:200]}")
    except json.JSONDecodeError:
        print("❌ Failed. Server returned HTML, not JSON.")
        print(f"Preview: {response.text[:200]}...")

except Exception as e:
    print(f"❌ Error: {e}")
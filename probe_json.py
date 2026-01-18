import cloudscraper
import json

scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'desktop': True})

# We want data for Jan 13, 2025
date = "2025-01-13"
ride_id = 129 # Seven Dwarfs Mine Train

# The "Safe Cracking" List - Common Rails JSON patterns
urls_to_test = [
    # 1. Standard Resource JSON
    f"https://queue-times.com/parks/6/rides/{ride_id}.json?given_date={date}",
    # 2. Localized JSON
    f"https://queue-times.com/en-US/parks/6/rides/{ride_id}.json?given_date={date}",
    # 3. Wait Times specific endpoint
    f"https://queue-times.com/parks/6/rides/{ride_id}/wait_times.json?given_date={date}",
    # 4. The HTML URL, but asking for JSON via Headers (Rails Magic)
    f"https://queue-times.com/parks/6/rides/{ride_id}?given_date={date}" 
]

print(f"🕵️ PROBING FOR HIDDEN JSON DATA ({date})...\n")

for i, url in enumerate(urls_to_test):
    print(f"Test #{i+1}: {url}")
    try:
        # For Test #4, we explicitly ask for JSON in the header
        if i == 3:
            scraper.headers.update({'Accept': 'application/json'})
        else:
            scraper.headers.update({'Accept': '*/*'})

        resp = scraper.get(url)
        print(f"   Status: {resp.status_code}")
        
        # Did we get JSON?
        try:
            data = resp.json()
            # Check if it looks like real data (lists, wait_times, etc.)
            if isinstance(data, list) or (isinstance(data, dict) and len(data) > 0):
                print("   ✅ JACKPOT! Valid JSON found.")
                print(f"   Data Snippet: {str(data)[:100]}...")
                print(f"   >>> USE THIS URL PATTERN <<<")
                break # Stop looking, we found it!
            else:
                print("   ⚠️  Valid JSON, but empty or weird structure.")
        except:
            print(f"   ❌ Not JSON (likely HTML). First 50 chars: {resp.text[:50].strip()}...")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    print("-" * 40)
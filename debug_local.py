import cloudscraper
import re

# 1. Setup the Scraper
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'desktop': True})
scraper.headers.update({'Accept-Language': 'en-US,en;q=0.9'})

# 2. Target URL (Seven Dwarfs Mine Train, known ID 129)
url = "https://queue-times.com/en-US/parks/6/rides/129?given_date=2025-01-13"

print(f"🔍 Inspecting: {url}")
response = scraper.get(url)

print(f"Status Code: {response.status_code}")
print("-" * 30)

# 3. Check for specific "Blocker" signals
html = response.text
if "Just a moment..." in html:
    print("🔴 BLOCK DETECTED: Cloudflare 'Just a moment' challenge.")
elif "Select your language" in html or "hreflang" in html and len(html) < 5000:
    print("🟠 REDIRECT DETECTED: Language selection page.")
elif "Chartkick" in html:
    print("🟢 SUCCESS: 'Chartkick' found in HTML.")
    
    # Test the Extraction Regex
    print("\n--- Testing Regex Extraction ---")
    # Looser regex that accepts single OR double quotes
    pattern = r'new Chartkick\[["\']LineChart["\']\]\(["\']chart-1["\'], (.*?)\);'
    match = re.search(pattern, html)
    
    if match:
        print("✅ Regex MATCHED! Data extracted.")
        print(f"Data snippet: {match.group(1)[:100]}...")
    else:
        print("❌ Regex FAILED. 'Chartkick' is there, but the pattern didn't match.")
        print("Here is the code snippet we missed:")
        snippet = re.search(r'new Chartkick.{0,100}', html)
        if snippet:
            print(snippet.group(0))
else:
    print("⚪ UNKNOWN: Page loaded, but 'Chartkick' keyword not found.")
    print("Page Title:", re.search(r'<title>(.*?)</title>', html).group(1) if re.search(r'<title>(.*?)</title>', html) else "No Title")

print("-" * 30)
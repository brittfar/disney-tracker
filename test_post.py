import cloudscraper
import re

# 1. Setup Scraper
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'desktop': True})
scraper.headers.update({
    'Accept-Language': 'en-US,en;q=0.9',
    'Origin': 'https://queue-times.com',
    'Referer': 'https://queue-times.com/'
})

# 2. Define Targets
# Seven Dwarfs Mine Train (ID 129)
post_url = "https://queue-times.com/parks/6/rides/129/day_jump"
target_date = "2024-12-25" # A past date we know has data

print(f"🚀 Attempting to POST date {target_date} to {post_url}...")

# 3. Perform the POST (Simulating the button click)
# Note: We let cloudscraper handle the redirects automatically
response = scraper.post(post_url, data={"given_date": target_date})

print(f"Status: {response.status_code}")
print(f"Final URL: {response.url}")

# 4. Check for the LineChart
if 'new Chartkick["LineChart"]' in response.text:
    print("\n✅ SUCCESS! We found the LineChart.")
    print("This proves we MUST use POST to get historical data.")
    
    # Extract a tiny snippet to prove it's real data
    match = re.search(r'new Chartkick\["LineChart"\].*?"Reported by park".*?data":(\[\[.*?\]\])', response.text, re.DOTALL)
    if match:
        print(f"Data Sample: {match.group(1)[:100]}...")
else:
    print("\n❌ FAILURE. Still getting the wrong page.")
    if 'new Chartkick["ColumnChart"]' in response.text:
        print("We are still trapped on the Summary Page (ColumnChart).")
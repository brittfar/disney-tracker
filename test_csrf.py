import cloudscraper
from bs4 import BeautifulSoup
import re

# 1. Setup Session
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'desktop': True})
ride_url = "https://queue-times.com/parks/6/rides/129"
jump_url = "https://queue-times.com/parks/6/rides/129/day_jump"
target_date = "2024-12-25"

print("1️⃣  Visiting page to get Security Token...")
response = scraper.get(ride_url)

# 2. Extract CSRF Token
soup = BeautifulSoup(response.text, 'html.parser')
token = soup.find('input', {'name': 'authenticity_token'})['value']
print(f"   🔑 Token Found: {token[:20]}...")

# 3. POST with the Token
print(f"2️⃣  Posting date {target_date}...")
payload = {
    'given_date': target_date,
    'authenticity_token': token,  # <--- The Missing Key
    'commit': 'Jump to date'
}
# Important: The 'Referer' header proves we came from the ride page
scraper.headers.update({'Referer': ride_url})

response = scraper.post(jump_url, data=payload)

print(f"   Status: {response.status_code}")
print(f"   Final URL: {response.url}")

# 4. Check for Data
if 'new Chartkick["LineChart"]' in response.text:
    print("\n✅ SUCCESS! LineChart Found.")
    match = re.search(r'new Chartkick\["LineChart"\].*?data":(\[\[.*?\]\])', response.text, re.DOTALL)
    if match:
        print(f"   Data Sample: {match.group(1)[:100]}...")
else:
    print("\n❌ FAILURE.")
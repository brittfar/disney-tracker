import cloudscraper

scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'desktop': True})
scraper.headers.update({'Accept-Language': 'en-US,en;q=0.9'})

# The URL we suspected was causing issues
target_url = "https://queue-times.com/en-US/parks/6/rides/129?given_date=2025-01-13"

print(f"Requesting: {target_url}")
response = scraper.get(target_url)

print("-" * 30)
print(f"Final URL: {response.url}") # <--- This is the evidence
print(f"Status:    {response.status_code}")
print("-" * 30)

if "given_date" not in response.url:
    print("🚨 PROOF FOUND: The server redirected us and stripped the date!")
    print("Fix: Remove '/en-US/' from the request.")
else:
    print("✅ URL is fine. The issue is elsewhere.")
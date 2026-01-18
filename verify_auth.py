import cloudscraper
from bs4 import BeautifulSoup

# CREDENTIALS (Use the new password if you changed it)
EMAIL = "dm012486@gmail.com"
PASSWORD = "DeadSmurf11"

def verify_session():
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'desktop': True})
    
    # 1. LOGIN
    print("🔑 Attempting Login...")
    login_url = "https://queue-times.com/users/sign_in"
    
    # Get Token
    resp = scraper.get(login_url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    token = soup.find('input', {'name': 'authenticity_token'})['value']
    
    # Post Credentials
    payload = {
        'user[email]': EMAIL,
        'user[password]': PASSWORD,
        'authenticity_token': token,
        'user[remember_me]': '1',
        'commit': 'Log in'
    }
    scraper.post(login_url, data=payload)
    
    # 2. VERIFY
    print("🕵️ Checking if session persists...")
    # Access a known historical page (Seven Dwarfs, Christmas 2024)
    test_url = "https://queue-times.com/parks/6/rides/129/2024?given_date=2024-12-25"
    response = scraper.get(test_url)
    
    # 3. DIAGNOSIS
    if "Logout" in response.text:
        print("✅ SUCCESS: The scraper is LOGGED IN.")
        if "Reported by park" in response.text:
            print("   ✅ Chart Data is VISIBLE.")
        else:
            print("   ⚠️  Logged in, but Chart Data is MISSING (Parsing issue).")
    elif "Please log in" in response.text:
        print("❌ FAILURE: The scraper was logged out immediately (Session dropped).")
    else:
        print("❓ UNKNOWN: Could not determine login status.")
        
    # Save debug for inspection
    with open("debug_auth_test.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    print("   -> Saved debug_auth_test.html")

if __name__ == "__main__":
    verify_session()
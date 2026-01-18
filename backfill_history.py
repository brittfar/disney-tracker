import cloudscraper
import time
import argparse
from datetime import datetime, timedelta
import json
import re
from bs4 import BeautifulSoup
from database import get_session
from schemas import WaitTime

# Queue-Times.com Ride IDs
DISNEY_RIDES = {
    "Magic Kingdom Park": {
        "Seven Dwarfs Mine Train": 129,
        "Space Mountain": 138,
        "Big Thunder Mountain Railroad": 130,
        "Tiana's Bayou Adventure": 13630, 
        "Pirates of the Caribbean": 137,
        "Haunted Mansion": 140,
        "Jungle Cruise": 134,
        "it's a small world": 133,
        "Peter Pan's Flight": 136,
        "Mad Tea Party": 135,
        "Dumbo the Flying Elephant": 132,
        "Buzz Lightyear's Space Ranger Spin": 131,
        "Astro Orbiter": 248,
        "Walt Disney's Carousel of Progress": 457,
        "Tomorrowland Speedway": 143,
        "The Barnstormer": 126,
        "Mickey's PhilharMagic": 171,
        "Enchanted Tales with Belle": 128,
        "Under the Sea - Journey of The Little Mermaid": 127,
        "The Many Adventures of Winnie the Pooh": 142,
        "The Magic Carpets of Aladdin": 141,
        "Tomorrowland Transit Authority PeopleMover": 1190,
        "TRON Lightcycle / Run": 11527,
        "Prince Charming Regal Carrousel": 161,
        "The Hall of Presidents": 356,
        "Swiss Family Treehouse": 355,
        "Country Bear Musical Jamboree": 1214,
        "Walt Disney's Enchanted Tiki Room": 334,
        "A Pirate's Adventure ~ Treasures of the Seven Seas": 1184,
        "Casey Jr. Splash 'N' Soak Station": 13764,
        "Walt Disney World Railroad - Fantasyland": 1181,
        "Walt Disney World Railroad - Main Street, U.S.A.": 1189,
        "Monsters Inc. Laugh Floor": 125,
    },
    "EPCOT": {
        "Spaceship Earth": 159,
        "Soarin' Around the World": 151,
        "Living with the Land": 156,
        "Mission: SPACE": 158,
        "Test Track": 160,
        "The Seas with Nemo & Friends": 153,
        "Frozen Ever After": 2679,
        "Journey Into Imagination With Figment": 155,
        "Gran Fiesta Tour Starring The Three Caballeros": 466,
        "Remy's Ratatouille Adventure": 10914,
        "Guardians of the Galaxy: Cosmic Rewind": 10916,
        "Turtle Talk With Crush": 152,
        "Disney and Pixar Short Film Festival": 2495,
        "Journey of Water, Inspired by Moana": 12387,
        "Canada Far and Wide in Circle-Vision 360": 829,
        "Awesome Planet": 7323,
    },
    "Disney's Hollywood Studios": {
        "The Twilight Zone Tower of Terror": 123,
        "Rock 'n' Roller Coaster Starring Aerosmith": 119,
        "Toy Story Mania!": 117,
        "Star Tours – The Adventures Continue": 120,
        "Slinky Dog Dash": 5476,
        "Alien Swirling Saucers": 5477,
        "Millennium Falcon: Smugglers Run": 6368,
        "Star Wars: Rise of the Resistance": 6369,
        "Mickey & Minnie's Runaway Railway": 6361,
        "Indiana Jones™ Epic Stunt Spectacular!": 6702,
        "For the First Time in Forever: A Frozen Sing-Along Celebration": 1174,
        "Beauty and the Beast – Live on Stage": 1176,
        "Walt Disney Presents": 5145,
        "Vacation Fun - An Original Animated Short with Mickey & Minnie": 7333,
        "The Little Mermaid – A Musical Adventure – New!": 14859,
    },
    "Disney's Animal Kingdom Theme Park": {
        "Avatar Flight of Passage": 4439,
        "Na'vi River Journey": 4438,
        "Expedition Everest - Legend of the Forbidden Mountain": 110,
        "Kilimanjaro Safaris": 113,
        "DINOSAUR": 111,
        "Kali River Rapids": 112,
        "TriceraTop Spin": 407,
        "It's Tough to Be a Bug!": 409,
        "Festival of the Lion King": 657,
        "Feathered Friends in Flight!": 10921,
        "Finding Nemo: The Big Blue... and Beyond!": 10920,
        "Gorilla Falls Exploration Trail": 651,
        "Wildlife Express Train": 655,
        "The Animation Experience at Conservation Station": 6680,
    }
}

def login(scraper, email, password):
    """
    Logs into queue-times.com to establish a session.
    """
    print(f"🔑 Logging in as {email}...")
    login_url = "https://queue-times.com/users/sign_in"
    
    try:
        # 1. Get the login page to grab CSRF token
        response = scraper.get(login_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check if already logged in
        if "Logout" in response.text:
            print("   ✅ Already logged in!")
            return True
            
        token_input = soup.find('input', {'name': 'authenticity_token'})
        if not token_input:
            print("   ❌ Failed to find login CSRF token.")
            return False
            
        # 2. Post credentials
        payload = {
            'user[email]': email,
            'user[password]': password,
            'authenticity_token': token_input['value'],
            'user[remember_me]': '1',
            'commit': 'Log in'
        }
        
        response = scraper.post(login_url, data=payload)
        
        # 3. Verify success
        if "Logout" in response.text or "Signed in successfully" in response.text:
            print("   ✅ Login successful!")
            return True
        else:
            print("   ❌ Login failed. Check credentials.")
            return False
            
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return False

def extract_graph_data(html_content):
    """
    Extracts data using a multi-strategy approach.
    Strategy 1: Robust Regex (Handles newlines and variations)
    Strategy 2: Substring Search & Bracket Counting (Failsafe)
    """
    
    # Quick check: Is the data even there?
    if "Reported by park" not in html_content:
        return []

    # --- STRATEGY 1: Aggressive Regex ---
    # Matches: new Chartkick["Any"]("id", [DATA], {options});
    # Uses re.DOTALL to match across newlines
    pattern = r'new Chartkick\[".*?"\]\(".*?", (\[.*?\]), \{'
    match = re.search(pattern, html_content, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1))
            for series in data:
                if series.get('name') == "Reported by park":
                    return series.get('data', [])
        except:
            pass # Fall through to Strategy 2

    # --- STRATEGY 2: "Search & Destroy" Parser ---
    # This ignores the Chartkick function and just grabs the data array
    try:
        # 1. Find the anchor text
        idx = html_content.find('Reported by park')
        if idx != -1:
            # 2. Find the "data": tag following it
            data_label_idx = html_content.find('"data":', idx)
            if data_label_idx != -1:
                # 3. Find the opening bracket [
                start_bracket = html_content.find('[', data_label_idx)
                if start_bracket != -1:
                    # 4. Count brackets to find the matching closing bracket ]
                    # This handles nested lists like [[time, val], [time, val]]
                    balance = 0
                    end_bracket = start_bracket
                    for i, char in enumerate(html_content[start_bracket:]):
                        if char == '[':
                            balance += 1
                        elif char == ']':
                            balance -= 1
                        
                        if balance == 0:
                            end_bracket = start_bracket + i + 1
                            break
                    
                    if end_bracket > start_bracket:
                        json_str = html_content[start_bracket:end_bracket]
                        return json.loads(json_str)
    except Exception:
        pass
            
    return []

def parse_ride_data(ride_data, ride_name, park_name, date):
    records = []
    
    # Validation: Ensure we aren't getting "Hourly Average" (integers 0..23)
    # The summary page (wrong data) uses integers for x-axis.
    # The daily page (correct data) uses Date Strings.
    if ride_data and len(ride_data) > 0 and isinstance(ride_data[0][0], int):
        return []

    try:
        for entry in ride_data:
            if isinstance(entry, list) and len(entry) >= 2:
                timestamp_str, wait_time_str = entry[0], entry[1]
                
                try:
                    dt = datetime.strptime(timestamp_str, "%m/%d/%y %H:%M:%S")
                except (ValueError, TypeError):
                    continue
                
                try:
                    wait_time = int(float(wait_time_str)) if wait_time_str is not None else 0
                except (ValueError, TypeError):
                    wait_time = 0
                
                records.append({
                    'ride_name': ride_name,
                    'park_name': park_name,
                    'wait_time': wait_time,
                    'is_open': wait_time > 0,
                    'timestamp': dt
                })
    except Exception as e:
        print(f"Error parsing Chartkick ride data for {ride_name}: {e}")
    return records

def backfill_historical_data(days=30, offset=0, start_year=2022, email=None, password=None):
    print(f"Starting historical backfill for {days} days (offset: {offset}, start_year: {start_year})...")
    
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )
    scraper.headers.update({
        'Accept-Language': 'en-US,en;q=0.9',
    })
    
    # Login
    if email and password:
        if not login(scraper, email, password):
            print("⛔ Aborting backfill due to login failure.")
            return
    else:
        print("⚠ WARNING: No credentials provided.")

    session = get_session()
    total_records = 0
    
    end_date = datetime.now() - timedelta(days=offset)
    start_date = end_date - timedelta(days=days)
    
    if start_date.year < start_year:
        start_date = datetime(start_year, 1, 1)
    
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        year_str = current_date.strftime('%Y')
        print(f"\nProcessing date: {date_str}")
        
        for park_name, rides in DISNEY_RIDES.items():
            print(f"  Processing {park_name}...")
            park_records = 0
            
            for ride_name, ride_id in rides.items():
                try:
                    park_id = get_park_id(park_name)
                    
                    # Direct Link to Historical Year Page
                    url = f"https://queue-times.com/parks/{park_id}/rides/{ride_id}/{year_str}?given_date={date_str}"
                    
                    print(f"    Fetching {ride_name}...")
                    response = scraper.get(url)
                    
                    if response.status_code != 200:
                        print(f"      ✗ HTTP Error: {response.status_code}")
                        continue

                    if "Please log in" in response.text and "Reported by park" not in response.text:
                         print(f"      ⛔ BLOCKED: Session invalid.")
                         continue

                    ride_data = extract_graph_data(response.text)
                    
                    if ride_data:
                        records = parse_ride_data(ride_data, ride_name, park_name, current_date)
                        if records:
                            for record in records:
                                wait_time_record = WaitTime(
                                    ride_name=record['ride_name'],
                                    park_name=record['park_name'],
                                    wait_time=record['wait_time'],
                                    status='Operating' if record['is_open'] else 'Closed',
                                    last_updated=record['timestamp']
                                )
                                session.add(wait_time_record)
                            session.commit()
                            total_records += len(records)
                            park_records += len(records)
                            print(f"      ✓ Added {len(records)} records")
                        else:
                            print(f"      ⚠ Data found but parsed 0 records (Check Date)")
                    else:
                        print(f"      ⚠ No graph data found")
                    
                    time.sleep(1.0)
                    
                except Exception as e:
                    print(f"      ✗ Error fetching {ride_name}: {e}")
                    continue
            
            print(f"  {park_name} total: {park_records} records")
        current_date += timedelta(days=1)
    
    session.close()
    print(f"\nBackfill complete! Total records added: {total_records}")

def get_park_id(park_name):
    park_ids = {
        "Magic Kingdom Park": 6,
        "EPCOT": 5,
        "Disney's Hollywood Studios": 7,
        "Disney's Animal Kingdom Theme Park": 8
    }
    return park_ids.get(park_name, 6)

if __name__ == "__main__":
    # --- FIX: Ensure database tables exist before starting ---
    from database import engine, Base
    print("🔧 Checking database structure...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables verified.")
    # ---------------------------------------------------------

    parser = argparse.ArgumentParser(description='Backfill historical Disney World wait time data')
    parser.add_argument('--days', type=int, default=30, help='Number of days to backfill (default: 30)')
    parser.add_argument('--offset', type=int, default=0, help='Days offset from today (default: 0)')
    parser.add_argument('--start-year', type=int, default=2022, help='Starting year for deep backfilling (default: 2022)')
    parser.add_argument('--email', type=str)
    parser.add_argument('--password', type=str)
    
    args = parser.parse_args()
    backfill_historical_data(days=args.days, offset=args.offset, start_year=args.start_year, email=args.email, password=args.password)
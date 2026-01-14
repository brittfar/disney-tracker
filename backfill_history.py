import cloudscraper
import time
import argparse
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
import re
from database import get_session
from schemas import WaitTime

# Queue-Times.com Ride IDs for all Disney World parks
DISNEY_RIDES = {
    "Magic Kingdom Park": {
        "Seven Dwarfs Mine Train": 136,
        "Space Mountain": 137,
        "Big Thunder Mountain Railroad": 138,
        "Splash Mountain": 139,
        "Pirates of the Caribbean": 140,
        "Haunted Mansion": 141,
        "Jungle Cruise": 142,
        "It's a Small World": 143,
        "Peter Pan's Flight": 144,
        "Mad Tea Party": 145,
        "Dumbo the Flying Elephant": 146,
        "Buzz Lightyear's Space Ranger Spin": 147,
        "Astro Orbiter": 148,
        "Carousel of Progress": 149,
        "Hall of Presidents": 150,
        "Monsters, Inc. Laugh Floor": 151,
        "Tomorrowland Speedway": 152,
        "Walt Disney World Railroad": 153,
        "Swiss Family Treehouse": 154,
        "Country Bear Jamboree": 155,
        "Liberty Square Riverboat": 156,
        "Frontierland Shootin' Arcade": 157,
        "The Barnstormer": 158,
        "Prince Charming Regal Carrousel": 159,
        "Mickey's PhilharMagic": 160,
        "Enchanted Tales with Belle": 161,
        "Under the Sea ~ Journey of the Little Mermaid": 162,
        "The Many Adventures of Winnie the Pooh": 163,
        "Goofy's Barnstormer": 164,
        "The Magic Carpets of Aladdin": 165,
        "Tomorrowland Transit Authority PeopleMover": 167,
    },
    "EPCOT": {
        "Test Track": 201,
        "Soarin' Around the World": 202,
        "Mission: SPACE": 203,
        "Spaceship Earth": 204,
        "The Seas with Nemo & Friends": 205,
        "Turtle Talk with Crush": 206,
        "Living with the Land": 207,
        "Journey into Imagination with Figment": 208,
        "Gran Fiesta Tour Starring The Three Caballeros": 209,
        "Frozen Ever After": 210,
        "Remy's Ratatouille Adventure": 211,
        "Guardians of the Galaxy: Cosmic Rewind": 212,
    },
    "Disney's Hollywood Studios": {
        "Rock 'n' Roller Coaster Starring Aerosmith": 301,
        "The Twilight Zone Tower of Terror": 302,
        "Slinky Dog Dash": 303,
        "Millennium Falcon: Smugglers Run": 304,
        "Star Wars: Rise of the Resistance": 305,
        "Toy Story Mania!": 306,
        "Mickey & Minnie's Runaway Railway": 307,
        "The Great Movie Ride": 308,
        "Indiana Jones Epic Stunt Spectacular": 309,
        "Beauty and the Beast Live on Stage": 310,
        "Fantasmic!": 311,
        "Voyage of the Little Mermaid": 312,
    },
    "Disney's Animal Kingdom Theme Park": {
        "Avatar Flight of Passage": 401,
        "Na'vi River Journey": 402,
        "Expedition Everest": 403,
        "Kilimanjaro Safaris": 404,
        "Dinosaur": 405,
        "Primeval Whirl": 406,
        "TriceraTop Spin": 407,
        "Kali River Rapids": 408,
        "It's Tough to Be a Bug!": 409,
        "Festival of the Lion King": 410,
        "Finding Nemo: The Musical": 411,
        "UP! A Great Bird Adventure": 412,
    }
}

def extract_graph_data(html_content):
    """
    Extract historical wait time data from the JavaScript graph data on the page.
    """
    try:
        # Look for JavaScript variable containing ride data
        # Common patterns: var ride_data = [...], window.rideData = [...], etc.
        patterns = [
            r'var\s+ride_data\s*=\s*(\[.*?\]);',
            r'window\.rideData\s*=\s*(\[.*?\]);',
            r'ride_data\s*=\s*(\[.*?\]);',
            r'data\s*:\s*(\[.*?\])',  # Generic data pattern
        ]
        
        for pattern in patterns:
            matches = re.search(pattern, html_content, re.DOTALL)
            if matches:
                json_str = matches.group(1)
                try:
                    data = json.loads(json_str)
                    return data
                except json.JSONDecodeError:
                    continue
        
        # Alternative: Look for any JSON arrays in the script tags
        soup = BeautifulSoup(html_content, 'html.parser')
        script_tags = soup.find_all('script')
        
        for script in script_tags:
            if script.string:
                # Look for JSON arrays in script content
                json_matches = re.findall(r'\[.*?\]', script.string, re.DOTALL)
                for match in json_matches:
                    try:
                        data = json.loads(match)
                        # Check if this looks like ride data (list of time/wait pairs)
                        if isinstance(data, list) and len(data) > 0:
                            # Validate structure - should contain time and wait data
                            if isinstance(data[0], (list, dict)) and len(data[0]) >= 2:
                                return data
                    except json.JSONDecodeError:
                        continue
        
        return None
        
    except Exception as e:
        print(f"Error extracting graph data: {e}")
        return None

def parse_ride_data(ride_data, ride_name, park_name, date):
    """
    Parse the extracted ride data into wait time records.
    """
    records = []
    
    try:
        # Queue-Times.com typically provides data as [timestamp, wait_time] pairs
        # or as objects with time and wait properties
        for entry in ride_data:
            if isinstance(entry, list) and len(entry) >= 2:
                timestamp, wait_time = entry[0], entry[1]
            elif isinstance(entry, dict):
                timestamp = entry.get('time') or entry.get('timestamp')
                wait_time = entry.get('wait') or entry.get('wait_time') or entry.get('waitTime')
            else:
                continue
            
            # Convert timestamp to datetime
            try:
                if isinstance(timestamp, (int, float)):
                    # Unix timestamp
                    dt = datetime.fromtimestamp(timestamp)
                elif isinstance(timestamp, str):
                    # Try to parse as ISO format
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    continue
            except (ValueError, TypeError):
                continue
            
            # Ensure wait_time is an integer
            try:
                wait_time = int(wait_time) if wait_time is not None else 0
            except (ValueError, TypeError):
                wait_time = 0
            
            records.append({
                'ride_name': ride_name,
                'park_name': park_name,
                'wait_time': wait_time,
                'is_open': wait_time > 0,  # Assume open if wait time > 0
                'timestamp': dt
            })
    
    except Exception as e:
        print(f"Error parsing ride data for {ride_name}: {e}")
    
    return records

def backfill_historical_data(days=30, offset=0, start_year=2022):
    """
    Backfill historical wait time data for all Disney World parks.
    
    Args:
        days (int): Number of days to process
        offset (int): Days offset from today (0 = today, 1 = yesterday, etc.)
        start_year (int): Starting year for deep backfilling
    """
    print(f"Starting historical backfill for {days} days (offset: {offset}, start_year: {start_year})...")
    
    # Initialize cloudscraper
    scraper = cloudscraper.create_scraper()
    
    session = get_session()
    total_records = 0
    
    # Calculate date range
    end_date = datetime.now() - timedelta(days=offset)
    start_date = end_date - timedelta(days=days)
    
    # Ensure we don't go before start_year
    if start_date.year < start_year:
        start_date = datetime(start_year, 1, 1)
        print(f"Adjusted start date to {start_date.strftime('%Y-%m-%d')} (start_year constraint)")
    
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        print(f"\nProcessing date: {date_str}")
        
        # Process all parks
        for park_name, rides in DISNEY_RIDES.items():
            print(f"  Processing {park_name}...")
            park_records = 0
            
            for ride_name, ride_id in rides.items():
                try:
                    # Construct URL for historical data
                    url = f"https://queue-times.com/en-US/parks/{get_park_id(park_name)}/rides/{ride_id}?given_date={date_str}"
                    
                    print(f"    Fetching {ride_name} data...")
                    
                    # Make request with cloudscraper (handles headers automatically)
                    response = scraper.get(url)
                    
                    # Debug: Print response status
                    print(f"      Response Status: {response.status_code if hasattr(response, 'status_code') else 'N/A'}")
                    
                    # Check if we got a valid response
                    if hasattr(response, 'status_code') and response.status_code != 200:
                        print(f"      ✗ HTTP Error: {response.status_code}")
                        continue
                    
                    # Extract graph data from the page
                    ride_data = extract_graph_data(response.text)
                    
                    if ride_data:
                        # Parse the data into records
                        records = parse_ride_data(ride_data, ride_name, park_name, current_date)
                        
                        if records:
                            # Bulk insert records
                            for record in records:
                                wait_time_record = WaitTime(
                                    ride_name=record['ride_name'],
                                    park_name=record['park_name'],
                                    wait_time=record['wait_time'],
                                    # Convert boolean is_open to String status
                                    status='Operating' if record['is_open'] else 'Closed',
                                    # Map timestamp to last_updated
                                    last_updated=record['timestamp']
                                )
                                session.add(wait_time_record)
                            
                            session.commit()
                            total_records += len(records)
                            park_records += len(records)
                            print(f"      ✓ Added {len(records)} records")
                        else:
                            print(f"      ⚠ No valid data found")
                    else:
                        # Enhanced debugging for failed data extraction
                        print(f"      ⚠ No graph data found")
                        if hasattr(response, 'text') and response.text:
                            print(f"      DEBUG: Page Title: {response.text[:200]}")
                        else:
                            print(f"      DEBUG: No response text available")
                    
                    # Rate limiting - be polite to their server
                    time.sleep(1.0)
                    
                except Exception as e:
                    print(f"      ✗ Error fetching {ride_name}: {e}")
                    continue
                except Exception as e:
                    print(f"      ✗ Unexpected error for {ride_name}: {e}")
                    continue
            
            print(f"  {park_name} total: {park_records} records")
        
        # Move to next day
        current_date += timedelta(days=1)
    
    session.close()
    print(f"\nBackfill complete! Total records added: {total_records}")

def get_park_id(park_name):
    """Get Queue-Times.com park ID from park name."""
    park_ids = {
        "Magic Kingdom Park": 6,
        "EPCOT": 5,
        "Disney's Hollywood Studios": 7,
        "Disney's Animal Kingdom Theme Park": 8
    }
    return park_ids.get(park_name, 6)  # Default to Magic Kingdom

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Backfill historical Disney World wait time data')
    parser.add_argument('--days', type=int, default=30, help='Number of days to backfill (default: 30)')
    parser.add_argument('--offset', type=int, default=0, help='Days offset from today (default: 0)')
    parser.add_argument('--start-year', type=int, default=2022, help='Starting year for deep backfilling (default: 2022)')
    
    args = parser.parse_args()
    
    # Run backfill with specified parameters
    backfill_historical_data(days=args.days, offset=args.offset, start_year=args.start_year)

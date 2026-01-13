import requests
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
import re
from database import get_session
from schemas import WaitTime

# Queue-Times.com Ride IDs for Magic Kingdom (expand as needed)
MAGIC_KINGDOM_RIDES = {
    "Seven Dwarfs Mine Train": 136,
    "Space Mountain": 137,
    "Big Thunder Mountain Railroad": 138,
    "Splash Mountain": 139,  # Note: This ride may be closed
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
    "Monsters, Inc. Laugh Floor": 166,
    "Tomorrowland Transit Authority PeopleMover": 167,
    "Walt Disney World Railroad - Fantasyland": 168,
    "Walt Disney World Railroad - Frontierland": 169,
    "Walt Disney World Railroad - Main Street, U.S.A.": 170
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

def backfill_historical_data(days=30):
    """
    Backfill historical wait time data for the last N days.
    """
    print(f"Starting historical backfill for the last {days} days...")
    
    session = get_session()
    total_records = 0
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        print(f"\nProcessing date: {date_str}")
        
        for ride_name, ride_id in MAGIC_KINGDOM_RIDES.items():
            try:
                # Construct URL for historical data
                url = f"https://queue-times.com/en-US/parks/6/rides/{ride_id}?given_date={date_str}"
                
                print(f"Fetching {ride_name} data for {date_str}...")
                
                # Make request with headers
                headers = {
                    'User-Agent': 'DisneyTracker/1.0 (Historical Data Collection)',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                }
                
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                
                # Extract graph data from the page
                ride_data = extract_graph_data(response.text)
                
                if ride_data:
                    # Parse the data into records
                    records = parse_ride_data(ride_data, ride_name, "Magic Kingdom Park", current_date)
                    
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
                        print(f"  ✓ Added {len(records)} records for {ride_name}")
                    else:
                        print(f"  ⚠ No valid data found for {ride_name}")
                else:
                    print(f"  ⚠ No graph data found for {ride_name}")
                
                # Rate limiting - be polite to their server
                time.sleep(2)
                
            except requests.exceptions.RequestException as e:
                print(f"  ✗ Error fetching {ride_name}: {e}")
                continue
            except Exception as e:
                print(f"  ✗ Unexpected error for {ride_name}: {e}")
                continue
        
        # Move to next day
        current_date += timedelta(days=1)
    
    session.close()
    print(f"\nBackfill complete! Total records added: {total_records}")

if __name__ == "__main__":
    # Run backfill for the last 30 days
    backfill_historical_data(days=30)

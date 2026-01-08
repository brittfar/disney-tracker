import requests
import json
from datetime import datetime
from database import get_session, WaitTime

# Walt Disney World Resort parent ID
WALT_DISNEY_WORLD_RESORT_ID = "e957da41-3552-4cf6-b636-5babc5cbc4e5"

def discover_parks():
    """
    Discover all Disney parks by querying the Walt Disney World Resort parent entity
    and extracting unique park IDs from the children.
    
    Returns:
        dict: Dictionary mapping park names to their entity IDs
    """
    url = f"https://api.themeparks.wiki/v1/entity/{WALT_DISNEY_WORLD_RESORT_ID}/children"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        park_ids = {}
        
        # The API returns a dict with a 'children' key
        if isinstance(data, dict) and 'children' in data:
            children = data['children']
            
            # Collect unique park IDs from parentId fields
            unique_parent_ids = set()
            for child in children:
                parent_id = child.get('parentId')
                if parent_id and parent_id != WALT_DISNEY_WORLD_RESORT_ID:
                    unique_parent_ids.add(parent_id)
            
            # Now get details for each unique park ID
            for park_id in unique_parent_ids:
                try:
                    park_url = f"https://api.themeparks.wiki/v1/entity/{park_id}"
                    park_response = requests.get(park_url, timeout=30)
                    park_response.raise_for_status()
                    
                    park_data = park_response.json()
                    
                    if park_data.get('entityType') == 'PARK':
                        park_name = park_data.get('name', 'Unknown Park')
                        park_ids[park_name] = park_id
                        
                except requests.exceptions.RequestException:
                    # If we can't get park details, skip this ID
                    continue
        
        return park_ids
        
    except requests.exceptions.RequestException as e:
        print(f"Error discovering parks: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing park discovery JSON: {e}")
        return {}
    except Exception as e:
        print(f"Unexpected error discovering parks: {e}")
        return {}

def fetch_park_data(park_name, park_id):
    """
    Fetch live ride data from ThemeParks.wiki API for a specific park.
    
    Args:
        park_name (str): Name of the park
        park_id (str): ThemeParks.wiki entity ID for the park
    
    Returns:
        list: List of processed ride records
    """
    url = f"https://api.themeparks.wiki/v1/entity/{park_id}/live"
    headers = {'User-Agent': 'DisneyTracker/1.0 (contact: yourname@example.com)'}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        rides = []
        
        if 'liveData' in data and isinstance(data['liveData'], list):
            for ride in data['liveData']:
                # Filter for ATTRACTIONs only (ignore SHOW, RESTAURANT, etc.)
                if ride.get('entityType') == 'ATTRACTION':
                    ride_name = ride.get('name', 'Unknown Ride')
                    
                    # Get wait time from the correct nested structure
                    wait_time = 0
                    is_open = True
                    
                    # Extract status first
                    status = ride.get('status', 'CLOSED')
                    is_open = status == 'OPERATING'
                    
                    # Extract wait time from queue.STANDBY.waitTime
                    if 'queue' in ride and isinstance(ride['queue'], dict):
                        queue_data = ride['queue']
                        standby_data = queue_data.get('STANDBY', {})
                        wait_time = standby_data.get('waitTime', 0) or 0
                    
                    # Force wait time to 0 if ride is closed or down
                    if not is_open or status in ['CLOSED', 'DOWN']:
                        wait_time = 0
                    
                    rides.append({
                        'ride_name': ride_name,
                        'park_name': park_name,
                        'wait_time': wait_time,
                        'is_open': is_open,
                        'timestamp': datetime.utcnow()
                    })
        
        # Log summary
        print(f"Found {len(rides)} active rides. Sample: {rides[0]['ride_name'] if rides else 'None'} = {rides[0]['wait_time'] if rides else 0} min")
        return rides
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {park_name}: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON for {park_name}: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error for {park_name}: {e}")
        return []

def insert_ride_data(ride_records):
    """
    Insert ride records into the database using SQLAlchemy.
    
    Args:
        ride_records (list): List of ride dictionaries to insert
    """
    if not ride_records:
        return 0
    
    session = get_session()
    try:
        # Create WaitTime objects
        wait_time_objects = [
            WaitTime(
                ride_name=record['ride_name'],
                park_name=record['park_name'],
                wait_time=record['wait_time'],
                is_open=record['is_open'],
                timestamp=record['timestamp']
            )
            for record in ride_records
        ]
        
        # Bulk insert
        session.bulk_save_objects(wait_time_objects)
        session.commit()
        
        return len(wait_time_objects)
        
    except Exception as e:
        session.rollback()
        print(f"Error inserting data: {e}")
        return 0
    finally:
        session.close()

def main():
    """
    Main function to discover parks, scrape their data, and insert into database.
    """
    print("Starting Disney World wait time scraping...")
    
    # Discover parks dynamically
    print("Discovering Disney World parks...")
    parks = discover_parks()
    
    if not parks:
        print("No parks discovered. Exiting.")
        return
    
    print(f"\nDiscovered {len(parks)} parks:")
    for park_name, park_id in parks.items():
        print(f"  {park_name}: {park_id}")
    
    print("\nStarting data collection...")
    total_records = 0
    
    for park_name, park_id in parks.items():
        print(f"\nFetching data for {park_name}...")
        
        # Fetch park data
        ride_records = fetch_park_data(park_name, park_id)
        
        if ride_records:
            # Insert into database
            inserted_count = insert_ride_data(ride_records)
            print(f"Successfully inserted {inserted_count} records for {park_name}")
            total_records += inserted_count
        else:
            print(f"No data retrieved for {park_name}")
    
    print(f"\nScraping complete. Total records inserted: {total_records}")

def run_scraper_job():
    """
    Run a single scraping job for manual dashboard refresh.
    This function can be called from the dashboard to force data updates.
    """
    print("Manual scraping job initiated from dashboard...")
    parks = discover_parks()
    
    if not parks:
        print("No parks discovered. Exiting.")
        return
    
    total_records = 0
    for park_name, park_id in parks.items():
        print(f"Fetching data for {park_name}...")
        ride_records = fetch_park_data(park_name, park_id)
        
        if ride_records:
            inserted_count = insert_ride_data(ride_records)
            print(f"Successfully inserted {inserted_count} records for {park_name}")
            total_records += inserted_count
        else:
            print(f"No data retrieved for {park_name}")
    
    print(f"Manual scraping complete. Total records inserted: {total_records}")

if __name__ == "__main__":
    main()

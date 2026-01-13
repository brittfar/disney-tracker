import requests
from datetime import datetime, timezone
# --- THE FIX IS HERE ---
from database import get_session   # Connection from database.py
from schemas import WaitTime       # Table definition from schemas.py
# -----------------------

# Queue-Times.com Park IDs
DISNEY_PARKS = {
    "Magic Kingdom Park": 6,
    "EPCOT": 5,
    "Disney's Hollywood Studios": 7,
    "Disney's Animal Kingdom Theme Park": 8
}

def discover_parks():
    """
    Return Disney World parks using Queue-Times.com park IDs.
    
    Returns:
        dict: Dictionary mapping park names to their Queue-Times.com IDs
    """
    print("Using Queue-Times.com park IDs...")
    return DISNEY_PARKS

def fetch_park_data(park_name, park_id):
    """
    Fetch live ride data from Queue-Times.com API for a specific park.
    
    Args:
        park_name (str): Name of the park
        park_id (int): Queue-Times.com park ID
    
    Returns:
        list: List of processed ride records
    """
    url = f"https://queue-times.com/parks/{park_id}/queue_times.json"
    
    print(f"Fetching data from {url}...")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        rides = []
        
        # Parse Queue-Times.com JSON structure: lands -> rides
        if 'lands' in data and isinstance(data['lands'], list):
            for land in data['lands']:
                if 'rides' in land and isinstance(land['rides'], list):
                    for ride in land['rides']:
                        ride_name = ride.get('name', 'Unknown Ride')
                        wait_time = ride.get('wait_time', 0) or 0
                        is_open = ride.get('is_open', False)
                        last_updated_str = ride.get('last_updated', '')
                        
                        # Convert last_updated string to datetime object
                        try:
                            if last_updated_str:
                                # Queue-Times.com typically provides ISO format
                                last_updated = datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
                            else:
                                last_updated = datetime.utcnow()
                        except (ValueError, AttributeError):
                            last_updated = datetime.utcnow()
                        
                        # Debug logging for first 3 rides
                        if len(rides) < 3:
                            print(f"DEBUG: {ride_name} -> Status: {'Open' if is_open else 'Closed'}, Wait: {wait_time}")
                        
                        rides.append({
                            'ride_name': ride_name,
                            'park_name': park_name,
                            'wait_time': wait_time,
                            'is_open': is_open,
                            'timestamp': last_updated
                        })
        
        # Check if we found any valid rides
        if not rides:
            print("WARNING: No valid rides found. API might be reporting everything as Closed.")
        
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

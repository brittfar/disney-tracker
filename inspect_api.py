import requests
import json
from pprint import pprint

def inspect_raw_api():
    """
    Inspect raw API response from ThemeParks.wiki for Magic Kingdom.
    """
    print("API INSPECTION TOOL")
    print("=" * 50)
    
    # Magic Kingdom ID
    magic_kingdom_id = "75ea578a-adc8-4116-a54d-dccb60765ef9"
    
    # API endpoint
    url = f"https://api.themeparks.wiki/v1/entity/{magic_kingdom_id}/live"
    
    print(f"Fetching data from: {url}")
    print(f"Park ID: {magic_kingdom_id}")
    print()
    
    try:
        # Make API request
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Parse JSON
        data = response.json()
        
        print("API RESPONSE STATUS:")
        print(f"Status Code: {response.status_code}")
        print(f"Response Size: {len(response.content)} bytes")
        print()
        
        # Show top-level structure
        print("TOP-LEVEL KEYS:")
        for key in data.keys():
            print(f"  {key}: {type(data[key])}")
        print()
        
        # Look for rides/attractions data
        if 'liveData' in data:
            live_data = data['liveData']
            print(f"Found 'liveData' with {len(live_data)} items (type: {type(live_data)})")
            
            # Find first ride with wait time
            ride_found = False
            for i, item in enumerate(live_data):
                if isinstance(item, dict) and 'name' in item:
                    ride_name = item.get('name', 'Unknown')
                    print(f"\nInspecting ride {i+1}: {ride_name}")
                    
                    # Check if this ride has wait time
                    if 'queue' in item and isinstance(item['queue'], dict):
                        queue_data = item['queue']
                        if 'STANDBY' in queue_data:
                            wait_time = queue_data['STANDBY'].get('waitTime')
                            if wait_time is not None and wait_time > 0:
                                print(f"*** FOUND RIDE WITH WAIT TIME: {wait_time} minutes ***")
                    
                    # Print the raw dictionary for this ride
                    print("\nRAW JSON FOR THIS RIDE:")
                    print("-" * 40)
                    pprint(item, width=120, depth=None)
                    print("-" * 40)
                    
                    # Stop after showing 5 rides or if we found one with wait time
                    if i >= 4 or ('queue' in item and isinstance(item['queue'], dict) and 
                                   'STANDBY' in item['queue'] and 
                                   item['queue']['STANDBY'].get('waitTime') is not None and 
                                   item['queue']['STANDBY'].get('waitTime') > 0):
                        ride_found = True
                        break
            
            if not ride_found:
                print("No rides found in liveData")
                # Show first few items anyway
                print("\nFirst few liveData items:")
                for i, item in enumerate(live_data[:3]):  # Only show first 3
                    print(f"\nItem {i+1}:")
                    print(f"Type: {type(item)}")
                    if isinstance(item, dict):
                        print(f"Keys: {list(item.keys())}")
                        if 'name' in item:
                            print(f"Name: {item['name']}")
        
        elif 'children' in data:
            children = data['children']
            print(f"Found 'children' with {len(children)} items")
            
            # Look for rides in children
            for i, child in enumerate(children[:3]):  # Show first 3
                print(f"\nChild {i+1}:")
                pprint(child, width=120, depth=2)
        
        else:
            print("No 'liveData' or 'children' key found")
            print("Available keys:", list(data.keys()))
        
        # If we have rides, find one with wait time
        if 'liveData' in data:
            live_data = data['liveData']
            for item in live_data:
                if isinstance(item, dict):
                    # Look for wait time in various possible fields
                    wait_fields = ['queue', 'waitTime', 'wait_time', 'wait', 'line']
                    ride_name = item.get('name', 'Unknown Ride')
                    
                    for field in wait_fields:
                        if field in item:
                            wait_value = item[field]
                            if isinstance(wait_value, dict) and 'STANDBY' in wait_value:
                                wait_time = wait_value['STANDBY'].get('wait', None)
                            elif isinstance(wait_value, (int, float)):
                                wait_time = wait_value
                            else:
                                wait_time = wait_value
                            
                            if wait_time is not None and wait_time > 0:
                                print(f"\n=== RIDE WITH WAIT TIME FOUND ===")
                                print(f"Ride: {ride_name}")
                                print(f"Wait Field: {field}")
                                print(f"Wait Value: {wait_time}")
                                print(f"Type: {type(wait_time)}")
                                print("\nRAW RIDE DATA:")
                                pprint(item, width=120, depth=None)
                                return
        
        print("\nNo rides with wait times found in current data")
        
    except requests.exceptions.RequestException as e:
        print(f"REQUEST ERROR: {e}")
        print("Check internet connection and API availability")
    except json.JSONDecodeError as e:
        print(f"JSON DECODE ERROR: {e}")
        print("Response may not be valid JSON")
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_raw_api()

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add current directory to path to import scraper
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_database_health():
    """
    Check database connectivity and data freshness.
    """
    print("DATABASE HEALTH CHECK")
    print("=" * 50)
    
    try:
        # Connect to database
        conn = sqlite3.connect('disney.db')
        
        # Get total number of rows
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM wait_times")
        total_rows = cursor.fetchone()[0]
        print(f"Total Records in wait_times: {total_rows:,}")
        
        # Get most recent timestamp
        cursor.execute("SELECT MAX(timestamp) FROM wait_times")
        latest_timestamp = cursor.fetchone()[0]
        
        if latest_timestamp:
            # Convert to datetime and human readable
            latest_dt = datetime.fromisoformat(latest_timestamp)
            latest_str = latest_dt.strftime("%Y-%m-%d %H:%M:%S")
            print(f"Most Recent Data: {latest_str}")
            
            # Calculate minutes since last update
            now = datetime.now()
            minutes_ago = (now - latest_dt).total_seconds() / 60
            
            print(f"Minutes Since Last Update: {minutes_ago:.1f}")
            
            # Recency check
            if minutes_ago > 20:
                print("CRITICAL: Data collection stopped. Scheduler is likely dead.")
                return False
            else:
                print("Database is receiving fresh data.")
                return True
        else:
            print("ERROR: No data found in database.")
            return False
            
    except Exception as e:
        print(f"DATABASE ERROR: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def test_api_connectivity():
    """
    Test the scraper API connectivity.
    """
    print("\nAPI CONNECTIVITY TEST")
    print("=" * 50)
    
    try:
        # Import scraper module
        from scraper import fetch_park_data
        print("Successfully imported scraper module")
        
        # Test Magic Kingdom API call
        magic_kingdom_id = "75ea578a-adc8-4116-a54d-dccb60765ef9"
        print(f"Testing API call to Magic Kingdom (ID: {magic_kingdom_id[:8]}...)")
        
        # Fetch data
        ride_data = fetch_park_data("Magic Kingdom Park", magic_kingdom_id)
        
        if ride_data:
            print(f"API SUCCESS: Retrieved {len(ride_data)} ride records")
            
            # Print first 3 rides
            print("\nSample Ride Data (First 3):")
            for i, ride in enumerate(ride_data[:3], 1):
                wait_time = ride.get('wait_time', 'N/A')
                ride_name = ride.get('ride_name', 'Unknown')
                print(f"  {i}. {ride_name}: {wait_time} minutes")
            
            return True
        else:
            print("API ERROR: No data returned from API")
            print("Possible causes:")
            print("   - ThemeParks.wiki API is down")
            print("   - Network connectivity issues")
            print("   - Invalid park ID")
            return False
            
    except ImportError as e:
        print(f"IMPORT ERROR: Could not import scraper module: {e}")
        print("Make sure scraper.py exists and is accessible")
        return False
    except Exception as e:
        print(f"API ERROR: {e}")
        print("Check network connection and API availability")
        return False

def check_file_system():
    """
    Check if required files exist.
    """
    print("\nFILE SYSTEM CHECK")
    print("=" * 50)
    
    required_files = [
        'disney.db',
        'scraper.py',
        'prediction.py',
        'dashboard.py',
        'api.py',
        'scheduler.py'
    ]
    
    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"OK {file} ({size:,} bytes)")
        else:
            print(f"MISSING: {file}")
            all_exist = False
    
    return all_exist

def main():
    """
    Main health check function.
    """
    print("DISNEY OMNI-TRACKER SYSTEM HEALTH CHECK")
    print("=" * 60)
    print(f"Check Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run all checks
    db_healthy = check_database_health()
    api_healthy = test_api_connectivity()
    files_healthy = check_file_system()
    
    # Summary
    print("\nSYSTEM HEALTH SUMMARY")
    print("=" * 50)
    
    if db_healthy and api_healthy and files_healthy:
        print("ALL SYSTEMS OPERATIONAL")
        print("   Database: Fresh data available")
        print("   API: Connectivity confirmed")
        print("   Files: All required files present")
        return 0
    else:
        print("SYSTEM ISSUES DETECTED")
        issues = []
        
        if not db_healthy:
            issues.append("Database data freshness")
        if not api_healthy:
            issues.append("API connectivity")
        if not files_healthy:
            issues.append("Missing files")
        
        for i, issue in enumerate(issues, 1):
            print(f"   Issue {i}: {issue}")
        
        print("\nRECOMMENDED ACTIONS:")
        if not db_healthy:
            print("   - Restart scheduler: python scheduler.py")
        if not api_healthy:
            print("   - Check internet connection")
            print("   - Verify ThemeParks.wiki API status")
        if not files_healthy:
            print("   - Restore missing files from backup")
        
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

from database import get_session, WaitTime
from sqlalchemy import func, text

def verify_database():
    """Query the database to show ride counts per park."""
    session = get_session()
    
    try:
        # Query ride counts per park
        result = session.query(
            func.count(WaitTime.id).label('ride_count'),
            WaitTime.park_name
        ).group_by(WaitTime.park_name).all()
        
        print("Ride counts per park:")
        for count, park in result:
            print(f"{park}: {count} rides")
        
        # Show total records
        total = session.query(func.count(WaitTime.id)).scalar()
        print(f"\nTotal records in database: {total}")
        
        # Show sample records
        print("\nSample records:")
        sample = session.query(WaitTime.ride_name, WaitTime.park_name, WaitTime.wait_time, WaitTime.is_open).limit(5).all()
        for ride_name, park_name, wait_time, is_open in sample:
            status = "Open" if is_open else "Closed"
            print(f"{ride_name} ({park_name}): {wait_time}min - {status}")
            
    except Exception as e:
        print(f"Error querying database: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    verify_database()

import sqlite3

DB_PATH = 'disney_complete.db'

def list_rides():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT ride_name FROM wait_times ORDER BY ride_name")
    rides = cursor.fetchall()
    conn.close()
    
    print(f"📋 Found {len(rides)} unique attractions:\n")
    for ride in rides:
        print(ride[0])

if __name__ == "__main__":
    list_rides()
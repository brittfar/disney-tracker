import sqlite3
import os
from datetime import datetime

DB_NAME = 'disney.db'

def inspect():
    if not os.path.exists(DB_NAME):
        print(f"❌ File {DB_NAME} not found!")
        return

    file_size = os.path.getsize(DB_NAME) / (1024 * 1024)
    print(f"📁 Database Size: {file_size:.2f} MB")

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # 1. INTEGRITY CHECK (Crucial for Disk I/O errors)
        print("\n🏥 Running Integrity Check (this might take a moment)...")
        cursor.execute("PRAGMA integrity_check;")
        result = cursor.fetchone()[0]
        if result == "ok":
            print("   ✅ Database integrity is GOOD.")
        else:
            print(f"   ❌ CORRUPTION DETECTED: {result}")
            print("   ⚠️  You may need to delete the file and restart.")
            return

        # 2. COUNT RECORDS
        print("\n📊 Data Statistics:")
        cursor.execute("SELECT COUNT(*) FROM wait_times")
        count = cursor.fetchone()[0]
        print(f"   Total Rows: {count:,}")

        if count == 0:
            print("   ⚠️  Database is empty.")
            return

        # 3. CHECK DATE RANGES
        cursor.execute("SELECT MIN(last_updated), MAX(last_updated) FROM wait_times")
        min_date, max_date = cursor.fetchone()
        print(f"   Earliest Date: {min_date}")
        print(f"   Latest Date:   {max_date}")

        # 4. CHECK FOR FUTURE JUNK
        # Anything beyond "today" is likely junk data (0 min waits)
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(f"SELECT COUNT(*) FROM wait_times WHERE last_updated > '{today}'")
        future_count = cursor.fetchone()[0]
        if future_count > 0:
            print(f"   ⚠️  WARNING: Found {future_count:,} records from the future (Junk Data).")
        
        # 5. SAMPLE DATA
        print("\n👀 Sample Data (First 5 valid records):")
        cursor.execute("SELECT * FROM wait_times LIMIT 5")
        rows = cursor.fetchall()
        for row in rows:
            print(f"   {row}")

    except Exception as e:
        print(f"\n❌ Error inspecting database: {e}")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    inspect()
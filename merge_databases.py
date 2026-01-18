import sqlite3
import os
import shutil

# --- CONFIGURATION ---
# The "Vault" (Old data)
OLD_DB = 'disney_MASTER.db'
# The "Fresh Batch" (New data you just scraped)
NEW_DB = 'disney.db'
# The Result
FINAL_DB = 'disney_complete.db'

def merge_data():
    print("🔄 Starting Database Merge...")

    # 1. Check if files exist
    if not os.path.exists(OLD_DB):
        print(f"❌ Error: Could not find {OLD_DB}")
        return
    if not os.path.exists(NEW_DB):
        print(f"❌ Error: Could not find {NEW_DB}")
        return

    # 2. Create the "Complete" file by copying the Old one first
    print(f"   📋 Copying {OLD_DB} to {FINAL_DB} (Starting base)...")
    shutil.copy2(OLD_DB, FINAL_DB)

    # 3. Connect to the NEW Complete file
    conn_dest = sqlite3.connect(FINAL_DB)
    cursor_dest = conn_dest.cursor()

    # 4. Attach the NEW scraped data
    print(f"   🔗 Attaching {NEW_DB}...")
    cursor_dest.execute(f"ATTACH DATABASE '{NEW_DB}' AS new_db")

    # 5. Insert only NEW records (avoiding duplicates)
    print("   🚀 Merging new records (this may take a minute)...")
    try:
        # We insert rows where the timestamp is NEWER than what we already have
        cursor_dest.execute("""
            INSERT INTO wait_times (ride_name, park_name, wait_time, status, last_updated)
            SELECT ride_name, park_name, wait_time, status, last_updated 
            FROM new_db.wait_times
            WHERE last_updated > (SELECT MAX(last_updated) FROM wait_times)
        """)
        
        rows_added = cursor_dest.rowcount
        conn_dest.commit()
        print(f"   ✅ Success! merged {rows_added:,} new records.")
        
    except Exception as e:
        print(f"   ❌ Merge Error: {e}")
        
    finally:
        conn_dest.close()
        print(f"\n🎉 DONE! You now have {FINAL_DB} ready for AI training.")

if __name__ == "__main__":
    merge_data()
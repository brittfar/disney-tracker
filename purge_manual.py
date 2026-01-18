import sqlite3
import time

DB_PATH = 'disney_complete.db'

# ⚠️ INSTRUCTIONS:
# This list contains attractions identified as Shows, Walkthroughs, or Movies.
# IF YOU WANT TO KEEP ONE: Delete its line from this list.
# Everything left in this list WILL BE DELETED from your database.

TO_DELETE = [
    "A Pirate's Adventure ~ Treasures of the Seven Seas",
    "Awesome Planet",
    "Beauty and the Beast – Live on Stage",
    "Canada Far and Wide in Circle-Vision 360",
    "Casey Jr. Splash 'N' Soak Station",
    "Country Bear Musical Jamboree",
    "Disney and Pixar Short Film Festival",
    "Enchanted Tales with Belle",
    "Feathered Friends in Flight!",
    "Festival of the Lion King",
    "Finding Nemo: The Big Blue... and Beyond!",
    "For the First Time in Forever: A Frozen Sing-Along Celebration",
    "Gorilla Falls Exploration Trail",
    "Indiana Jones™ Epic Stunt Spectacular!",
    "Journey of Water, Inspired by Moana",
    "Swiss Family Treehouse",
    "The Animation Experience at Conservation Station",
    "The Hall of Presidents",
    "The Little Mermaid – A Musical Adventure – New!",
    "Vacation Fun - An Original Animated Short with Mickey & Minnie",
    "Walt Disney Presents",
    "Wildlife Express Train"
]

def run_manual_purge():
    print(f"🚨 READY TO PURGE {len(TO_DELETE)} ATTRACTIONS.")
    print("   (If you want to save any, edit the 'TO_DELETE' list in the script now!)")
    
    confirm = input("Type 'YES' to delete these rows and shrink the DB: ")
    if confirm != "YES":
        print("❌ Aborted.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n   🔪 Deleting rows...")
    
    # Efficiently delete all matching names
    placeholders = ','.join('?' for _ in TO_DELETE)
    query = f"DELETE FROM wait_times WHERE ride_name IN ({placeholders})"
    cursor.execute(query, TO_DELETE)
    
    deleted_count = cursor.rowcount
    conn.commit()
    print(f"   ❌ Removed {deleted_count:,} rows.")

    # CRITICAL: Vacuum to release the disk space
    print("   🧹 Vacuuming database (this shrinks the file size)...")
    conn.execute("VACUUM")
    
    conn.close()
    print("\n✅ DONE! Run the Get-Item command to check your new size.")

if __name__ == "__main__":
    run_manual_purge()
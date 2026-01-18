import sqlite3
import pandas as pd
import os

# Point this to your BACKUP file
DB_NAME = 'derp.db'

def inspect_weather_quality():
    if not os.path.exists(DB_NAME):
        print(f"❌ File {DB_NAME} not found!")
        return

    print(f"🕵️ Inspecting {DB_NAME}...")
    conn = sqlite3.connect(DB_NAME)
    
    try:
        # 1. Check if Weather Table Exists
        print("\n1️⃣ Checking table structure...")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='weather_history'")
        if not cursor.fetchone():
            print("   ❌ 'weather_history' table is MISSING in this backup.")
            return
        print("   ✅ 'weather_history' table found.")

        # 2. Count Rows & Date Range
        print("\n2️⃣ Checking data volume...")
        df = pd.read_sql("SELECT timestamp, temperature, precipitation FROM weather_history", conn)
        
        if df.empty:
            print("   ⚠️ Table exists but is EMPTY.")
            return
            
        print(f"   ✅ Found {len(df):,} weather records.")
        print(f"   📅 Range: {df['timestamp'].min()} to {df['timestamp'].max()}")

        # 3. Quality Check (Null Values)
        print("\n3️⃣ Checking data quality...")
        null_temps = df['temperature'].isnull().sum()
        null_rain = df['precipitation'].isnull().sum()
        
        if null_temps == 0 and null_rain == 0:
            print("   ✅ Quality is PERFECT (No missing values).")
        else:
            print(f"   ⚠️ WARNING: Found gaps!")
            print(f"      - Missing Temperatures: {null_temps}")
            print(f"      - Missing Precipitation: {null_rain}")

        # 4. Preview
        print("\n👀 Data Preview (First 5 rows):")
        print(df.head())

    except Exception as e:
        print(f"❌ Error reading database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    inspect_weather_quality()
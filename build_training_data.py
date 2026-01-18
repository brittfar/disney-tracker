import sqlite3
import pandas as pd
import holidays
import os

# --- CONFIGURATION ---
DB_PATH = 'disney_complete.db' 
WEATHER_PATH = 'weather_history.csv'
OUTPUT_FILE = 'final_training_data.csv'

def build_dataset():
    print(f"🚀 Starting Feature Engineering on {DB_PATH}...")

    # --- 1. Check Files ---
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: Database {DB_PATH} not found!")
        return
    if not os.path.exists(WEATHER_PATH):
        print(f"❌ Error: Weather file {WEATHER_PATH} not found! Run fetch_weather.py first.")
        return

    # --- 2. Load Wait Times ---
    print(f"   📂 Loading wait times from database (this takes a moment)...")
    conn = sqlite3.connect(DB_PATH)
    
    query = """
    SELECT ride_name, wait_time, last_updated, status
    FROM wait_times
    WHERE status != 'Closed' 
    AND wait_time >= 0
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    print(f"   ✅ Loaded {len(df):,} rows.")

    # Convert timestamp
    df['last_updated'] = pd.to_datetime(df['last_updated'])
    
    # Round to nearest hour for weather matching
    df['merge_time'] = df['last_updated'].dt.round('h')

    # --- 3. Load Weather ---
    print(f"   🌤️ Loading weather from {WEATHER_PATH}...")
    weather_df = pd.read_csv(WEATHER_PATH)
    weather_df['time'] = pd.to_datetime(weather_df['time'])
    
    # Merge
    print("   🔗 Merging datasets...")
    df = pd.merge(df, weather_df, left_on='merge_time', right_on='time', how='left')
    df.drop(columns=['merge_time', 'time'], inplace=True)
    
    # Fill missing weather
    df['temperature'] = df['temperature'].ffill()
    df['precipitation'] = df['precipitation'].fillna(0.0)

    # --- 4. Feature Engineering (Time) ---
    print("   ⏰ Creating Time Features...")
    df['hour'] = df['last_updated'].dt.hour
    df['month'] = df['last_updated'].dt.month
    df['day_of_week'] = df['last_updated'].dt.dayofweek
    df['is_weekend'] = df['day_of_week'].apply(lambda x: 1 if x >= 5 else 0)

    # --- 5. Feature Engineering (Holidays) ---
    print("   🎄 Calculating Holidays (US)...")
    us_holidays = holidays.US(years=range(2022, 2027))
    
    df['date_only'] = df['last_updated'].dt.date
    df['is_holiday'] = df['date_only'].apply(lambda x: 1 if x in us_holidays else 0)
    df.drop(columns=['date_only'], inplace=True)

    # --- 6. Save Final File ---
    print(f"   💾 Saving to {OUTPUT_FILE}...")
    df.to_csv(OUTPUT_FILE, index=False)
    
    print("\n🎉 DONE! Your data is ready for Machine Learning.")
    print(f"   Final Dataset Shape: {df.shape}")
    print("   Columns:", list(df.columns))

# --- THIS IS THE PART YOU WERE MISSING ---
if __name__ == "__main__":
    build_dataset()
import pandas as pd
import os

FILE_NAME = 'final_training_data.csv'

def verify_holidays():
    if not os.path.exists(FILE_NAME):
        print(f"❌ Could not find {FILE_NAME}. Did you run build_training_data.py?")
        return

    print(f"🎄 Inspecting {FILE_NAME} for Holiday Data...")
    
    # Load just the date and holiday columns to be fast
    df = pd.read_csv(FILE_NAME, usecols=['last_updated', 'is_holiday'])
    
    # 1. Count Total Holidays
    total_rows = len(df)
    holiday_rows = df[df['is_holiday'] == 1]
    holiday_count = len(holiday_rows)
    
    if holiday_count == 0:
        print("   ⚠️  WARNING: Found 0 holiday records!")
        print("      Did you install the 'holidays' library? (pip install holidays)")
        return

    print(f"   ✅ Success! Found {holiday_count:,} records marked as holidays.")
    print(f"   📊 That is {holiday_count/total_rows:.1%} of your total data.")

    # 2. Show which holidays it found
    print("\n   📅 Sample of Holiday Dates Found:")
    # Get unique dates marked as holidays
    df['date'] = pd.to_datetime(df['last_updated']).dt.date
    unique_holidays = df[df['is_holiday'] == 1]['date'].unique()
    
    # Sort and show the first 10
    unique_holidays.sort()
    for date in unique_holidays[:10]:
        print(f"      - {date}")
    
    print("      ... and many more.")

if __name__ == "__main__":
    verify_holidays()
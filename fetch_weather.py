import requests
import pandas as pd
from datetime import datetime

# Configuration
LAT = 28.3772   # Disney World Latitude
LON = -81.5707  # Disney World Longitude
START_DATE = "2022-01-01"
END_DATE = datetime.now().strftime("%Y-%m-%d")

def fetch_weather():
    print("🌤️ Fetching historical weather for Orlando...")
    
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "hourly": "temperature_2m,precipitation",
        "timezone": "America/New_York",
        "temperature_unit": "fahrenheit"
    }

    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        print(f"❌ Error fetching weather: {response.text}")
        return

    data = response.json()
    
    # Process the data
    hourly = data['hourly']
    df = pd.DataFrame({
        'time': hourly['time'],
        'temperature': hourly['temperature_2m'],
        'precipitation': hourly['precipitation']
    })
    
    # Convert 'time' string to actual datetime objects
    df['time'] = pd.to_datetime(df['time'])
    
    # Save to CSV
    output_file = 'weather_history.csv'
    df.to_csv(output_file, index=False)
    
    print(f"✅ Weather data saved to {output_file}")
    print(f"   Records: {len(df):,}")

if __name__ == "__main__":
    fetch_weather()
import requests
from datetime import datetime, timedelta
from database import get_session
from schemas import WeatherHistory

def fetch_historical_weather():
    """
    Fetch hourly historical weather data for Orlando from Open-Meteo API.
    Range: 2022-01-01 to Yesterday.
    """
    print("Starting historical weather backfill for Orlando...")
    
    # Orlando coordinates
    lat, lon = 28.4179, -81.5812
    
    # Calculate date range (2022-01-01 to yesterday)
    start_date = datetime(2022, 1, 1)
    end_date = datetime.now() - timedelta(days=1)
    
    # Format dates for API
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    # Open-Meteo API URL
    url = f"https://archive-api.open-meteo.com/v1/archive"
    
    params = {
        'latitude': lat,
        'longitude': lon,
        'start_date': start_str,
        'end_date': end_str,
        'hourly': 'temperature_2m,precipitation',
        'timezone': 'America/New_York'
    }
    
    try:
        print(f"Fetching weather data from {start_str} to {end_str}...")
        
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        if 'hourly' not in data:
            print("Error: No hourly data found in response")
            return
        
        hourly_data = data['hourly']
        times = hourly_data.get('time', [])
        temperatures = hourly_data.get('temperature_2m', [])
        precipitations = hourly_data.get('precipitation', [])
        
        print(f"Found {len(times)} hourly weather records")
        
        # Process and insert data
        session = get_session()
        total_records = 0
        
        for i, (time_str, temp, precip) in enumerate(zip(times, temperatures, precipitations)):
            try:
                # Parse timestamp
                timestamp = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                
                # Determine if it's rainy (precipitation > 0.5mm)
                is_rainy = precip > 0.5
                
                # Create weather record
                weather_record = WeatherHistory(
                    timestamp=timestamp,
                    temperature=float(temp) if temp is not None else 0.0,
                    precipitation=float(precip) if precip is not None else 0.0,
                    is_rainy=is_rainy
                )
                
                session.add(weather_record)
                total_records += 1
                
                # Progress indicator
                if (i + 1) % 1000 == 0:
                    print(f"  Processed {i + 1} records...")
                
            except Exception as e:
                print(f"  Error processing record {i}: {e}")
                continue
        
        # Commit all records
        session.commit()
        session.close()
        
        print(f"Weather backfill complete! Total records added: {total_records}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    fetch_historical_weather()

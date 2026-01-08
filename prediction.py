import pandas as pd
import sqlite3
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from datetime import datetime, timedelta
import numpy as np

def train_and_predict(park_name, future_minutes=60):
    """
    Train a Random Forest model on historical wait time data and predict future wait times.
    Now includes ride_name as a feature for per-ride predictions.
    
    Args:
        park_name (str): Name of the park to predict for
        future_minutes (int): Number of minutes into the future to predict
    
    Returns:
        tuple: (model, label_encoder, df) or None if insufficient data
    """
    try:
        # Load data for the specific park from disney.db
        conn = sqlite3.connect('disney.db')
        query = "SELECT * FROM wait_times WHERE park_name = ? ORDER BY timestamp"
        df = pd.read_sql(query, conn, params=[park_name])
        conn.close()
        
        # Check if we have enough data (minimum 50 records)
        if len(df) < 50:
            return None, None, None
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Feature Engineering: Convert timestamp into numeric features
        df['hour_of_day'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['minute'] = df['timestamp'].dt.minute
        
        # Encode ride names as numeric features
        label_encoder = LabelEncoder()
        df['ride_name_encoded'] = label_encoder.fit_transform(df['ride_name'])
        
        # Prepare features and target
        features = ['hour_of_day', 'day_of_week', 'minute', 'ride_name_encoded']
        X = df[features]
        y = df['wait_time']
        
        # Train Random Forest model
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        return model, label_encoder, df
        
    except Exception as e:
        print(f"Error in prediction: {e}")
        return None, None, None

def get_ride_recommendation(park_name, ride_name, current_wait):
    """
    Generate a 'Buy/Sell' recommendation for a specific ride based on AI predictions.
    
    Args:
        park_name (str): Name of the park
        ride_name (str): Name of the specific ride
        current_wait (int): Current wait time in minutes
    
    Returns:
        str: Recommendation with emoji and reasoning
    """
    try:
        # Get trained model and data
        model, label_encoder, df = train_and_predict(park_name)
        
        if model is None:
            return '[LOADING] GATHERING DATA'
        
        # Check if we have enough data for this specific ride
        ride_data = df[df['ride_name'] == ride_name]
        if len(ride_data) < 10:  # Minimum 10 records for this specific ride
            return '[LOADING] GATHERING DATA'
        
        # Get current time
        current_time = datetime.now()
        current_hour = current_time.hour
        
        # Generate predictions for remaining hours of the day (until park closing, assume 10 PM)
        future_predictions = []
        
        for hour in range(current_hour + 1, 23):  # Until 10 PM (22:00)
            for minute in [0, 30]:  # Every 30 minutes
                future_time = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # Encode the ride name
                try:
                    ride_encoded = label_encoder.transform([ride_name])[0]
                except ValueError:
                    # Ride not found in training data
                    return '[LOADING] GATHERING DATA'
                
                # Create features for prediction
                features = np.array([[
                    hour,  # hour_of_day
                    future_time.dayofweek,  # day_of_week
                    minute,  # minute
                    ride_encoded  # ride_name_encoded
                ]])
                
                # Make prediction
                predicted_wait = model.predict(features)[0]
                predicted_wait = max(0, predicted_wait)  # Ensure non-negative
                
                future_predictions.append({
                    'time': future_time,
                    'predicted_wait': predicted_wait
                })
        
        if not future_predictions:
            return '[LOADING] GATHERING DATA'
        
        # Find the lowest predicted wait time
        lowest_prediction = min(future_predictions, key=lambda x: x['predicted_wait'])
        lowest_wait = lowest_prediction['predicted_wait']
        lowest_time = lowest_prediction['time'].strftime('%I:%M %p')
        
        # Apply recommendation logic
        if current_wait <= lowest_wait:
            return f'[GREEN] GO NOW - Best time of day'
        elif current_wait > lowest_wait + 15:
            return f'[RED] WAIT - Predicting drop to {lowest_wait:.0f}m at {lowest_time}'
        else:
            return f'[YELLOW] NEUTRAL - Similar wait times expected'
        
    except Exception as e:
        print(f"Error in recommendation: {e}")
        return '[LOADING] GATHERING DATA'

def get_average_wait_by_time(park_name):
    """
    Get average wait times by hour of day for reference.
    
    Args:
        park_name (str): Name of the park
    
    Returns:
        pd.DataFrame: DataFrame with hour and average_wait columns
    """
    try:
        conn = sqlite3.connect('disney.db')
        query = """
        SELECT hour_of_day, AVG(wait_time) as average_wait 
        FROM (
            SELECT strftime('%H', timestamp) as hour_of_day, wait_time 
            FROM wait_times 
            WHERE park_name = ?
        ) 
        GROUP BY hour_of_day 
        ORDER BY hour_of_day
        """
        df = pd.read_sql(query, conn, params=[park_name])
        conn.close()
        
        return df
        
    except Exception as e:
        print(f"Error getting average wait times: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    # Test the prediction function
    parks = ["Magic Kingdom Park", "EPCOT", "Disney's Hollywood Studios", "Disney's Animal Kingdom Theme Park"]
    
    for park in parks:
        print(f"\nTesting predictions for {park}:")
        predictions = train_and_predict(park, future_minutes=30)
        
        if predictions is not None:
            print(f"Generated {len(predictions)} predictions")
            print(f"Sample predictions:")
            print(predictions.head())
        else:
            print("Insufficient data for predictions")

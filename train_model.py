import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

# --- CONFIGURATION ---
INPUT_FILE = 'final_training_data.csv'
MODEL_FILE = 'disney_model.joblib'
ENCODER_FILE = 'ride_encoder.joblib'

# ⚠️ SAFETY SWITCH: 
# Training on 10 million rows takes a LOT of RAM. 
# We will use 10% (fraction=0.1) for the first run to test speed.
# If your laptop handles this easily, you can increase it to 0.5 or 1.0 later.
SAMPLE_FRACTION = 0.1 

def train_brain():
    print("🧠 Initializing Training Sequence...")

    # 1. Load Data
    print(f"   📂 Loading {INPUT_FILE}...")
    # Read only specific columns to save memory
    cols = ['ride_name', 'wait_time', 'temperature', 'precipitation', 
            'hour', 'month', 'day_of_week', 'is_weekend', 'is_holiday']
    
    df = pd.read_csv(INPUT_FILE, usecols=cols)
    print(f"   ✅ Loaded {len(df):,} rows.")

    # 2. Sample Data (To prevent crashing)
    if SAMPLE_FRACTION < 1.0:
        print(f"   ✂️  Sampling {SAMPLE_FRACTION*100}% of data for speed...")
        df = df.sample(frac=SAMPLE_FRACTION, random_state=42)
        print(f"      Training on {len(df):,} rows.")

    # 3. Encode Ride Names (AI needs numbers, not text)
    print("   🔢 Encoding Ride Names...")
    le = LabelEncoder()
    df['ride_id'] = le.fit_transform(df['ride_name'])
    
    # Save the encoder (We need this to translate back later!)
    joblib.dump(le, ENCODER_FILE)

    # 4. Split Data (Features vs Target)
    X = df[['ride_id', 'temperature', 'precipitation', 'hour', 'month', 'day_of_week', 'is_weekend', 'is_holiday']]
    y = df['wait_time']

    # Split into Training (80%) and Testing (20%)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 5. Train the Model
    print("   🏋️  Training Random Forest (This uses all CPU cores)...")
    # n_estimators=100 means 100 "decision trees"
    # n_jobs=-1 means "use all processor cores"
    model = RandomForestRegressor(n_estimators=50, max_depth=20, n_jobs=-1, random_state=42)
    model.fit(X_train, y_train)

    # 6. Evaluate
    print("   🧐 Testing Accuracy...")
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)

    print(f"\n   📊 REPORT CARD:")
    print(f"      Average Error (MAE): +/- {mae:.2f} minutes")
    print(f"      Accuracy Score (R²): {r2:.2f} (1.0 is perfect)")

    # 7. Save
    print(f"   💾 Saving the Brain to {MODEL_FILE}...")
    joblib.dump(model, MODEL_FILE)
    print("   🎉 Model Trained & Saved!")

if __name__ == "__main__":
    train_brain()
import os
import glob
import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import joblib
import datetime
import holidays

# --- 1. SELF-HEALING (Must be at the very top) ---
if not os.path.exists("disney_complete.db"):
    print("rebuilding database...")
    db_parts = sorted(glob.glob("disney_complete.db.part*"))
    if db_parts:
        with open("disney_complete.db", "wb") as dest:
            for part in db_parts:
                with open(part, "rb") as source:
                    dest.write(source.read())

# --- 2. CONFIG ---
st.set_page_config(
    page_title="Disney Planner",
    layout="centered",  # Centered is better for mobile "app" feel
    initial_sidebar_state="collapsed"
)

# --- 3. THEME & CSS ---
# Solid Pastel Background + High Contrast Text + No Sidebar
st.markdown("""
    <style>
        /* HIDE DEFAULT STREAMLIT ELEMENTS */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        [data-testid="stSidebar"] {display: none;}

        /* APP BACKGROUND */
        .stApp {
            background-color: #FDFBF7; /* Cream/Pastel Off-White */
        }

        /* TEXT STYLING */
        h1, h2, h3, h4, h5, p, div, label, span {
            color: #1A1A1A !important; /* Almost Black for high contrast */
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        }

        /* CARDS */
        .data-card {
            background-color: #FFFFFF;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            margin-bottom: 15px;
            border: 1px solid #E0E0E0;
        }

        /* METRICS */
        div[data-testid="metric-container"] {
            background-color: #FFFFFF;
            border: 1px solid #E0E0E0;
            border-radius: 10px;
            padding: 10px;
            box-shadow: none;
        }
        
        /* INPUT FIELDS */
        .stSelectbox, .stDateInput, .stTimeInput {
            color: #1A1A1A;
        }
    </style>
""", unsafe_allow_html=True)

# --- 4. DATA LOADING ---
DB_NAME = 'disney_complete.db'
MODEL_FILE = 'disney_model.joblib'
ENCODER_FILE = 'ride_encoder.joblib'

@st.cache_resource
def load_ai():
    # Attempt to load AI, fail gracefully if missing/too big
    try:
        return joblib.load(MODEL_FILE), joblib.load(ENCODER_FILE)
    except:
        return None, None

model, encoder = load_ai()

def load_ride_data(ride, days):
    conn = sqlite3.connect(DB_NAME)
    query = f"""
        SELECT last_updated, wait_time FROM wait_times 
        WHERE ride_name = ? AND last_updated > date('now', '-{days} days')
        ORDER BY last_updated ASC
    """
    df = pd.read_sql_query(query, conn, params=(ride,))
    conn.close()
    return df

def get_all_rides():
    conn = sqlite3.connect(DB_NAME)
    rides = pd.read_sql("SELECT DISTINCT ride_name FROM wait_times ORDER BY ride_name", conn)
    conn.close()
    return rides['ride_name'].tolist()

# --- 5. APP LAYOUT ---

# Header
st.markdown("<h1>Disney Wait Planner</h1>", unsafe_allow_html=True)

# Controls (Collapsible for Mobile Space Saving)
with st.expander("SETTINGS & CONTROLS", expanded=True):
    all_rides = get_all_rides()
    if all_rides:
        selected_ride = st.selectbox("Select Attraction", all_rides)
    else:
        st.error("No rides found in database.")
        selected_ride = None
    
    days_back = st.slider("History (Days)", 7, 365, 30)

if selected_ride:
    # --- TAB 1: CURRENT STATUS ---
    st.markdown("### Current Status")
    
    data = load_ride_data(selected_ride, days_back)
    
    if not data.empty:
        data['last_updated'] = pd.to_datetime(data['last_updated'])
        current_wait = data.iloc[-1]['wait_time']
        avg_wait = int(data['wait_time'].mean())
        
        # Simple 2-column layout for metrics
        c1, c2 = st.columns(2)
        c1.metric("Current Wait", f"{current_wait} min")
        c2.metric("Average (30d)", f"{avg_wait} min")

        # Chart
        st.markdown('<div class="data-card">', unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=data['last_updated'], 
            y=data['wait_time'], 
            mode='lines', 
            line=dict(color='#FF4B4B', width=2)
        ))
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            height=250,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(gridcolor='#F0F0F0'),
            xaxis=dict(gridcolor='#F0F0F0')
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.info("No data available for this ride.")

    # --- TAB 2: CRYSTAL BALL (PREDICTION) ---
    st.markdown("### Wait Time Prediction")
    st.markdown('<div class="data-card">', unsafe_allow_html=True)
    
    if model:
        col_input, col_pred = st.columns([1,1])
        
        with col_input:
            p_date = st.date_input("Date", datetime.date.today())
            p_time = st.time_input("Time", datetime.time(12, 0))
            
        with col_pred:
            if st.button("Predict Wait", use_container_width=True):
                try:
                    # Feature Engineering
                    ride_id = encoder.transform([selected_ride])[0]
                    hour = p_time.hour
                    month = p_date.month
                    day = p_date.weekday()
                    is_weekend = 1 if day >= 5 else 0
                    us_holidays = holidays.US(years=[p_date.year])
                    is_holiday = 1 if p_date in us_holidays else 0
                    
                    # Assume 75F and no rain for quick prediction
                    features = [[ride_id, 75, 0.0, hour, month, day, is_weekend, is_holiday]]
                    prediction = int(model.predict(features)[0])
                    
                    st.markdown(f"<h2 style='text-align: center; color: #FF4B4B !important;'>{prediction} min</h2>", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error: {e}")
    else:
        st.warning("⚠️ Prediction Model not loaded (Memory Limit).")
        st.markdown("To enable predictions, this app needs to be hosted on a platform with >1GB RAM.")
        
    st.markdown('</div>', unsafe_allow_html=True)
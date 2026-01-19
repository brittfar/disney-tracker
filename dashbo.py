import os
import glob
import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import joblib
import datetime
import holidays

# --- 1. SELF-HEALING ---
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
    page_title="Disney",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 3. CSS Styling (Simplified) ---
st.markdown("""
    <style>
        /* Hide Top Bar & Footer for App Feel */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        [data-testid="stSidebar"] {display: none;}

        /* App Background - Clean Off-White */
        .stApp {
            background-color: #F5F7FA;
        }

        /* Make Tabs look like App Navigation */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background-color: white;
            padding: 10px 10px 0px 10px;
            border-radius: 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            border-radius: 5px;
        }

        /* Remove extra padding at top */
        .block-container {
            padding-top: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

# --- 4. DATA LOGIC ---
DB_NAME = 'disney_complete.db'
MODEL_FILE = 'disney_model.joblib'
ENCODER_FILE = 'ride_encoder.joblib'

@st.cache_resource
def load_ai():
    try:
        return joblib.load(MODEL_FILE), joblib.load(ENCODER_FILE)
    except:
        return None, None

model, encoder = load_ai()

def load_ride_data(ride, days):
    conn = sqlite3.connect(DB_NAME)
    query = f"SELECT last_updated, wait_time FROM wait_times WHERE ride_name = ? AND last_updated > date('now', '-{days} days') ORDER BY last_updated ASC"
    df = pd.read_sql_query(query, conn, params=(ride,))
    conn.close()
    return df

def get_rides_for_park(park_name):
    # Hardcoded directory matches your DB names
    PARK_DIRECTORY = {
        "Magic Kingdom": ["Seven Dwarfs Mine Train", "Space Mountain", "Big Thunder Mountain Railroad", "Haunted Mansion", "Pirates of the Caribbean", "Jungle Cruise", "Peter Pan's Flight", "TRON Lightcycle / Run", "Tiana's Bayou Adventure"],
        "Epcot": ["Guardians of the Galaxy: Cosmic Rewind", "Remy's Ratatouille Adventure", "Frozen Ever After", "Test Track", "Soarin' Around the World", "Spaceship Earth"],
        "Hollywood Studios": ["Star Wars: Rise of the Resistance", "Slinky Dog Dash", "The Twilight Zone Tower of Terror", "Rock 'n' Roller Coaster Starring Aerosmith", "Mickey & Minnie's Runaway Railway", "Millennium Falcon: Smugglers Run", "Toy Story Mania!"],
        "Animal Kingdom": ["Avatar Flight of Passage", "Na'vi River Journey", "Expedition Everest - Legend of the Forbidden Mountain", "Kilimanjaro Safaris", "DINOSAUR"]
    }
    return PARK_DIRECTORY.get(park_name, [])

# --- 5. APP UI ---

# Create Tabs for Parks (The "App Navigation")
park_tabs = st.tabs(["MK", "EPCOT", "HS", "AK"])
park_names = ["Magic Kingdom", "Epcot", "Hollywood Studios", "Animal Kingdom"]

# Loop to create content for each tab
for tab, park_name in zip(park_tabs, park_names):
    with tab:
        # 1. RIDE SELECTOR
        my_rides = get_rides_for_park(park_name)
        selected_ride = st.selectbox(f"Ride at {park_name}", my_rides, label_visibility="collapsed")

        if selected_ride:
            data = load_ride_data(selected_ride, 30)
            
            if not data.empty:
                current_wait = data.iloc[-1]['wait_time']
                avg_wait = int(data['wait_time'].mean())

                # 2. METRICS CARD
                with st.container(border=True):
                    c1, c2 = st.columns(2)
                    c1.metric("Wait Now", f"{current_wait}m")
                    c2.metric("Avg (30d)", f"{avg_wait}m")

                # 3. CHART CARD
                with st.container(border=True):
                    st.caption(f"History: {selected_ride}")
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=pd.to_datetime(data['last_updated']), 
                        y=data['wait_time'], 
                        mode='lines', 
                        line=dict(color='#2196F3', width=2),
                        fill='tozeroy',
                        fillcolor='rgba(33, 150, 243, 0.1)'
                    ))
                    fig.update_layout(height=200, margin=dict(l=0,r=0,t=0,b=0), xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#eee'), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

                # 4. PREDICTION CARD
                with st.container(border=True):
                    if model:
                        c_time, c_btn = st.columns([2,1])
                        p_time = c_time.time_input("Plan Time", datetime.time(12,0), label_visibility="collapsed")
                        if c_btn.button("Predict", key=f"btn_{park_name}", use_container_width=True):
                            try:
                                ride_id = encoder.transform([selected_ride])[0]
                                now = datetime.datetime.now()
                                pred = int(model.predict([[ride_id, 75, 0.0, p_time.hour, now.month, now.weekday(), 0, 0]])[0])
                                st.info(f"Forecast: {pred} min wait")
                            except:
                                st.error("Error")
                    else:
                        st.caption("🔮 AI Forecast (Disabled on Free Host)")
            else:
                st.warning("No data yet.")
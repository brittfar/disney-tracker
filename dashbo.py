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
    page_title="Disney App",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 3. PARK DATA (For Filtering) ---
PARK_DIRECTORY = {
    "Magic Kingdom": [
        "Seven Dwarfs Mine Train", "Space Mountain", "Big Thunder Mountain Railroad",
        "Haunted Mansion", "Pirates of the Caribbean", "Jungle Cruise",
        "Peter Pan's Flight", "It's a Small World", "Buzz Lightyear's Space Ranger Spin",
        "The Many Adventures of Winnie the Pooh", "Under the Sea - Journey of the Little Mermaid",
        "Dumbo the Flying Elephant", "Mad Tea Party", "Tomorrowland Speedway",
        "Magic Carpets of Aladdin", "Astro Orbiter", "Barnstormer",
        "TRON Lightcycle / Run", "Tiana's Bayou Adventure"
    ],
    "Epcot": [
        "Guardians of the Galaxy: Cosmic Rewind", "Remy's Ratatouille Adventure",
        "Frozen Ever After", "Test Track", "Soarin' Around the World",
        "Spaceship Earth", "Mission: SPACE", "The Seas with Nemo & Friends",
        "Living with the Land", "Journey Into Imagination with Figment",
        "Gran Fiesta Tour Starring The Three Caballeros"
    ],
    "Hollywood Studios": [
        "Star Wars: Rise of the Resistance", "Slinky Dog Dash", 
        "The Twilight Zone Tower of Terror", "Rock 'n' Roller Coaster Starring Aerosmith",
        "Mickey & Minnie's Runaway Railway", "Millennium Falcon: Smugglers Run",
        "Toy Story Mania!", "Alien Swirling Saucers", "Star Tours – The Adventures Continue"
    ],
    "Animal Kingdom": [
        "Avatar Flight of Passage", "Na'vi River Journey", 
        "Expedition Everest - Legend of the Forbidden Mountain", "Kilimanjaro Safaris",
        "DINOSAUR", "Kali River Rapids", "TriceraTop Spin", "It's Tough to Be a Bug!"
    ]
}

# --- 4. AGGRESSIVE APP STYLING ---
st.markdown("""
    <style>
        /* HIDE STREAMLIT CHROME */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        [data-testid="stSidebar"] {display: none;}
        
        /* FULL SCREEN PASTEL BACKGROUND */
        .stApp {
            background-color: #E3F2FD; /* Solid Pastel Blue */
        }
        
        /* TEXT CONTRAST */
        h1, h2, h3, p, label, span, div {
            color: #121212 !important; /* Almost Black */
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }

        /* REMOVE PADDING TO FEEL LIKE APP */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
        }

        /* CARDS */
        .data-card {
            background-color: #FFFFFF;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            margin-bottom: 16px;
        }

        /* METRICS */
        div[data-testid="metric-container"] {
            background-color: #FFFFFF;
            border: 1px solid #E0E0E0;
            border-radius: 12px;
            padding: 10px;
        }
        
        /* HIDE LABELS FOR CLEANER LOOK */
        .stSelectbox label { display: none; }
        .stRadio label { display: none; }
    </style>
""", unsafe_allow_html=True)

# --- 5. DATA LOADING ---
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
    query = f"""
        SELECT last_updated, wait_time FROM wait_times 
        WHERE ride_name = ? AND last_updated > date('now', '-{days} days')
        ORDER BY last_updated ASC
    """
    df = pd.read_sql_query(query, conn, params=(ride,))
    conn.close()
    return df

def get_available_rides_in_db():
    conn = sqlite3.connect(DB_NAME)
    rides = pd.read_sql("SELECT DISTINCT ride_name FROM wait_times", conn)
    conn.close()
    return rides['ride_name'].tolist()

# --- 6. INTERFACE ---

# Step 1: Park Selection (Horizontal Pills/Radio)
# "Select Park" text is hidden by CSS, but label exists for accessibility
selected_park = st.radio("Select Park", list(PARK_DIRECTORY.keys()), horizontal=True)

# Step 2: Ride Selection (Filtered)
db_rides = get_available_rides_in_db()
expected_rides = PARK_DIRECTORY.get(selected_park, [])
# Intersect DB rides with Park rides
available_rides = [r for r in db_rides if r in expected_rides]

if not available_rides:
    # Fallback if names don't match perfect
    available_rides = db_rides 

selected_ride = st.selectbox("Select Ride", available_rides)

# Step 3: Data Display
if selected_ride:
    # Load 30 days of data by default
    data = load_ride_data(selected_ride, 30)
    
    if not data.empty:
        data['last_updated'] = pd.to_datetime(data['last_updated'])
        current_wait = data.iloc[-1]['wait_time']
        avg_wait = int(data['wait_time'].mean())

        # METRICS ROW
        c1, c2 = st.columns(2)
        c1.metric("Current", f"{current_wait} m")
        c2.metric("Avg (30d)", f"{avg_wait} m")

        # CHART CARD
        st.markdown('<div class="data-card">', unsafe_allow_html=True)
        st.caption("Wait Time History (30 Days)")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=data['last_updated'], 
            y=data['wait_time'], 
            mode='lines', 
            line=dict(color='#2196F3', width=3),
            fill='tozeroy',
            fillcolor='rgba(33, 150, 243, 0.1)'
        ))
        fig.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            height=200,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='#F5F5F5')
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)
        
    else:
        st.info("No data available.")

    # PREDICTION CARD (Still Lite Mode)
    st.markdown('<div class="data-card">', unsafe_allow_html=True)
    st.caption("Predict Future Wait")
    
    if model:
        # Inputs
        col_input, col_btn = st.columns([2,1])
        with col_input:
            p_time = st.time_input("Time", datetime.time(12, 0))
        with col_btn:
            st.write("") # Spacer
            st.write("") # Spacer
            predict_btn = st.button("Go", use_container_width=True)

        if predict_btn:
            try:
                # Prediction Logic
                ride_id = encoder.transform([selected_ride])[0]
                hour = p_time.hour
                # Use today's date for simplicity
                now = datetime.datetime.now()
                features = [[ride_id, 75, 0.0, hour, now.month, now.weekday(), 0, 0]]
                pred = int(model.predict(features)[0])
                st.markdown(f"<h2 style='text-align:center; color:#2196F3 !important; margin:0;'>{pred} min</h2>", unsafe_allow_html=True)
            except:
                st.error("Error")
    else:
        st.caption("AI Model Disabled (Memory Limit)")
        st.write("Upgrade host to enable predictions.")
    
    st.markdown('</div>', unsafe_allow_html=True)
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import joblib
import datetime
import holidays

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Disney Pastel Planner", 
    page_icon="✨", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- RESOURCES ---
DB_NAME = 'disney_complete.db'
MODEL_FILE = 'disney_model.joblib'
ENCODER_FILE = 'ride_encoder.joblib'

# --- THE PARK DIRECTORY (Manual Override) ---
# Since your DB doesn't have park names, we map them here.
# These names must match your database ride names EXACTLY.
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

# --- THEMES ---
PARK_THEMES = {
    "Magic Kingdom": {
        "color": "#FFB7B2", "accent": "#A2E1DB", 
        "gradient": "linear-gradient(135deg, #FFDEE9 0%, #B5FFFC 100%)",
        "icon": "🏰", "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Cinderella_Castle_2011.jpg/1200px-Cinderella_Castle_2011.jpg"
    },
    "Epcot": {
        "color": "#E2F0CB", "accent": "#C7CEEA", 
        "gradient": "linear-gradient(135deg, #E0C3FC 0%, #8EC5FC 100%)",
        "icon": "🌐", "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Spaceship_Earth_at_night.jpg/1200px-Spaceship_Earth_at_night.jpg"
    },
    "Hollywood Studios": {
        "color": "#FFDAC1", "accent": "#FF9AA2", 
        "gradient": "linear-gradient(135deg, #F6D365 0%, #FDA085 100%)",
        "icon": "🎬", "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/58/Disney%27s_Hollywood_Studios_Entrance.jpg/1200px-Disney%27s_Hollywood_Studios_Entrance.jpg"
    },
    "Animal Kingdom": {
        "color": "#B5EAD7", "accent": "#E2F0CB", 
        "gradient": "linear-gradient(135deg, #D4FC79 0%, #96E6A1 100%)",
        "icon": "🦁", "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Tree_of_Life_2016.jpg/1200px-Tree_of_Life_2016.jpg"
    }
}

@st.cache_resource
def load_ai():
    try:
        return joblib.load(MODEL_FILE), joblib.load(ENCODER_FILE)
    except:
        return None, None

model, encoder = load_ai()

# --- HELPER FUNCTIONS ---
def get_available_rides_in_db():
    """Get a list of ALL rides that actually exist in your database"""
    conn = sqlite3.connect(DB_NAME)
    rides = pd.read_sql("SELECT DISTINCT ride_name FROM wait_times", conn)
    conn.close()
    return rides['ride_name'].tolist()

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

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/3/32/Walt_Disney_Studios_Motion_Pictures_logo.svg/800px-Walt_Disney_Studios_Motion_Pictures_logo.svg.png", use_container_width=True)
    
    st.header("✨ Park Hopper")
    
    # 1. PARK SELECTION
    selected_park = st.radio("Choose your Park:", list(PARK_THEMES.keys()))
    theme = PARK_THEMES[selected_park]

    st.markdown("---")
    
    # 2. RIDE SELECTION (Filtered by Manual Directory)
    # Get all rides that exist in the DB
    db_rides = get_available_rides_in_db()
    
    # Filter: Only show rides that are in the selected park AND in the database
    # This prevents "No Rides Found" if your DB names match our directory
    # If a ride is in the DB but not our directory, we won't see it (safety filter)
    expected_rides = PARK_DIRECTORY.get(selected_park, [])
    
    # Fuzzy match logic: Check if the ride name from our list is inside the DB list
    # We use a set intersection to be fast
    available_rides = [r for r in db_rides if r in expected_rides]
    
    # FALLBACK: If the intersection is empty (names don't match), show ALL DB rides
    # This ensures the app never breaks, even if the names are slightly different.
    if not available_rides:
        st.warning(f"Could not map rides for {selected_park}. Showing all.")
        available_rides = db_rides
        
    selected_ride = st.selectbox("📍 Select Attraction", available_rides)
    days_back = st.slider("📅 History Lookback", 7, 1200, 700)

# --- DYNAMIC CSS ---
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;500;700&display=swap');
        * {{ font-family: 'Poppins', sans-serif; color: #444; }}
        .stApp {{ background: {theme['gradient']}; background-attachment: fixed; }}
        [data-testid="stSidebar"] {{ background-color: rgba(255, 255, 255, 0.85); border-right: 2px solid white; }}
        
        .pastel-card {{
            background: rgba(255, 255, 255, 0.85);
            border-radius: 20px;
            padding: 25px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.6);
            margin-bottom: 20px;
        }}
        h1, h2, h3 {{ color: #555 !important; }}
        div[data-testid="metric-container"] {{
            background: white; border-radius: 15px; padding: 15px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05); color: #555;
            border: 2px solid {theme['color']};
        }}
        [data-testid="metric-value"] {{ color: #333 !important; }}
        .stTabs [aria-selected="true"] {{
            background-color: {theme['color']} !important; color: #444 !important; border-radius: 20px;
        }}
        .magic-box {{
            background: white; border-radius: 25px; padding: 30px; text-align: center;
            border: 4px solid {theme['accent']}; box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown(f"""
    <div style="border-radius: 20px; height: 250px; background-image: url('{theme['image']}'); background-size: cover; background-position: center; display: flex; align-items: flex-end; box-shadow: 0 10px 20px rgba(0,0,0,0.1); margin-bottom: 20px;">
        <div style="width: 100%; background: linear-gradient(to top, rgba(255,255,255,0.9), transparent); padding: 20px; border-bottom-left-radius: 20px; border-bottom-right-radius: 20px;">
            <h1 style="margin:0; font-size: 3rem; color: #444;">{theme['icon']} {selected_park}</h1>
            <p style="margin:0; font-size: 1.2rem; color: #666;">Analytics for <b>{selected_ride}</b></p>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- TABS ---
tab1, tab2 = st.tabs(["📊 Stats & Charts", "🔮 Magic Crystal Ball"])

with tab1:
    if selected_ride:
        data = load_ride_data(selected_ride, days_back)
        if not data.empty:
            data['last_updated'] = pd.to_datetime(data['last_updated'])
            col1, col2, col3, col4 = st.columns(4)
            current_wait = data.iloc[-1]['wait_time']
            avg_wait = int(data['wait_time'].mean())
            max_wait = data['wait_time'].max()
            busy_hour = data.groupby(data['last_updated'].dt.hour)['wait_time'].mean().idxmax()

            col1.metric("Current Wait", f"{current_wait} min")
            col2.metric("Average", f"{avg_wait} min")
            col3.metric("Peak Wait", f"{max_wait} min")
            col4.metric("Busiest At", f"{busy_hour}:00")
            
            st.markdown('<div class="pastel-card"><h4>📉 Wait Time History</h4>', unsafe_allow_html=True)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=data['last_updated'], y=data['wait_time'], mode='lines', fill='tozeroy',
                line=dict(color=theme['accent'], width=3), fillcolor=theme['color']
            ))
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#555'), height=350, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info(f"No data found for {selected_ride}. Try increasing the history lookback.")

with tab2:
    st.markdown('<div class="pastel-card">', unsafe_allow_html=True)
    col_in, col_out = st.columns([1, 1])
    with col_in:
        st.subheader("⚙️ Prediction Settings")
        pred_date = st.date_input("Date", datetime.date.today() + datetime.timedelta(days=1))
        pred_time = st.time_input("Time", datetime.time(12, 0))
        pred_temp = st.slider("Temperature (°F)", 40, 100, 75)
        pred_rain = st.checkbox("Is it Raining?", value=False)
        btn = st.button("🔮 Reveal Wait Time", type="primary", use_container_width=True)

    with col_out:
        if btn and model:
            try:
                ride_id = encoder.transform([selected_ride])[0]
                hour = pred_time.hour
                month = pred_date.month
                day_of_week = pred_date.weekday()
                is_weekend = 1 if day_of_week >= 5 else 0
                us_holidays = holidays.US(years=[pred_date.year])
                is_holiday = 1 if pred_date in us_holidays else 0
                precip = 1.0 if pred_rain else 0.0
                
                features = [[ride_id, pred_temp, precip, hour, month, day_of_week, is_weekend, is_holiday]]
                prediction = int(model.predict(features)[0])
                
                st.markdown(f"""
                    <div class="magic-box">
                        <h4 style="color:#888; margin:0;">PREDICTED WAIT</h4>
                        <h1 style="font-size: 5rem; color:{theme['accent']}; margin:0;">{prediction}</h1>
                        <h3 style="margin:0; color:#aaa;">minutes</h3>
                    </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {e}")
        elif not model:
            st.warning("Model not loaded.")
    st.markdown('</div>', unsafe_allow_html=True)
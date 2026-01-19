import os
import glob
import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import datetime

# --- 1. SELF-HEALING (Database Reconstruction) ---
if not os.path.exists("disney_complete.db"):
    db_parts = sorted(glob.glob("disney_complete.db.part*"))
    if db_parts:
        with open("disney_complete.db", "wb") as dest:
            for part in db_parts:
                with open(part, "rb") as source:
                    dest.write(source.read())

# --- 2. CONFIG & STYLING ---
st.set_page_config(page_title="Disney Planner", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        /* Clean Mobile Look */
        #MainMenu, footer, header {visibility: hidden;}
        [data-testid="stSidebar"] {display: none;}
        .stApp {background-color: #F5F7FA;}
        .block-container {padding-top: 1rem; padding-bottom: 2rem;}
        
        /* Cards */
        .plan-card {
            background-color: white; border-radius: 15px; padding: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 15px;
            text-align: center; border: 1px solid #eee;
        }
        
        /* Verdict Text */
        .verdict-go {color: #2ECC71; font-weight: bold; font-size: 1.5rem;}
        .verdict-wait {color: #E74C3C; font-weight: bold; font-size: 1.5rem;}
        
        /* Park Selector Styling */
        div[role="radiogroup"] {justify-content: center;}
    </style>
""", unsafe_allow_html=True)

DB_NAME = 'disney_complete.db'

# --- 3. DATA FUNCTIONS (The "Lightweight AI") ---
def get_live_wait(ride):
    """Get the very latest wait time"""
    conn = sqlite3.connect(DB_NAME)
    # Get last record
    row = pd.read_sql_query(f"SELECT wait_time FROM wait_times WHERE ride_name = ? ORDER BY last_updated DESC LIMIT 1", conn, params=(ride,))
    conn.close()
    return row.iloc[0]['wait_time'] if not row.empty else None

def get_typical_day_curve(ride):
    """
    Get average wait time per hour for the current day of week.
    This replaces the 'Heavy AI' with 'Smart Stats'.
    """
    day_of_week = datetime.datetime.today().weekday() # 0=Monday, 6=Sunday
    conn = sqlite3.connect(DB_NAME)
    
    # SQL Magic: Average wait times grouped by hour for this specific day of week
    # We ignore data older than 90 days to keep it fresh
    query = f"""
        SELECT strftime('%H', last_updated) as hour, AVG(wait_time) as avg_wait
        FROM wait_times
        WHERE ride_name = ? 
        AND cast(strftime('%w', last_updated) as int) = ?
        AND last_updated > date('now', '-90 days')
        GROUP BY hour
        ORDER BY hour
    """
    df = pd.read_sql_query(query, conn, params=(ride, day_of_week))
    conn.close()
    return df

def get_best_park_today():
    """Rank parks by their current average wait time"""
    conn = sqlite3.connect(DB_NAME)
    # Get average wait of all rides in the last 2 hours per park? 
    # Since we don't store 'park' column explicitly in DB (we mapped it in python), 
    # we have to query ALL rides and map them.
    
    # 1. Get latest wait for EVERY ride
    query = """
        SELECT ride_name, wait_time 
        FROM wait_times 
        WHERE last_updated > datetime('now', '-2 hours')
        GROUP BY ride_name 
        ORDER BY last_updated DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # 2. Map to Parks
    PARK_MAP = {
        "Magic Kingdom": ["Seven Dwarfs", "Space Mountain", "Big Thunder", "Haunted Mansion", "Pirates", "Jungle Cruise", "Peter Pan", "TRON", "Tiana"],
        "Epcot": ["Guardians", "Remy", "Frozen", "Test Track", "Soarin", "Spaceship Earth"],
        "Hollywood Studios": ["Rise of the Resistance", "Slinky Dog", "Tower of Terror", "Rock 'n' Roller", "Runaway Railway", "Smugglers Run"],
        "Animal Kingdom": ["Flight of Passage", "Na'vi", "Expedition Everest", "Kilimanjaro", "DINOSAUR"]
    }
    
    park_scores = {}
    for park, keywords in PARK_MAP.items():
        # Fuzzy match ride names
        park_rides = df[df['ride_name'].str.contains('|'.join(keywords), case=False, regex=True)]
        if not park_rides.empty:
            avg_wait = park_rides['wait_time'].mean()
            park_scores[park] = int(avg_wait)
        else:
            park_scores[park] = 0
            
    return pd.DataFrame(list(park_scores.items()), columns=['Park', 'AvgWait']).sort_values('AvgWait')

# --- 4. APP INTERFACE ---

# A. PARK SELECTOR (Cleaner Radio)
parks = ["Magic Kingdom", "Epcot", "Hollywood Studios", "Animal Kingdom"]
selected_park = st.radio("Park", parks, horizontal=True, label_visibility="collapsed")

# B. RIDE SELECTOR (Filtered)
PARK_RIDES = {
    "Magic Kingdom": ["Seven Dwarfs Mine Train", "Space Mountain", "Big Thunder Mountain Railroad", "Haunted Mansion", "Pirates of the Caribbean", "TRON Lightcycle / Run"],
    "Epcot": ["Guardians of the Galaxy: Cosmic Rewind", "Remy's Ratatouille Adventure", "Frozen Ever After", "Test Track", "Soarin' Around the World"],
    "Hollywood Studios": ["Star Wars: Rise of the Resistance", "Slinky Dog Dash", "The Twilight Zone Tower of Terror", "Rock 'n' Roller Coaster Starring Aerosmith", "Mickey & Minnie's Runaway Railway"],
    "Animal Kingdom": ["Avatar Flight of Passage", "Na'vi River Journey", "Expedition Everest - Legend of the Forbidden Mountain", "Kilimanjaro Safaris"]
}
rides = PARK_RIDES.get(selected_park, [])
selected_ride = st.selectbox("Attraction", rides)

# --- 5. THE "PLANNER" LOGIC ---
if selected_ride:
    current_wait = get_live_wait(selected_ride)
    if current_wait is None: current_wait = 0
    
    # Get the "Typical" curve for today
    curve = get_typical_day_curve(selected_ride)
    
    if not curve.empty:
        curve['hour'] = curve['hour'].astype(int)
        
        # Determine "Verdict"
        # Find average wait for RIGHT NOW (current hour)
        current_hour = datetime.datetime.now().hour
        typical_now = curve[curve['hour'] == current_hour]['avg_wait'].mean()
        if pd.isna(typical_now): typical_now = current_wait # Fallback
        
        diff = current_wait - typical_now
        
        st.markdown(f"<div class='plan-card'>", unsafe_allow_html=True)
        st.caption("VERDICT")
        
        if diff < -5:
            st.markdown(f"<div class='verdict-go'>✅ GO NOW!</div>", unsafe_allow_html=True)
            st.write(f"Wait is **{int(abs(diff))} min lower** than usual.")
        elif diff > 10:
            st.markdown(f"<div class='verdict-wait'>🛑 WAIT</div>", unsafe_allow_html=True)
            st.write(f"Wait is **{int(diff)} min higher** than usual.")
        else:
            st.write("⚠️ Normal Traffic. Go if you want.")
            
        col1, col2 = st.columns(2)
        col1.metric("Wait Now", f"{current_wait} m")
        col2.metric("Typical", f"{int(typical_now)} m")
        st.markdown("</div>", unsafe_allow_html=True)

        # FORECAST CHART
        st.markdown("### 🕒 Forecast for Today")
        st.caption("Gray line = Typical wait for this day of week")
        
        fig = go.Figure()
        # Typical Line
        fig.add_trace(go.Bar(
            x=curve['hour'], 
            y=curve['avg_wait'],
            marker_color='#E0E0E0',
            name="Typical"
        ))
        # Highlight current hour
        fig.add_trace(go.Bar(
            x=[current_hour],
            y=[current_wait],
            marker_color='#2196F3',
            name="Right Now"
        ))
        
        fig.update_layout(
            barmode='overlay',
            height=200,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
            xaxis=dict(tickmode='linear', tick0=8, dtick=2, title="Hour of Day"),
            yaxis=dict(showgrid=True, gridcolor='#f0f0f0')
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
    else:
        st.info("Not enough history to predict this ride yet.")

# --- 6. "BEST PARK" LEADERBOARD ---
st.markdown("---")
with st.expander("🏆 Which Park is Best Today?"):
    scores = get_best_park_today()
    if not scores.empty:
        st.write("Average wait across all major rides:")
        for index, row in scores.iterrows():
            st.progress(min(int(row['AvgWait']), 100) / 100, text=f"{row['Park']}: {row['AvgWait']} min avg")
    else:
        st.write("Collecting data...")
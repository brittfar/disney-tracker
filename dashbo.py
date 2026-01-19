import os
import glob
import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import datetime
import holidays

# --- 1. SELF-HEALING ---
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
        #MainMenu, footer, header {visibility: hidden;}
        [data-testid="stSidebar"] {display: none;}
        .stApp {background-color: #F5F7FA;}
        .block-container {padding-top: 1rem; padding-bottom: 2rem;}
        
        /* Cards */
        .plan-card {
            background-color: white; border-radius: 15px; padding: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 15px;
            border: 1px solid #eee;
        }
        
        /* Verdict Colors */
        .v-go {color: #2ECC71; font-weight: 800;}
        .v-wait {color: #E74C3C; font-weight: 800;}
        
        /* Crowd Level Colors */
        .crowd-low {color: #2ECC71; font-weight: bold; font-size: 2rem;}
        .crowd-med {color: #F1C40F; font-weight: bold; font-size: 2rem;}
        .crowd-high {color: #E67E22; font-weight: bold; font-size: 2rem;}
        .crowd-max {color: #E74C3C; font-weight: bold; font-size: 2rem;}
    </style>
""", unsafe_allow_html=True)

DB_NAME = 'disney_complete.db'

# --- 3. LOGIC ENGINES ---

def get_live_wait(ride):
    """Get latest wait time from DB"""
    conn = sqlite3.connect(DB_NAME)
    row = pd.read_sql_query(f"SELECT wait_time FROM wait_times WHERE ride_name = ? ORDER BY last_updated DESC LIMIT 1", conn, params=(ride,))
    conn.close()
    return row.iloc[0]['wait_time'] if not row.empty else 0

def get_typical_curve(ride):
    """Get hourly averages for today's day-of-week"""
    day_of_week = datetime.datetime.today().weekday()
    conn = sqlite3.connect(DB_NAME)
    query = f"""
        SELECT strftime('%H', last_updated) as hour, AVG(wait_time) as avg_wait
        FROM wait_times
        WHERE ride_name = ? AND cast(strftime('%w', last_updated) as int) = ?
        AND last_updated > date('now', '-90 days')
        GROUP BY hour ORDER BY hour
    """
    df = pd.read_sql_query(query, conn, params=(ride, day_of_week))
    conn.close()
    return df

def calculate_crowd_score(date_obj, park):
    """
    The 'Heuristic Brain' - Calculates a 1-10 score based on rules.
    """
    score = 3.0 # Base score
    
    # 1. Seasonality
    month = date_obj.month
    if month in [9]: score -= 2        # September is dead (Hurricane/School)
    elif month in [1, 2]: score -= 1   # Jan/Feb quiet
    elif month in [3, 4]: score += 2   # Spring Break
    elif month in [6, 7]: score += 2   # Summer
    elif month in [12]: score += 3     # Christmas season
    
    # 2. Weekend Bump
    if date_obj.weekday() >= 5: # Sat/Sun
        score += 2
    elif date_obj.weekday() == 4: # Friday
        score += 1

    # 3. Holiday Nuke (Automatic High Scores)
    us_holidays = holidays.US(years=[date_obj.year])
    if date_obj in us_holidays:
        score += 4 # Massive bump for actual holidays
    
    # Check for adjacent holiday days (e.g., day after Thanksgiving)
    for h_date in us_holidays:
        delta = (date_obj - h_date).days
        if abs(delta) <= 2 and abs(delta) > 0:
            score += 2

    # 4. Park Specific Bias
    if park == "Magic Kingdom": score += 1
    if park == "Animal Kingdom": score -= 1 # Usually falls off faster
    
    # Clamp score 1-10
    return max(1, min(10, int(score)))

# --- 4. UI: HEADER ---
# Simple park selector at top
parks = ["Magic Kingdom", "Epcot", "Hollywood Studios", "Animal Kingdom"]
selected_park = st.radio("Park", parks, horizontal=True, label_visibility="collapsed")

# --- 5. UI: CROWD CALENDAR (FUTURE) ---
with st.expander("📅 Future Crowd Calendar", expanded=False):
    c_date = st.date_input("Check Date", datetime.date.today() + datetime.timedelta(days=1))
    
    if c_date:
        score = calculate_crowd_score(c_date, selected_park)
        
        # Determine Color/Label
        if score <= 4:
            css_class = "crowd-low"
            label = "LIGHT CROWDS"
            desc = "Great day to visit. Walk-ons likely."
        elif score <= 7:
            css_class = "crowd-med"
            label = "MODERATE"
            desc = "Standard wait times. Use Genie+."
        elif score <= 9:
            css_class = "crowd-high"
            label = "HEAVY"
            desc = "Crowded. Plan carefully."
        else:
            css_class = "crowd-max"
            label = "MAX CAPACITY"
            desc = "Pack your patience. It's chaos."
            
        # Display Card
        st.markdown(f"""
            <div class="plan-card" style="text-align:center;">
                <div style="font-size:1rem; color:#888;">CROWD LEVEL</div>
                <div class="{css_class}">{score}/10</div>
                <div style="font-weight:bold; color:#555;">{label}</div>
                <div style="font-size:0.9rem; margin-top:5px; color:#666;">{desc}</div>
            </div>
        """, unsafe_allow_html=True)

# --- 6. UI: TODAY'S PLANNER ---
st.markdown("### Today's Action Plan")

# Filter Rides
PARK_RIDES = {
    "Magic Kingdom": ["Seven Dwarfs Mine Train", "Space Mountain", "Big Thunder Mountain Railroad", "Haunted Mansion", "Pirates of the Caribbean", "TRON Lightcycle / Run"],
    "Epcot": ["Guardians of the Galaxy: Cosmic Rewind", "Remy's Ratatouille Adventure", "Frozen Ever After", "Test Track", "Soarin' Around the World"],
    "Hollywood Studios": ["Star Wars: Rise of the Resistance", "Slinky Dog Dash", "The Twilight Zone Tower of Terror", "Rock 'n' Roller Coaster Starring Aerosmith", "Mickey & Minnie's Runaway Railway"],
    "Animal Kingdom": ["Avatar Flight of Passage", "Na'vi River Journey", "Expedition Everest - Legend of the Forbidden Mountain", "Kilimanjaro Safaris"]
}
rides = PARK_RIDES.get(selected_park, [])
selected_ride = st.selectbox("Attraction", rides)

if selected_ride:
    current = get_live_wait(selected_ride)
    curve = get_typical_curve(selected_ride)
    
    if not curve.empty:
        curve['hour'] = curve['hour'].astype(int)
        
        # Verdict Logic
        hour_now = datetime.datetime.now().hour
        typical = curve[curve['hour'] == hour_now]['avg_wait'].mean()
        if pd.isna(typical): typical = current
        
        diff = current - typical
        
        st.markdown(f"<div class='plan-card'>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.metric("Wait Now", f"{current}m")
        c2.metric("Typical", f"{int(typical)}m")
        
        st.write("---")
        
        if diff < -5:
            st.markdown(f"<div class='v-go'>✅ GO NOW</div>", unsafe_allow_html=True)
            st.caption(f"Saving {int(abs(diff))} mins vs usual.")
        elif diff > 10:
            st.markdown(f"<div class='v-wait'>🛑 WAIT</div>", unsafe_allow_html=True)
            st.caption(f"Wait is {int(diff)} mins higher than normal.")
        else:
            st.write("⚖️ Normal Traffic")
            
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Simple Forecast Chart
        st.caption("Rest of Day Forecast")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=curve['hour'], y=curve['avg_wait'], marker_color='#ddd'))
        fig.add_trace(go.Bar(x=[hour_now], y=[current], marker_color='#2196F3'))
        fig.update_layout(height=150, margin=dict(l=0,r=0,t=0,b=0), xaxis=dict(showgrid=False), yaxis=dict(showgrid=False), paper_bgcolor='white', plot_bgcolor='white', showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
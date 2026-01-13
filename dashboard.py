import streamlit as st
import pandas as pd
import plotly.express as px
import time
# --- THE FIX IS HERE ---
from database import engine, Base, SessionLocal
from schemas import WaitTime
# -----------------------

# Ensure database tables exist
Base.metadata.create_all(bind=engine)

# Configuration
st.set_page_config(
    page_title="Disney Omni-Tracker",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_data():
    """
    Load data from database with error handling and empty data fallback.
    """
    try:
        # Try to load data from database
        query = "SELECT ride_name, wait_time, park_name, last_updated FROM wait_times ORDER BY last_updated DESC"
        df = pd.read_sql(query, engine)
        
        # Return empty DataFrame with correct columns if no data
        if df.empty:
            return pd.DataFrame(columns=['ride_name', 'wait_time', 'park_name', 'last_updated'])
        
        return df
    except Exception as e:
        # Return empty DataFrame if anything fails
        st.error(f"Database error: {e}")
        return pd.DataFrame(columns=['ride_name', 'wait_time', 'park_name', 'last_updated'])

def get_latest_data(df):
    """
    Get the latest wait time for each ride.
    """
    if df.empty:
        return df
    
    # Convert last_updated to datetime if it's not already
    df['last_updated'] = pd.to_datetime(df['last_updated'])
    
    # Get the latest record for each ride
    latest_data = df.loc[df.groupby('ride_name')['last_updated'].idxmax()]
    return latest_data

def main():
    st.title("🏰 Disney Omni-Tracker")
    st.markdown("Real-time wait times with AI-powered recommendations")
    
    # Load data
    df = load_data()
    
    # Sidebar with manual refresh
    st.sidebar.header("Controls")
    
    if st.sidebar.button('🔄 Force Update Data'):
        with st.spinner('Fetching fresh data from Disney...'):
            try:
                import scraper
                scraper.run_scraper_job()
                st.success('Data updated!')
                st.rerun()
            except Exception as e:
                st.error(f'Error updating data: {e}')
    
    # Handle empty data case
    if df.empty:
        st.warning('⚠️ Database is empty. Click "Force Update Data" in the sidebar to start!')
        return
    
    # Get latest data for each ride
    latest_data = get_latest_data(df)
    
    if latest_data.empty:
        st.warning('⚠️ No recent data available. Click "Force Update Data" in the sidebar to refresh!')
        return
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Get unique parks
    parks = sorted(latest_data['park_name'].unique())
    selected_park = st.sidebar.selectbox(
        "Select Park",
        options=parks,
        index=0 if len(parks) > 0 else None
    )
    
    # Filter for selected park
    park_data = latest_data[latest_data['park_name'] == selected_park].copy()
    
    # Park header
    st.header(f"🎢 {selected_park}")
    
    # Sort by wait time (ascending - shortest waits first)
    park_data = park_data.sort_values('wait_time', ascending=True)
    
    # Display metrics
    total_rides = len(park_data)
    avg_wait = park_data['wait_time'].mean()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Rides", total_rides)
    with col2:
        st.metric("Average Wait", f"{avg_wait:.1f} min")
    with col3:
        open_rides = len(park_data[park_data['wait_time'] > 0])
        st.metric("Rides with Waits", open_rides)
    
    # Tile grid display
    st.subheader("🎯 Ride Wait Times")
    
    # Create tile grid (3 columns)
    cols = st.columns(3)
    for i, (_, ride) in enumerate(park_data.iterrows()):
        with cols[i % 3]:
            # Card container
            with st.container():
                # Ride name
                st.subheader(ride['ride_name'])
                
                # Wait time with color coding
                wait_time = ride['wait_time']
                if wait_time == 0:
                    st.success("⚡ No Wait!")
                elif wait_time <= 15:
                    st.info(f"⏱️ {wait_time} min")
                elif wait_time <= 30:
                    st.warning(f"⏱️ {wait_time} min")
                else:
                    st.error(f"⏱️ {wait_time} min")
                
                # Park name
                st.caption(f"📍 {ride['park_name']}")
                
                # Last updated
                if 'last_updated' in ride and pd.notna(ride['last_updated']):
                    time_ago = pd.Timestamp.now() - pd.to_datetime(ride['last_updated'])
                    if time_ago.total_seconds() < 3600:
                        st.caption(f"🕐 Updated {int(time_ago.total_seconds()/60)} min ago")
                    else:
                        st.caption(f"🕐 Updated {int(time_ago.total_seconds()/3600)} hours ago")

if __name__ == "__main__":
    main()

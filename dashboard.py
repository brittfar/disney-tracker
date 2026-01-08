import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sqlite3
import prediction
import styles
from database import engine, Base
from schemas import WaitTime

# Apply mobile CSS styling
st.markdown(styles.MOBILE_CSS, unsafe_allow_html=True)

# Database self-healing - ensure tables exist
Base.metadata.create_all(bind=engine)

# Configuration
st.set_page_config(
    page_title="Disney Omni-Tracker",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_data():
    """
    Load data from SQLite database using Pandas.
    Converts timestamp column to datetime objects.
    """
    try:
        # Connect to database and load all data
        conn = sqlite3.connect('disney.db')
        df = pd.read_sql("SELECT * FROM wait_times", conn)
        conn.close()
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

def main():
    """
    Main dashboard function with all visualizations.
    """
    st.title("🏰 Disney World Wait Time Dashboard")
    
    # Load data
    df = load_data()
    
    if df.empty:
        st.warning("No data available. Please run the scraper first using: python scraper.py")
        return
    
    # Sidebar filter for park selection
    st.sidebar.header("Filters")
    
    # Manual refresh button
    if st.sidebar.button('🔄 Force Update Data'):
        with st.spinner('Fetching fresh data from Disney...'):
            try:
                import scraper
                scraper.run_scraper_job()
                st.success('Data updated!')
                st.rerun()
            except Exception as e:
                st.error(f'Error updating data: {e}')
    
    # Get unique parks
    parks = sorted(df['park_name'].unique())
    selected_park = st.sidebar.selectbox(
        "Select Park",
        options=parks,
        index=0 if len(parks) > 0 else None
    )
    
    # Filter dataframe for selected park
    park_data = df[df['park_name'] == selected_park].copy()
    
    if park_data.empty:
        st.warning(f"No data available for {selected_park}")
        return
    
    # Display metrics
    st.header("📊 Park Metrics")
    
    # Calculate metrics
    avg_wait = park_data['wait_time'].mean()
    most_crowded_ride = park_data.loc[park_data['wait_time'].idxmax()]
    
    # Display metric cards
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            label="Average Wait Time",
            value=f"{avg_wait:.1f} minutes",
            delta=None
        )
    
    with col2:
        if not pd.isna(most_crowded_ride['wait_time']):
            st.metric(
                label="Most Crowded Ride",
                value=most_crowded_ride['ride_name'],
                delta=f"{most_crowded_ride['wait_time']} min wait"
            )
        else:
            st.metric(
                label="Most Crowded Ride",
                value="No data",
                delta=None
            )
    
    # AI Predictions Status
    st.header("🤖 AI Predictions")
    model, label_encoder, df = prediction.train_and_predict(selected_park, future_minutes=60)
    
    if model is not None:
        st.success("✅ AI predictions available for this park")
    else:
        st.warning("🔄 Gathering more data for predictions...")
    
    # Ride Recommendations Table
    st.header("🎢 Ride Recommendations")
    
    # Get latest data for each ride
    latest_data = park_data.sort_values('timestamp').groupby('ride_name').tail(1).copy()
    
    # Add AI recommendations
    recommendations = []
    for _, ride in latest_data.iterrows():
        recommendation = prediction.get_ride_recommendation(
                selected_park, 
                ride['ride_name'], 
                ride['wait_time']
            )
        # Convert ASCII back to emojis for display
        if '[GREEN]' in recommendation:
            recommendation = recommendation.replace('[GREEN]', '🟢')
        elif '[RED]' in recommendation:
            recommendation = recommendation.replace('[RED]', '🔴')
        elif '[YELLOW]' in recommendation:
            recommendation = recommendation.replace('[YELLOW]', '🟡')
        elif '[LOADING]' in recommendation:
            recommendation = recommendation.replace('[LOADING]', '🔄')
        recommendations.append(recommendation)
    
    latest_data['AI Recommendation'] = recommendations
    
    # Create new columns for better visualization
    latest_data['Advice'] = latest_data['AI Recommendation']
    latest_data['Wait'] = latest_data['wait_time']
    latest_data['Crowd Level'] = latest_data['wait_time']
    
    # Sort by recommendation priority (GO first, then NEUTRAL, then WAIT, then GATHERING DATA)
    def sort_priority(rec):
        if '🟢 GO' in rec:
            return 0
        elif '🟡 NEUTRAL' in rec:
            return 1
        elif '🔴 WAIT' in rec:
            return 2
        else:
            return 3
    
    latest_data['sort_priority'] = latest_data['Advice'].apply(sort_priority)
    latest_data = latest_data.sort_values('sort_priority').drop('sort_priority', axis=1)
    
    # Display data as tile grid
    st.header("🎢 Ride Recommendations")
    
    for index, row in latest_data.iterrows():
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.subheader(row['ride_name'])
                st.caption(row['Advice'])
            
            with col2:
                # Determine delta and delta color based on advice
                if '🟢 GO' in row['Advice']:
                    delta_text = "🟢 GO"
                    delta_color = "inverse"
                elif '🔴 WAIT' in row['Advice']:
                    delta_text = "🔴 WAIT"
                    delta_color = "inverse"
                else:
                    delta_text = ""
                    delta_color = "normal"
                
                st.metric(
                    label="Wait Time",
                    value=f"{row['Wait']} min",
                    delta=delta_text,
                    delta_color=delta_color
                )

# Run dashboard
if __name__ == "__main__":
    main()

# To run this dashboard:
# streamlit run dashboard.py

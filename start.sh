#!/bin/bash
# Run database initializer (using standard python)
echo "Initializing Database..."
python init_db.py

# Start background scheduler
echo "Starting Scheduler..."
python scheduler.py &

# Start Dashboard (using standard streamlit)
echo "Starting Dashboard..."
streamlit run dashboard.py --server.port $PORT --server.address 0.0.0.0

#!/bin/bash
echo "Initializing Database..."
python init_db.py
echo "Starting Scheduler..."
python scheduler.py &
echo "Starting Dashboard..."
python -m streamlit run dashboard.py --server.port $PORT --server.address 0.0.0.0

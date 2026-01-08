#!/bin/bash
echo "Starting Scheduler..."
python scheduler.py &
echo "Starting Dashboard..."
streamlit run dashboard.py --server.port $PORT --server.address 0.0.0.0

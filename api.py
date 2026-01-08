from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List

from database import get_db, WaitTime
from schemas import RideSchema, ParkSchema

# Initialize FastAPI app
app = FastAPI(
    title="Disney World Wait Time API",
    description="REST API for Disney World ride wait times",
    version="1.0.0"
)

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_model=dict)
async def root():
    """
    Root endpoint to check if API is running.
    """
    return {"status": "Disney API is running"}

@app.get("/parks", response_model=List[ParkSchema])
async def get_parks(db: Session = Depends(get_db)):
    """
    Get list of all unique park names in the database.
    """
    try:
        # Query distinct park names
        parks = db.query(WaitTime.park_name).distinct().all()
        park_list = [ParkSchema(park_name=park[0]) for park in parks]
        return park_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/parks/{park_name}/waittimes", response_model=List[RideSchema])
async def get_park_wait_times(park_name: str, db: Session = Depends(get_db)):
    """
    Get the latest wait time record for every ride in a specific park.
    Returns only the most recent record for each ride (not all historical data).
    """
    try:
        # Subquery to find the most recent timestamp for each ride in the park
        latest_times = db.query(
            WaitTime.ride_name,
            func.max(WaitTime.timestamp).label('max_timestamp')
        ).filter(
            WaitTime.park_name == park_name
        ).group_by(
            WaitTime.ride_name
        ).subquery()
        
        # Main query to get the complete records for the latest times
        latest_records = db.query(WaitTime).join(
            latest_times,
            (WaitTime.ride_name == latest_times.c.ride_name) & 
            (WaitTime.timestamp == latest_times.c.max_timestamp)
        ).filter(
            WaitTime.park_name == park_name
        ).all()
        
        if not latest_records:
            raise HTTPException(
                status_code=404, 
                detail=f"No wait times found for park: {park_name}"
            )
        
        return latest_records
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# To run this API server:
# 1. Make sure you're in the virtual environment: venv\Scripts\activate
# 2. Run: uvicorn api:app --reload --host 0.0.0.0 --port 8000
# 3. Visit http://localhost:8000/docs for interactive API documentation
# 4. Visit http://localhost:8000 for root endpoint

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

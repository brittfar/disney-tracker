from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class RideSchema(BaseModel):
    """
    Pydantic model for ride wait time data.
    Hides internal database ID and formats output nicely.
    """
    ride_name: str
    park_name: str
    wait_time: int
    is_open: bool
    timestamp: datetime
    
    class Config:
        from_attributes = True

class ParkSchema(BaseModel):
    """
    Pydantic model for park names.
    """
    park_name: str
    
    class Config:
        from_attributes = True

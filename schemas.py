from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean
from database import Base

class WaitTime(Base):
    __tablename__ = "wait_times"

    id = Column(Integer, primary_key=True, index=True)
    ride_name = Column(String, index=True)
    wait_time = Column(Integer)
    status = Column(String)
    last_updated = Column(DateTime)
    park_name = Column(String)

class WeatherHistory(Base):
    __tablename__ = "weather_history"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, index=True)
    temperature = Column(Float)
    precipitation = Column(Float)
    is_rainy = Column(Boolean)  # True if precipitation > 0.5
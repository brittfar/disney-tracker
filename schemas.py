from sqlalchemy import Column, Integer, String, DateTime
from database import Base

class WaitTime(Base):
    __tablename__ = "wait_times"
    id = Column(Integer, primary_key=True, index=True)
    ride_name = Column(String, index=True)
    wait_time = Column(Integer)
    status = Column(String)
    last_updated = Column(DateTime)
    park_name = Column(String)

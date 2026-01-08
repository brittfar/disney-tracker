import sqlite3
import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class WaitTime(Base):
    __tablename__ = 'wait_times'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ride_name = Column(String)
    park_name = Column(String)
    wait_time = Column(Integer)
    is_open = Column(Boolean)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Database setup with cloud support
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL:
    # Fix Render URL format for SQLAlchemy compatibility
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    # Use PostgreSQL cloud database
    print(f"Using cloud database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'PostgreSQL'}")
    engine = create_engine(DATABASE_URL)
else:
    # Fall back to local SQLite database
    print("Using local SQLite database: disney.db")
    engine = create_engine('sqlite:///disney.db')

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def setup_database():
    Base.metadata.create_all(bind=engine)
    return engine

def get_session():
    engine = setup_database()
    Session = sessionmaker(bind=engine)
    return Session()

def get_db():
    """
    Dependency function for FastAPI to get database session.
    Ensures proper session handling for each request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    engine = setup_database()
    db_type = "cloud database" if DATABASE_URL else "local SQLite database"
    print(f"Database setup complete. {db_type} configured with wait_times table.")

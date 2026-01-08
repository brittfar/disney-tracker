from database import engine, Base
from schemas import WaitTime

if __name__ == '__main__':
    print("Resetting database...")
    # DROP old table to force a schema update
    try:
        WaitTime.__table__.drop(engine)
        print("Old table dropped.")
    except:
        pass # Table didn't exist yet
    
    # Create new table with correct columns
    Base.metadata.create_all(bind=engine)
    print("New tables created successfully!")

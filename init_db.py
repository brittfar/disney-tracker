from database import engine, Base
from schemas import WaitTime

if __name__ == '__main__':
    print("Checking database...")
    Base.metadata.create_all(bind=engine)
    print("Database ready (Existing data preserved).")

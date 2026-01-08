from database import engine, Base
from schemas import WaitTime

if __name__ == '__main__':
    Base.metadata.create_all(bind=engine)
    print('Database tables created successfully.')

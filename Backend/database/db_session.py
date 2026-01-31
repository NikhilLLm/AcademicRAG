import os
from sqlalchemy import create_engine
from Backend.database.tables import Base
from sqlalchemy.orm import sessionmaker
# Get the path to 'Backend/database' folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "sql_database.db")

# Use 4 slashes for absolute path on Windows
engine = create_engine(f"sqlite:///{db_path}")

# Create all Tables
Base.metadata.create_all(engine)

#Creating Utility Function for Session


def get_session():
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


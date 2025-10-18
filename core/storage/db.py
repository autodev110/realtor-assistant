import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env file (if you created one)
# We fall back to the SQLite default if the env var isn't set, 
# though it's best practice to use os.getenv in a real project
load_dotenv()
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./realtor.db")

# 1. Create the SQLAlchemy Engine
# The connect_args are only needed for SQLite to allow multiple threads 
# (required by FastAPI/Uvicorn workers) to access the same DB connection.
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 2. Create the SessionLocal class
# This session will be used to handle database connections during a request.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Import Base from models.py for schema setup
from .models import Base 

# 4. Create database tables
# This step is essential for the quickstart using SQLite.
# For production/Postgres with Docker, this is often done separately 
# or via an init script, but we keep it here for the MVP run.
def create_db_and_tables():
    # Only creates tables if they don't exist
    Base.metadata.create_all(bind=engine)
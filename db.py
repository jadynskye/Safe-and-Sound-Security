# backend/db.py

# Import the SQLAlchemy tools I need
#I'm learning this as a go so I will add as many comments as needed to remember 
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Database's location
SQLALCHEMY_DATABASE_URL = "sqlite:///./safeandsound.db"

# Create  database engine (connecting to SQLite)
# connect_args so multiple threads don't crash
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# SessionLocal to talk to the database
# autocommit=False to call commit myself
# autoflush=False to not push changes until I commit
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base = "blueprint" that all my tables will inherit from
Base = declarative_base()
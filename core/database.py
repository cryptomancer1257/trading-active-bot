import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database configuration from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Use SQLite for local development (easier setup)
    SQLALCHEMY_DATABASE_URL = "sqlite:///./bot_marketplace.db"
else:
    SQLALCHEMY_DATABASE_URL = DATABASE_URL

# Configure connection pool for high concurrency
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=20,           # Increase from default 5 to 20
    max_overflow=40,        # Increase from default 10 to 40
    pool_timeout=60,        # Increase timeout from 30 to 60 seconds
    pool_recycle=3600,      # Recycle connections after 1 hour
    pool_pre_ping=True      # Verify connections before using
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
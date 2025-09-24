#!/usr/bin/env python3
"""
Initialize database with tables
"""
from core.database import engine, Base
from core import models

def init_database():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine, checkfirst=True)
    print("✅ Database tables created successfully!")

if __name__ == "__main__":
    init_database()

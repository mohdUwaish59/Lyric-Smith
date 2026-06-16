#!/usr/bin/env python3
"""
init_db.py - Initialize the database tables
"""

from database import engine, Base
from models import Session, Message, Song

def init_database():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully!")

if __name__ == "__main__":
    init_database()

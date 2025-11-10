"""
Initialize database tables.
Run this script to create all database tables.
"""
from app.db import Base, engine
from app import models

if __name__ == "__main__":
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


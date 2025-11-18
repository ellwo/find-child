"""
Initialize database tables and create default system user.
Run this script to create all database tables and initialize default user.
"""
import os
from dotenv import load_dotenv
from app.db import Base, engine, SessionLocal
from app import models
from app.auth import get_password_hash
from app import crud

load_dotenv()

def init_default_system_user():
    """Create default system user if it doesn't exist."""
    db = SessionLocal()
    try:
        system_username = os.getenv("SYSTEM_USER_USERNAME", "admin")
        system_email = os.getenv("SYSTEM_USER_EMAIL", "admin@example.com")
        system_password = os.getenv("SYSTEM_USER_PASSWORD", "admin123")
        
        # Check if user already exists
        existing_user = crud.get_user_by_username(db, system_username)
        if existing_user:
            print(f"System user '{system_username}' already exists, skipping creation.")
            return
        
        # Create default system user
        # Truncate password if too long (bcrypt limit is 72 bytes)
        if len(system_password.encode('utf-8')) > 72:
            system_password = system_password[:72]
            print(f"Warning: Password truncated to 72 bytes")
        
        hashed_password = get_password_hash(system_password)
        crud.create_user(
            db=db,
            username=system_username,
            email=system_email,
            hashed_password=hashed_password,
            is_system_user=True
        )
        print(f"Default system user '{system_username}' created successfully!")
        print(f"Username: {system_username}")
        print(f"Email: {system_email}")
        print(f"Password: {system_password}")
        print("Please change the default password after first login!")
    except Exception as e:
        print(f"Error creating default system user: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
    
    print("\nInitializing default system user...")
    init_default_system_user()
    print("\nDatabase initialization completed!")


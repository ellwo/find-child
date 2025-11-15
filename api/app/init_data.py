"""
Initialize database with default data (admin user, system settings).
Run this script once after database setup.
"""
import os
from sqlalchemy.orm import Session
from app.db import SessionLocal, engine
from app import models, schemas, auth, crud


def init_default_data():
    """Initialize default data."""
    db: Session = SessionLocal()
    try:
        # Create system settings if not exists
        settings = crud.get_system_settings(db)
        if not settings:
            default_settings = schemas.SystemSettingsBase(
                school_name="مدرسة النموذج",
                school_address="",
                school_latitude=None,
                school_longitude=None,
                default_morning_start="06:00",
                default_morning_end="10:00",
                default_afternoon_start="12:30",
                default_afternoon_end="15:00",
                attendance_interval_minutes=5,
                attendance_similarity_threshold=0.9,
                max_daily_attendances=2,
                websocket_enabled=True
            )
            crud.create_system_settings(db, default_settings)
            print("✓ System settings created")
        else:
            # Update existing settings to add new fields if they don't exist
            try:
                if not hasattr(settings, 'attendance_similarity_threshold') or settings.attendance_similarity_threshold is None:
                    settings.attendance_similarity_threshold = 0.9
                if not hasattr(settings, 'max_daily_attendances') or settings.max_daily_attendances is None:
                    settings.max_daily_attendances = 2
                db.commit()
                print("✓ System settings updated with new fields")
            except Exception as e:
                print(f"Note: Could not update settings fields (may need migration): {str(e)}")
            print("✓ System settings already exist")
        
        # Create default admin user if not exists
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        admin_email = os.getenv("ADMIN_EMAIL", "admin@school.com")
        
        existing_admin = auth.get_user_by_username(db, admin_username)
        if not existing_admin:
            admin_user_data = schemas.UserCreate(
                username=admin_username,
                email=admin_email,
                phone=None,
                password=admin_password,
                role=models.UserRole.SYSTEM_ADMIN,
                is_active=True
            )
            try:
                admin_user = auth.create_user(db, admin_user_data)
                print(f"✓ Admin user created: {admin_username} / {admin_password}")
            except Exception as e:
                print(f"✗ Failed to create admin user: {str(e)}")
        else:
            print(f"✓ Admin user already exists: {admin_username}")
        
        db.commit()
        print("\n✓ Initialization complete!")
        
    except Exception as e:
        print(f"✗ Error during initialization: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    # Ensure all tables are created
    models.Base.metadata.create_all(bind=engine)
    print("Initializing default data...\n")
    init_default_data()



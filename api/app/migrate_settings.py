"""
Migration script to add new fields to SystemSettings table.
Run this once to update existing database.
"""
from sqlalchemy import text
from app.db import SessionLocal, engine

def migrate_settings():
    """Add new fields to system_settings table if they don't exist."""
    try:
        # Check if columns exist and add them if not
        with engine.begin() as conn:  # Use begin() for autocommit
            # Check for attendance_similarity_threshold
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='system_settings' 
                AND column_name='attendance_similarity_threshold'
            """))
            if not result.fetchone():
                print("Adding attendance_similarity_threshold column...")
                conn.execute(text("""
                    ALTER TABLE system_settings 
                    ADD COLUMN attendance_similarity_threshold FLOAT DEFAULT 0.9 NOT NULL
                """))
                print("✓ attendance_similarity_threshold added")
            else:
                print("✓ attendance_similarity_threshold already exists")
            
            # Check for max_daily_attendances
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='system_settings' 
                AND column_name='max_daily_attendances'
            """))
            if not result.fetchone():
                print("Adding max_daily_attendances column...")
                conn.execute(text("""
                    ALTER TABLE system_settings 
                    ADD COLUMN max_daily_attendances INTEGER DEFAULT 2 NOT NULL
                """))
                print("✓ max_daily_attendances added")
            else:
                print("✓ max_daily_attendances already exists")
            
            # Update existing records with default values if needed
            conn.execute(text("""
                UPDATE system_settings 
                SET attendance_similarity_threshold = 0.9 
                WHERE attendance_similarity_threshold IS NULL
            """))
            conn.execute(text("""
                UPDATE system_settings 
                SET max_daily_attendances = 2 
                WHERE max_daily_attendances IS NULL
            """))
            
        print("\n✓ Migration complete!")
        
    except Exception as e:
        print(f"✗ Error during migration: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Running database migration...\n")
    migrate_settings()


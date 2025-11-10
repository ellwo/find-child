"""
Utility functions for file handling, date parsing, etc.
"""
import os
import random
import string
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional


def generate_random_string(length: int = 8) -> str:
    """Generate a random string of given length."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def get_storage_path() -> str:
    """Get the storage path from environment variable."""
    return os.getenv("STORAGE_PATH", "/data/storage")


def save_face_image(image_data: bytes, camera_id: str, timestamp: Optional[datetime] = None) -> str:
    """
    Save face image to storage with organized directory structure.
    Returns the relative file path.
    """
    if timestamp is None:
        timestamp = datetime.utcnow()
    
    storage_base = get_storage_path()
    # Create path: faces/YYYY/MM/DD/camera_id/HHMMSS_random.jpg
    year = timestamp.strftime("%Y")
    month = timestamp.strftime("%M")
    day = timestamp.strftime("%d")
    time_str = timestamp.strftime("%H%M%S")
    random_str = generate_random_string(8)
    
    file_dir = Path(storage_base) / "faces" / year / month / day / camera_id
    file_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{time_str}_{random_str}.jpg"
    file_path = file_dir / filename
    
    with open(file_path, "wb") as f:
        f.write(image_data)
    
    # Return relative path from storage base
    relative_path = str(file_path.relative_to(storage_base))
    return relative_path


def get_image_url(file_path: str) -> str:
    """
    Convert file path to public URL for serving static files.
    Assumes files are served at /storage/...
    """
    # Ensure path uses forward slashes
    normalized_path = file_path.replace("\\", "/")
    if not normalized_path.startswith("/"):
        normalized_path = "/" + normalized_path
    return f"/storage{normalized_path}"


def parse_date(date_str: Optional[str]) -> Optional[date]:
    """Parse YYYY-MM-DD date string."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None


def get_today_utc() -> date:
    """Get today's date in UTC."""
    return datetime.utcnow().date()


def parse_iso_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO-8601 datetime string."""
    if not dt_str:
        return None
    try:
        # Try parsing with timezone info
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        try:
            # Try without timezone
            return datetime.fromisoformat(dt_str)
        except ValueError:
            return None


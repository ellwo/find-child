"""
CRUD operations for database models.
"""
from datetime import datetime, date
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app import models, schemas


def get_camera_by_code(db: Session, code: str) -> Optional[models.Camera]:
    """Get camera by code."""
    return db.query(models.Camera).filter(models.Camera.code == code).first()


def create_or_update_camera(db: Session, code: str, name: Optional[str] = None) -> models.Camera:
    """Create or update camera record."""
    camera = get_camera_by_code(db, code)
    now = datetime.utcnow()
    
    if camera:
        # Update existing camera
        if name:
            camera.name = name
        camera.last_seen_ts = now
        camera.total_images += 1
    else:
        # Create new camera
        camera = models.Camera(
            code=code,
            name=name,
            first_seen_ts=now,
            last_seen_ts=now,
            total_images=1
        )
        db.add(camera)
    
    db.commit()
    db.refresh(camera)
    return camera


def create_captured_image(
    db: Session,
    camera_id: str,
    camera_name: Optional[str],
    timestamp: datetime,
    file_path: str,
    compreface_face_id: Optional[str] = None
) -> models.CapturedImage:
    """Create a captured image record."""
    image = models.CapturedImage(
        camera_id=camera_id,
        camera_name=camera_name,
        timestamp=timestamp,
        file_path=file_path,
        compreface_face_id=compreface_face_id
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


def update_captured_image_compreface_id(
    db: Session,
    image_id: int,
    compreface_face_id: str
) -> Optional[models.CapturedImage]:
    """Update compreface_face_id for a captured image."""
    image = db.query(models.CapturedImage).filter(models.CapturedImage.id == image_id).first()
    if image:
        image.compreface_face_id = compreface_face_id
        db.commit()
        db.refresh(image)
    return image


def get_images_by_compreface_ids(
    db: Session,
    compreface_face_ids: List[str],
    start_ts: Optional[datetime] = None,
    end_ts: Optional[datetime] = None
) -> List[models.CapturedImage]:
    """Get images by CompreFace face IDs, optionally filtered by timestamp range."""
    query = db.query(models.CapturedImage).filter(
        models.CapturedImage.compreface_face_id.in_(compreface_face_ids)
    )
    
    if start_ts:
        query = query.filter(models.CapturedImage.timestamp >= start_ts)
    if end_ts:
        query = query.filter(models.CapturedImage.timestamp <= end_ts)
    
    return query.all()


def get_images_by_date_range(
    db: Session,
    start_date: date,
    end_date: date,
    camera_ids: Optional[List[str]] = None,
    skip: int = 0,
    limit: int = 20
) -> Tuple[List[models.CapturedImage], int]:
    """Get images by date range with optional camera filter and pagination."""
    # Convert dates to datetime ranges (start of day to end of day in UTC)
    start_ts = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=None)
    end_ts = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=None)
    
    query = db.query(models.CapturedImage).filter(
        and_(
            models.CapturedImage.timestamp >= start_ts,
            models.CapturedImage.timestamp <= end_ts
        )
    )
    
    if camera_ids:
        query = query.filter(models.CapturedImage.camera_id.in_(camera_ids))
    
    total = query.count()
    
    images = query.order_by(models.CapturedImage.timestamp.desc()).offset(skip).limit(limit).all()
    
    return images, total


def get_all_cameras(db: Session) -> List[models.Camera]:
    """Get all registered cameras."""
    return db.query(models.Camera).order_by(models.Camera.code).all()


def get_image_by_id(db: Session, image_id: int) -> Optional[models.CapturedImage]:
    """Get captured image by ID."""
    return db.query(models.CapturedImage).filter(models.CapturedImage.id == image_id).first()


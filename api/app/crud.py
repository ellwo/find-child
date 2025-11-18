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
    compreface_face_id: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    place_name: Optional[str] = None,
    description: Optional[str] = None
) -> models.CapturedImage:
    """Create a captured image record."""
    image = models.CapturedImage(
        camera_id=camera_id,
        camera_name=camera_name,
        timestamp=timestamp,
        file_path=file_path,
        compreface_face_id=compreface_face_id,
        latitude=latitude,
        longitude=longitude,
        place_name=place_name,
        description=description
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


# User CRUD operations
def create_user(
    db: Session,
    username: str,
    email: str,
    hashed_password: str,
    is_system_user: bool = False
) -> models.User:
    """Create a new user."""
    user = models.User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        is_system_user=is_system_user,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """Get user by username."""
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Get user by email."""
    return db.query(models.User).filter(models.User.email == email).first()


# Missing Report CRUD operations
def generate_report_number(db: Session) -> str:
    """Generate a unique report number in format REP-YYYY-XXXX."""
    current_year = datetime.utcnow().year
    
    # Get the last report number for this year
    last_report = db.query(models.MissingReport).filter(
        models.MissingReport.report_number.like(f"REP-{current_year}-%")
    ).order_by(models.MissingReport.report_number.desc()).first()
    
    if last_report:
        # Extract the number part and increment
        try:
            last_number = int(last_report.report_number.split("-")[-1])
            next_number = last_number + 1
        except (ValueError, IndexError):
            next_number = 1
    else:
        next_number = 1
    
    return f"REP-{current_year}-{next_number:04d}"


def create_missing_report(
    db: Session,
    reporter_name: str,
    reporter_email: str,
    reporter_phone: str,
    child_name: str,
    child_photo_path: str,
    child_compreface_face_id: Optional[str] = None,
    created_by_user_id: Optional[int] = None
) -> models.MissingReport:
    """Create a new missing report."""
    report_number = generate_report_number(db)
    
    report = models.MissingReport(
        report_number=report_number,
        reporter_name=reporter_name,
        reporter_email=reporter_email,
        reporter_phone=reporter_phone,
        child_name=child_name,
        child_photo_path=child_photo_path,
        child_compreface_face_id=child_compreface_face_id,
        status=models.ReportStatus.OPEN,
        created_by_user_id=created_by_user_id
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_missing_report_by_number(db: Session, report_number: str) -> Optional[models.MissingReport]:
    """Get missing report by report number."""
    return db.query(models.MissingReport).filter(
        models.MissingReport.report_number == report_number
    ).first()


def get_missing_report_by_phone_and_number(
    db: Session,
    phone: str,
    report_number: str
) -> Optional[models.MissingReport]:
    """Get missing report by phone and report number (for tracking)."""
    return db.query(models.MissingReport).filter(
        and_(
            models.MissingReport.reporter_phone == phone,
            models.MissingReport.report_number == report_number
        )
    ).first()


def get_open_reports(db: Session) -> List[models.MissingReport]:
    """Get all open reports."""
    return db.query(models.MissingReport).filter(
        models.MissingReport.status == models.ReportStatus.OPEN
    ).all()


def get_in_progress_reports(db: Session) -> List[models.MissingReport]:
    """Get all in-progress reports."""
    return db.query(models.MissingReport).filter(
        models.MissingReport.status == models.ReportStatus.IN_PROGRESS
    ).all()


def get_all_reports(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    status: Optional[models.ReportStatus] = None
) -> Tuple[List[models.MissingReport], int]:
    """Get all reports with optional status filter and pagination."""
    query = db.query(models.MissingReport)
    
    if status:
        query = query.filter(models.MissingReport.status == status)
    
    total = query.count()
    reports = query.order_by(models.MissingReport.created_at.desc()).offset(skip).limit(limit).all()
    
    return reports, total


def get_report_by_id(db: Session, report_id: int) -> Optional[models.MissingReport]:
    """Get report by ID."""
    return db.query(models.MissingReport).filter(models.MissingReport.id == report_id).first()


def update_report_status(
    db: Session,
    report_id: int,
    new_status: models.ReportStatus
) -> Optional[models.MissingReport]:
    """Update report status."""
    report = get_report_by_id(db, report_id)
    if report:
        report.status = new_status
        if new_status == models.ReportStatus.CLOSED:
            report.closed_at = datetime.utcnow()
        db.commit()
        db.refresh(report)
    return report


def close_report(db: Session, report_id: int) -> Optional[models.MissingReport]:
    """Close a report."""
    return update_report_status(db, report_id, models.ReportStatus.CLOSED)


def create_report_match(
    db: Session,
    report_id: int,
    captured_image_id: int,
    similarity_score: float,
    camera_id: str,
    camera_name: Optional[str] = None
) -> models.ReportMatch:
    """Create a report match record."""
    match = models.ReportMatch(
        report_id=report_id,
        captured_image_id=captured_image_id,
        similarity_score=similarity_score,
        camera_id=camera_id,
        camera_name=camera_name
    )
    db.add(match)
    
    # Update report status to in_progress if it's open
    report = get_report_by_id(db, report_id)
    if report and report.status == models.ReportStatus.OPEN:
        report.status = models.ReportStatus.IN_PROGRESS
    
    db.commit()
    db.refresh(match)
    return match


def get_report_matches(db: Session, report_id: int) -> List[models.ReportMatch]:
    """Get all matches for a report."""
    return db.query(models.ReportMatch).filter(
        models.ReportMatch.report_id == report_id
    ).order_by(models.ReportMatch.matched_at.desc()).all()


def update_report_match_notification(
    db: Session,
    match_id: int,
    external_api_called: bool = True
) -> Optional[models.ReportMatch]:
    """Update report match notification status."""
    match = db.query(models.ReportMatch).filter(models.ReportMatch.id == match_id).first()
    if match:
        match.external_api_called = external_api_called
        match.notified_at = datetime.utcnow()
        db.commit()
        db.refresh(match)
    return match


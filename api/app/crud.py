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


# System Settings CRUD
def get_system_settings(db: Session) -> Optional[models.SystemSettings]:
    """Get system settings (should only be one record)."""
    return db.query(models.SystemSettings).first()


def create_system_settings(db: Session, settings_data: schemas.SystemSettingsBase) -> models.SystemSettings:
    """Create system settings."""
    settings = models.SystemSettings(**settings_data.dict())
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


def update_system_settings(db: Session, settings_data: schemas.SystemSettingsBase) -> Optional[models.SystemSettings]:
    """Update system settings."""
    settings = get_system_settings(db)
    if not settings:
        return create_system_settings(db, settings_data)
    
    for key, value in settings_data.dict().items():
        setattr(settings, key, value)
    
    settings.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(settings)
    return settings


# GPS Tracker CRUD
def get_gps_tracker_by_device_id(db: Session, device_id: str) -> Optional[models.GPSTracker]:
    """Get GPS tracker by device ID."""
    return db.query(models.GPSTracker).filter(models.GPSTracker.device_id == device_id).first()


def get_gps_tracker_by_id(db: Session, tracker_id: int) -> Optional[models.GPSTracker]:
    """Get GPS tracker by ID."""
    return db.query(models.GPSTracker).filter(models.GPSTracker.id == tracker_id).first()


def get_all_gps_trackers(db: Session) -> List[models.GPSTracker]:
    """Get all GPS trackers."""
    return db.query(models.GPSTracker).order_by(models.GPSTracker.device_id).all()


def create_gps_tracker(db: Session, tracker_data: schemas.GPSTrackerCreate) -> models.GPSTracker:
    """Create a GPS tracker."""
    if get_gps_tracker_by_device_id(db, tracker_data.device_id):
        raise ValueError(f"GPS tracker with device_id {tracker_data.device_id} already exists")
    
    tracker = models.GPSTracker(**tracker_data.dict())
    db.add(tracker)
    db.commit()
    db.refresh(tracker)
    return tracker


def update_gps_tracker(db: Session, tracker_id: int, tracker_data: schemas.GPSTrackerBase) -> Optional[models.GPSTracker]:
    """Update GPS tracker."""
    tracker = get_gps_tracker_by_id(db, tracker_id)
    if not tracker:
        return None
    
    for key, value in tracker_data.dict().items():
        setattr(tracker, key, value)
    
    db.commit()
    db.refresh(tracker)
    return tracker


def update_gps_tracker_location(
    db: Session,
    device_id: str,
    latitude: float,
    longitude: float,
    timestamp: Optional[datetime] = None
) -> Optional[models.GPSTracker]:
    """Update GPS tracker location."""
    tracker = get_gps_tracker_by_device_id(db, device_id)
    if not tracker:
        return None
    
    tracker.last_latitude = latitude
    tracker.last_longitude = longitude
    tracker.last_update_timestamp = timestamp or datetime.utcnow()
    db.commit()
    db.refresh(tracker)
    return tracker


# Bus CRUD
def get_bus_by_id(db: Session, bus_id: int) -> Optional[models.Bus]:
    """Get bus by ID."""
    return db.query(models.Bus).filter(models.Bus.id == bus_id).first()


def get_bus_by_number(db: Session, bus_number: str) -> Optional[models.Bus]:
    """Get bus by bus number."""
    return db.query(models.Bus).filter(models.Bus.bus_number == bus_number).first()


def get_all_buses(db: Session, skip: int = 0, limit: int = 100) -> Tuple[List[models.Bus], int]:
    """Get all buses with pagination."""
    total = db.query(models.Bus).count()
    buses = db.query(models.Bus).offset(skip).limit(limit).all()
    return buses, total


def create_bus(db: Session, bus_data: schemas.BusCreate) -> models.Bus:
    """Create a bus."""
    if get_bus_by_number(db, bus_data.bus_number):
        raise ValueError(f"Bus with number {bus_data.bus_number} already exists")
    
    bus = models.Bus(**bus_data.dict())
    db.add(bus)
    db.commit()
    db.refresh(bus)
    return bus


def update_bus(db: Session, bus_id: int, bus_data: schemas.BusUpdate) -> Optional[models.Bus]:
    """Update bus."""
    bus = get_bus_by_id(db, bus_id)
    if not bus:
        return None
    
    update_data = bus_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(bus, key, value)
    
    bus.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(bus)
    return bus


def delete_bus(db: Session, bus_id: int) -> bool:
    """Delete bus."""
    bus = get_bus_by_id(db, bus_id)
    if not bus:
        return False
    
    db.delete(bus)
    db.commit()
    return True


# Student CRUD
def get_student_by_id(db: Session, student_id: int) -> Optional[models.Student]:
    """Get student by ID."""
    return db.query(models.Student).filter(models.Student.id == student_id).first()


def get_students_by_parent(db: Session, parent_id: int) -> List[models.Student]:
    """Get all students for a parent."""
    return db.query(models.Student).filter(models.Student.parent_id == parent_id).all()


def get_students_by_bus(db: Session, bus_id: int) -> List[models.Student]:
    """Get all students on a bus."""
    return db.query(models.Student).filter(models.Student.bus_id == bus_id).all()


def get_all_students(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    bus_id: Optional[int] = None,
    parent_id: Optional[int] = None
) -> Tuple[List[models.Student], int]:
    """Get all students with optional filters."""
    query = db.query(models.Student)
    
    if bus_id:
        query = query.filter(models.Student.bus_id == bus_id)
    if parent_id:
        query = query.filter(models.Student.parent_id == parent_id)
    
    total = query.count()
    students = query.offset(skip).limit(limit).all()
    return students, total


def create_student(db: Session, student_data: schemas.StudentCreate) -> models.Student:
    """Create a student."""
    student = models.Student(**student_data.dict())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def update_student(db: Session, student_id: int, student_data: schemas.StudentUpdate) -> Optional[models.Student]:
    """Update student."""
    student = get_student_by_id(db, student_id)
    if not student:
        return None
    
    update_data = student_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(student, key, value)
    
    student.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(student)
    return student


def delete_student(db: Session, student_id: int) -> bool:
    """Delete student."""
    student = get_student_by_id(db, student_id)
    if not student:
        return False
    
    db.delete(student)
    db.commit()
    return True


# Attendance CRUD
def create_attendance(
    db: Session,
    student_id: int,
    bus_id: int,
    detected_image_path: str,
    similarity_score: float,
    detected_at: datetime,
    gps_latitude: Optional[float] = None,
    gps_longitude: Optional[float] = None,
    gender_detected: Optional[models.Gender] = None
) -> models.Attendance:
    """Create an attendance record."""
    attendance = models.Attendance(
        student_id=student_id,
        bus_id=bus_id,
        detected_image_path=detected_image_path,
        similarity_score=similarity_score,
        detected_at=detected_at,
        gps_latitude=gps_latitude,
        gps_longitude=gps_longitude,
        gender_detected=gender_detected
    )
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return attendance


def get_last_attendance_by_student(db: Session, student_id: int) -> Optional[models.Attendance]:
    """Get last attendance record for a student."""
    return db.query(models.Attendance).filter(
        models.Attendance.student_id == student_id
    ).order_by(models.Attendance.detected_at.desc()).first()


def get_attendance_history(
    db: Session,
    student_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100
) -> Tuple[List[models.Attendance], int]:
    """Get attendance history for a student."""
    query = db.query(models.Attendance).filter(
        models.Attendance.student_id == student_id
    )
    
    if start_date:
        start_ts = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=None)
        query = query.filter(models.Attendance.detected_at >= start_ts)
    if end_date:
        end_ts = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=None)
        query = query.filter(models.Attendance.detected_at <= end_ts)
    
    total = query.count()
    attendances = query.order_by(models.Attendance.detected_at.desc()).offset(skip).limit(limit).all()
    return attendances, total


def get_attendances_today(db: Session) -> int:
    """Get count of attendances today."""
    today = datetime.utcnow().date()
    start_ts = datetime.combine(today, datetime.min.time()).replace(tzinfo=None)
    end_ts = datetime.combine(today, datetime.max.time()).replace(tzinfo=None)
    return db.query(models.Attendance).filter(
        and_(
            models.Attendance.detected_at >= start_ts,
            models.Attendance.detected_at <= end_ts
        )
    ).count()


# GPS Log CRUD
def create_gps_log(
    db: Session,
    tracker_id: int,
    latitude: float,
    longitude: float,
    timestamp: datetime,
    bus_id: Optional[int] = None,
    is_near_school: bool = False
) -> models.GPSLog:
    """Create a GPS log entry."""
    gps_log = models.GPSLog(
        tracker_id=tracker_id,
        bus_id=bus_id,
        latitude=latitude,
        longitude=longitude,
        timestamp=timestamp,
        is_near_school=is_near_school
    )
    db.add(gps_log)
    db.commit()
    db.refresh(gps_log)
    return gps_log


def get_gps_logs_by_tracker(
    db: Session,
    tracker_id: int,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000
) -> List[models.GPSLog]:
    """Get GPS logs for a tracker within time range."""
    query = db.query(models.GPSLog).filter(
        models.GPSLog.tracker_id == tracker_id
    )
    
    if start_time:
        query = query.filter(models.GPSLog.timestamp >= start_time)
    if end_time:
        query = query.filter(models.GPSLog.timestamp <= end_time)
    
    return query.order_by(models.GPSLog.timestamp.desc()).limit(limit).all()


def get_gps_logs_by_bus(
    db: Session,
    bus_id: int,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000
) -> List[models.GPSLog]:
    """Get GPS logs for a bus within time range."""
    query = db.query(models.GPSLog).filter(
        models.GPSLog.bus_id == bus_id
    )
    
    if start_time:
        query = query.filter(models.GPSLog.timestamp >= start_time)
    if end_time:
        query = query.filter(models.GPSLog.timestamp <= end_time)
    
    return query.order_by(models.GPSLog.timestamp.asc()).limit(limit).all()


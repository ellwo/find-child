"""
Face recognition service - Student identification and attendance recording.
"""
from typing import Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.orm import Session

from app import models, crud
from app.compreface_client import compare_faces
from app.utils import get_storage_path, get_image_url
from app.services.gps_service import is_near_school


def identify_student_from_face(
    db: Session,
    camera_id: str,
    image_path: str,
    gender_detected: Optional[models.Gender] = None
) -> Optional[Tuple[models.Student, float]]:
    """
    Identify a student from a face image captured by a camera.
    Returns (student, similarity_score) or None if no match found.
    """
    # Get bus associated with camera
    camera = crud.get_camera_by_code(db, camera_id)
    if not camera:
        return None
    
    bus = None
    if camera.bus:
        bus = camera.bus
    else:
        # Try to find bus by camera_id
        bus = db.query(models.Bus).filter(models.Bus.camera_id == camera_id).first()
    
    if not bus:
        return None
    
    # Get all students on this bus
    students = crud.get_students_by_bus(db, bus.id)
    if not students:
        return None
    
    # Compare face with all students
    best_match = None
    best_similarity = 0.0
    threshold = 0.7  # Minimum similarity threshold
    
    full_image_path = Path(get_storage_path()) / image_path
    
    for student in students:
        if not student.face_image_path or not student.compreface_face_id:
            continue
        
        # Skip if gender doesn't match (if detected)
        if gender_detected and student.gender != gender_detected:
            continue
        
        student_image_path = Path(get_storage_path()) / student.face_image_path
        if not student_image_path.exists():
            continue
        
        try:
            similarity = compare_faces(str(full_image_path), str(student_image_path))
            if similarity > best_similarity and similarity >= threshold:
                best_similarity = similarity
                best_match = student
        except Exception as e:
            print(f"Error comparing faces for student {student.id}: {str(e)}")
            continue
    
    if best_match:
        return (best_match, best_similarity)
    
    return None


def record_attendance(
    db: Session,
    student_id: int,
    bus_id: int,
    detected_image_path: str,
    similarity_score: float,
    detected_at: datetime,
    gps_latitude: Optional[float] = None,
    gps_longitude: Optional[float] = None,
    gender_detected: Optional[models.Gender] = None
) -> Optional[models.Attendance]:
    """
    Record attendance for a student.
    Checks attendance interval before creating/updating record.
    """
    # Get system settings for attendance interval
    settings = crud.get_system_settings(db)
    interval_minutes = settings.attendance_interval_minutes if settings else 5
    
    # Check last attendance
    last_attendance = crud.get_last_attendance_by_student(db, student_id)
    
    if last_attendance:
        # Check if enough time has passed
        time_diff = detected_at - last_attendance.detected_at
        if time_diff.total_seconds() < (interval_minutes * 60):
            # Update existing attendance instead of creating new one
            last_attendance.detected_image_path = detected_image_path
            last_attendance.similarity_score = similarity_score
            last_attendance.detected_at = detected_at
            if gps_latitude is not None:
                last_attendance.gps_latitude = gps_latitude
            if gps_longitude is not None:
                last_attendance.gps_longitude = gps_longitude
            if gender_detected:
                last_attendance.gender_detected = gender_detected
            
            db.commit()
            db.refresh(last_attendance)
            return last_attendance
    
    # Create new attendance record
    attendance = crud.create_attendance(
        db=db,
        student_id=student_id,
        bus_id=bus_id,
        detected_image_path=detected_image_path,
        similarity_score=similarity_score,
        detected_at=detected_at,
        gps_latitude=gps_latitude,
        gps_longitude=gps_longitude,
        gender_detected=gender_detected
    )
    
    return attendance



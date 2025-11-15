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
    
    # Get similarity threshold from settings
    settings = crud.get_system_settings(db)
    threshold = settings.attendance_similarity_threshold if settings else 0.9
    
    # Compare face with all students
    best_match = None
    best_similarity = 0.0
    
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
    Implements new logic:
    - Determines attendance_type based on time (before 12:00 = ENTRY, after = EXIT)
    - Checks similarity threshold from settings (default 0.9)
    - Checks max daily attendances per type from settings (default 2)
    - Only updates if new similarity is higher than existing for same type
    """
    # Determine attendance type based on time (before 12:00 = ENTRY, after = EXIT)
    attendance_type = models.AttendanceType.ENTRY if detected_at.hour < 12 else models.AttendanceType.EXIT
    
    # Get system settings
    settings = crud.get_system_settings(db)
    similarity_threshold = settings.attendance_similarity_threshold if settings else 0.9
    max_daily_attendances = settings.max_daily_attendances if settings else 2
    
    # Check if similarity score meets threshold
    if similarity_score < similarity_threshold:
        print(f"Similarity score {similarity_score} below threshold {similarity_threshold}")
        return None
    
    # Check today's attendance for this student and attendance type
    today_attendance = crud.get_attendance_today_by_student_and_type(db, student_id, attendance_type)
    today_count_by_type = crud.get_attendances_today_by_student_and_type(db, student_id, attendance_type)
    
    if today_attendance:
        # If there's an existing attendance today for this type, check similarity
        if similarity_score > today_attendance.similarity_score:
            # Update existing attendance with better similarity
            today_attendance.detected_image_path = detected_image_path
            today_attendance.similarity_score = similarity_score
            today_attendance.detected_at = detected_at
            if gps_latitude is not None:
                today_attendance.gps_latitude = gps_latitude
            if gps_longitude is not None:
                today_attendance.gps_longitude = gps_longitude
            if gender_detected:
                today_attendance.gender_detected = gender_detected
            
            db.commit()
            db.refresh(today_attendance)
            return today_attendance
        else:
            # Existing attendance has higher similarity, don't update
            print(f"Existing attendance has higher similarity ({today_attendance.similarity_score} > {similarity_score})")
            return today_attendance
    
    # Check if max daily attendances reached for this type
    if today_count_by_type >= max_daily_attendances:
        print(f"Max daily attendances ({max_daily_attendances}) reached for student {student_id} type {attendance_type.value}")
        return None
    
    # Create new attendance record
    attendance = crud.create_attendance(
        db=db,
        student_id=student_id,
        bus_id=bus_id,
        detected_image_path=detected_image_path,
        similarity_score=similarity_score,
        detected_at=detected_at,
        attendance_type=attendance_type,
        gps_latitude=gps_latitude,
        gps_longitude=gps_longitude,
        gender_detected=gender_detected
    )
    
    return attendance



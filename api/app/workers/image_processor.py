"""
Background worker for processing camera images.
Uses Celery for async task processing.
"""
import os
import json
from datetime import datetime
from pathlib import Path
from celery import Celery
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app import models, crud
from app.compreface_client import detect_face, index_face
from app.services import face_recognition
from app.utils import get_storage_path, get_image_url

# Initialize Celery app
redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
celery_app = Celery('image_processor', broker=redis_url, backend=redis_url)


@celery_app.task(bind=True, max_retries=3)
def process_camera_image(
    self,
    image_path: str,
    camera_id: str,
    camera_name: str,
    timestamp_str: str
):
    """
    Process camera image in background.
    
    Args:
        image_path: Relative path to the saved image
        camera_id: Camera identifier
        camera_name: Camera name
        timestamp_str: ISO format timestamp string
    """
    db: Session = SessionLocal()
    try:
        # Parse timestamp
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        if timestamp.tzinfo:
            timestamp = timestamp.replace(tzinfo=None)
        
        full_image_path = Path(get_storage_path()) / image_path
        
        # Step 1: Detect if image contains a face
        face_detected = False
        try:
            face_detected = detect_face(str(full_image_path))
            if not face_detected:
                print(f"Warning: No face detected in image from camera {camera_id}. Skipping student identification.")
                # Still save the image but don't try to identify student
                camera = crud.create_or_update_camera(db, camera_id, camera_name)
                captured_image = crud.create_captured_image(
                    db=db,
                    camera_id=camera_id,
                    camera_name=camera_name,
                    timestamp=timestamp,
                    file_path=image_path,
                    compreface_face_id=None
                )
                db.commit()
                return {
                    "status": "processed",
                    "face_detected": False,
                    "image_id": captured_image.id
                }
        except Exception as e:
            print(f"Warning: Face detection failed: {str(e)}. Proceeding with student identification anyway.")
            face_detected = True
        
        # Step 2: If face detected, proceed with student identification
        if face_detected:
            # Create or update camera record
            camera = crud.create_or_update_camera(db, camera_id, camera_name)
            
            # Create captured image record
            captured_image = crud.create_captured_image(
                db=db,
                camera_id=camera_id,
                camera_name=camera_name,
                timestamp=timestamp,
                file_path=image_path,
                compreface_face_id=None
            )
            
            # Index face in CompreFace (optional - for future searches)
            compreface_face_id = None
            try:
                compreface_face_id = index_face(str(full_image_path))
                # Update the record with compreface_face_id
                crud.update_captured_image_compreface_id(db, captured_image.id, compreface_face_id)
            except Exception as e:
                print(f"Warning: Failed to index face in CompreFace: {str(e)}")
            
            # Step 3: Try to identify student and record attendance
            try:
                # Get bus associated with camera
                bus = None
                if camera.bus:
                    bus = camera.bus
                else:
                    bus = db.query(models.Bus).filter(models.Bus.camera_id == camera_id).first()
                
                if bus:
                    # Get GPS location from tracker
                    gps_latitude = None
                    gps_longitude = None
                    if bus.gps_tracker_id:
                        tracker = crud.get_gps_tracker_by_id(db, bus.gps_tracker_id)
                        if tracker:
                            gps_latitude = tracker.last_latitude
                            gps_longitude = tracker.last_longitude
                    
                    # Identify student from face
                    result = face_recognition.identify_student_from_face(
                        db, camera_id, image_path, gender_detected=None
                    )
                    
                    if result:
                        student, similarity = result
                        # Record attendance
                        attendance = face_recognition.record_attendance(
                            db=db,
                            student_id=student.id,
                            bus_id=bus.id,
                            detected_image_path=image_path,
                            similarity_score=similarity,
                            detected_at=timestamp,
                            gps_latitude=gps_latitude,
                            gps_longitude=gps_longitude,
                            gender_detected=None
                        )
                        
                        # Broadcast attendance update via Redis pub/sub (for WebSocket broadcasting)
                        if attendance:
                            try:
                                import redis
                                redis_client = redis.from_url(redis_url)
                                attendance_message = {
                                    "type": "attendance",
                                    "student_id": student.id,
                                    "data": {
                                        "attendance_id": attendance.id,
                                        "detected_at": attendance.detected_at.isoformat(),
                                        "similarity_score": attendance.similarity_score,
                                        "gps_location": {
                                            "latitude": attendance.gps_latitude,
                                            "longitude": attendance.gps_longitude
                                        }
                                    }
                                }
                                redis_client.publish("attendance_updates", json.dumps(attendance_message))
                                print(f"Attendance recorded and published for student {student.id} with similarity {similarity:.2f}")
                            except Exception as e:
                                print(f"Warning: Failed to publish attendance update: {str(e)}")
                                print(f"Attendance still recorded for student {student.id} with similarity {similarity:.2f}")
            except Exception as e:
                print(f"Warning: Failed to identify student or record attendance: {str(e)}")
            
            db.commit()
            return {
                "status": "processed",
                "face_detected": True,
                "image_id": captured_image.id,
                "compreface_face_id": compreface_face_id
            }
        
        return {"status": "processed", "face_detected": False}
        
    except Exception as e:
        db.rollback()
        print(f"Error processing image: {str(e)}")
        # Retry the task
        raise self.retry(exc=e, countdown=60)
    finally:
        db.close()


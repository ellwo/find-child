"""
Admin API routes - System administration endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from datetime import date, datetime

from app import models, schemas, crud
from app.db import get_db
from app.dependencies import require_admin
from app.utils import get_image_url, get_storage_path
from pathlib import Path

router = APIRouter(prefix="/api/admin", tags=["admin"])


# Bus Management
@router.post("/buses", response_model=schemas.BusResponse, status_code=status.HTTP_201_CREATED)
async def create_bus(
    bus_data: schemas.BusCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Create a new bus."""
    try:
        bus = crud.create_bus(db, bus_data)
        return bus
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/buses", response_model=List[schemas.BusResponse])
async def get_buses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Get all buses."""
    buses, total = crud.get_all_buses(db, skip=skip, limit=limit)
    return buses


@router.get("/buses/{bus_id}", response_model=schemas.BusResponse)
async def get_bus(
    bus_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Get bus by ID."""
    bus = crud.get_bus_by_id(db, bus_id)
    if not bus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bus not found"
        )
    return bus


@router.put("/buses/{bus_id}", response_model=schemas.BusResponse)
async def update_bus(
    bus_id: int,
    bus_data: schemas.BusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Update bus."""
    bus = crud.update_bus(db, bus_id, bus_data)
    if not bus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bus not found"
        )
    return bus


@router.delete("/buses/{bus_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bus(
    bus_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Delete bus."""
    if not crud.delete_bus(db, bus_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bus not found"
        )


# Parent Management
@router.post("/parents", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def create_parent(
    parent_data: schemas.ParentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Create a new parent."""
    user_data = schemas.UserCreate(
        username=parent_data.username,
        email=parent_data.email,
        phone=parent_data.phone,
        password=parent_data.password,
        role=models.UserRole.PARENT,
        is_active=True
    )
    try:
        from app import auth
        user = auth.create_user(db, user_data)
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/parents", response_model=List[schemas.UserResponse])
async def get_parents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Get all parents."""
    parents = db.query(models.User).filter(
        models.User.role == models.UserRole.PARENT
    ).offset(skip).limit(limit).all()
    return parents


@router.get("/parents/{parent_id}", response_model=schemas.UserResponse)
async def get_parent(
    parent_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Get parent by ID."""
    parent = db.query(models.User).filter(
        models.User.id == parent_id,
        models.User.role == models.UserRole.PARENT
    ).first()
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent not found"
        )
    return parent


@router.put("/parents/{parent_id}", response_model=schemas.UserResponse)
async def update_parent(
    parent_id: int,
    parent_data: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Update parent."""
    parent = db.query(models.User).filter(
        models.User.id == parent_id,
        models.User.role == models.UserRole.PARENT
    ).first()
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent not found"
        )
    
    update_data = parent_data.dict(exclude_unset=True)
    if "password" in update_data:
        from app import auth
        update_data["hashed_password"] = auth.get_password_hash(update_data.pop("password"))
    
    for key, value in update_data.items():
        setattr(parent, key, value)
    
    db.commit()
    db.refresh(parent)
    return parent


@router.delete("/parents/{parent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_parent(
    parent_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Delete parent."""
    parent = db.query(models.User).filter(
        models.User.id == parent_id,
        models.User.role == models.UserRole.PARENT
    ).first()
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent not found"
        )
    db.delete(parent)
    db.commit()


# Student Management
@router.post("/students", response_model=schemas.StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    student_data: schemas.StudentCreate,
    face_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Create a new student with optional face image."""
    student = crud.create_student(db, student_data)
    
    # Handle face image upload if provided
    if face_image:
        from app.compreface_client import index_face
        from app.utils import save_face_image
        
        image_data = await face_image.read()
        file_path = save_face_image(image_data, f"student_{student.id}", datetime.utcnow())
        full_file_path = Path(get_storage_path()) / file_path
        
        # Index face in CompreFace
        compreface_face_id = None
        try:
            compreface_face_id = index_face(str(full_file_path))
        except Exception as e:
            print(f"Warning: Failed to index face in CompreFace: {str(e)}")
        
        # Update student with face image info
        student.face_image_path = file_path
        student.compreface_face_id = compreface_face_id
        db.commit()
        db.refresh(student)
    
    return student


@router.get("/students", response_model=List[schemas.StudentResponse])
async def get_students(
    skip: int = 0,
    limit: int = 100,
    bus_id: Optional[int] = None,
    parent_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Get all students with optional filters."""
    students, total = crud.get_all_students(db, skip=skip, limit=limit, bus_id=bus_id, parent_id=parent_id)
    return students


@router.get("/students/{student_id}", response_model=schemas.StudentResponse)
async def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Get student by ID."""
    student = crud.get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    return student


@router.put("/students/{student_id}", response_model=schemas.StudentResponse)
async def update_student(
    student_id: int,
    student_data: schemas.StudentUpdate,
    face_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Update student."""
    student = crud.update_student(db, student_id, student_data)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Handle face image update if provided
    if face_image:
        from app.compreface_client import index_face
        from app.utils import save_face_image
        
        image_data = await face_image.read()
        file_path = save_face_image(image_data, f"student_{student.id}", datetime.utcnow())
        full_file_path = Path(get_storage_path()) / file_path
        
        # Index face in CompreFace
        compreface_face_id = None
        try:
            compreface_face_id = index_face(str(full_file_path))
        except Exception as e:
            print(f"Warning: Failed to index face in CompreFace: {str(e)}")
        
        student.face_image_path = file_path
        student.compreface_face_id = compreface_face_id
        db.commit()
        db.refresh(student)
    
    return student


@router.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Delete student."""
    if not crud.delete_student(db, student_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )


# GPS Tracker Management
@router.post("/trackers", response_model=schemas.GPSTrackerResponse, status_code=status.HTTP_201_CREATED)
async def create_tracker(
    tracker_data: schemas.GPSTrackerCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Create a new GPS tracker."""
    try:
        tracker = crud.create_gps_tracker(db, tracker_data)
        return tracker
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/trackers", response_model=List[schemas.GPSTrackerResponse])
async def get_trackers(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Get all GPS trackers."""
    trackers = crud.get_all_gps_trackers(db)
    return trackers


@router.put("/trackers/{tracker_id}", response_model=schemas.GPSTrackerResponse)
async def update_tracker(
    tracker_id: int,
    tracker_data: schemas.GPSTrackerBase,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Update GPS tracker."""
    tracker = crud.update_gps_tracker(db, tracker_id, tracker_data)
    if not tracker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GPS tracker not found"
        )
    return tracker


# System Settings
@router.get("/settings", response_model=schemas.SystemSettingsResponse)
async def get_settings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Get system settings."""
    settings = crud.get_system_settings(db)
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="System settings not found"
        )
    return settings


@router.put("/settings", response_model=schemas.SystemSettingsResponse)
async def update_settings(
    settings_data: schemas.SystemSettingsBase,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Update system settings."""
    settings = crud.update_system_settings(db, settings_data)
    return settings


# Dashboard Stats
@router.get("/dashboard/stats", response_model=schemas.DashboardStats)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Get dashboard statistics."""
    total_buses = db.query(models.Bus).count()
    active_buses = db.query(models.Bus).filter(models.Bus.is_active == True).count()
    total_students = db.query(models.Student).count()
    total_parents = db.query(models.User).filter(models.User.role == models.UserRole.PARENT).count()
    total_attendances_today = crud.get_attendances_today(db)
    
    # Count buses with active GPS tracking
    buses_with_tracking = db.query(models.Bus).join(
        models.GPSTracker, models.Bus.gps_tracker_id == models.GPSTracker.id
    ).filter(
        models.GPSTracker.is_active == True,
        models.GPSTracker.last_update_timestamp.isnot(None)
    ).count()
    
    return schemas.DashboardStats(
        total_buses=total_buses,
        active_buses=active_buses,
        total_students=total_students,
        total_parents=total_parents,
        total_attendances_today=total_attendances_today,
        buses_with_active_tracking=buses_with_tracking
    )


# Reports
@router.get("/reports/attendance")
async def get_attendance_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    bus_id: Optional[int] = None,
    student_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Get attendance report."""
    query = db.query(models.Attendance)
    
    if start_date:
        start_ts = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=None)
        query = query.filter(models.Attendance.detected_at >= start_ts)
    if end_date:
        end_ts = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=None)
        query = query.filter(models.Attendance.detected_at <= end_ts)
    if bus_id:
        query = query.filter(models.Attendance.bus_id == bus_id)
    if student_id:
        query = query.filter(models.Attendance.student_id == student_id)
    
    attendances = query.order_by(models.Attendance.detected_at.desc()).all()
    return attendances


@router.get("/reports/buses-status")
async def get_buses_status(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Get buses status report."""
    buses = db.query(models.Bus).all()
    result = []
    for bus in buses:
        tracker = None
        if bus.gps_tracker_id:
            tracker = crud.get_gps_tracker_by_id(db, bus.gps_tracker_id)
        
        result.append({
            "bus_id": bus.id,
            "bus_number": bus.bus_number,
            "driver_name": bus.driver_name,
            "is_active": bus.is_active,
            "gps_tracker": {
                "device_id": tracker.device_id if tracker else None,
                "last_location": {
                    "latitude": tracker.last_latitude if tracker else None,
                    "longitude": tracker.last_longitude if tracker else None,
                },
                "last_update": tracker.last_update_timestamp if tracker else None,
            } if tracker else None,
            "students_count": db.query(models.Student).filter(models.Student.bus_id == bus.id).count()
        })
    return result


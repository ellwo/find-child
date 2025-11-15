"""
Parent API routes - Parent endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta

from app import models, schemas, crud
from app.db import get_db
from app.dependencies import require_parent

router = APIRouter(prefix="/api/parent", tags=["parent"])


@router.get("/students", response_model=List[schemas.StudentResponse])
async def get_my_students(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_parent)
):
    """Get all students for the current parent."""
    students = crud.get_students_by_parent(db, current_user.id)
    return [schemas.StudentResponse.from_orm_with_url(s) for s in students]


@router.get("/students/{student_id}", response_model=schemas.StudentResponse)
async def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_parent)
):
    """Get student details (only if belongs to current parent)."""
    student = crud.get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    if student.parent_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this student"
        )
    
    return schemas.StudentResponse.from_orm_with_url(student)


@router.get("/students/{student_id}/last-attendance", response_model=Optional[schemas.AttendanceResponse])
async def get_last_attendance(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_parent)
):
    """Get last attendance record for a student."""
    student = crud.get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    if student.parent_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this student"
        )
    
    attendance = crud.get_last_attendance_by_student(db, student_id)
    return attendance


@router.get("/students/{student_id}/attendance-history")
async def get_attendance_history(
    student_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_parent)
):
    """Get attendance history for a student."""
    student = crud.get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    if student.parent_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this student"
        )
    
    attendances, total = crud.get_attendance_history(
        db, student_id, start_date=start_date, end_date=end_date, skip=skip, limit=limit
    )
    return {
        "total": total,
        "items": attendances
    }


@router.get("/students/{student_id}/bus-location")
async def get_bus_location(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_parent)
):
    """Get current bus location for a student."""
    student = crud.get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    if student.parent_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this student"
        )
    
    if not student.bus_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student is not assigned to a bus"
        )
    
    bus = crud.get_bus_by_id(db, student.bus_id)
    if not bus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bus not found"
        )
    
    tracker = None
    if bus.gps_tracker_id:
        tracker = crud.get_gps_tracker_by_id(db, bus.gps_tracker_id)
    
    # Check if WebSocket is enabled in system settings (this controls real-time tracking)
    # Bus activity times (morning_start, morning_end, etc.) are now just informational
    settings = crud.get_system_settings(db)
    is_active_time = settings.websocket_enabled if settings else True
    
    return {
        "bus": {
            "id": bus.id,
            "bus_number": bus.bus_number,
            "driver_name": bus.driver_name,
            "driver_phone": bus.driver_phone
        },
        "location": {
            "latitude": tracker.last_latitude if tracker else None,
            "longitude": tracker.last_longitude if tracker else None,
            "last_update": tracker.last_update_timestamp if tracker else None
        },
        "is_active_time": is_active_time,
        "tracker_active": tracker.is_active if tracker else False
    }


@router.get("/students/{student_id}/route-history")
async def get_route_history(
    student_id: int,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_parent)
):
    """Get route history for a student's bus."""
    student = crud.get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    if student.parent_id != current_user.id and current_user.role != models.UserRole.SYSTEM_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this student"
        )
    
    if not student.bus_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student is not assigned to a bus"
        )
    
    bus = crud.get_bus_by_id(db, student.bus_id)
    if not bus or not bus.gps_tracker_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bus or GPS tracker not found"
        )
    
    # Default to today if no time range provided
    if not start_time:
        start_time = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    if not end_time:
        end_time = datetime.utcnow()
    
    gps_logs = crud.get_gps_logs_by_bus(db, bus.id, start_time, end_time)
    
    return {
        "bus_id": bus.id,
        "bus_number": bus.bus_number,
        "route_points": [
            {
                "latitude": log.latitude,
                "longitude": log.longitude,
                "timestamp": log.timestamp,
                "is_near_school": log.is_near_school
            }
            for log in gps_logs
        ]
    }



"""
Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from app.models import UserRole, Gender


# Authentication Schemas
class Token(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data schema."""
    user_id: Optional[int] = None
    username: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request schema."""
    username: Optional[str] = None  # Can be email or phone
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str


class UserResponse(BaseModel):
    """User response schema."""
    id: int
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# System Settings Schemas
class SystemSettingsBase(BaseModel):
    """Base system settings schema."""
    school_name: str
    school_address: Optional[str] = None
    school_latitude: Optional[float] = None
    school_longitude: Optional[float] = None
    default_morning_start: Optional[str] = None
    default_morning_end: Optional[str] = None
    default_afternoon_start: Optional[str] = None
    default_afternoon_end: Optional[str] = None
    attendance_interval_minutes: int = 5
    attendance_similarity_threshold: float = 0.9
    max_daily_attendances: int = 2
    websocket_enabled: bool = True


class SystemSettingsResponse(SystemSettingsBase):
    """System settings response schema."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# GPS Tracker Schemas
class GPSTrackerBase(BaseModel):
    """Base GPS tracker schema."""
    device_id: str
    device_name: Optional[str] = None
    is_active: bool = True


class GPSTrackerCreate(GPSTrackerBase):
    """GPS tracker create schema."""
    pass


class GPSTrackerResponse(GPSTrackerBase):
    """GPS tracker response schema."""
    id: int
    last_latitude: Optional[float] = None
    last_longitude: Optional[float] = None
    last_update_timestamp: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Bus Schemas
class BusBase(BaseModel):
    """Base bus schema."""
    bus_number: str
    driver_name: str
    driver_phone: str
    gps_tracker_id: Optional[int] = None
    camera_id: Optional[str] = None
    morning_start: Optional[str] = None
    morning_end: Optional[str] = None
    afternoon_start: Optional[str] = None
    afternoon_end: Optional[str] = None
    is_active: bool = True


class BusCreate(BusBase):
    """Bus create schema."""
    pass


class BusUpdate(BaseModel):
    """Bus update schema."""
    bus_number: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    gps_tracker_id: Optional[int] = None
    camera_id: Optional[str] = None
    morning_start: Optional[str] = None
    morning_end: Optional[str] = None
    afternoon_start: Optional[str] = None
    afternoon_end: Optional[str] = None
    is_active: Optional[bool] = None


class BusResponse(BusBase):
    """Bus response schema."""
    id: int
    created_at: datetime
    updated_at: datetime
    gps_tracker: Optional[GPSTrackerResponse] = None

    class Config:
        from_attributes = True


# User/Parent Schemas
class UserBase(BaseModel):
    """Base user schema."""
    username: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: UserRole
    is_active: bool = True


class UserCreate(UserBase):
    """User create schema."""
    password: str


class UserUpdate(BaseModel):
    """User update schema."""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class ParentCreate(BaseModel):
    """Parent create schema."""
    username: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str


# Student Schemas
class StudentBase(BaseModel):
    """Base student schema."""
    name: str
    age: int
    gender: Gender
    parent_id: int
    bus_id: Optional[int] = None
    home_address: Optional[str] = None
    home_latitude: Optional[float] = None
    home_longitude: Optional[float] = None


class StudentCreate(StudentBase):
    """Student create schema."""
    pass


class StudentUpdate(BaseModel):
    """Student update schema."""
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[Gender] = None
    parent_id: Optional[int] = None
    bus_id: Optional[int] = None
    home_address: Optional[str] = None
    home_latitude: Optional[float] = None
    home_longitude: Optional[float] = None


class StudentResponse(StudentBase):
    """Student response schema."""
    id: int
    face_image_path: Optional[str] = None
    compreface_face_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    parent: Optional[UserResponse] = None
    bus: Optional[BusResponse] = None
    image_url: Optional[str] = None  # URL to access the face image

    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm_with_url(cls, obj, image_url: Optional[str] = None):
        """Create StudentResponse with image_url."""
        from app.utils import get_image_url
        data = {
            "id": obj.id,
            "name": obj.name,
            "age": obj.age,
            "gender": obj.gender,
            "parent_id": obj.parent_id,
            "bus_id": obj.bus_id,
            "home_address": obj.home_address,
            "home_latitude": obj.home_latitude,
            "home_longitude": obj.home_longitude,
            "face_image_path": obj.face_image_path,
            "compreface_face_id": obj.compreface_face_id,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
            "parent": obj.parent,
            "bus": obj.bus,
            "image_url": image_url or (get_image_url(obj.face_image_path) if obj.face_image_path else None),
        }
        return cls(**data)


# Attendance Schemas
class AttendanceResponse(BaseModel):
    """Attendance response schema."""
    id: int
    student_id: int
    bus_id: int
    detected_image_path: str
    similarity_score: float
    detected_at: datetime
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    gender_detected: Optional[Gender] = None
    created_at: datetime
    student: Optional[StudentResponse] = None
    bus: Optional[BusResponse] = None
    image_url: Optional[str] = None  # URL to access the detected image

    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm_with_url(cls, obj, image_url: Optional[str] = None):
        """Create AttendanceResponse with image_url."""
        from app.utils import get_image_url
        data = {
            "id": obj.id,
            "student_id": obj.student_id,
            "bus_id": obj.bus_id,
            "detected_image_path": obj.detected_image_path,
            "similarity_score": obj.similarity_score,
            "detected_at": obj.detected_at,
            "gps_latitude": obj.gps_latitude,
            "gps_longitude": obj.gps_longitude,
            "gender_detected": obj.gender_detected,
            "created_at": obj.created_at,
            "student": obj.student,
            "bus": obj.bus,
            "image_url": image_url or get_image_url(obj.detected_image_path),
        }
        return cls(**data)


# GPS Log Schemas
class GPSLogResponse(BaseModel):
    """GPS log response schema."""
    id: int
    tracker_id: int
    bus_id: Optional[int] = None
    latitude: float
    longitude: float
    timestamp: datetime
    is_near_school: bool
    created_at: datetime

    class Config:
        from_attributes = True


# GPS Update Schema
class GPSUpdateRequest(BaseModel):
    """GPS update request schema."""
    device_id: str
    latitude: float
    longitude: float
    timestamp: Optional[datetime] = None


# Dashboard Schemas
class DashboardStats(BaseModel):
    """Dashboard statistics schema."""
    total_buses: int
    active_buses: int
    total_students: int
    total_parents: int
    total_attendances_today: int
    buses_with_active_tracking: int


# Camera Schemas (existing)
class CameraResponse(BaseModel):
    """Camera information response."""
    id: int
    code: str
    name: Optional[str] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    total_images: int

    class Config:
        from_attributes = True


class CapturedImageBase(BaseModel):
    """Base schema for captured image."""
    camera_id: str
    camera_name: Optional[str] = None
    timestamp: datetime
    file_path: str
    compreface_face_id: Optional[str] = None


class CapturedImageCreate(CapturedImageBase):
    """Schema for creating a captured image."""
    pass


class CapturedImageResponse(BaseModel):
    """Captured image response schema."""
    id: int
    camera_id: str
    camera_name: Optional[str] = None
    timestamp: datetime
    image_url: str
    compreface_face_id: Optional[str] = None

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    """Response after uploading a camera face."""
    id: int
    image_url: str
    camera_id: str
    timestamp: datetime
    compreface_face_id: Optional[str] = None


class SearchResult(BaseModel):
    """Search result item."""
    image_url: str
    camera_id: str
    camera_name: Optional[str] = None
    timestamp: datetime
    similarity: float


class SearchResponse(BaseModel):
    """Search by image response."""
    results: List[SearchResult]
    total: int


class SavedImagesResponse(BaseModel):
    """Paginated saved images response."""
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[CapturedImageResponse]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    database: str
    compreface: str
    stats: Optional[dict] = None


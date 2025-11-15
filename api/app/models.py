"""
SQLAlchemy database models.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Boolean, Float, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.db import Base
import enum


class UserRole(str, enum.Enum):
    """User role enumeration."""
    SYSTEM_ADMIN = "system_admin"
    PARENT = "parent"


class Gender(str, enum.Enum):
    """Gender enumeration."""
    MALE = "male"
    FEMALE = "female"


class SystemSettings(Base):
    """System settings model - stores general system configuration."""
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    school_name = Column(String, nullable=False)
    school_address = Column(Text, nullable=True)
    school_latitude = Column(Float, nullable=True)
    school_longitude = Column(Float, nullable=True)
    # Default activity times (JSON format)
    default_morning_start = Column(String, nullable=True)  # HH:MM format
    default_morning_end = Column(String, nullable=True)
    default_afternoon_start = Column(String, nullable=True)
    default_afternoon_end = Column(String, nullable=True)
    attendance_interval_minutes = Column(Integer, default=5, nullable=False)  # فارق التحضير
    attendance_similarity_threshold = Column(Float, default=0.9, nullable=False)  # نسبة التشابه المطلوبة (90%)
    max_daily_attendances = Column(Integer, default=2, nullable=False)  # عدد التحضيرات المسموح في اليوم
    websocket_enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class GPSTracker(Base):
    """GPS Tracker device model."""
    __tablename__ = "gps_trackers"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, unique=True, index=True, nullable=False)
    device_name = Column(String, nullable=True)
    last_latitude = Column(Float, nullable=True)
    last_longitude = Column(Float, nullable=True)
    last_update_timestamp = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    buses = relationship("Bus", back_populates="gps_tracker")
    gps_logs = relationship("GPSLog", back_populates="tracker")


class Camera(Base):
    """Camera model - tracks registered cameras."""
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)  # camera_id
    name = Column(String, nullable=True)
    first_seen_ts = Column(DateTime(timezone=True), nullable=True)
    last_seen_ts = Column(DateTime(timezone=True), nullable=True)
    total_images = Column(Integer, default=0, nullable=False)

    # Relationship to captured images
    images = relationship("CapturedImage", back_populates="camera")
    # Relationship to bus
    bus = relationship("Bus", back_populates="camera", uselist=False)


class Bus(Base):
    """Bus model - school buses."""
    __tablename__ = "buses"

    id = Column(Integer, primary_key=True, index=True)
    bus_number = Column(String, unique=True, index=True, nullable=False)
    driver_name = Column(String, nullable=False)
    driver_phone = Column(String, nullable=False)
    gps_tracker_id = Column(Integer, ForeignKey("gps_trackers.id"), nullable=True, index=True)
    camera_id = Column(String, ForeignKey("cameras.code"), nullable=True, index=True)
    # Activity times (JSON format)
    morning_start = Column(String, nullable=True)  # HH:MM format
    morning_end = Column(String, nullable=True)
    afternoon_start = Column(String, nullable=True)
    afternoon_end = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    gps_tracker = relationship("GPSTracker", back_populates="buses")
    camera = relationship("Camera", back_populates="bus")
    students = relationship("Student", back_populates="bus")
    attendances = relationship("Attendance", back_populates="bus")
    gps_logs = relationship("GPSLog", back_populates="bus")


class User(Base):
    """User model - system admins and parents."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    phone = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    students = relationship("Student", back_populates="parent")


class Student(Base):
    """Student model."""
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    age = Column(Integer, nullable=False)
    gender = Column(SQLEnum(Gender), nullable=False)
    face_image_path = Column(String, nullable=True)
    compreface_face_id = Column(String, nullable=True, index=True)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    bus_id = Column(Integer, ForeignKey("buses.id"), nullable=True, index=True)
    home_address = Column(Text, nullable=True)
    home_latitude = Column(Float, nullable=True)
    home_longitude = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    parent = relationship("User", back_populates="students")
    bus = relationship("Bus", back_populates="students")
    attendances = relationship("Attendance", back_populates="student")


class Attendance(Base):
    """Attendance record model."""
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    bus_id = Column(Integer, ForeignKey("buses.id"), nullable=False, index=True)
    detected_image_path = Column(String, nullable=False)
    similarity_score = Column(Float, nullable=False)
    detected_at = Column(DateTime(timezone=True), nullable=False, index=True)
    gps_latitude = Column(Float, nullable=True)
    gps_longitude = Column(Float, nullable=True)
    gender_detected = Column(SQLEnum(Gender), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    student = relationship("Student", back_populates="attendances")
    bus = relationship("Bus", back_populates="attendances")


class GPSLog(Base):
    """GPS location log model."""
    __tablename__ = "gps_logs"

    id = Column(Integer, primary_key=True, index=True)
    tracker_id = Column(Integer, ForeignKey("gps_trackers.id"), nullable=False, index=True)
    bus_id = Column(Integer, ForeignKey("buses.id"), nullable=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    is_near_school = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    tracker = relationship("GPSTracker", back_populates="gps_logs")
    bus = relationship("Bus", back_populates="gps_logs")


class CapturedImage(Base):
    """Captured face image model - stores metadata about uploaded face images."""
    __tablename__ = "captured_images"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String, ForeignKey("cameras.code"), nullable=False, index=True)
    camera_name = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    file_path = Column(String, nullable=False)
    compreface_face_id = Column(String, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship to camera
    camera = relationship("Camera", back_populates="images")


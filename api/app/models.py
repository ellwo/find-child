"""
SQLAlchemy database models.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Boolean, Float, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.db import Base
import enum


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
    
    # New fields for location and place information
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    place_name = Column(String, nullable=True)
    description = Column(Text, nullable=True)

    # Relationship to camera
    camera = relationship("Camera", back_populates="images")
    # Relationship to report matches
    report_matches = relationship("ReportMatch", back_populates="captured_image")


class ReportStatus(str, enum.Enum):
    """Report status enum."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class User(Base):
    """User model for authentication."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_system_user = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    created_reports = relationship("MissingReport", back_populates="created_by_user")


class MissingReport(Base):
    """Missing child report model."""
    __tablename__ = "missing_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_number = Column(String, unique=True, index=True, nullable=False)  # REP-YYYY-XXXX
    reporter_name = Column(String, nullable=False)
    reporter_email = Column(String, nullable=False)
    reporter_phone = Column(String, nullable=False)
    child_name = Column(String, nullable=False)
    child_photo_path = Column(String, nullable=False)
    child_compreface_face_id = Column(String, nullable=True, index=True)
    status = Column(SQLEnum(ReportStatus), default=ReportStatus.OPEN, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    created_by_user = relationship("User", back_populates="created_reports")
    matches = relationship("ReportMatch", back_populates="report", cascade="all, delete-orphan")


class ReportMatch(Base):
    """Report match model - stores matches between captured images and reports."""
    __tablename__ = "report_matches"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("missing_reports.id"), nullable=False, index=True)
    captured_image_id = Column(Integer, ForeignKey("captured_images.id"), nullable=False, index=True)
    similarity_score = Column(Float, nullable=False)
    camera_id = Column(String, nullable=False)
    camera_name = Column(String, nullable=True)
    matched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    notified_at = Column(DateTime(timezone=True), nullable=True)
    external_api_called = Column(Boolean, default=False, nullable=False)

    # Relationships
    report = relationship("MissingReport", back_populates="matches")
    captured_image = relationship("CapturedImage", back_populates="report_matches")


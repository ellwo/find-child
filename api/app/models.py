"""
SQLAlchemy database models.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db import Base


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

    # Relationship to camera
    camera = relationship("Camera", back_populates="images")


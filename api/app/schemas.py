"""
Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


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


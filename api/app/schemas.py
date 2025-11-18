"""
Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr


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
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    place_name: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    """Response after uploading a camera face."""
    id: int
    image_url: str
    camera_id: str
    timestamp: datetime
    compreface_face_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    place_name: Optional[str] = None
    description: Optional[str] = None


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


# Authentication Schemas
class UserLogin(BaseModel):
    """User login schema."""
    username: str
    password: str


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """User response schema."""
    id: int
    username: str
    email: str
    is_active: bool
    is_system_user: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Missing Report Schemas
class MissingReportCreate(BaseModel):
    """Schema for creating a missing report."""
    reporter_name: str
    reporter_email: EmailStr
    reporter_phone: str
    child_name: str
    child_photo: str  # Base64 encoded image or file path


class MissingReportResponse(BaseModel):
    """Missing report response schema."""
    id: int
    report_number: str
    reporter_name: str
    reporter_email: str
    reporter_phone: str
    child_name: str
    child_photo_url: str
    status: str
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReportStatusUpdate(BaseModel):
    """Schema for updating report status."""
    status: str = Field(..., pattern="^(open|in_progress|resolved|closed)$")


class ReportMatchResponse(BaseModel):
    """Report match response schema."""
    id: int
    report_id: int
    captured_image_id: int
    similarity_score: float
    camera_id: str
    camera_name: Optional[str] = None
    matched_at: datetime
    image_url: str

    class Config:
        from_attributes = True


class ReportTrackRequest(BaseModel):
    """Schema for tracking a report."""
    phone: str
    report_number: str


class ReportTrackResponse(BaseModel):
    """Report tracking response schema."""
    report: MissingReportResponse
    matches: List[ReportMatchResponse] = []


class ReportListResponse(BaseModel):
    """Paginated reports response."""
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[MissingReportResponse]


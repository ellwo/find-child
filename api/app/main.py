"""
FastAPI main application with all endpoints.
"""
import os
import tempfile
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException, Header, status, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app import crud, models, schemas
from app.db import get_db, engine
from app.compreface_client import index_face, search_face, compare_faces
from app.utils import (
    save_face_image, get_image_url, parse_date, get_today_utc,
    parse_iso_datetime, get_storage_path
)
from app import auth
from app.dependencies import get_current_user, require_admin, require_parent
from app.routers import admin, parent
from app.services import gps_service, face_recognition
from app.websocket import websocket_admin_buses, websocket_parent_student, websocket_device_gps, manager
import asyncio
import json
import redis

load_dotenv()

# Initialize database tables (init_data.py will be called from Dockerfile)
models.Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Face Recognition API",
    description="API for ESP32-CAM face uploads, CompreFace integration, and image search",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for serving images
storage_path = get_storage_path()
faces_dir = Path(storage_path) / "faces"
faces_dir.mkdir(parents=True, exist_ok=True)

# Mount static file serving
app.mount("/storage", StaticFiles(directory=storage_path), name="storage")

# Include routers
app.include_router(admin.router)
app.include_router(parent.router)


# Redis subscriber for attendance updates from worker
async def redis_subscriber():
    """Subscribe to Redis pub/sub for attendance updates and broadcast via WebSocket."""
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    
    # Wait for Redis to be available (with retries)
    max_retries = 10
    retry_delay = 2
    redis_client = None
    
    for attempt in range(max_retries):
        try:
            redis_client = redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=2)
            redis_client.ping()  # Test connection
            print(f"Redis subscriber connected successfully (attempt {attempt + 1})")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Redis connection attempt {attempt + 1} failed, retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
            else:
                print(f"Warning: Redis subscriber failed after {max_retries} attempts: {str(e)}")
                print("WebSocket broadcasting from worker will not work until Redis is available.")
                return
    
    if not redis_client:
        return
    
    try:
        pubsub = redis_client.pubsub()
        pubsub.subscribe("attendance_updates")
        
        print("Redis subscriber started for attendance updates")
        
        # Process messages in async loop (non-blocking)
        while True:
            try:
                # Get next message (non-blocking check)
                message = pubsub.get_message(timeout=1.0)
                if message and message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        student_id = data.get("student_id")
                        attendance_data = data.get("data", {})
                        
                        # Broadcast via WebSocket
                        await manager.broadcast_attendance(student_id, attendance_data)
                    except Exception as e:
                        print(f"Error processing attendance update from Redis: {str(e)}")
                else:
                    # No message, yield control
                    await asyncio.sleep(0.1)
            except Exception as e:
                print(f"Error in Redis subscriber loop: {str(e)}")
                await asyncio.sleep(1)  # Wait before retrying
    except Exception as e:
        print(f"Error in Redis subscriber: {str(e)}")


@app.on_event("startup")
async def startup_event():
    """Start background tasks on startup."""
    # Run database migration first
    try:
        from app.migrate_settings import migrate_settings
        migrate_settings()
    except Exception as e:
        print(f"Warning: Migration failed (may already be applied): {str(e)}")
    
    # Start Redis subscriber in background
    asyncio.create_task(redis_subscriber())


# Get API key from environment
CAMERA_API_KEY = os.getenv("CAMERA_API_KEY", "changeme_camera_api_key")
GPS_DEVICE_API_KEY = os.getenv("GPS_DEVICE_API_KEY", "changeme_gps_api_key")


def verify_api_key(x_api_key: str = Header(...)) -> bool:
    """Verify API key for camera uploads."""
    if x_api_key != CAMERA_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return True


def verify_gps_api_key(x_api_key: str = Header(...)) -> bool:
    """Verify API key for GPS device updates."""
    if x_api_key != GPS_DEVICE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid GPS device API key"
        )
    return True


@app.get("/health", response_model=schemas.HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    health_status = {
        "status": "healthy",
        "database": "unknown",
        "compreface": "unknown",
        "stats": {}
    }
    
    # Check database
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check CompreFace
    try:
        import requests
        compreface_url = os.getenv("COMPREFACE_URL", "http://compreface-api:8080")
        # Try to reach CompreFace API health endpoint
        response = requests.get(f"{compreface_url}/api/v1/status", timeout=5)
        if response.status_code == 200:
            health_status["compreface"] = "connected"
        else:
            health_status["compreface"] = f"status: {response.status_code}"
    except Exception as e:
        health_status["compreface"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Get basic stats
    try:
        total_images = db.query(models.CapturedImage).count()
        total_cameras = db.query(models.Camera).count()
        health_status["stats"] = {
            "total_images": total_images,
            "total_cameras": total_cameras
        }
    except Exception:
        pass
    
    return health_status


# Authentication Endpoints
@app.post("/api/auth/login", response_model=schemas.Token)
async def login(login_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Login endpoint - accepts username, email, or phone."""
    user = auth.authenticate_user(
        db,
        username=login_data.username,
        email=login_data.email,
        phone=login_data.phone,
        password=login_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email/phone or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth.create_access_token(
        data={"sub": user.id, "username": user.username}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me", response_model=schemas.UserResponse)
async def get_current_user_info(current_user: models.User = Depends(get_current_user)):
    """Get current user information."""
    return current_user


@app.post("/api/auth/refresh", response_model=schemas.Token)
async def refresh_token(current_user: models.User = Depends(get_current_user)):
    """Refresh access token."""
    access_token = auth.create_access_token(
        data={"sub": current_user.id, "username": current_user.username}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/api/upload_camera_face", response_model=schemas.UploadResponse)
async def upload_camera_face(
    camera_id: str = Form(...),
    camera_name: Optional[str] = Form(None),
    timestamp: Optional[str] = Form(None),
    image: UploadFile = File(...),
    x_api_key: str = Header(..., alias="X-API-KEY"),
    db: Session = Depends(get_db)
):
    """
    Upload a cropped face image from ESP32-CAM.
    Requires X-API-KEY header for authentication.
    """
    # Verify API key
    verify_api_key(x_api_key)
    
    # Validate image file
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Parse timestamp
    if timestamp:
        parsed_timestamp = parse_iso_datetime(timestamp)
        if not parsed_timestamp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid timestamp format. Use ISO-8601 (e.g., 2025-11-10T15:30:00Z)"
            )
    else:
        parsed_timestamp = datetime.utcnow()
    
    # Read image data
    image_data = await image.read()
    if len(image_data) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image file is empty"
        )
    
    # Save image file
    try:
        file_path = save_face_image(image_data, camera_id, parsed_timestamp)
        full_file_path = Path(get_storage_path()) / file_path
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save image: {str(e)}"
        )
    
    # Create or update camera record (minimal DB operation)
    camera = crud.create_or_update_camera(db, camera_id, camera_name)
    db.commit()
    
    # Queue image processing task in background worker
    # All processing (face detection, recognition, attendance) happens in background
    try:
        from app.workers.image_processor import process_camera_image
        task = process_camera_image.delay(
            image_path=file_path,
            camera_id=camera_id,
            camera_name=camera_name or camera_id,
            timestamp_str=parsed_timestamp.isoformat()
        )
        
        # Return immediate response - camera device gets 200 OK immediately
        image_url = get_image_url(file_path)
        return schemas.UploadResponse(
            id=0,  # Will be set by worker after processing
            image_url=image_url,
        camera_id=camera_id,
        timestamp=parsed_timestamp,
        compreface_face_id=None
    )
    except Exception as e:
        # If Celery is not available, log error but still return 200
        # This ensures camera device always gets a response
        print(f"Error: Celery not available, image saved but processing failed: {str(e)}")
        print(f"Image saved at: {file_path}")
    image_url = get_image_url(file_path)
    return schemas.UploadResponse(
            id=0,
        image_url=image_url,
        camera_id=camera_id,
        timestamp=parsed_timestamp,
            compreface_face_id=None
    )


@app.post("/api/search_by_image", response_model=schemas.SearchResponse)
async def search_by_image(
    image: UploadFile = File(...),
    start_ts: Optional[str] = Form(None),
    end_ts: Optional[str] = Form(None),
    threshold: float = Form(0.7),
    limit: int = Form(50),
    db: Session = Depends(get_db)
):
    """
    Search for similar faces by image.
    Uses CompreFace search API and filters results by time range and similarity threshold.
    """
    # Validate threshold
    if not 0.0 <= threshold <= 1.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Threshold must be between 0.0 and 1.0"
        )
    
    # Validate limit
    if limit < 1 or limit > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 1000"
        )
    
    # Parse timestamps
    if start_ts:
        parsed_start_ts = parse_iso_datetime(start_ts)
        if not parsed_start_ts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_ts format. Use ISO-8601"
            )
    else:
        parsed_start_ts = datetime.utcnow() - timedelta(days=1)
    
    if end_ts:
        parsed_end_ts = parse_iso_datetime(end_ts)
        if not parsed_end_ts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_ts format. Use ISO-8601"
            )
    else:
        parsed_end_ts = datetime.utcnow()
    
    # Read query image
    image_data = await image.read()
    if len(image_data) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image file is empty"
        )
    
    # Save query image temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        tmp_file.write(image_data)
        tmp_file_path = tmp_file.name
    
    try:
        # Search in CompreFace
        search_results = search_face(tmp_file_path, limit=limit)
        
        if not search_results:
            # Fallback: if CompreFace search doesn't return face IDs, use compare method
            # This is slower but more reliable
            print("Warning: CompreFace search returned no results, using fallback method")
            
            # Get candidate images from DB in time range
            all_images = db.query(models.CapturedImage).filter(
                models.CapturedImage.timestamp >= parsed_start_ts,
                models.CapturedImage.timestamp <= parsed_end_ts,
                models.CapturedImage.compreface_face_id.isnot(None)
            ).all()
            
            fallback_results = []
            for img in all_images:
                try:
                    full_path = Path(get_storage_path()) / img.file_path
                    if full_path.exists():
                        similarity = compare_faces(tmp_file_path, str(full_path))
                        if similarity >= threshold:
                            fallback_results.append({
                                "image": img,
                                "similarity": similarity
                            })
                except Exception as e:
                    print(f"Error comparing with image {img.id}: {str(e)}")
                    continue
            
            # Sort by similarity
            fallback_results.sort(key=lambda x: x["similarity"], reverse=True)
            
            # Format results
            results = []
            for item in fallback_results[:limit]:
                img = item["image"]
                results.append(schemas.SearchResult(
                    image_url=get_image_url(img.file_path),
                    camera_id=img.camera_id,
                    camera_name=img.camera_name,
                    timestamp=img.timestamp,
                    similarity=item["similarity"]
                ))
            
            return schemas.SearchResponse(results=results, total=len(results))
        
        # Extract face IDs from search results
        face_ids = [r["face_id"] for r in search_results]
        
        # Get images from DB by CompreFace face IDs
        db_images = crud.get_images_by_compreface_ids(
            db,
            face_ids,
            start_ts=parsed_start_ts,
            end_ts=parsed_end_ts
        )
        
        # Create a mapping of compreface_face_id -> image
        image_map = {img.compreface_face_id: img for img in db_images if img.compreface_face_id}
        
        # Build results with similarity scores
        results = []
        for search_result in search_results:
            face_id = search_result["face_id"]
            similarity = search_result["score"]
            
            if similarity >= threshold and face_id in image_map:
                img = image_map[face_id]
                results.append(schemas.SearchResult(
                    image_url=get_image_url(img.file_path),
                    camera_id=img.camera_id,
                    camera_name=img.camera_name,
                    timestamp=img.timestamp,
                    similarity=similarity
                ))
        
        # Results are already sorted by similarity from CompreFace
        return schemas.SearchResponse(results=results, total=len(results))
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )
    finally:
        # Clean up temporary file
        try:
            os.unlink(tmp_file_path)
        except Exception:
            pass


@app.get("/api/saved_images", response_model=schemas.SavedImagesResponse)
async def get_saved_images(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    camera_ids: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get paginated list of saved face images with optional filters.
    Defaults to today's images if no dates provided.
    """
    # Validate pagination
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page must be >= 1"
        )
    
    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page size must be between 1 and 100"
        )
    
    # Parse dates
    if start_date:
        parsed_start_date = parse_date(start_date)
        if not parsed_start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD"
            )
    else:
        parsed_start_date = get_today_utc()
    
    if end_date:
        parsed_end_date = parse_date(end_date)
        if not parsed_end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD"
            )
    else:
        parsed_end_date = parsed_start_date
    
    # Parse camera IDs
    camera_id_list = None
    if camera_ids:
        camera_id_list = [cid.strip() for cid in camera_ids.split(",") if cid.strip()]
    
    # Get images
    skip = (page - 1) * page_size
    images, total = crud.get_images_by_date_range(
        db,
        parsed_start_date,
        parsed_end_date,
        camera_ids=camera_id_list,
        skip=skip,
        limit=page_size
    )
    
    # Format response
    items = []
    for img in images:
        items.append(schemas.CapturedImageResponse(
            id=img.id,
            camera_id=img.camera_id,
            camera_name=img.camera_name,
            timestamp=img.timestamp,
            image_url=get_image_url(img.file_path),
            compreface_face_id=img.compreface_face_id
        ))
    
    total_pages = (total + page_size - 1) // page_size
    
    return schemas.SavedImagesResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=items
    )


@app.get("/api/cameras", response_model=List[schemas.CameraResponse])
async def get_cameras(db: Session = Depends(get_db)):
    """Get list of all registered cameras."""
    cameras = crud.get_all_cameras(db)
    return [
        schemas.CameraResponse(
            id=cam.id,
            code=cam.code,
            name=cam.name,
            first_seen=cam.first_seen_ts,
            last_seen=cam.last_seen_ts,
            total_images=cam.total_images
        )
        for cam in cameras
    ]


# GPS Device Endpoints
@app.post("/api/device/gps/update")
async def update_gps_location(
    gps_data: schemas.GPSUpdateRequest,
    x_api_key: str = Header(..., alias="X-API-KEY"),
    db: Session = Depends(get_db)
):
    """Update GPS location from GPS tracker device."""
    # Verify API key
    verify_gps_api_key(x_api_key)
    
    # Get or create tracker
    tracker = crud.get_gps_tracker_by_device_id(db, gps_data.device_id)
    if not tracker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"GPS tracker with device_id {gps_data.device_id} not found"
        )
    
    # Update tracker location
    timestamp = gps_data.timestamp or datetime.utcnow()
    crud.update_gps_tracker_location(
        db, gps_data.device_id, gps_data.latitude, gps_data.longitude, timestamp
    )
    
    # Get bus associated with tracker
    bus = db.query(models.Bus).filter(models.Bus.gps_tracker_id == tracker.id).first()
    
    # Get system settings to check if near school
    settings = crud.get_system_settings(db)
    is_near = False
    if settings and settings.school_latitude and settings.school_longitude:
        is_near = gps_service.is_near_school(
            gps_data.latitude,
            gps_data.longitude,
            settings.school_latitude,
            settings.school_longitude
        )
    
    # Create GPS log entry
    crud.create_gps_log(
        db=db,
        tracker_id=tracker.id,
        latitude=gps_data.latitude,
        longitude=gps_data.longitude,
        timestamp=timestamp,
        bus_id=bus.id if bus else None,
        is_near_school=is_near
    )
    
    # Broadcast location update via WebSocket
    if bus:
        try:
            await manager.broadcast_bus_location(bus.id, gps_data.latitude, gps_data.longitude, timestamp)
            # Broadcast to parents of students on this bus
            students = crud.get_students_by_bus(db, bus.id)
            for student in students:
                await manager.broadcast_student_location(
                    student.id, bus.id, gps_data.latitude, gps_data.longitude, timestamp
                )
        except Exception as e:
            print(f"Warning: Failed to broadcast GPS update: {str(e)}")
    
    return {
        "status": "success",
        "device_id": gps_data.device_id,
        "latitude": gps_data.latitude,
        "longitude": gps_data.longitude,
        "timestamp": timestamp,
        "is_near_school": is_near
    }


# WebSocket Endpoints
@app.websocket("/ws/admin/buses")
async def ws_admin_buses(websocket: WebSocket):
    """WebSocket endpoint for admin to track all buses."""
    await websocket_admin_buses(websocket)


@app.websocket("/ws/parent/{student_id}")
async def ws_parent_student(websocket: WebSocket, student_id: int):
    """WebSocket endpoint for parent to track a specific student's bus."""
    await websocket_parent_student(websocket, student_id)


@app.websocket("/ws/device/gps/{tracker_id}")
async def ws_device_gps(websocket: WebSocket, tracker_id: str):
    """WebSocket endpoint for GPS device to send location updates."""
    await websocket_device_gps(websocket, tracker_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


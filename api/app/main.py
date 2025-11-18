"""
FastAPI main application with all endpoints.
"""
import os
import tempfile
import shutil
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException, Header, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app import crud, models, schemas
from app.db import get_db, engine
from app.compreface_client import index_face, search_face, compare_faces, detect_face, detect_all_faces, extract_faces_from_image
from app.auth import authenticate_user, create_access_token, get_current_user, get_current_system_user
from app.utils import (
    save_face_image, get_image_url, parse_date, get_today_utc,
    parse_iso_datetime, get_storage_path
)

load_dotenv()

# Initialize database tables
models.Base.metadata.create_all(bind=engine)

# Create FastAPI app with increased max request size
app = FastAPI(
    title="Face Recognition API",
    description="API for ESP32-CAM face uploads, CompreFace integration, and image search",
    version="1.0.0"
)

# Note: Max request size is controlled by uvicorn/Starlette
# Default is 1MB, but we can handle larger files by reading them in chunks
# The actual limit is set in uvicorn command line or via environment variable

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8002",
        "http://127.0.0.1:8002",
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

# Get API key from environment
CAMERA_API_KEY = os.getenv("CAMERA_API_KEY", "changeme_camera_api_key")


def verify_api_key(x_api_key: str = Header(...)) -> bool:
    """Verify API key for camera uploads."""
    if x_api_key != CAMERA_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
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


def compare_with_reports_background(
    captured_image: models.CapturedImage,
    compreface_face_id: str
):
    """
    Background job to compare captured image with in-progress reports.
    """
    from app.db import SessionLocal
    from app.external_api import notify_external_api
    
    db = SessionLocal()
    try:
        # Get all open and in-progress reports (reports that are active)
        open_reports = crud.get_open_reports(db)
        in_progress_reports = crud.get_in_progress_reports(db)
        reports = open_reports + in_progress_reports
        
        if not reports:
            print("No active reports to compare with")
            return
        
        print(f"Comparing image {captured_image.id} with {len(reports)} in-progress reports...")
        
        # Compare with each report
        for report in reports:
            if not report.child_compreface_face_id:
                continue
            
            try:
                # Compare faces using CompreFace
                full_file_path = Path(get_storage_path()) / captured_image.file_path
                child_photo_path = Path(get_storage_path()) / report.child_photo_path
                
                if not full_file_path.exists() or not child_photo_path.exists():
                    continue
                
                similarity = compare_faces(str(full_file_path), str(child_photo_path))
                
                # If similarity > 0.88, create a match
                if similarity > 0.88:
                    print(f"Match found! Report {report.report_number} - Similarity: {similarity:.2%}")
                    
                    # Create report match
                    match = crud.create_report_match(
                        db=db,
                        report_id=report.id,
                        captured_image_id=captured_image.id,
                        similarity_score=similarity,
                        camera_id=captured_image.camera_id,
                        camera_name=captured_image.camera_name
                    )
                    
                    # Notify external API in background
                    try:
                        notify_external_api(report, captured_image, similarity, match.id)
                    except Exception as e:
                        print(f"Error notifying external API: {str(e)}")
                        
            except Exception as e:
                print(f"Error comparing with report {report.report_number}: {str(e)}")
                continue
                
    except Exception as e:
        print(f"Error in compare_with_reports_background: {str(e)}")
    finally:
        db.close()


def process_image_background(
    image_data: bytes,
    camera_id: str,
    camera_name: Optional[str],
    parsed_timestamp: datetime,
    temp_file_path: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    place_name: Optional[str] = None,
    description: Optional[str] = None
):
    """
    Background job to process uploaded image:
    1. Detect all faces in the image
    2. If multiple faces: extract each face and process separately
    3. If single face: process normally
    4. If no face: delete temporary file and ignore
    """
    from app.db import SessionLocal
    
    db = SessionLocal()
    try:
        # Detect all faces in the image
        detected_faces = []
        try:
            detected_faces = detect_all_faces(temp_file_path)
        except Exception as e:
            print(f"Error detecting faces: {str(e)}")
            # If detection fails, we'll ignore the image to be safe
            detected_faces = []
        
        if not detected_faces:
            # No face detected - delete temporary file and ignore
            print(f"No face detected in image from camera {camera_id}, ignoring...")
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass
            return
        
        num_faces = len(detected_faces)
        print(f"Detected {num_faces} face(s) in image from camera {camera_id}")
        
        # Create or update camera record
        try:
            camera = crud.create_or_update_camera(db, camera_id, camera_name)
        except Exception as e:
            print(f"Error creating/updating camera: {str(e)}")
        
        # Process each face separately
        if num_faces > 1:
            # Multiple faces detected - extract and process each face
            print(f"Multiple faces detected ({num_faces}), extracting individual faces...")
            
            # Create temp directory for extracted faces
            temp_dir = tempfile.mkdtemp()
            
            try:
                # Extract all faces from the image
                extracted_face_paths = extract_faces_from_image(temp_file_path, detected_faces, temp_dir)
                
                if not extracted_face_paths:
                    print(f"Warning: Failed to extract faces from image, processing original image as single face")
                    # Fallback to single face processing - save original image and process it
                    try:
                        original_file_path = save_face_image(image_data, camera_id, parsed_timestamp)
                        original_full_path = Path(get_storage_path()) / original_file_path
                        
                        compreface_face_id = index_face(str(original_full_path))
                        captured_image = crud.create_captured_image(
                            db=db,
                            camera_id=camera_id,
                            camera_name=camera_name,
                            timestamp=parsed_timestamp,
                            file_path=original_file_path,
                            compreface_face_id=compreface_face_id,
                            latitude=latitude,
                            longitude=longitude,
                            place_name=place_name,
                            description=description
                        )
                        if compreface_face_id:
                            compare_with_reports_background(captured_image, compreface_face_id)
                    except Exception as e:
                        print(f"Error in fallback single face processing: {str(e)}")
                    continue
                
                # Process each extracted face
                for face_idx, face_path in enumerate(extracted_face_paths):
                    try:
                        # Read the extracted face image
                        with open(face_path, 'rb') as f:
                            face_image_data = f.read()
                        
                        # Save extracted face to permanent storage
                        face_file_path = save_face_image(
                            face_image_data, 
                            camera_id, 
                            parsed_timestamp,
                            suffix=f"_face_{face_idx}"
                        )
                        face_full_path = Path(get_storage_path()) / face_file_path
                        
                        # Create captured image record for this face
                        captured_image = crud.create_captured_image(
                            db=db,
                            camera_id=camera_id,
                            camera_name=camera_name,
                            timestamp=parsed_timestamp,
                            file_path=face_file_path,
                            compreface_face_id=None,
                            latitude=latitude,
                            longitude=longitude,
                            place_name=place_name,
                            description=description
                        )
                        
                        # Index face in CompreFace
                        compreface_face_id = None
                        try:
                            compreface_face_id = index_face(str(face_full_path))
                            crud.update_captured_image_compreface_id(db, captured_image.id, compreface_face_id)
                            print(f"Successfully indexed face {face_idx} with ID: {compreface_face_id}")
                            
                            # Compare with reports in background
                            if compreface_face_id:
                                compare_with_reports_background(captured_image, compreface_face_id)
                        except Exception as e:
                            print(f"Warning: Failed to index face {face_idx} in CompreFace: {str(e)}")
                            # Continue with next face even if indexing fails
                        
                    except Exception as e:
                        print(f"Error processing face {face_idx}: {str(e)}")
                        # Continue with next face
                        continue
                
                # Clean up extracted faces from temp directory
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    print(f"Warning: Failed to clean up temp directory: {str(e)}")
                    
            except Exception as e:
                print(f"Error extracting faces: {str(e)}")
                # Fallback: try to process original image as single face
                try:
                    # Save original image
                    original_file_path = save_face_image(image_data, camera_id, parsed_timestamp)
                    original_full_path = Path(get_storage_path()) / original_file_path
                    
                    compreface_face_id = index_face(str(original_full_path))
                    # Create a single record for the original image
                    captured_image = crud.create_captured_image(
                        db=db,
                        camera_id=camera_id,
                        camera_name=camera_name,
                        timestamp=parsed_timestamp,
                        file_path=original_file_path,
                        compreface_face_id=compreface_face_id,
                        latitude=latitude,
                        longitude=longitude,
                        place_name=place_name,
                        description=description
                    )
                    if compreface_face_id:
                        compare_with_reports_background(captured_image, compreface_face_id)
                except Exception as e2:
                    print(f"Error in fallback processing: {str(e2)}")
        else:
            # Single face detected - process normally
            print(f"Single face detected, processing normally...")
            
            # Save original image file to permanent storage
            try:
                original_file_path = save_face_image(image_data, camera_id, parsed_timestamp)
                original_full_path = Path(get_storage_path()) / original_file_path
            except Exception as e:
                print(f"Error saving original image: {str(e)}")
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass
                return
            
            # Create captured image record
            try:
                captured_image = crud.create_captured_image(
                    db=db,
                    camera_id=camera_id,
                    camera_name=camera_name,
                    timestamp=parsed_timestamp,
                    file_path=original_file_path,
                    compreface_face_id=None,
                    latitude=latitude,
                    longitude=longitude,
                    place_name=place_name,
                    description=description
                )
            except Exception as e:
                print(f"Error creating captured image record: {str(e)}")
                try:
                    os.unlink(original_full_path)
                except Exception:
                    pass
                return
            
            # Index face in CompreFace
            compreface_face_id = None
            try:
                compreface_face_id = index_face(str(original_full_path))
                crud.update_captured_image_compreface_id(db, captured_image.id, compreface_face_id)
                print(f"Successfully indexed face with ID: {compreface_face_id}")
                
                # Compare with reports in background
                if compreface_face_id:
                    compare_with_reports_background(captured_image, compreface_face_id)
            except Exception as e:
                # Log error but don't fail - image is saved
                print(f"Warning: Failed to index face in CompreFace: {str(e)}")
        
        # Clean up temporary file
        try:
            os.unlink(temp_file_path)
        except Exception:
            pass
            
    except Exception as e:
        print(f"Error in background job: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


@app.post("/api/upload_camera_face", response_model=schemas.UploadResponse)
async def upload_camera_face(
    background_tasks: BackgroundTasks,
    camera_id: str = Form(...),
    camera_name: Optional[str] = Form(None),
    timestamp: Optional[str] = Form(None),
    image: UploadFile = File(...),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    place_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    x_api_key: str = Header(..., alias="X-API-KEY"),
    db: Session = Depends(get_db)
):
    """
    Upload an image from ESP32-CAM.
    The image will be processed in background: checked for faces, and saved only if a face is detected.
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
    
    # Save image temporarily for background processing
    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            tmp_file.write(image_data)
            temp_file_path = tmp_file.name
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save temporary image: {str(e)}"
        )
    
    # Add background task to process image (face detection, saving, indexing)
    background_tasks.add_task(
        process_image_background,
        image_data=image_data,
        camera_id=camera_id,
        camera_name=camera_name,
        parsed_timestamp=parsed_timestamp,
        temp_file_path=temp_file_path,
        latitude=latitude,
        longitude=longitude,
        place_name=place_name,
        description=description
    )
    
    # Return immediate response (processing happens in background)
    return schemas.UploadResponse(
        id=0,  # Will be set after background processing
        image_url="",  # Will be set after background processing
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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_system_user)
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
            compreface_face_id=img.compreface_face_id,
            latitude=img.latitude,
            longitude=img.longitude,
            place_name=img.place_name,
            description=img.description
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


# Authentication Endpoints
@app.post("/api/auth/login", response_model=schemas.Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login endpoint - returns JWT token."""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return schemas.Token(access_token=access_token, token_type="bearer")


@app.get("/api/auth/me", response_model=schemas.UserResponse)
async def get_current_user_info(
    current_user: models.User = Depends(get_current_user)
):
    """Get current user information."""
    return current_user


@app.post("/api/auth/refresh", response_model=schemas.Token)
async def refresh_token(
    current_user: models.User = Depends(get_current_user)
):
    """Refresh access token."""
    access_token = create_access_token(data={"sub": current_user.username})
    return schemas.Token(access_token=access_token, token_type="bearer")


# Missing Report Endpoints (Public)
@app.post("/api/reports/create", response_model=schemas.MissingReportResponse)
async def create_missing_report(
    reporter_name: str = Form(...),
    reporter_email: str = Form(...),
    reporter_phone: str = Form(...),
    child_name: str = Form(...),
    child_photo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Create a new missing report. Public endpoint - no auth required."""
    # Validate image file
    if not child_photo.content_type or not child_photo.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Read image data
    image_data = await child_photo.read()
    if len(image_data) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image file is empty"
        )
    
    # Save image temporarily for face detection
    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            tmp_file.write(image_data)
            temp_file_path = tmp_file.name
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save temporary image: {str(e)}"
        )
    
    # Detect all faces in the image
    detected_faces = []
    try:
        detected_faces = detect_all_faces(temp_file_path)
    except Exception as e:
        print(f"Error detecting faces: {str(e)}")
        detected_faces = []
    
    if not detected_faces:
        # Clean up temp file
        try:
            os.unlink(temp_file_path)
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image must contain at least one face"
        )
    
    # If multiple faces detected, extract the largest face (or first one)
    photo_path = None
    full_photo_path = None
    compreface_face_id = None
    
    if len(detected_faces) > 1:
        print(f"Multiple faces detected ({len(detected_faces)}) in child photo, extracting largest face...")
        
        # Find the largest face (by area)
        largest_face = None
        largest_area = 0
        for face in detected_faces:
            box = face.get("box", {})
            area = (box.get("x_max", 0) - box.get("x_min", 0)) * (box.get("y_max", 0) - box.get("y_min", 0))
            if area > largest_area:
                largest_area = area
                largest_face = face
        
        if largest_face:
            # Extract the largest face
            temp_dir = tempfile.mkdtemp()
            try:
                extracted_faces = extract_faces_from_image(temp_file_path, [largest_face], temp_dir)
                if extracted_faces:
                    # Read the extracted face
                    with open(extracted_faces[0], 'rb') as f:
                        face_image_data = f.read()
                    
                    # Save the extracted face
                    photo_path = save_face_image(face_image_data, "reports", datetime.utcnow())
                    full_photo_path = Path(get_storage_path()) / photo_path
                    
                    # Index the extracted face
                    try:
                        compreface_face_id = index_face(str(full_photo_path))
                    except Exception as e:
                        print(f"Warning: Failed to index extracted face in CompreFace: {str(e)}")
                    
                    # Clean up temp directory
                    try:
                        shutil.rmtree(temp_dir)
                    except Exception:
                        pass
                else:
                    # Fallback to original image
                    photo_path = save_face_image(image_data, "reports", datetime.utcnow())
                    full_photo_path = Path(get_storage_path()) / photo_path
            except Exception as e:
                print(f"Error extracting face: {str(e)}")
                # Fallback to original image
                photo_path = save_face_image(image_data, "reports", datetime.utcnow())
                full_photo_path = Path(get_storage_path()) / photo_path
        else:
            # Fallback to original image
            photo_path = save_face_image(image_data, "reports", datetime.utcnow())
            full_photo_path = Path(get_storage_path()) / photo_path
    else:
        # Single face - save original image
        try:
            photo_path = save_face_image(image_data, "reports", datetime.utcnow())
            full_photo_path = Path(get_storage_path()) / photo_path
        except Exception as e:
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save image: {str(e)}"
            )
    
    # Index face in CompreFace if not already indexed
    if not compreface_face_id:
        try:
            compreface_face_id = index_face(str(full_photo_path))
        except Exception as e:
            print(f"Warning: Failed to index face in CompreFace: {str(e)}")
    
    # Create report
    try:
        report = crud.create_missing_report(
            db=db,
            reporter_name=reporter_name,
            reporter_email=reporter_email,
            reporter_phone=reporter_phone,
            child_name=child_name,
            child_photo_path=photo_path,
            child_compreface_face_id=compreface_face_id
        )
    except Exception as e:
        # Clean up saved file
        try:
            os.unlink(full_photo_path)
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create report: {str(e)}"
        )
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_file_path)
        except Exception:
            pass
    
    return schemas.MissingReportResponse(
        id=report.id,
        report_number=report.report_number,
        reporter_name=report.reporter_name,
        reporter_email=report.reporter_email,
        reporter_phone=report.reporter_phone,
        child_name=report.child_name,
        child_photo_url=get_image_url(report.child_photo_path),
        status=report.status.value,
        created_at=report.created_at,
        updated_at=report.updated_at,
        closed_at=report.closed_at
    )


@app.post("/api/reports/track", response_model=schemas.ReportTrackResponse)
async def track_report(
    track_request: schemas.ReportTrackRequest,
    db: Session = Depends(get_db)
):
    """Track a report by phone and report number. Public endpoint."""
    report = crud.get_missing_report_by_phone_and_number(
        db, track_request.phone, track_request.report_number
    )
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found or phone number does not match"
        )
    
    # Get matches
    matches = crud.get_report_matches(db, report.id)
    match_responses = []
    for match in matches:
        captured_image = crud.get_image_by_id(db, match.captured_image_id)
        if captured_image:
            match_responses.append(schemas.ReportMatchResponse(
                id=match.id,
                report_id=match.report_id,
                captured_image_id=match.captured_image_id,
                similarity_score=match.similarity_score,
                camera_id=match.camera_id,
                camera_name=match.camera_name,
                matched_at=match.matched_at,
                image_url=get_image_url(captured_image.file_path)
            ))
    
    return schemas.ReportTrackResponse(
        report=schemas.MissingReportResponse(
            id=report.id,
            report_number=report.report_number,
            reporter_name=report.reporter_name,
            reporter_email=report.reporter_email,
            reporter_phone=report.reporter_phone,
            child_name=report.child_name,
            child_photo_url=get_image_url(report.child_photo_path),
            status=report.status.value,
            created_at=report.created_at,
            updated_at=report.updated_at,
            closed_at=report.closed_at
        ),
        matches=match_responses
    )


@app.post("/api/reports/{report_number}/close")
async def close_report_by_number(
    report_number: str,
    phone: str = Form(...),
    db: Session = Depends(get_db)
):
    """Close a report by report number and phone. Public endpoint."""
    report = crud.get_missing_report_by_phone_and_number(db, phone, report_number)
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found or phone number does not match"
        )
    
    if report.status == models.ReportStatus.CLOSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report is already closed"
        )
    
    crud.close_report(db, report.id)
    
    return {"message": "Report closed successfully", "report_number": report_number}


# Admin Report Endpoints (SystemUser Only)
@app.get("/api/admin/reports", response_model=schemas.ReportListResponse)
async def get_all_reports_admin(
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_system_user)
):
    """Get all reports with pagination. SystemUser only."""
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
    
    # Parse status filter
    status_enum = None
    if status_filter:
        try:
            status_enum = models.ReportStatus(status_filter)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}"
            )
    
    skip = (page - 1) * page_size
    reports, total = crud.get_all_reports(db, skip=skip, limit=page_size, status=status_enum)
    
    items = []
    for report in reports:
        items.append(schemas.MissingReportResponse(
            id=report.id,
            report_number=report.report_number,
            reporter_name=report.reporter_name,
            reporter_email=report.reporter_email,
            reporter_phone=report.reporter_phone,
            child_name=report.child_name,
            child_photo_url=get_image_url(report.child_photo_path),
            status=report.status.value,
            created_at=report.created_at,
            updated_at=report.updated_at,
            closed_at=report.closed_at
        ))
    
    total_pages = (total + page_size - 1) // page_size
    
    return schemas.ReportListResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=items
    )


@app.get("/api/admin/reports/{report_id}", response_model=schemas.MissingReportResponse)
async def get_report_by_id_admin(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_system_user)
):
    """Get report by ID. SystemUser only."""
    report = crud.get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    return schemas.MissingReportResponse(
        id=report.id,
        report_number=report.report_number,
        reporter_name=report.reporter_name,
        reporter_email=report.reporter_email,
        reporter_phone=report.reporter_phone,
        child_name=report.child_name,
        child_photo_url=get_image_url(report.child_photo_path),
        status=report.status.value,
        created_at=report.created_at,
        updated_at=report.updated_at,
        closed_at=report.closed_at
    )


@app.put("/api/admin/reports/{report_id}/status", response_model=schemas.MissingReportResponse)
async def update_report_status_admin(
    report_id: int,
    status_update: schemas.ReportStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_system_user)
):
    """Update report status. SystemUser only."""
    try:
        new_status = models.ReportStatus(status_update.status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {status_update.status}"
        )
    
    report = crud.update_report_status(db, report_id, new_status)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    return schemas.MissingReportResponse(
        id=report.id,
        report_number=report.report_number,
        reporter_name=report.reporter_name,
        reporter_email=report.reporter_email,
        reporter_phone=report.reporter_phone,
        child_name=report.child_name,
        child_photo_url=get_image_url(report.child_photo_path),
        status=report.status.value,
        created_at=report.created_at,
        updated_at=report.updated_at,
        closed_at=report.closed_at
    )


@app.get("/api/admin/reports/{report_id}/matches", response_model=List[schemas.ReportMatchResponse])
async def get_report_matches_admin(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_system_user)
):
    """Get all matches for a report. SystemUser only."""
    report = crud.get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    matches = crud.get_report_matches(db, report_id)
    match_responses = []
    for match in matches:
        captured_image = crud.get_image_by_id(db, match.captured_image_id)
        if captured_image:
            match_responses.append(schemas.ReportMatchResponse(
                id=match.id,
                report_id=match.report_id,
                captured_image_id=match.captured_image_id,
                similarity_score=match.similarity_score,
                camera_id=match.camera_id,
                camera_name=match.camera_name,
                matched_at=match.matched_at,
                image_url=get_image_url(captured_image.file_path)
            ))
    
    return match_responses


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


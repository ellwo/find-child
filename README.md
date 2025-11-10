# Face Recognition API - ESP32-CAM Integration

A complete FastAPI backend prototype that integrates ESP32-CAM cameras with CompreFace for face recognition and PostgreSQL for metadata storage. This system allows ESP32-CAM devices to upload cropped face images, which are indexed in CompreFace and stored in PostgreSQL for search and retrieval.

## Architecture

```
ESP32-CAM → FastAPI → CompreFace → PostgreSQL
                ↓
            Static File Serving
```

- **ESP32-CAM**: Detects faces locally and uploads cropped face images
- **FastAPI**: Receives uploads, indexes faces in CompreFace, stores metadata in PostgreSQL
- **CompreFace**: Face recognition service for indexing and searching faces
- **PostgreSQL**: Stores image metadata, camera information, and face IDs

## Features

- ✅ Upload cropped face images from ESP32-CAM cameras
- ✅ Automatic face indexing in CompreFace
- ✅ Search for faces by image with time range and similarity threshold
- ✅ List saved images with date and camera filters
- ✅ Pagination support
- ✅ Camera registration and tracking
- ✅ Health check endpoint
- ✅ Swagger UI documentation at `/docs`
- ✅ OpenAPI JSON at `/openapi.json`

## Prerequisites

- Docker and Docker Compose
- At least 4GB RAM (CompreFace requires significant memory)
- Ports 8000 (API/CompreFace) and 5432 (PostgreSQL) available

## Quick Start

1. **Clone and setup environment:**

```bash
cp .env.example .env
# Edit .env and set your COMPREFACE_API_KEY (see below)
```

2. **Get CompreFace API Key:**

   After starting the services, CompreFace will be available at `http://localhost:8000`. You need to:
   
   - Access CompreFace admin UI (usually at `http://localhost:8000/admin`)
   - Create a subject/collection for face recognition
   - Generate an API key for that subject
   - Update `COMPREFACE_API_KEY` in your `.env` file
   
   **Note**: The exact CompreFace API endpoints may vary by version. The implementation assumes:
   - Index endpoint: `POST /api/v1/faces`
   - Search endpoint: `POST /api/v1/search`
   - Compare endpoint: `POST /api/v1/verify`
   
   If your CompreFace version uses different endpoints, you may need to adjust `api/app/compreface_client.py`.

3. **Start services:**

```bash
docker-compose up -d
```

4. **Check health:**

```bash
curl http://localhost:8000/health
```

5. **Access Swagger UI:**

Open `http://localhost:8000/docs` in your browser.

## Configuration

### Environment Variables

See `.env.example` for all available configuration options:

- **Database**: PostgreSQL connection settings
- **CompreFace**: URL and API key for face recognition service
- **Storage**: Path for storing uploaded face images
- **Security**: API key for camera uploads (`CAMERA_API_KEY`)

### CompreFace Setup

CompreFace is included in `docker-compose.yml` using the official image `exadelinc/compreface:latest`. 

**Important**: You must configure CompreFace and obtain an API key:

1. Wait for CompreFace to fully start (may take 1-2 minutes)
2. Access CompreFace admin interface
3. Create a subject/collection
4. Generate an API key
5. Update `COMPREFACE_API_KEY` in `.env`
6. Restart the API service: `docker-compose restart api`

## API Endpoints

### 1. Upload Camera Face

Upload a cropped face image from ESP32-CAM.

**Endpoint**: `POST /api/upload_camera_face`

**Headers**:
- `X-API-KEY`: Camera API key (from `CAMERA_API_KEY` env var)

**Form Data**:
- `camera_id` (required): Unique camera identifier (e.g., `mall_cam_01`)
- `camera_name` (optional): Human-readable camera name
- `timestamp` (optional): ISO-8601 timestamp (e.g., `2025-11-10T15:30:00Z`). If omitted, server uses current UTC time.
- `image` (required): JPEG image file (cropped face, recommended 80x80 to 200x200 pixels)

**Example**:

```bash
curl -X POST "http://localhost:8000/api/upload_camera_face" \
  -H "X-API-KEY: changeme_camera_api_key" \
  -F "camera_id=mall_cam_01" \
  -F "camera_name=Mall Entrance Camera" \
  -F "timestamp=2025-11-10T15:30:00Z" \
  -F "image=@face.jpg"
```

**Response**:

```json
{
  "id": 1,
  "image_url": "/storage/faces/2025/11/10/mall_cam_01/153000_abc12345.jpg",
  "camera_id": "mall_cam_01",
  "timestamp": "2025-11-10T15:30:00Z",
  "compreface_face_id": "face_12345"
}
```

### 2. Search by Image

Search for similar faces using a query image.

**Endpoint**: `POST /api/search_by_image`

**Form Data**:
- `image` (required): Query image file
- `start_ts` (optional): Start of time window (ISO-8601). Default: 24 hours ago
- `end_ts` (optional): End of time window (ISO-8601). Default: now
- `threshold` (optional): Minimum similarity score (0.0-1.0). Default: 0.7
- `limit` (optional): Maximum results. Default: 50

**Example**:

```bash
curl -X POST "http://localhost:8000/api/search_by_image" \
  -F "image=@query_face.jpg" \
  -F "start_ts=2025-11-10T00:00:00Z" \
  -F "end_ts=2025-11-10T23:59:59Z" \
  -F "threshold=0.75" \
  -F "limit=20"
```

**Response**:

```json
{
  "results": [
    {
      "image_url": "/storage/faces/2025/11/10/mall_cam_01/153000_abc12345.jpg",
      "camera_id": "mall_cam_01",
      "camera_name": "Mall Entrance Camera",
      "timestamp": "2025-11-10T15:30:00Z",
      "similarity": 0.89
    }
  ],
  "total": 1
}
```

**Fallback Behavior**: If CompreFace search API doesn't return face IDs directly, the system falls back to:
1. Querying the database for all images in the time window
2. Comparing the query image with each candidate using CompreFace compare endpoint
3. Filtering by similarity threshold

This fallback is slower but more reliable. It's automatically used when the primary search method fails.

### 3. Get Saved Images

List saved face images with filters and pagination.

**Endpoint**: `GET /api/saved_images`

**Query Parameters**:
- `start_date` (optional): Start date (YYYY-MM-DD). Default: today (UTC)
- `end_date` (optional): End date (YYYY-MM-DD). Default: `start_date` (so default returns today's images)
- `camera_ids` (optional): Comma-separated camera IDs to filter (e.g., `mall_cam_01,office_cam_02`)
- `page` (optional): Page number. Default: 1
- `page_size` (optional): Items per page (max 100). Default: 20

**Example**:

```bash
curl "http://localhost:8000/api/saved_images?start_date=2025-11-10&end_date=2025-11-10&camera_ids=mall_cam_01&page=1&page_size=20"
```

**Response**:

```json
{
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8,
  "items": [
    {
      "id": 1,
      "camera_id": "mall_cam_01",
      "camera_name": "Mall Entrance Camera",
      "timestamp": "2025-11-10T15:30:00Z",
      "image_url": "/storage/faces/2025/11/10/mall_cam_01/153000_abc12345.jpg",
      "compreface_face_id": "face_12345"
    }
  ]
}
```

### 4. Get Cameras

List all registered cameras.

**Endpoint**: `GET /api/cameras`

**Example**:

```bash
curl "http://localhost:8000/api/cameras"
```

**Response**:

```json
[
  {
    "id": 1,
    "code": "mall_cam_01",
    "name": "Mall Entrance Camera",
    "first_seen": "2025-11-10T10:00:00Z",
    "last_seen": "2025-11-10T18:30:00Z",
    "total_images": 245
  }
]
```

### 5. Health Check

Check system health and connectivity.

**Endpoint**: `GET /health`

**Example**:

```bash
curl "http://localhost:8000/health"
```

**Response**:

```json
{
  "status": "healthy",
  "database": "connected",
  "compreface": "connected",
  "stats": {
    "total_images": 1234,
    "total_cameras": 5
  }
}
```

## ESP32-CAM Integration

### Payload Format

ESP32-CAM devices should send HTTP POST requests to `/api/upload_camera_face` with the following:

**Headers**:
```
X-API-KEY: <CAMERA_API_KEY>
Content-Type: multipart/form-data
```

**Body (multipart/form-data)**:
- `camera_id` (string, required): Unique camera identifier (e.g., `mall_cam_01`)
- `camera_name` (string, optional): Human-readable name
- `timestamp` (string, optional): ISO-8601 format (e.g., `2025-11-10T15:30:00Z`). If omitted, server uses current UTC time.
- `image` (file, required): JPEG binary data of cropped face image

**Important Notes**:
- ESP32-CAM should **only send cropped face images** (not full frames) to minimize bandwidth
- Use local face detection (e.g., ESP-WHO library) to crop faces before uploading
- Recommended image size: 80x80 to 200x200 pixels
- Send at a reasonable rate to avoid flooding the API
- The backend handles deduplication and indexing

### Example ESP32-CAM Code Structure

```cpp
// Pseudocode for ESP32-CAM
void uploadFace(camera_fb_t* fb, String cameraId) {
  HTTPClient http;
  http.begin("http://your-api:8000/api/upload_camera_face");
  http.addHeader("X-API-KEY", CAMERA_API_KEY);
  
  http.addHeader("Content-Type", "multipart/form-data");
  
  // Create multipart form data
  String body = "--boundary\r\n";
  body += "Content-Disposition: form-data; name=\"camera_id\"\r\n\r\n";
  body += cameraId + "\r\n";
  body += "--boundary\r\n";
  body += "Content-Disposition: form-data; name=\"image\"; filename=\"face.jpg\"\r\n";
  body += "Content-Type: image/jpeg\r\n\r\n";
  // Append image data
  body += "--boundary--\r\n";
  
  http.POST(body);
  http.end();
}
```

## File Storage

Face images are stored in an organized directory structure:

```
{STORAGE_PATH}/faces/YYYY/MM/DD/{camera_id}/{HHMMSS}_{random}.jpg
```

Example:
```
/data/storage/faces/2025/11/10/mall_cam_01/153000_abc12345.jpg
```

Images are served as static files at `/storage/faces/...` URLs.

## Database Schema

### Tables

**cameras**:
- `id` (PK): Auto-increment integer
- `code` (unique): Camera identifier string
- `name`: Optional camera name
- `first_seen_ts`: First image timestamp
- `last_seen_ts`: Most recent image timestamp
- `total_images`: Count of images from this camera

**captured_images**:
- `id` (PK): Auto-increment integer
- `camera_id` (FK): References `cameras.code`
- `camera_name`: Camera name at time of capture
- `timestamp`: UTC timestamp of capture
- `file_path`: Relative path to stored image
- `compreface_face_id`: Face ID from CompreFace (nullable)
- `created_at`: Record creation timestamp

## Similarity Thresholds

The similarity threshold (`threshold` parameter) controls how strict the face matching is:

- **0.9-1.0**: Very strict, only very similar faces
- **0.7-0.9**: Moderate, good balance (default: 0.7)
- **0.5-0.7**: Lenient, more matches but may include false positives
- **< 0.5**: Very lenient, many matches but high false positive rate

**Recommendation**: Start with 0.7 and adjust based on your use case.

## Troubleshooting

### CompreFace Connection Issues

1. Check if CompreFace is running: `docker-compose ps`
2. Wait for CompreFace to fully initialize (may take 1-2 minutes)
3. Verify API key is correct in `.env`
4. Check CompreFace logs: `docker-compose logs compreface`
5. Verify CompreFace API endpoints match your version (see `api/app/compreface_client.py`)

### Database Connection Issues

1. Check PostgreSQL is running: `docker-compose ps postgres`
2. Verify database credentials in `.env`
3. Check PostgreSQL logs: `docker-compose logs postgres`
4. Ensure `DATABASE_URL` or `POSTGRES_*` variables are set correctly

### Image Upload Fails

1. Verify `X-API-KEY` header matches `CAMERA_API_KEY` in `.env`
2. Check file size (should be reasonable for cropped faces)
3. Verify image format is JPEG
4. Check API logs: `docker-compose logs api`

### Search Returns No Results

1. Verify faces are being indexed (check `compreface_face_id` in responses)
2. Adjust similarity threshold (try lower values like 0.5)
3. Check time range covers when images were uploaded
4. Verify CompreFace search API is working (check logs)

## Security Considerations

This is a **prototype** system. For production use:

- ✅ Use HTTPS/TLS for all API communication
- ✅ Use strong, unique API keys and rotate them regularly
- ✅ Implement rate limiting on upload endpoints
- ✅ Add authentication/authorization for search endpoints
- ✅ Restrict network access to internal networks only
- ✅ Regularly update dependencies
- ✅ Implement proper logging and monitoring
- ✅ Use secrets management (not plain `.env` files)
- ✅ Add input validation and sanitization
- ✅ Implement CORS policies if serving web UI

## Development

### Project Structure

```
.
├── docker-compose.yml          # Service orchestration
├── .env.example                # Environment variable template
├── README.md                   # This file
└── api/
    ├── Dockerfile              # API container definition
    ├── requirements.txt        # Python dependencies
    └── app/
        ├── __init__.py
        ├── main.py             # FastAPI application
        ├── db.py               # Database connection
        ├── models.py           # SQLAlchemy models
        ├── schemas.py          # Pydantic schemas
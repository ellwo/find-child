You are an expert backend engineer. Create a complete, runnable prototype repository that implements a FastAPI backend integrated with CompreFace and PostgreSQL, packaged and run via docker-compose. Keep it minimal and focused: this is a working prototype for testing the flow ESP32-CAM -> API -> CompreFace -> Postgres -> UI.

Goal
- ESP32-CAM cameras detect faces locally, upload cropped face images to the API.
- The API indexes every uploaded face in CompreFace and stores metadata in Postgres.
- The API provides search by image (time range + threshold) using CompreFace, and a `/saved_images` endpoint to list saved images with filters and pagination.
- FastAPI must provide Swagger UI at `/docs` and OpenAPI JSON at `/openapi.json`.

High-level requirements
1. Tech stack:
   - Python 3.11+, FastAPI, SQLAlchemy, Pydantic, Requests, python-multipart.
   - Postgres (configured from `.env`, allow preference for DATABASE_URL).
   - CompreFace service in docker-compose, accessible by COMPREFACE_URL and COMPREFACE_API_KEY in `.env`.
   - Simple local file storage for face crops (no cloud). Serve images as static files for prototype.

2. docker-compose:
   - One `docker-compose.yml` with three services: `api`, `postgres`, `compreface`.
   - `postgres` uses official image (e.g., `postgres:15`) with env from `.env`.
   - `compreface` use `exadelinc/compreface:latest` (document assumption in README).
   - `api` built from `./api` and uses `env_file: .env`. Ensure network allows `api` to reach `compreface` and `postgres`.
   - Provide persistent volumes for Postgres and the API storage folder.

3. `.env.example`:
   - Include:
     POSTGRES_USER=postgres
     POSTGRES_PASSWORD=changeme
     POSTGRES_DB=facesdb
     POSTGRES_HOST=postgres
     POSTGRES_PORT=5432
     DATABASE_URL=postgresql://postgres:changeme@postgres:5432/facesdb
     COMPREFACE_URL=http://compreface:8000
     COMPREFACE_API_KEY=changeme_compreface_key
     BACKEND_HOST=0.0.0.0
     BACKEND_PORT=8000
     SECRET_KEY=verysecret
     STORAGE_PATH=/data/storage
   - App should prefer DATABASE_URL if present, otherwise build URL from POSTGRES_* values.

4. API endpoints and behavior (must include OpenAPI/Swagger docs):
   - `POST /api/upload_camera_face`
     - Accept multipart/form-data fields:
       * `camera_id` (string, required) — unique camera code (e.g., mall_cam_01)
       * `camera_name` (string, optional)
       * `timestamp` (ISO-8601 string, optional). If omitted, use server UTC now.
       * `image` (file, required) — JPEG of cropped face (ESP32 should send cropped face only).
     - Security: require `X-API-KEY` header for camera uploads (simple API key check).
     - On receive:
       * Validate API key.
       * Save file under `{STORAGE_PATH}/faces/YYYY/MM/DD/{camera_id}/{HHMMSS}_{random}.jpg`.
       * Create DB record in table `captured_images` with fields: id (PK), camera_id, camera_name, timestamp (UTC), file_path, compreface_face_id (nullable).
       * Call CompreFace index API to index this face and store returned `compreface_face_id` into the DB record.
       * Return JSON with stored id, public image URL, camera_id, timestamp, and compreface_face_id.
   - `POST /api/search_by_image`
     - Accept multipart/form-data:
       * `image` (file, required) — query image.
       * `start_ts` (ISO optional) — start of time window; if absent, default to 24 hours before now.
       * `end_ts` (ISO optional) — end of time window; if absent, default to now.
       * `threshold` (float optional 0..1, default 0.7) — min similarity to include match.
       * `limit` (int optional, default 50) — max results requested from CompreFace.
     - Behavior:
       * Save query image temporarily.
       * Send query image to CompreFace search API and obtain candidate `face_id` + similarity scores.
       * Map returned `face_id`s to DB rows by `compreface_face_id`.
       * Filter resulting rows by timestamp being between start_ts and end_ts, and similarity >= threshold.
       * Return JSON list sorted by similarity descending: `{image_url, camera_id, camera_name, timestamp, similarity}`.
       * If CompreFace search cannot return face IDs, implement a documented fallback: query DB for candidate images in time window and call CompreFace compare endpoint per candidate (note this will be slower). Document fallback in README.
   - `GET /api/saved_images`
     - Purpose: list stored face images with metadata; supports filters and pagination.
     - Query parameters:
       * `start_date` (YYYY-MM-DD optional) — default = today (server local date or UTC; choose UTC and document).
       * `end_date` (YYYY-MM-DD optional) — default = start_date (so default returns today's images).
       * `camera_ids` (comma separated camera_id list optional) — if provided, filter those cameras. If not provided, default to ESP32 cameras (explain camera_type below) or all cameras. The prototype should support filtering by camera_id values.
       * `page` (int optional, default 1)
       * `page_size` (int optional, default 20, max 100)
     - Behavior:
       * Return paginated results with metadata: `{total, page, page_size, total_pages, items: [{id, image_url, camera_id, camera_name, timestamp, compreface_face_id}]}`.
       * Default `page_size` is 20.
   - `GET /api/cameras` — list registered cameras (id, name, first_seen, last_seen, total_images).
   - `GET /health` — returns overall health: DB reachable, CompreFace reachable, and basic stats (optional).

5. Database & models
   - Use SQLAlchemy ORM.
   - Models:
     * `Camera` with id (PK auto), code (unique camera_id string), name, first_seen_ts, last_seen_ts, total_images (counts maintained on ingest).
     * `CapturedImage` with id (PK), camera_id (FK to Camera.code or camera.id), camera_name, timestamp (UTC), file_path (absolute or relative), compreface_face_id (string), created_at.
   - Provide `init_db.py` to create tables automatically.

6. CompreFace client
   - `compreface_client.py` module with two functions:
     * `index_face(file_path) -> compreface_face_id` — calls COMPREFACE_URL index endpoint, returns face id or raises error; retry lightly on transient failures.
     * `search_face(query_file_path, limit=50) -> list[{"face_id": str, "score": float}]` — calls CompreFace search endpoint and returns list.
   - Read COMPREFACE_URL and COMPREFACE_API_KEY from env; document exact endpoints assumed and note they may need adjustment.
   - Store the `compreface_face_id` returned by index_face in DB immediately after successful indexing.

7. File storage & serving
   - Use STORAGE_PATH from .env.
   - Save only cropped face images (ESP32 must crop before sending).
   - Expose `/storage/faces/...` as static files served by the API (for prototype). Provide correct public URLs in API responses.

8. ESP32-CAM payload example (explain clearly so firmware devs know what to send)
   - HTTP POST to `/api/upload_camera_face`
   - Headers:
     * `X-API-KEY: <CAMERA_API_KEY>` (backend must validate)
     * `Content-Type: multipart/form-data`
   - Body fields:
     * `camera_id` (string) — e.g., `mall_cam_01`
     * `camera_name` (optional) — human readable name
     * `timestamp` (optional ISO-8601) — e.g., `2025-11-10T15:30:00Z`. If omitted, server uses current UTC.
     * `image` — binary JPEG of cropped face (recommended size 80x80..200x200)
     * (optional) `location` — textual location if available
   - ESP32 should only send **cropped face images** to minimize bandwidth. Use local face detection (ESP-WHO) to crop. Send at a reasonable rate (avoid flooding); backend will deduplicate/ingest.

9. Pagination, filters, defaults (implementation rules)
   - `/saved_images` defaults:
     * If `start_date` and `end_date` are omitted, return images from today (UTC) only.
     * `page_size` defaults to 20 and cannot exceed 100.
   - Return proper HTTP status codes and helpful error messages for invalid params.

10. Security & config
    - Load secrets and config from `.env` via `python-dotenv` or environment variables.
    - Use a simple API key check for camera uploads; include a `CAMERA_API_KEY` value in `.env.example` or allow multiple keys stored in a config table for prototype.
    - Document basic security suggestions in README (HTTPS, long-lived API keys, rotate keys, limit exposure).

11. Deliverables (exact file list to create)
    - `docker-compose.yml`
    - `.env.example`
    - `README.md` with run instructions, where to get COMPREFACE_API_KEY, how to open `/docs`, example curl for upload and search, notes on thresholds, fallback behavior, and ESP32 payload.
    - `api/Dockerfile`
    - `api/requirements.txt`
    - `api/app/main.py` (FastAPI app + routers)
    - `api/app/db.py` (SQLAlchemy engine + session)
    - `api/app/models.py`
    - `api/app/schemas.py`
    - `api/app/crud.py`
    - `api/app/compreface_client.py`
    - `api/app/utils.py`
    - `api/app/init_db.py`
    - Any additional small helper files needed.
    - Keep code synchronous for simplicity. Use clear inline comments.

12. Behavior specifics (repeat key points)
    - On ingest: index face in CompreFace, store returned `compreface_face_id`.
    - On search: use CompreFace search, map returned face ids to DB rows, filter by timestamp threshold and return final matches.
    - `/saved_images` must support filters, default date = today, pagination 20 per page.

13. Testing and examples
    - Provide sample `curl` commands in README:
      * Upload camera face sample (with X-API-KEY header)
      * Search by image sample
      * Call `/saved_images` with pagination and date filters
    - Provide example responses for each.

14. Keep it minimal but runnable. If any CompreFace endpoint path or JSON differs between versions, implement a sensible default path and document how to change it. Mention fallback strategy in README.

Now generate the full repository files and their contents exactly as text so I can create the files locally. Do not ask clarifying questions — make reasonable assumptions if necessary, and document them in the README. Output only the files and their contents (organized by path).

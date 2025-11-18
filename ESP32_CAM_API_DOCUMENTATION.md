# ESP32-CAM Image Upload API Documentation

## Overview
This document describes how to upload images from ESP32-CAM to the Smart Mirrors System API. The API will automatically detect faces in the uploaded images and only save images that contain faces.

## Endpoint
**URL:** `POST /api/upload_camera_face`

**Base URL:** `http://your-backend-host:8000` (or your server IP/domain)

**Full URL:** `http://your-backend-host:8000/api/upload_camera_face`

## Authentication
You must include an API key in the request header:
- **Header Name:** `X-API-KEY`
- **Header Value:** Your camera API key (configured in backend `.env` file as `CAMERA_API_KEY`)

## Request Format
The request must be sent as **multipart/form-data** (standard HTTP file upload format).

## Required Fields

### Headers
- `X-API-KEY`: Your camera API key (required)
- `Content-Type`: Will be set automatically as `multipart/form-data` when using HTTPClient

### Form Fields

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| `camera_id` | string | **Yes** | Unique identifier for your camera (e.g., "mall_cam_01", "entrance_01") |
| `image` | file | **Yes** | The image file (JPEG format recommended) |
| `camera_name` | string | No | Human-readable camera name (e.g., "Mall Entrance Camera") |
| `timestamp` | string | No | ISO-8601 timestamp in UTC (e.g., "2025-01-15T10:30:00Z"). If not provided, server will use current time |
| `latitude` | float | No | GPS latitude coordinate (e.g., 24.7136) |
| `longitude` | float | No | GPS longitude coordinate (e.g., 46.6753) |
| `place_name` | string | No | Name of the location (e.g., "Riyadh Park Mall") |
| `description` | string | No | Additional description or notes |

## Response Format

### Success Response (200 OK)
```json
{
  "id": 0,
  "image_url": "",
  "camera_id": "mall_cam_01",
  "timestamp": "2025-01-15T10:30:00Z",
  "compreface_face_id": null
}
```

**Note:** The response is returned immediately. Image processing (face detection, saving, indexing) happens in the background. The `id` and `image_url` will be 0 and empty respectively in the immediate response.

### Error Responses

**401 Unauthorized:**
```json
{
  "detail": "Invalid API key"
}
```

**400 Bad Request:**
```json
{
  "detail": "File must be an image"
}
```
or
```json
{
  "detail": "Image file is empty"
}
```

## Example Code (Arduino/ESP32)

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include "esp_camera.h"

// Configuration
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* BACKEND_URL = "http://your-backend-host:8000/api/upload_camera_face";
const char* CAMERA_API_KEY = "your_camera_api_key";
const char* CAMERA_ID = "mall_cam_01";
const char* CAMERA_NAME = "Mall Entrance Camera";

// GPS coordinates (if available)
float latitude = 24.7136;
float longitude = 46.6753;
const char* place_name = "Riyadh Park Mall";
const char* description = "Main entrance camera";

void setup() {
  Serial.begin(115200);
  
  // Connect to WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  
  // Initialize camera (your camera init code here)
  // ...
}

void loop() {
  // Capture image
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed");
    return;
  }
  
  // Upload image
  uploadImage(fb->buf, fb->len);
  
  // Return frame buffer
  esp_camera_fb_return(fb);
  
  delay(5000); // Wait 5 seconds before next capture
}

void uploadImage(uint8_t* imageData, size_t imageLen) {
  HTTPClient http;
  
  http.begin(BACKEND_URL);
  http.addHeader("X-API-KEY", CAMERA_API_KEY);
  
  // Create multipart form data
  String boundary = "----ESP32CAMBoundary";
  http.addHeader("Content-Type", "multipart/form-data; boundary=" + boundary);
  
  // Build multipart body
  String body = "";
  
  // camera_id field
  body += "--" + boundary + "\r\n";
  body += "Content-Disposition: form-data; name=\"camera_id\"\r\n\r\n";
  body += String(CAMERA_ID) + "\r\n";
  
  // camera_name field (optional)
  if (CAMERA_NAME) {
    body += "--" + boundary + "\r\n";
    body += "Content-Disposition: form-data; name=\"camera_name\"\r\n\r\n";
    body += String(CAMERA_NAME) + "\r\n";
  }
  
  // timestamp field (optional - ISO-8601 format)
  String timestamp = getISOTimestamp();
  body += "--" + boundary + "\r\n";
  body += "Content-Disposition: form-data; name=\"timestamp\"\r\n\r\n";
  body += timestamp + "\r\n";
  
  // latitude field (optional)
  if (latitude != 0.0) {
    body += "--" + boundary + "\r\n";
    body += "Content-Disposition: form-data; name=\"latitude\"\r\n\r\n";
    body += String(latitude, 6) + "\r\n";
  }
  
  // longitude field (optional)
  if (longitude != 0.0) {
    body += "--" + boundary + "\r\n";
    body += "Content-Disposition: form-data; name=\"longitude\"\r\n\r\n";
    body += String(longitude, 6) + "\r\n";
  }
  
  // place_name field (optional)
  if (place_name) {
    body += "--" + boundary + "\r\n";
    body += "Content-Disposition: form-data; name=\"place_name\"\r\n\r\n";
    body += String(place_name) + "\r\n";
  }
  
  // description field (optional)
  if (description) {
    body += "--" + boundary + "\r\n";
    body += "Content-Disposition: form-data; name=\"description\"\r\n\r\n";
    body += String(description) + "\r\n";
  }
  
  // image file field
  body += "--" + boundary + "\r\n";
  body += "Content-Disposition: form-data; name=\"image\"; filename=\"image.jpg\"\r\n";
  body += "Content-Type: image/jpeg\r\n\r\n";
  
  // Calculate total body size
  size_t bodyStartLen = body.length();
  size_t totalLen = bodyStartLen + imageLen + (boundary.length() + 6); // +6 for closing boundary
  
  // Send request
  http.beginRequest();
  http.POST();
  http.sendHeader("Content-Length", String(totalLen));
  
  // Send body start
  http.write((uint8_t*)body.c_str(), bodyStartLen);
  
  // Send image data
  http.write(imageData, imageLen);
  
  // Send closing boundary
  String closing = "\r\n--" + boundary + "--\r\n";
  http.write((uint8_t*)closing.c_str(), closing.length());
  
  http.endRequest();
  
  // Get response
  int httpCode = http.getResponseCode();
  String response = http.getString();
  
  Serial.print("HTTP Response code: ");
  Serial.println(httpCode);
  Serial.print("Response: ");
  Serial.println(response);
  
  http.end();
  
  if (httpCode == 200) {
    Serial.println("Image uploaded successfully!");
  } else {
    Serial.print("Upload failed with code: ");
    Serial.println(httpCode);
  }
}

String getISOTimestamp() {
  // Get current time and format as ISO-8601
  // Example: "2025-01-15T10:30:00Z"
  // Note: You may need to sync time via NTP for accurate timestamps
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) {
    return "";
  }
  
  char buffer[30];
  strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%SZ", &timeinfo);
  return String(buffer);
}
```

## Alternative: Using HTTPClient Stream (More Memory Efficient)

For large images, you can use streaming to avoid loading the entire image into memory:

```cpp
void uploadImageStream(uint8_t* imageData, size_t imageLen) {
  HTTPClient http;
  WiFiClient *client;
  
  http.begin(BACKEND_URL);
  http.addHeader("X-API-KEY", CAMERA_API_KEY);
  
  String boundary = "----ESP32CAMBoundary";
  http.addHeader("Content-Type", "multipart/form-data; boundary=" + boundary);
  
  // Start request
  http.beginRequest();
  http.POST();
  
  // Build and send form fields
  String partStart = "--" + boundary + "\r\n";
  partStart += "Content-Disposition: form-data; name=\"camera_id\"\r\n\r\n";
  partStart += String(CAMERA_ID) + "\r\n";
  
  // Add other fields...
  
  // Image header
  partStart += "--" + boundary + "\r\n";
  partStart += "Content-Disposition: form-data; name=\"image\"; filename=\"image.jpg\"\r\n";
  partStart += "Content-Type: image/jpeg\r\n\r\n";
  
  // Send headers and form fields
  client = http.getStreamPtr();
  if (client) {
    client->print(partStart);
    
    // Stream image data
    size_t written = 0;
    const uint8_t* ptr = imageData;
    size_t remain = imageLen;
    
    while (remain > 0) {
      size_t toWrite = (remain > 1024) ? 1024 : remain;
      size_t actuallyWritten = client->write(ptr, toWrite);
      if (actuallyWritten == 0) break;
      written += actuallyWritten;
      ptr += actuallyWritten;
      remain -= actuallyWritten;
    }
    
    // Closing boundary
    String closing = "\r\n--" + boundary + "--\r\n";
    client->print(closing);
  }
  
  http.endRequest();
  
  int httpCode = http.getResponseCode();
  Serial.print("HTTP Code: ");
  Serial.println(httpCode);
  
  http.end();
}
```

## Important Notes

1. **Face Detection**: The server automatically detects faces in uploaded images. Images without faces will be ignored and not saved.

2. **Background Processing**: Image processing happens in the background. The API returns immediately, so don't wait for processing to complete.

3. **Image Format**: JPEG format is recommended for smaller file sizes. The server accepts any image format (JPEG, PNG, etc.).

4. **Rate Limiting**: Implement a minimum interval between uploads (e.g., 2-5 seconds) to avoid overwhelming the server.

5. **Error Handling**: Always check the HTTP response code. Retry failed uploads with exponential backoff.

6. **GPS Coordinates**: If your ESP32 has GPS module, include latitude and longitude. This helps track where images were captured.

7. **Timestamp Format**: Use ISO-8601 format with 'Z' suffix for UTC time (e.g., "2025-01-15T10:30:00Z"). Sync time via NTP for accuracy.

8. **Memory Management**: For large images, use streaming upload to avoid running out of memory.

## Testing

You can test the API using curl:

```bash
curl -X POST http://your-backend-host:8000/api/upload_camera_face \
  -H "X-API-KEY: your_camera_api_key" \
  -F "camera_id=mall_cam_01" \
  -F "camera_name=Test Camera" \
  -F "latitude=24.7136" \
  -F "longitude=46.6753" \
  -F "place_name=Test Location" \
  -F "description=Test upload" \
  -F "image=@/path/to/image.jpg"
```

## Support

For issues or questions, contact the backend development team.


# ESP32-CAM Setup Guide for Safe Journey System

## Hardware Requirements

- ESP32-CAM Development Board (AI-Thinker or compatible)
- USB to Serial adapter (for programming)
- Power supply (5V, 2A recommended)
- MicroSD card (optional, for local storage)

## Software Requirements

### Arduino IDE Setup

1. **Install ESP32 Board Support**:
   - Open Arduino IDE
   - Go to **File → Preferences**
   - Add this URL to "Additional Board Manager URLs":
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - Go to **Tools → Board → Boards Manager**
   - Search for "ESP32" and install "esp32 by Espressif Systems"

2. **Select Board**:
   - Go to **Tools → Board → ESP32 Arduino → AI Thinker ESP32-CAM**

3. **Required Libraries** (usually included with ESP32):
   - WiFi
   - HTTPClient
   - esp_camera.h (included with ESP32 board support)

4. **Additional Files Needed**:
   - `camera_pins.h` - Pin definitions for ESP32-CAM
     - This file should be in the same directory as your `.ino` file
     - If missing, you can find it in ESP32 examples: **File → Examples → ESP32 → Camera → CameraWebServer**

## Configuration

Before uploading, update these values in `esp_cam.ino`:

```cpp
// WiFi Configuration
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Backend API Configuration
const char* BACKEND_UPLOAD_URL = "http://your-api-server:8000/api/upload_camera_face";
const char* CAMERA_API_KEY = "changeme_camera_api_key";  // Must match CAMERA_API_KEY in .env
const char* CAMERA_ID = "bus_cam_01";  // Camera ID - will be created automatically
const char* CAMERA_NAME = "Bus Camera 01";  // Optional camera name

// Upload Settings
const unsigned long UPLOAD_INTERVAL_MS = 5000;  // Upload every 5 seconds
```

### Important Notes:

1. **CAMERA_API_KEY**: Must match the `CAMERA_API_KEY` value in your `.env` file
   - Default: `changeme_camera_api_key`
   - Change this in production!

2. **BACKEND_UPLOAD_URL**:
   - For local development: `http://localhost:8000/api/upload_camera_face`
   - For production: `http://your-server-ip:8000/api/upload_camera_face`
   - If using HTTPS: `https://your-domain.com/api/upload_camera_face`

3. **CAMERA_ID**: 
   - This will be automatically created in the database if it doesn't exist
   - Use a unique ID for each camera (e.g., `bus_cam_01`, `bus_cam_02`)
   - This ID should match the `camera_id` used when creating buses in the admin panel

4. **UPLOAD_INTERVAL_MS**:
   - Default: 5000ms (5 seconds)
   - Adjust based on your needs
   - Lower values = more frequent uploads = higher bandwidth usage
   - Higher values = less frequent uploads = lower bandwidth usage

## Upload Instructions

1. **Connect ESP32-CAM**:
   - Connect USB to Serial adapter to ESP32-CAM
   - Make sure GPIO0 is connected to GND for upload mode
   - Connect to computer via USB

2. **Arduino IDE Settings**:
   - Select board: **Tools → Board → AI Thinker ESP32-CAM**
   - Select port: **Tools → Port → (your ESP32 port)**
   - Set upload speed: **Tools → Upload Speed → 115200**
   - Set partition scheme: **Tools → Partition Scheme → Huge APP (3MB No OTA/1MB SPIFFS)**

3. **Upload**:
   - Click **Upload** button
   - Wait for compilation and upload to complete
   - After upload, disconnect GPIO0 from GND and press RESET button

## Testing

1. **Open Serial Monitor**:
   - Go to **Tools → Serial Monitor**
   - Set baud rate to **115200**
   - You should see:
     - WiFi connection status
     - Camera initialization
     - NTP time sync
     - Image capture and upload confirmations

2. **Expected Output**:
   ```
   =========================================
   ESP32-CAM for Safe Journey System
   =========================================
   
   ✓ Camera initialized
   Connecting to WiFi: YourNetwork
   ........
   WiFi connected!
   IP address: 192.168.1.100
   ✓ NTP time synchronized
   
   =========================================
   Configuration:
     Camera ID: bus_cam_01
     Camera Name: Bus Camera 01
     API URL: http://your-api-server:8000/api/upload_camera_face
     Upload Interval: 5 seconds
   =========================================
   
   Starting image capture and upload...
   
   Captured frame: 640x480, size: 45234 bytes
   Uploading image: 45234 bytes, total payload: 45321 bytes
   Camera ID: bus_cam_01, Timestamp: 2024-01-01T12:00:00Z
   Upload HTTP code: 200
   ✓ Upload successful!
   ```

## Troubleshooting

### Camera Initialization Failed

- **Problem**: "Camera init failed with error 0x..."
- **Solutions**:
  - Check if PSRAM is enabled (required for ESP32-CAM)
  - Verify board selection is correct (AI Thinker ESP32-CAM)
  - Check camera module connections
  - Try different partition scheme

### WiFi Connection Failed

- **Problem**: "WiFi connection failed!"
- **Solutions**:
  - Check SSID and password are correct
  - Ensure WiFi is 2.4GHz (ESP32 doesn't support 5GHz)
  - Check signal strength (move closer to router)
  - Verify router allows new device connections

### Upload Failed

- **Problem**: "Upload failed" or HTTP error codes
- **Solutions**:
  - Verify `BACKEND_UPLOAD_URL` is correct and accessible
  - Check `CAMERA_API_KEY` matches `.env` file
  - Ensure API server is running
  - Check network connectivity
  - For HTTPS, ensure certificate is valid
  - Check Serial Monitor for detailed error messages

### No Images Being Captured

- **Problem**: "Camera capture failed"
- **Solutions**:
  - Check camera module is properly connected
  - Verify camera pins configuration
  - Check if camera module is compatible
  - Try resetting the board

### Out of Memory Errors

- **Problem**: "Failed to allocate memory"
- **Solutions**:
  - Reduce image quality: `config.jpeg_quality = 15` (higher = lower quality = smaller size)
  - Reduce frame size: `config.frame_size = FRAMESIZE_QVGA`
  - Increase partition size for APP
  - Reduce upload frequency

## Features

- ✅ Automatic WiFi connection with reconnection
- ✅ NTP time synchronization for accurate timestamps
- ✅ Automatic retry on upload failure (3 attempts)
- ✅ Detailed logging for debugging
- ✅ Web interface for live preview (optional)
- ✅ Background processing - camera gets immediate 200 OK response

## API Integration

The camera sends images to `/api/upload_camera_face` endpoint with:

- **Method**: POST
- **Content-Type**: multipart/form-data
- **Headers**:
  - `X-API-KEY`: Your camera API key
- **Form Fields**:
  - `camera_id` (required): Camera identifier
  - `camera_name` (optional): Human-readable camera name
  - `timestamp` (optional): ISO 8601 timestamp
  - `image` (required): JPEG image file

The backend processes images in the background using Celery, so the camera receives an immediate 200 OK response.

## Power Consumption

- **Active (capturing/uploading)**: ~200-300mA
- **Idle**: ~80-150mA
- **Deep Sleep** (not implemented): ~10-20μA

For battery-powered applications, consider implementing deep sleep between captures.

## Security Notes

⚠️ **Important**: 
- Change `CAMERA_API_KEY` in production
- Use HTTPS for production deployments
- Keep WiFi credentials secure
- Regularly update ESP32 firmware


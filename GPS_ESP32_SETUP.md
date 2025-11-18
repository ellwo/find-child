# GPS Tracker ESP32 Setup Guide

## Hardware Requirements

- ESP32 Development Board
- GPS Module (NEO-6M, NEO-7M, or compatible)
- Antenna for GPS module
- Power supply (USB or external)

## Wiring

Connect the GPS module to ESP32:

```
GPS Module    ESP32
-----------   -----
VCC      ->   5V (or 3.3V if module supports it)
GND      ->   GND
TX       ->   GPIO 16 (RXD2)
RX       ->   GPIO 17 (TXD2)
```

## Software Requirements

### Arduino IDE Libraries

Install the following libraries via Arduino Library Manager:

1. **WiFi** (usually included with ESP32 board support)
2. **HTTPClient** (usually included with ESP32 board support)
3. **ArduinoJson** by Benoit Blanchon (version 6.x or 7.x)
   - Install from: Library Manager → Search "ArduinoJson"
4. **TinyGPS++** by Mikal Hart
   - Install from: Library Manager → Search "TinyGPSPlus"

### ESP32 Board Support

1. Open Arduino IDE
2. Go to **File → Preferences**
3. Add this URL to "Additional Board Manager URLs":
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
4. Go to **Tools → Board → Boards Manager**
5. Search for "ESP32" and install "esp32 by Espressif Systems"
6. Select your board: **Tools → Board → ESP32 Arduino → ESP32 Dev Module**

## Configuration

Before uploading, update these values in `gps-esp.ino`:

```cpp
const char* ssid = "YOUR_WIFI_SSID";           // Your WiFi network name
const char* password = "YOUR_WIFI_PASSWORD";   // Your WiFi password
const char* api_url = "http://your-api-server:8000/api/device/gps/update";
const char* device_id = "GPS_TRACKER_001";      // Must match device_id in database
const char* api_key = "changeme_gps_api_key";  // Must match GPS_DEVICE_API_KEY in .env
```

### Important Notes:

1. **device_id**: This must match the `device_id` of a GPS tracker created in the admin panel.
   - Go to Admin Panel → Trackers → Create Tracker
   - Use the same `device_id` here

2. **api_url**: 
   - For local development: `http://localhost:8000/api/device/gps/update`
   - For production: `http://your-server-ip:8000/api/device/gps/update`
   - If using HTTPS: `https://your-domain.com/api/device/gps/update`

3. **api_key**: Must match the `GPS_DEVICE_API_KEY` value in your `.env` file

## Upload Instructions

1. Connect ESP32 to your computer via USB
2. Select the correct port: **Tools → Port → (your ESP32 port)**
3. Select board: **Tools → Board → ESP32 Dev Module**
4. Set upload speed: **Tools → Upload Speed → 115200**
5. Click **Upload** button

## Testing

1. Open Serial Monitor: **Tools → Serial Monitor**
2. Set baud rate to **115200**
3. You should see:
   - WiFi connection status
   - GPS data being received
   - API update confirmations

## Troubleshooting

### GPS Not Getting Fix

- **Problem**: "GPS: Waiting for fix..." message persists
- **Solutions**:
  - Ensure GPS module has clear view of sky
  - Wait 2-5 minutes for first fix (cold start)
  - Check antenna connection
  - Verify GPS module is powered correctly

### WiFi Connection Failed

- **Problem**: "WiFi connection failed!"
- **Solutions**:
  - Check SSID and password are correct
  - Ensure WiFi is 2.4GHz (ESP32 doesn't support 5GHz)
  - Check signal strength (move closer to router)
  - Verify router allows new device connections

### API Update Failed

- **Problem**: "HTTP Request failed" or error response
- **Solutions**:
  - Verify `api_url` is correct and accessible
  - Check `api_key` matches `.env` file
  - Verify `device_id` exists in database
  - Check server is running and accessible
  - For HTTPS, ensure certificate is valid

### No GPS Data Received

- **Problem**: "WARNING: No GPS data received"
- **Solutions**:
  - Check wiring (TX/RX connections)
  - Verify GPS module baud rate is 9600
  - Test GPS module with another device
  - Check GPS module power supply

## Update Interval

The default update interval is 30 seconds. To change it, modify:

```cpp
const unsigned long UPDATE_INTERVAL = 30000;  // milliseconds
```

## Serial Monitor Output

Expected output:

```
=========================================
GPS Tracker for Safe Journey System
=========================================

GPS Serial started at 9600 baud
Connecting to WiFi: YourNetwork
........
WiFi connected!
IP address: 192.168.1.100
Signal strength (RSSI): -45 dBm

Setup complete!
Device ID: GPS_TRACKER_001
API URL: http://your-api-server:8000/api/device/gps/update
Update interval: 30 seconds

GPS Location: 24.713600, 46.675300 | Date: 1/1/2024 Time: 12:00:00 | Satellites: 8 | HDOP: 1.2
Sending GPS update to API... HTTP Response code: 200
✓ GPS update sent successfully!
```

## Database Setup

Before using the GPS tracker, ensure:

1. A GPS tracker is created in the admin panel with matching `device_id`
2. The tracker is assigned to a bus (optional, but required for full functionality)
3. The API server is running and accessible

## Power Consumption

- **Active (sending updates)**: ~80-150mA
- **Idle (waiting)**: ~50-80mA
- **Deep Sleep** (not implemented): ~10-20μA

For battery-powered applications, consider implementing deep sleep between updates.


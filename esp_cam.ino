#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <time.h>

//
// WARNING!!! Make sure that you have either selected ESP32 Wrover Module,
//            or another board which has PSRAM enabled
//

// Select camera model
// #define CAMERA_MODEL_WROVER_KIT
//#define CAMERA_MODEL_ESP_EYE
//#define CAMERA_MODEL_M5STACK_PSRAM
//#define CAMERA_MODEL_M5STACK_WIDE
#define CAMERA_MODEL_AI_THINKER

#include "camera_pins.h"

// ============================================
// CONFIGURATION - Update these values
// ============================================
const char* ssid = "rado";
const char* password = "77425252";

// Backend API Configuration
const char* BACKEND_UPLOAD_URL = "https://safe-trip.nabaai.com/api/upload_camera_face";
const char* CAMERA_API_KEY = "changeme_camera_api_key";  // Must match CAMERA_API_KEY in .env
const char* CAMERA_ID = "bus_cam_03";  // Camera ID - will be created automatically if doesn't exist
const char* CAMERA_NAME = "Bus Camera 03";  // Optional camera name

// Upload Settings
const unsigned long UPLOAD_INTERVAL_MS = 5000;  // Upload every 5 seconds
const int MAX_RETRY_ATTEMPTS = 3;  // Maximum retry attempts on upload failure
const unsigned long RETRY_DELAY_MS = 2000;  // Delay between retries (ms)

// Forward declaration
void startCameraServer();

// Global variables
unsigned long lastUploadMillis = 0;
bool wifiConnected = false;

// ============================================
// Timestamp Helper - Get ISO 8601 timestamp
// ============================================
String getTimestampISO() {
    time_t now;
    time(&now);
    struct tm timeinfo;
    gmtime_r(&now, &timeinfo);
    char buf[25];
    strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", &timeinfo);
    return String(buf);
}

// ============================================
// WiFi Connection Helper
// ============================================
void connectToWiFi() {
    Serial.print("Connecting to WiFi: ");
    Serial.println(ssid);
    
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);
    
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(500);
        Serial.print(".");
        attempts++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        wifiConnected = true;
        Serial.println("\nWiFi connected!");
        Serial.print("IP address: ");
        Serial.println(WiFi.localIP());
        Serial.print("Signal strength (RSSI): ");
        Serial.print(WiFi.RSSI());
        Serial.println(" dBm");
    } else {
        wifiConnected = false;
        Serial.println("\nWiFi connection failed!");
        Serial.println("Please check your WiFi credentials.");
    }
}

// ============================================
// Image Upload Helper
// ============================================
bool uploadImage(const uint8_t* image_buf, size_t image_len) {
    if (!wifiConnected || WiFi.status() != WL_CONNECTED) {
        Serial.println("WiFi not connected, cannot upload");
        return false;
    }

    HTTPClient http;
    http.setTimeout(30000); // 30s timeout for large images
    
    String boundary = "----ESP32CAMBoundary";
    http.begin(BACKEND_UPLOAD_URL);
    http.addHeader("X-API-KEY", CAMERA_API_KEY);
    http.addHeader("Content-Type", "multipart/form-data; boundary=" + boundary);

    // Build multipart form data
    String bodyStart = "";
    
    // camera_id (required)
    bodyStart += "--" + boundary + "\r\n";
    bodyStart += "Content-Disposition: form-data; name=\"camera_id\"\r\n\r\n" + String(CAMERA_ID) + "\r\n";
    
    // camera_name (optional)
    if (strlen(CAMERA_NAME) > 0) {
        bodyStart += "--" + boundary + "\r\n";
        bodyStart += "Content-Disposition: form-data; name=\"camera_name\"\r\n\r\n" + String(CAMERA_NAME) + "\r\n";
    }
    
    // timestamp (optional - ISO 8601 format)
    String timestamp = getTimestampISO();
    bodyStart += "--" + boundary + "\r\n";
    bodyStart += "Content-Disposition: form-data; name=\"timestamp\"\r\n\r\n" + timestamp + "\r\n";
    
    // image file (required)
    bodyStart += "--" + boundary + "\r\n";
    bodyStart += "Content-Disposition: form-data; name=\"image\"; filename=\"" + String(CAMERA_ID) + "_" + String(millis()) + ".jpg\"\r\n";
    bodyStart += "Content-Type: image/jpeg\r\n\r\n";

    String bodyEnd = "\r\n--" + boundary + "--\r\n";

    size_t fullLen = bodyStart.length() + image_len + bodyEnd.length();
    uint8_t* payload = (uint8_t*)malloc(fullLen);
    if (!payload) {
        Serial.println("Failed to allocate memory for payload");
        return false;
    }

    // Copy all parts to payload
    size_t offset = 0;
    memcpy(payload + offset, bodyStart.c_str(), bodyStart.length());
    offset += bodyStart.length();
    memcpy(payload + offset, image_buf, image_len);
    offset += image_len;
    memcpy(payload + offset, bodyEnd.c_str(), bodyEnd.length());

    Serial.printf("Uploading image: %u bytes, total payload: %u bytes\n", (unsigned int)image_len, (unsigned int)fullLen);
    Serial.printf("Camera ID: %s, Timestamp: %s\n", CAMERA_ID, timestamp.c_str());
    
    int httpCode = http.sendRequest("POST", payload, fullLen);
    free(payload);

    if (httpCode > 0) {
        Serial.printf("Upload HTTP code: %d\n", httpCode);
        
        if (httpCode >= 200 && httpCode < 300) {
            String response = http.getString();
            Serial.println("✓ Upload successful!");
            Serial.println("Response: " + response);
            http.end();
            return true;
        } else {
            Serial.printf("✗ Upload failed with code: %d\n", httpCode);
            String response = http.getString();
            Serial.println("Response: " + response);
            http.end();
            return false;
        }
    } else {
        Serial.printf("✗ Upload failed: %s\n", http.errorToString(httpCode).c_str());
        http.end();
        return false;
    }
}

// ============================================
// Upload with Retry Logic
// ============================================
bool uploadImageWithRetry(const uint8_t* image_buf, size_t image_len) {
    for (int attempt = 1; attempt <= MAX_RETRY_ATTEMPTS; attempt++) {
        if (uploadImage(image_buf, image_len)) {
            return true;
        }
        
        if (attempt < MAX_RETRY_ATTEMPTS) {
            Serial.printf("Retry %d/%d in %lu ms...\n", attempt + 1, MAX_RETRY_ATTEMPTS, RETRY_DELAY_MS);
            delay(RETRY_DELAY_MS);
        }
    }
    
    Serial.println("✗ All upload attempts failed");
    return false;
}

// ============================================
// Setup Function
// ============================================
void setup() {
    Serial.begin(115200);
    Serial.setDebugOutput(true);
    delay(1000);
    
    Serial.println("\n=========================================");
    Serial.println("ESP32-CAM for Safe Journey System");
    Serial.println("=========================================\n");

    // Camera configuration
    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer = LEDC_TIMER_0;
    config.pin_d0 = Y2_GPIO_NUM;
    config.pin_d1 = Y3_GPIO_NUM;
    config.pin_d2 = Y4_GPIO_NUM;
    config.pin_d3 = Y5_GPIO_NUM;
    config.pin_d4 = Y6_GPIO_NUM;
    config.pin_d5 = Y7_GPIO_NUM;
    config.pin_d6 = Y8_GPIO_NUM;
    config.pin_d7 = Y9_GPIO_NUM;
    config.pin_xclk = XCLK_GPIO_NUM;
    config.pin_pclk = PCLK_GPIO_NUM;
    config.pin_vsync = VSYNC_GPIO_NUM;
    config.pin_href = HREF_GPIO_NUM;
    config.pin_sscb_sda = SIOD_GPIO_NUM;
    config.pin_sscb_scl = SIOC_GPIO_NUM;
    config.pin_pwdn = PWDN_GPIO_NUM;
    config.pin_reset = RESET_GPIO_NUM;
    config.xclk_freq_hz = 20000000;
    config.pixel_format = PIXFORMAT_JPEG;

    if(psramFound()){
        config.frame_size = FRAMESIZE_UXGA;
        config.jpeg_quality = 10;
        config.fb_count = 2;
    } else {
        config.frame_size = FRAMESIZE_SVGA;
        config.jpeg_quality = 12;
        config.fb_count = 1;
    }

#if defined(CAMERA_MODEL_ESP_EYE)
    pinMode(13, INPUT_PULLUP);
    pinMode(14, INPUT_PULLUP);
#endif

    // Initialize camera
    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.printf("Camera init failed with error 0x%x\n", err);
        return;
    }
    Serial.println("✓ Camera initialized");

    // Configure camera sensor
    sensor_t * s = esp_camera_sensor_get();
    if (s->id.PID == OV3660_PID) {
        s->set_vflip(s, 1);
        s->set_brightness(s, 1);
        s->set_saturation(s, -2);
    }
    s->set_framesize(s, FRAMESIZE_VGA);

#if defined(CAMERA_MODEL_M5STACK_WIDE)
    s->set_vflip(s, 1);
    s->set_hmirror(s, 1);
#endif

    // Connect to WiFi
    connectToWiFi();

    // Configure NTP time for accurate timestamps
    if (wifiConnected) {
        configTime(0, 0, "pool.ntp.org", "time.nist.gov");
        Serial.println("Waiting for NTP time sync...");
        time_t now = time(nullptr);
        int retries = 0;
        while (now < 1000000000 && retries < 20) {
            delay(500);
            now = time(nullptr);
            retries++;
        }
        if (now >= 1000000000) {
            Serial.println("✓ NTP time synchronized");
        } else {
            Serial.println("⚠ NTP time sync failed, using system time");
        }
    }

    // Start camera web server (optional - for debugging)
    startCameraServer();

    Serial.println("\n=========================================");
    Serial.println("Configuration:");
    Serial.print("  Camera ID: ");
    Serial.println(CAMERA_ID);
    Serial.print("  Camera Name: ");
    Serial.println(CAMERA_NAME);
    Serial.print("  API URL: ");
    Serial.println(BACKEND_UPLOAD_URL);
    Serial.print("  Upload Interval: ");
    Serial.print(UPLOAD_INTERVAL_MS / 1000);
    Serial.println(" seconds");
    Serial.println("=========================================\n");

    if (wifiConnected) {
        Serial.print("Camera Ready! Web interface: http://");
        Serial.println(WiFi.localIP());
    }
    
    Serial.println("Starting image capture and upload...\n");
    lastUploadMillis = 0;
}

// ============================================
// Main Loop
// ============================================
void loop() {
    // Check WiFi connection
    if (WiFi.status() != WL_CONNECTED) {
        if (wifiConnected) {
            Serial.println("WiFi disconnected! Attempting to reconnect...");
            wifiConnected = false;
        }
        connectToWiFi();
    }
    
    // Capture and upload images at specified interval
    unsigned long now = millis();
    if (wifiConnected && (now - lastUploadMillis >= UPLOAD_INTERVAL_MS || lastUploadMillis == 0)) {
        camera_fb_t* fb = esp_camera_fb_get();
        if (fb) {
            Serial.printf("Captured frame: %dx%d, size: %u bytes\n", 
                         fb->width, fb->height, (unsigned int)fb->len);
            
            // Upload with retry logic
            if (uploadImageWithRetry(fb->buf, fb->len)) {
                lastUploadMillis = now;
            } else {
                // Even if upload fails, update timestamp to avoid flooding
                lastUploadMillis = now;
            }
            
            esp_camera_fb_return(fb);
        } else {
            Serial.println("✗ Camera capture failed");
        }
    }
    
    delay(10); // Small delay to prevent watchdog issues
}

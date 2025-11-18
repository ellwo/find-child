#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>

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

const char* ssid = "rado";
const char* password = "77425252";

// Forward declaration only — do NOT define it here
void startCameraServer();

// ---------------- Backend upload settings ----------------
const char* BACKEND_UPLOAD_URL = "https://ai-mirrors.socialaipilot.com/api/upload_camera_face";
const char* CAMERA_API_KEY = "changeme_camera_api_key";
const char* CAMERA_ID = "mall_cam_01";
const unsigned long UPLOAD_INTERVAL_MS = 5000;
unsigned long lastUploadMillis = 0;

// ---------------- Timestamp helper ----------------
String getTimestampISO() {
    time_t now;
    time(&now);
    struct tm timeinfo;
    gmtime_r(&now, &timeinfo);
    char buf[25];
    strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", &timeinfo);
    return String(buf);
}

// ---------------- Image upload helper ----------------
bool uploadImage(const uint8_t* image_buf, size_t image_len) {
    if (WiFi.status() != WL_CONNECTED) return false;

    HTTPClient http;
    http.setTimeout(10000); // 10s timeout
    String boundary = "----ESP32CAMBoundary";
    http.begin(BACKEND_UPLOAD_URL);
    http.addHeader("X-API-KEY", CAMERA_API_KEY);
    http.addHeader("Content-Type", "multipart/form-data; boundary=" + boundary);

    String bodyStart = "";
    bodyStart += "--" + boundary + "\r\n";
    bodyStart += "Content-Disposition: form-data; name=\"camera_id\"\r\n\r\n" + String(CAMERA_ID) + "\r\n";
    bodyStart += "--" + boundary + "\r\n";
    bodyStart += "Content-Disposition: form-data; name=\"timestamp\"\r\n\r\n" + getTimestampISO() + "\r\n";
    bodyStart += "--" + boundary + "\r\n";
    bodyStart += "Content-Disposition: form-data; name=\"image\"; filename=\"" + String(CAMERA_ID) + "_" + String(millis()) + ".jpg\"\r\n";
    bodyStart += "Content-Type: image/jpeg\r\n\r\n";

    String bodyEnd = "\r\n--" + boundary + "--\r\n";

    size_t fullLen = bodyStart.length() + image_len + bodyEnd.length();
    uint8_t* payload = (uint8_t*)malloc(fullLen);
    if (!payload) return false;

    memcpy(payload, bodyStart.c_str(), bodyStart.length());
    memcpy(payload + bodyStart.length(), image_buf, image_len);
    memcpy(payload + bodyStart.length() + image_len, bodyEnd.c_str(), bodyEnd.length());

    int httpCode = http.sendRequest("POST", payload, fullLen);
    free(payload);

    if (httpCode > 0) {
        Serial.printf("Upload HTTP code: %d\n", httpCode);
        Serial.println("Response: " + http.getString());
        http.end();
        return (httpCode >= 200 && httpCode < 300);
    } else {
        Serial.printf("Upload failed: %s\n", http.errorToString(httpCode).c_str());
        http.end();
        return false;
    }
}

// ---------------- Setup ----------------
void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();

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

  // camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

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

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");

  startCameraServer(); // Keep your original call

  Serial.print("Camera Ready! Use 'http://");
  Serial.print(WiFi.localIP());
  Serial.println("' to connect");

  lastUploadMillis = 0;
}

// ---------------- Loop ----------------
void loop() {
  unsigned long now = millis();
  if (now - lastUploadMillis >= UPLOAD_INTERVAL_MS) {
    camera_fb_t* fb = esp_camera_fb_get();
    if(fb){
      Serial.printf("Captured frame: %dx%d, size: %u bytes\n", fb->width, fb->height, (unsigned int)fb->len);
      uploadImage(fb->buf, fb->len); // upload to backend
      esp_camera_fb_return(fb);
      lastUploadMillis = now;
    } else {
      Serial.println("Camera capture failed");
    }
  }
  delay(10); // tiny delay
}
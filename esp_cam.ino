/*
  ESP32-CAM: detect faces locally (ESP-WHO), and upload frames when a face is found.

  - Sends multipart/form-data POST to BACKEND_UPLOAD_URL
  - Header: X-API-KEY: CAMERA_API_KEY
  - Form fields:
      camera_id (string)
      camera_name (string, optional)
      timestamp (ISO-8601 string, UTC)
      bbox (json string: {"x":..,"y":..,"w":..,"h":..} )  // face bounding box in pixels in the frame
      image (file) -> JPEG buffer (full frame by default)
  - Note: For reliability this sketch sends the full JPEG frame when a face is detected.
    The backend may crop the face using bbox if you want to store only the face region.
    Cropping and re-encoding JPEG on the ESP32 is possible but more complex and
    not implemented here (commented where you can extend).

  Requirements:
  - ESP32 board support installed.
  - esp_camera.h and esp-who face detection headers (fd_forward.h) available.
    See https://github.com/espressif/esp-who for setup and examples.
*/

#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include "ArduinoJson.h"

// --- Replace these with your settings ---
const char* WIFI_SSID = "YOUR_SSID";
const char* WIFI_PASSWORD = "YOUR_PASS";

const char* BACKEND_UPLOAD_URL = "http://your-backend-host:8000/api/upload_camera_face";
const char* CAMERA_API_KEY = "changeme_camera_api_key";
const char* CAMERA_ID = "mall_cam_01";
const char* CAMERA_NAME = "Mall Entrance 01";

// Minimum milliseconds between uploads for same camera to avoid flooding
const unsigned long UPLOAD_MIN_INTERVAL_MS = 2000; // 2 seconds

// --- Camera configuration: AI-Thinker module pinout (common ESP32-CAM) ---
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM     0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// Configure your desired frame size here.
// For reduced upload size use FRAMESIZE_VGA or smaller (e.g., QVGA).
// Smaller frames make uploads faster and reduce bandwidth.
#define CAMERA_FRAME_SIZE FRAMESIZE_VGA

// Include ESP-WHO face detect forward header (from esp-who examples).
// Make sure you have esp-who installed and the header path available.
extern "C" {
  #include "fd_forward.h"
  #include "dl_lib.h"
}

static camera_fb_t * fb = NULL;
static unsigned long lastUploadMillis = 0;

// Initialize camera
bool initCamera() {
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
  config.pixel_format = PIXFORMAT_JPEG; // JPEG output
  config.frame_size = CAMERA_FRAME_SIZE;
  config.jpeg_quality = 10; // 0-63 lower means higher quality; adjust
  config.fb_count = 1;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x\n", err);
    return false;
  }
  return true;
}

// Connect to WiFi
void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.printf("Connecting to WiFi %s", WIFI_SSID);
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED) {
    delay(250);
    Serial.print(".");
    if (millis() - start > 20000) { // 20s timeout
      Serial.println("\nFailed to connect to WiFi (timeout). Will retry in loop.");
      return;
    }
  }
  Serial.println("\nConnected to WiFi!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

// Helper to get current timestamp as ISO-8601 UTC
String getTimestampISO() {
  time_t now;
  time(&now);
  struct tm timeinfo;
  gmtime_r(&now, &timeinfo);
  char buf[25];
  strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", &timeinfo);
  return String(buf);
}

// Build multipart/form-data body and post
bool uploadImageWithMetadata(const uint8_t* image_buf, size_t image_len,
                             const char* filename,
                             int bbox_x, int bbox_y, int bbox_w, int bbox_h,
                             const char* camera_id,
                             const char* camera_name,
                             const char* timestamp) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected; abort upload.");
    return false;
  }

  HTTPClient http;
  String boundary = "----ESP32CAMBoundary";
  String url = BACKEND_UPLOAD_URL;
  http.begin(url);
  http.addHeader("X-API-KEY", CAMERA_API_KEY);
  http.addHeader("Content-Type", "multipart/form-data; boundary=" + boundary);

  // Build multipart body manually (careful with memory)
  // For large images this can be heavy on RAM. So we use stream via WiFiClient directly.
  WiFiClient * stream = http.getStreamPtr();
  if (!stream) {
    Serial.println("Failed to get stream pointer");
    http.end();
    return false;
  }

  // Start request
  String partStart;
  // camera_id field
  partStart = "--" + boundary + "\r\n";
  partStart += "Content-Disposition: form-data; name=\"camera_id\"\r\n\r\n";
  partStart += String(camera_id) + "\r\n";

  // camera_name
  partStart += "--" + boundary + "\r\n";
  partStart += "Content-Disposition: form-data; name=\"camera_name\"\r\n\r\n";
  partStart += String(camera_name) + "\r\n";

  // timestamp
  partStart += "--" + boundary + "\r\n";
  partStart += "Content-Disposition: form-data; name=\"timestamp\"\r\n\r\n";
  partStart += String(timestamp) + "\r\n";

  // bbox json
  DynamicJsonDocument bboxDoc(128);
  bboxDoc["x"] = bbox_x;
  bboxDoc["y"] = bbox_y;
  bboxDoc["w"] = bbox_w;
  bboxDoc["h"] = bbox_h;
  String bboxJson;
  serializeJson(bboxDoc, bboxJson);

  partStart += "--" + boundary + "\r\n";
  partStart += "Content-Disposition: form-data; name=\"bbox\"\r\n\r\n";
  partStart += bboxJson + "\r\n";

  // image file header
  partStart += "--" + boundary + "\r\n";
  partStart += "Content-Disposition: form-data; name=\"image\"; filename=\"" + String(filename) + "\"\r\n";
  partStart += "Content-Type: image/jpeg\r\n\r\n";

  // end boundary footer (after file)
  String partEnd = "\r\n--" + boundary + "--\r\n";

  // Build full content-length if needed (we'll stream so not setting length)
  // Write parts to stream
  stream->print(partStart);

  // Write binary image buffer
  size_t written = 0;
  const uint8_t* ptr = image_buf;
  size_t remain = image_len;
  const size_t CHUNK = 1024;
  while (remain > 0) {
    size_t toWrite = (remain > CHUNK) ? CHUNK : remain;
    stream->write(ptr, toWrite);
    ptr += toWrite;
    remain -= toWrite;
    written += toWrite;
    // optional small delay to avoid watchdog in extreme cases
    delay(0);
  }

  // write footer
  stream->print(partEnd);

  // finish and get response
  int httpCode = http.sendRequest("POST", NULL, 0);
  if (httpCode > 0) {
    String resp = http.getString();
    Serial.printf("Upload HTTP code: %d\n", httpCode);
    Serial.println("Response: " + resp);
    http.end();
    return (httpCode >= 200 && httpCode < 300);
  } else {
    Serial.printf("Upload failed, error: %s\n", http.errorToString(httpCode).c_str());
    http.end();
    return false;
  }
}

// Wrapper that captures a frame and uploads
void captureAndUpload(int bbox_x, int bbox_y, int bbox_w, int bbox_h) {
  // Prevent flooding: minimal interval between uploads
  unsigned long now = millis();
  if (now - lastUploadMillis < UPLOAD_MIN_INTERVAL_MS) {
    // Too soon; skip
    return;
  }

  // Capture frame (JPEG)
  camera_fb_t * fb_capture = esp_camera_fb_get();
  if (!fb_capture) {
    Serial.println("Camera frame capture failed");
    return;
  }

  // Use JPEG buffer directly
  const uint8_t* jpgBuf = fb_capture->buf;
  size_t jpgLen = fb_capture->len;

  // create filename from timestamp
  String ts = getTimestampISO();
  String filename = String(CAMERA_ID) + "_" + String(millis()) + ".jpg";

  Serial.printf("Uploading image (len=%u bytes) with bbox x=%d y=%d w=%d h=%d\n",
                (unsigned int)jpgLen, bbox_x, bbox_y, bbox_w, bbox_h);

  bool ok = uploadImageWithMetadata(jpgBuf, jpgLen, filename.c_str(),
                                    bbox_x, bbox_y, bbox_w, bbox_h,
                                    CAMERA_ID, CAMERA_NAME, ts.c_str());
  if (ok) {
    Serial.println("Upload succeeded");
    lastUploadMillis = now;
  } else {
    Serial.println("Upload failed");
  }

  esp_camera_fb_return(fb_capture);
}

// ------------------- face detection callback setup -------------------
// We will call face detection on each frame and if a face is found, upload frame with bbox.
// Using ESP-WHO: fd_forward() returns number of faces and fills detected bounding boxes.
// See esp-who examples for details and ensure you include correct headers and link libs.

// Helper to run face detection on a frame and return first bbox found
bool detect_face_and_get_bbox(camera_fb_t* frame, int *out_x, int *out_y, int *out_w, int *out_h) {
  if (!frame) return false;

  // fd_forward expects (uint8_t* img, int w, int h, int isRGB);
  // Since frame->buf is JPEG, usually you need to run detection on decoded frame.
  // Some ESP-WHO examples run detection directly on continuous frames or YUV buffers.
  // For simplicity we will call fd_forward on the framebuffer when possible.
  // NOTE: This assumes the board and build include fd_forward and appropriate decoding paths.
  // If fd_forward cannot accept JPEG directly in your build, refer to esp-who examples.

  // Convert fb to BGR or RGB if necessary before calling fd_forward. The following
  // example calls fd_forward on the framebuffer directly as many examples do.
  // You may need to adapt based on your esp-who version.

  int img_w = frame->width;
  int img_h = frame->height;

  // Example call (from esp-who demo). Return value is number of faces.
  face_align_type_t face_align;
  int faces = fd_forward((uint8_t*)frame->buf, img_w, img_h, &face_align);
  if (faces <= 0) {
    return false;
  }

  // fd_forward populates global fd results; use fd_get_bbox to read the first bbox
  // NOTE: these helper functions exist in esp-who examples; ensure headers are present.
  int x = 0, y = 0, w = 0, h = 0;
  if (fd_get_box(&x, &y, &w, &h)) {
    *out_x = x;
    *out_y = y;
    *out_w = w;
    *out_h = h;
    return true;
  }

  // fallback: if fd_get_box not available, return false
  return false;
}

// ------------------- setup + loop -------------------
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println();
  Serial.println("ESP32-CAM face upload prototype starting...");

  // Init camera
  if (!initCamera()) {
    Serial.println("Camera init failed. Halting.");
    while (true) delay(1000);
  }

  // Connect WiFi
  connectWiFi();

  // Setup time (optional): get time via NTP so timestamps are correct
  configTime(0, 0, "pool.ntp.org", "time.nist.gov");
  Serial.println("Waiting for NTP time...");
  time_t now = time(nullptr);
  int retry = 0;
  while (now < 8 * 3600 * 2 && retry < 10) {
    delay(1000);
    Serial.print(".");
    now = time(nullptr);
    retry++;
  }
  Serial.println();
  Serial.println("NTP ready");

  lastUploadMillis = 0;
}

void loop() {
  // Capture a frame for detection
  fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Frame capture failed");
    delay(100);
    return;
  }

  int bx = 0, by = 0, bw = 0, bh = 0;
  bool faceFound = false;

  // Try face detection on this frame
  faceFound = detect_face_and_get_bbox(fb, &bx, &by, &bw, &bh);

  if (faceFound) {
    Serial.printf("Face detected at x=%d y=%d w=%d h=%d\n", bx, by, bw, bh);

    // Optionally, you can crop the face region and re-encode to JPEG here before upload.
    // That requires decoding the JPEG to raw pixels and re-encoding the cropped patch back to JPEG.
    // This is more complex and may need extra libraries (TJpgDec and JPEG encoder).
    // For the prototype, we upload the whole frame and include bbox for server-side cropping.

    // Upload the captured frame and bbox
    // Note: captureAndUpload will capture a new frame. To reuse 'fb' you can adjust the function,
    // but here we return fb and call captureAndUpload which captures again to get fresh buffer.
    // To upload current fb content instead, modify uploadImageWithMetadata to accept current buffer pointer.
    esp_camera_fb_return(fb);
    fb = NULL;

    // Capture and upload (uses new capture inside)
    captureAndUpload(bx, by, bw, bh);
  } else {
    // No face: return buffer and continue
    esp_camera_fb_return(fb);
    fb = NULL;
  }

  // small delay - adjust to balance CPU usage and detection frequency
  delay(150);
}

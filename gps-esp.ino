#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <TinyGPS++.h>

// ============================================
// CONFIGURATION - Update these values
// ============================================
// WiFi Settings (may vary by location)
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// API Settings (same for all devices)
const char* api_url = "https://safe-trip.nabaai.com/api/device/gps/update";
const char* api_key = "changeme_gps_api_key";  // Must match GPS_DEVICE_API_KEY in .env

// Device Settings (UNIQUE for each GPS tracker)
const char* device_id = "GPS_TRACKER_001";  // ⚠️ CHANGE THIS for each device - Must match device_id in database

// GPS Configuration
#define RXD2 16
#define TXD2 17
#define GPS_BAUD 9600

// Update interval (milliseconds)
const unsigned long UPDATE_INTERVAL = 30000;  // 30 seconds

// ============================================
// Global Objects
// ============================================
HardwareSerial gpsSerial(2);
TinyGPSPlus gps;
unsigned long lastUpdateTime = 0;
bool wifiConnected = false;

// ============================================
// Setup Function
// ============================================
void setup() {
  // Serial Monitor
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n=========================================");
  Serial.println("GPS Tracker for Safe Journey System");
  Serial.println("=========================================\n");
  
  // Start GPS Serial
  gpsSerial.begin(GPS_BAUD, SERIAL_8N1, RXD2, TXD2);
  Serial.println("GPS Serial started at 9600 baud");
  
  // Connect to WiFi
  connectToWiFi();
  
  Serial.println("\nSetup complete!");
  Serial.print("Device ID: ");
  Serial.println(device_id);
  Serial.print("API URL: ");
  Serial.println(api_url);
  Serial.print("Update interval: ");
  Serial.print(UPDATE_INTERVAL / 1000);
  Serial.println(" seconds\n");
}

// ============================================
// Main Loop
// ============================================
void loop() {
  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected! Attempting to reconnect...");
    wifiConnected = false;
    connectToWiFi();
  }
  
  // Read GPS data
  while (gpsSerial.available() > 0) {
    if (gps.encode(gpsSerial.read())) {
      // GPS data successfully parsed
      displayGPSInfo();
    }
  }
  
  // Check if it's time to send update
  unsigned long currentTime = millis();
  if (wifiConnected && gps.location.isValid() && 
      (currentTime - lastUpdateTime >= UPDATE_INTERVAL || lastUpdateTime == 0)) {
    sendGPSUpdate();
    lastUpdateTime = currentTime;
  }
  
  // If GPS data is stale (older than 5 seconds), warn user
  if (millis() > 5000 && gps.charsProcessed() < 10) {
    Serial.println("WARNING: No GPS data received. Check GPS module connection.");
    delay(2000);
  }
  
  delay(100);
}

// ============================================
// WiFi Connection
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
// Display GPS Information
// ============================================
void displayGPSInfo() {
  if (gps.location.isValid()) {
    Serial.print("GPS Location: ");
    Serial.print(gps.location.lat(), 6);
    Serial.print(", ");
    Serial.print(gps.location.lng(), 6);
    Serial.print(" | ");
    
    if (gps.date.isValid()) {
      Serial.print("Date: ");
      Serial.print(gps.date.day());
      Serial.print("/");
      Serial.print(gps.date.month());
      Serial.print("/");
      Serial.print(gps.date.year());
      Serial.print(" ");
    }
    
    if (gps.time.isValid()) {
      Serial.print("Time: ");
      if (gps.time.hour() < 10) Serial.print("0");
      Serial.print(gps.time.hour());
      Serial.print(":");
      if (gps.time.minute() < 10) Serial.print("0");
      Serial.print(gps.time.minute());
      Serial.print(":");
      if (gps.time.second() < 10) Serial.print("0");
      Serial.print(gps.time.second());
    }
    
    Serial.print(" | Satellites: ");
    Serial.print(gps.satellites.value());
    Serial.print(" | HDOP: ");
    Serial.println(gps.hdop.value() / 100.0);
  } else {
    Serial.println("GPS: Waiting for fix...");
  }
}

// ============================================
// Send GPS Update to API
// ============================================
void sendGPSUpdate() {
  if (!gps.location.isValid()) {
    Serial.println("Cannot send update: GPS location not valid");
    return;
  }
  
  // Create JSON payload
  StaticJsonDocument<200> doc;
  doc["device_id"] = device_id;
  doc["latitude"] = gps.location.lat();
  doc["longitude"] = gps.location.lng();
  
  // Add timestamp if available
  if (gps.date.isValid() && gps.time.isValid()) {
    // Create ISO 8601 timestamp
    char timestamp[25];
    snprintf(timestamp, sizeof(timestamp), "%04d-%02d-%02dT%02d:%02d:%02dZ",
             gps.date.year(),
             gps.date.month(),
             gps.date.day(),
             gps.time.hour(),
             gps.time.minute(),
             gps.time.second());
    doc["timestamp"] = timestamp;
  }
  
  // Serialize JSON
  String jsonPayload;
  serializeJson(doc, jsonPayload);
  
  // Send HTTP POST request
  HTTPClient http;
  http.begin(api_url);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-KEY", api_key);
  
  Serial.print("Sending GPS update to API... ");
  int httpResponseCode = http.POST(jsonPayload);
  
  if (httpResponseCode > 0) {
    Serial.print("HTTP Response code: ");
    Serial.println(httpResponseCode);
    
    if (httpResponseCode == 200) {
      String response = http.getString();
      Serial.println("✓ GPS update sent successfully!");
      
      // Parse response if needed
      StaticJsonDocument<200> responseDoc;
      DeserializationError error = deserializeJson(responseDoc, response);
      if (!error && responseDoc.containsKey("is_near_school")) {
        bool isNearSchool = responseDoc["is_near_school"];
        if (isNearSchool) {
          Serial.println("  → Bus is near school!");
        }
      }
    } else {
      Serial.print("✗ Error: ");
      Serial.println(http.getString());
    }
  } else {
    Serial.print("✗ HTTP Request failed: ");
    Serial.println(http.errorToString(httpResponseCode));
  }
  
  http.end();
  Serial.println();
}

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <WiFiManager.h>
#include <ESPAsyncWebServer.h>
#include <AsyncElegantOTA.h>
#include <EEPROM.h>
#include <esp_task_wdt.h>
#include <DHT.h>
#include <Adafruit_BME280.h>
#include <Wire.h>
#include <HTTPUpdate.h>

// Hardware pin definitions
#define DHT_PIN 4
#define DHT_TYPE DHT22
#define MOTION_PIN 5
#define LIGHT_SENSOR_PIN A0
#define LED_PIN 2
#define BUTTON_PIN 0

// Device configuration
const char* DEVICE_TYPE = "Sensor Node";
const char* FIRMWARE_VERSION = "1.0.0";
String DEVICE_ID = "";
String MAC_ADDRESS = "";

// MQTT Configuration
const char* MQTT_SERVER = "192.168.1.100";
const int MQTT_PORT = 1883;
const char* MQTT_USER = "";
const char* MQTT_PASSWORD = "";

// Topics
String TOPIC_BASE = "";
String TOPIC_STATUS = "";
String TOPIC_STATE = "";
String TOPIC_ONLINE = "";
String TOPIC_COMMAND = "";
String TOPIC_OTA = "";

// Sensors
DHT dht(DHT_PIN, DHT_TYPE);
Adafruit_BME280 bme;
bool bmeAvailable = false;

// WiFi and MQTT clients
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
AsyncWebServer server(80);

// Device state
struct SensorState {
  float temperature = 0.0;
  float humidity = 0.0;
  float pressure = 0.0;
  int light_level = 0;
  bool motion_detected = false;
  bool online = false;
  unsigned long lastHeartbeat = 0;
  unsigned long lastSensorRead = 0;
  unsigned long lastPublish = 0;
};

SensorState sensorState;

// OTA update variables
bool otaInProgress = false;
String otaUrl = "";

// Function declarations
void setupHardware();
void setupWiFi();
void setupMQTT();
void setupOTA();
void setupTopics();
void connectToWiFi();
void connectToMQTT();
void mqttCallback(char* topic, byte* payload, unsigned int length);
void publishStatus();
void publishSensorData();
void publishOnlineStatus(bool online);
void handleCommand(JsonDocument& doc);
void handleOTACommand(JsonDocument& doc);
void readSensors();
void performOTAUpdate();

void setup() {
  Serial.begin(115200);
  Serial.println("\n=== Home Automation Sensor Node ===");
  Serial.println("Firmware Version: " + String(FIRMWARE_VERSION));
  
  // Initialize watchdog
  esp_task_wdt_init(30, true);
  esp_task_wdt_add(NULL);
  
  // Setup hardware
  setupHardware();
  
  // Generate device ID from MAC
  MAC_ADDRESS = WiFi.macAddress();
  DEVICE_ID = "sensor_node_" + MAC_ADDRESS;
  DEVICE_ID.replace(":", "");
  DEVICE_ID.toLowerCase();
  
  Serial.println("Device ID: " + DEVICE_ID);
  Serial.println("MAC Address: " + MAC_ADDRESS);
  
  // Setup topics
  setupTopics();
  
  // Setup WiFi
  setupWiFi();
  
  // Setup MQTT
  setupMQTT();
  
  // Setup OTA
  setupOTA();
  
  Serial.println("Setup complete!");
}

void loop() {
  // Reset watchdog
  esp_task_wdt_reset();
  
  // Handle WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    connectToWiFi();
  }
  
  // Handle MQTT connection
  if (!mqttClient.connected()) {
    connectToMQTT();
  } else {
    mqttClient.loop();
  }
  
  // Read sensors every 5 seconds
  unsigned long now = millis();
  if (now - sensorState.lastSensorRead > 5000) {
    readSensors();
    sensorState.lastSensorRead = now;
  }
  
  // Publish sensor data every 30 seconds
  if (now - sensorState.lastPublish > 30000) {
    publishSensorData();
    sensorState.lastPublish = now;
  }
  
  // Send heartbeat every 60 seconds
  if (now - sensorState.lastHeartbeat > 60000) {
    publishOnlineStatus(true);
    sensorState.lastHeartbeat = now;
  }
  
  // Handle OTA update if requested
  if (otaInProgress) {
    performOTAUpdate();
  }
  
  delay(1000);
}

void setupHardware() {
  Serial.println("Setting up hardware...");
  
  // Initialize EEPROM
  EEPROM.begin(512);
  
  // Setup pins
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(MOTION_PIN, INPUT);
  
  // Initialize DHT sensor
  dht.begin();
  
  // Initialize BME280 sensor
  if (bme.begin(0x76)) {
    bmeAvailable = true;
    Serial.println("BME280 sensor initialized");
  } else {
    Serial.println("BME280 sensor not found, using DHT22 only");
  }
  
  Serial.println("Hardware setup complete");
}

void setupWiFi() {
  Serial.println("Setting up WiFi...");
  
  WiFiManager wifiManager;
  wifiManager.setConfigPortalTimeout(300);
  
  if (!wifiManager.autoConnect(("SensorNode_" + DEVICE_ID).c_str())) {
    Serial.println("Failed to connect to WiFi, restarting...");
    delay(3000);
    ESP.restart();
  }
  
  Serial.println("WiFi connected!");
  Serial.println("IP address: " + WiFi.localIP().toString());
}

void setupMQTT() {
  Serial.println("Setting up MQTT...");
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
  mqttClient.setKeepAlive(60);
  Serial.println("MQTT setup complete");
}

void setupOTA() {
  Serial.println("Setting up OTA...");
  AsyncElegantOTA.begin(&server);
  
  server.on("/info", HTTP_GET, [](AsyncWebServerRequest *request){
    StaticJsonDocument<300> doc;
    doc["device_id"] = DEVICE_ID;
    doc["device_type"] = DEVICE_TYPE;
    doc["firmware_version"] = FIRMWARE_VERSION;
    doc["mac_address"] = MAC_ADDRESS;
    doc["ip_address"] = WiFi.localIP().toString();
    doc["temperature"] = sensorState.temperature;
    doc["humidity"] = sensorState.humidity;
    doc["pressure"] = sensorState.pressure;
    doc["light_level"] = sensorState.light_level;
    doc["motion_detected"] = sensorState.motion_detected;
    doc["free_heap"] = ESP.getFreeHeap();
    doc["uptime"] = millis();
    
    String response;
    serializeJson(doc, response);
    request->send(200, "application/json", response);
  });
  
  server.begin();
  Serial.println("OTA and web server started");
}

void setupTopics() {
  TOPIC_BASE = "homeautomation/devices/" + DEVICE_ID;
  TOPIC_STATUS = TOPIC_BASE + "/status";
  TOPIC_STATE = TOPIC_BASE + "/state";
  TOPIC_ONLINE = TOPIC_BASE + "/online";
  TOPIC_COMMAND = TOPIC_BASE + "/command";
  TOPIC_OTA = TOPIC_BASE + "/ota";
}

void connectToWiFi() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Connecting to WiFi...");
    WiFi.begin();
    
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
      delay(500);
      Serial.print(".");
      attempts++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
      Serial.println("\nWiFi connected!");
    } else {
      Serial.println("\nWiFi connection failed, will retry...");
    }
  }
}

void connectToMQTT() {
  if (WiFi.status() != WL_CONNECTED) return;
  
  Serial.println("Connecting to MQTT...");
  
  String willTopic = TOPIC_ONLINE;
  String willMessage = "{\"online\":false}";
  
  if (mqttClient.connect(DEVICE_ID.c_str(), MQTT_USER, MQTT_PASSWORD, 
                        willTopic.c_str(), 1, true, willMessage.c_str())) {
    Serial.println("MQTT connected!");
    
    mqttClient.subscribe(TOPIC_COMMAND.c_str());
    mqttClient.subscribe(TOPIC_OTA.c_str());
    
    publishOnlineStatus(true);
    publishStatus();
    
    sensorState.online = true;
  } else {
    Serial.println("MQTT connection failed, rc=" + String(mqttClient.state()));
    sensorState.online = false;
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String topicStr = String(topic);
  String message = "";
  
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  Serial.println("Received [" + topicStr + "]: " + message);
  
  StaticJsonDocument<512> doc;
  DeserializationError error = deserializeJson(doc, message);
  
  if (error) {
    Serial.println("Failed to parse JSON: " + String(error.c_str()));
    return;
  }
  
  if (topicStr == TOPIC_COMMAND) {
    handleCommand(doc);
  } else if (topicStr == TOPIC_OTA) {
    handleOTACommand(doc);
  }
}

void handleCommand(JsonDocument& doc) {
  String command = doc["command"];
  
  if (command == "get_sensors") {
    readSensors();
    publishSensorData();
  } else if (command == "get_status") {
    publishStatus();
  } else if (command == "restart") {
    publishOnlineStatus(false);
    delay(1000);
    ESP.restart();
  }
}

void handleOTACommand(JsonDocument& doc) {
  String action = doc["action"];
  
  if (action == "update") {
    otaUrl = doc["url"].as<String>();
    Serial.println("OTA update requested: " + otaUrl);
    otaInProgress = true;
  } else if (action == "check") {
    StaticJsonDocument<200> response;
    response["device_id"] = DEVICE_ID;
    response["current_version"] = FIRMWARE_VERSION;
    response["status"] = "ready_for_update";
    
    String responseStr;
    serializeJson(response, responseStr);
    mqttClient.publish(TOPIC_STATUS.c_str(), responseStr.c_str());
  }
}

void readSensors() {
  // Read DHT sensor
  float temp = dht.readTemperature();
  float hum = dht.readHumidity();
  
  if (!isnan(temp) && !isnan(hum)) {
    sensorState.temperature = temp;
    sensorState.humidity = hum;
  }
  
  // Read BME280 if available
  if (bmeAvailable) {
    sensorState.temperature = bme.readTemperature();
    sensorState.humidity = bme.readHumidity();
    sensorState.pressure = bme.readPressure() / 100.0F; // Convert to hPa
  }
  
  // Read light sensor
  sensorState.light_level = analogRead(LIGHT_SENSOR_PIN);
  
  // Read motion sensor
  sensorState.motion_detected = digitalRead(MOTION_PIN);
}

void publishSensorData() {
  StaticJsonDocument<400> doc;
  doc["device_id"] = DEVICE_ID;
  doc["temperature"] = sensorState.temperature;
  doc["humidity"] = sensorState.humidity;
  doc["pressure"] = sensorState.pressure;
  doc["light_level"] = sensorState.light_level;
  doc["motion_detected"] = sensorState.motion_detected;
  doc["timestamp"] = millis();
  
  String message;
  serializeJson(doc, message);
  
  if (mqttClient.connected()) {
    mqttClient.publish(TOPIC_STATE.c_str(), message.c_str());
  }
}

void publishStatus() {
  StaticJsonDocument<300> doc;
  doc["device_id"] = DEVICE_ID;
  doc["device_type"] = DEVICE_TYPE;
  doc["firmware_version"] = FIRMWARE_VERSION;
  doc["mac_address"] = MAC_ADDRESS;
  doc["ip_address"] = WiFi.localIP().toString();
  doc["online"] = sensorState.online;
  doc["wifi_rssi"] = WiFi.RSSI();
  doc["free_heap"] = ESP.getFreeHeap();
  doc["uptime"] = millis();
  
  String message;
  serializeJson(doc, message);
  
  if (mqttClient.connected()) {
    mqttClient.publish(TOPIC_STATUS.c_str(), message.c_str(), true);
  }
}

void publishOnlineStatus(bool online) {
  StaticJsonDocument<100> doc;
  doc["online"] = online;
  doc["timestamp"] = millis();
  
  String message;
  serializeJson(doc, message);
  
  if (mqttClient.connected()) {
    mqttClient.publish(TOPIC_ONLINE.c_str(), message.c_str(), true);
  }
  
  sensorState.online = online;
}

void performOTAUpdate() {
  if (otaUrl.length() == 0) {
    otaInProgress = false;
    return;
  }
  
  Serial.println("Starting OTA update from: " + otaUrl);
  
  StaticJsonDocument<200> status;
  status["device_id"] = DEVICE_ID;
  status["status"] = "updating";
  status["progress"] = 0;
  
  String statusStr;
  serializeJson(status, statusStr);
  mqttClient.publish(TOPIC_STATUS.c_str(), statusStr.c_str());
  
  WiFiClient client;
  t_httpUpdate_return ret = httpUpdate.update(client, otaUrl);
  
  switch (ret) {
    case HTTP_UPDATE_FAILED:
      Serial.println("OTA Update failed: " + httpUpdate.getLastErrorString());
      status["status"] = "failed";
      status["error"] = httpUpdate.getLastErrorString();
      break;
      
    case HTTP_UPDATE_NO_UPDATES:
      Serial.println("No OTA updates available");
      status["status"] = "no_update";
      break;
      
    case HTTP_UPDATE_OK:
      Serial.println("OTA Update successful, restarting...");
      status["status"] = "success";
      break;
  }
  
  serializeJson(status, statusStr);
  mqttClient.publish(TOPIC_STATUS.c_str(), statusStr.c_str());
  
  otaInProgress = false;
  otaUrl = "";
  
  if (ret == HTTP_UPDATE_OK) {
    delay(2000);
    ESP.restart();
  }
}
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <WiFiManager.h>
#include <ESPAsyncWebServer.h>
#include <AsyncElegantOTA.h>
#include <EEPROM.h>
#include <esp_task_wdt.h>

// Hardware pin definitions
#define LED_PIN 2
#define BUTTON_PIN 0
#define RELAY_PIN 4
#define PWM_CHANNEL 0
#define PWM_FREQ 5000
#define PWM_RESOLUTION 8

// Device configuration
const char* DEVICE_TYPE = "Smart Light";
const char* FIRMWARE_VERSION = "1.0.0";
String DEVICE_ID = "";
String MAC_ADDRESS = "";

// MQTT Configuration
const char* MQTT_SERVER = "192.168.1.100";  // Update with your MQTT broker IP
const int MQTT_PORT = 1883;
const char* MQTT_USER = "";  // Add if authentication is required
const char* MQTT_PASSWORD = "";

// Topics
String TOPIC_BASE = "";
String TOPIC_STATUS = "";
String TOPIC_STATE = "";
String TOPIC_ONLINE = "";
String TOPIC_COMMAND = "";
String TOPIC_OTA = "";

// WiFi and MQTT clients
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
AsyncWebServer server(80);

// Device state
struct DeviceState {
  bool power = false;
  int brightness = 100;
  int color_r = 255;
  int color_g = 255;
  int color_b = 255;
  bool online = false;
  unsigned long lastHeartbeat = 0;
  unsigned long lastStateUpdate = 0;
};

DeviceState deviceState;

// Button handling
volatile bool buttonPressed = false;
unsigned long lastButtonPress = 0;
const unsigned long DEBOUNCE_DELAY = 50;

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
void publishState();
void publishOnlineStatus(bool online);
void handleCommand(JsonDocument& doc);
void handleOTACommand(JsonDocument& doc);
void updateLED();
void handleButton();
void IRAM_ATTR buttonISR();
void saveStateToEEPROM();
void loadStateFromEEPROM();
void performOTAUpdate();

void setup() {
  Serial.begin(115200);
  Serial.println("\n=== Home Automation Smart Light ===");
  Serial.println("Firmware Version: " + String(FIRMWARE_VERSION));
  
  // Initialize watchdog
  esp_task_wdt_init(30, true);
  esp_task_wdt_add(NULL);
  
  // Setup hardware
  setupHardware();
  
  // Load saved state
  loadStateFromEEPROM();
  
  // Generate device ID from MAC
  MAC_ADDRESS = WiFi.macAddress();
  DEVICE_ID = "smart_light_" + MAC_ADDRESS;
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
  
  // Initial state update
  updateLED();
  
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
  
  // Handle button press
  if (buttonPressed) {
    handleButton();
    buttonPressed = false;
  }
  
  // Send heartbeat every 30 seconds
  unsigned long now = millis();
  if (now - deviceState.lastHeartbeat > 30000) {
    publishOnlineStatus(true);
    deviceState.lastHeartbeat = now;
  }
  
  // Send state update every 5 seconds if state changed
  if (now - deviceState.lastStateUpdate > 5000) {
    publishState();
    deviceState.lastStateUpdate = now;
  }
  
  // Handle OTA update if requested
  if (otaInProgress) {
    performOTAUpdate();
  }
  
  delay(100);
}

void setupHardware() {
  Serial.println("Setting up hardware...");
  
  // Initialize EEPROM
  EEPROM.begin(512);
  
  // Setup LED PWM
  ledcSetup(PWM_CHANNEL, PWM_FREQ, PWM_RESOLUTION);
  ledcAttachPin(LED_PIN, PWM_CHANNEL);
  
  // Setup relay pin
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);
  
  // Setup button with interrupt
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(BUTTON_PIN), buttonISR, FALLING);
  
  Serial.println("Hardware setup complete");
}

void setupWiFi() {
  Serial.println("Setting up WiFi...");
  
  WiFiManager wifiManager;
  
  // Set timeout for configuration portal
  wifiManager.setConfigPortalTimeout(300); // 5 minutes
  
  // Custom parameters for MQTT configuration
  WiFiManagerParameter custom_mqtt_server("server", "MQTT Server", MQTT_SERVER, 40);
  WiFiManagerParameter custom_mqtt_port("port", "MQTT Port", "1883", 6);
  WiFiManagerParameter custom_mqtt_user("user", "MQTT User", MQTT_USER, 32);
  WiFiManagerParameter custom_mqtt_pass("pass", "MQTT Password", MQTT_PASSWORD, 32);
  
  wifiManager.addParameter(&custom_mqtt_server);
  wifiManager.addParameter(&custom_mqtt_port);
  wifiManager.addParameter(&custom_mqtt_user);
  wifiManager.addParameter(&custom_mqtt_pass);
  
  // Try to connect or start configuration portal
  if (!wifiManager.autoConnect(("SmartLight_" + DEVICE_ID).c_str())) {
    Serial.println("Failed to connect to WiFi and configure, restarting...");
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
  mqttClient.setSocketTimeout(30);
  
  Serial.println("MQTT setup complete");
}

void setupOTA() {
  Serial.println("Setting up OTA...");
  
  // Start AsyncElegantOTA
  AsyncElegantOTA.begin(&server);
  
  // Add custom endpoint for device info
  server.on("/info", HTTP_GET, [](AsyncWebServerRequest *request){
    StaticJsonDocument<200> doc;
    doc["device_id"] = DEVICE_ID;
    doc["device_type"] = DEVICE_TYPE;
    doc["firmware_version"] = FIRMWARE_VERSION;
    doc["mac_address"] = MAC_ADDRESS;
    doc["ip_address"] = WiFi.localIP().toString();
    doc["free_heap"] = ESP.getFreeHeap();
    doc["uptime"] = millis();
    
    String response;
    serializeJson(doc, response);
    request->send(200, "application/json", response);
  });
  
  // Add device control endpoint
  server.on("/control", HTTP_POST, [](AsyncWebServerRequest *request){
    if (request->hasParam("power", true)) {
      String powerParam = request->getParam("power", true)->value();
      deviceState.power = (powerParam == "true" || powerParam == "1");
      updateLED();
      publishState();
      request->send(200, "text/plain", "OK");
    } else {
      request->send(400, "text/plain", "Missing power parameter");
    }
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
  
  Serial.println("Topics configured:");
  Serial.println("  Status: " + TOPIC_STATUS);
  Serial.println("  State: " + TOPIC_STATE);
  Serial.println("  Online: " + TOPIC_ONLINE);
  Serial.println("  Command: " + TOPIC_COMMAND);
  Serial.println("  OTA: " + TOPIC_OTA);
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
      Serial.println("IP: " + WiFi.localIP().toString());
    } else {
      Serial.println("\nWiFi connection failed, will retry...");
    }
  }
}

void connectToMQTT() {
  if (WiFi.status() != WL_CONNECTED) {
    return;
  }
  
  Serial.println("Connecting to MQTT...");
  
  // Create will message for offline status
  String willTopic = TOPIC_ONLINE;
  String willMessage = "{\"online\":false}";
  
  if (mqttClient.connect(DEVICE_ID.c_str(), MQTT_USER, MQTT_PASSWORD, 
                        willTopic.c_str(), 1, true, willMessage.c_str())) {
    Serial.println("MQTT connected!");
    
    // Subscribe to command topic
    if (mqttClient.subscribe(TOPIC_COMMAND.c_str())) {
      Serial.println("Subscribed to: " + TOPIC_COMMAND);
    }
    
    if (mqttClient.subscribe(TOPIC_OTA.c_str())) {
      Serial.println("Subscribed to: " + TOPIC_OTA);
    }
    
    // Publish online status
    publishOnlineStatus(true);
    publishStatus();
    
    deviceState.online = true;
  } else {
    Serial.println("MQTT connection failed, rc=" + String(mqttClient.state()));
    deviceState.online = false;
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String topicStr = String(topic);
  String message = "";
  
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  Serial.println("Received [" + topicStr + "]: " + message);
  
  // Parse JSON message
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
  JsonObject parameters = doc["parameters"];
  
  Serial.println("Handling command: " + command);
  
  if (command == "set_power") {
    deviceState.power = parameters["power"];
    updateLED();
    publishState();
  }
  else if (command == "set_brightness") {
    deviceState.brightness = parameters["brightness"];
    if (deviceState.brightness < 0) deviceState.brightness = 0;
    if (deviceState.brightness > 100) deviceState.brightness = 100;
    updateLED();
    publishState();
  }
  else if (command == "set_color") {
    deviceState.color_r = parameters["r"];
    deviceState.color_g = parameters["g"];
    deviceState.color_b = parameters["b"];
    updateLED();
    publishState();
  }
  else if (command == "toggle") {
    deviceState.power = !deviceState.power;
    updateLED();
    publishState();
  }
  else if (command == "get_status") {
    publishStatus();
    publishState();
  }
  else if (command == "restart") {
    Serial.println("Restart command received");
    publishOnlineStatus(false);
    delay(1000);
    ESP.restart();
  }
  
  // Save state after any change
  saveStateToEEPROM();
}

void handleOTACommand(JsonDocument& doc) {
  String action = doc["action"];
  
  if (action == "update") {
    otaUrl = doc["url"].as<String>();
    Serial.println("OTA update requested: " + otaUrl);
    otaInProgress = true;
  } else if (action == "check") {
    // Publish current firmware version
    StaticJsonDocument<200> response;
    response["device_id"] = DEVICE_ID;
    response["current_version"] = FIRMWARE_VERSION;
    response["status"] = "ready_for_update";
    
    String responseStr;
    serializeJson(response, responseStr);
    mqttClient.publish(TOPIC_STATUS.c_str(), responseStr.c_str());
  }
}

void updateLED() {
  if (deviceState.power) {
    // Turn on relay
    digitalWrite(RELAY_PIN, HIGH);
    
    // Set LED brightness (simplified - just use brightness value)
    int pwmValue = map(deviceState.brightness, 0, 100, 0, 255);
    ledcWrite(PWM_CHANNEL, pwmValue);
  } else {
    // Turn off relay and LED
    digitalWrite(RELAY_PIN, LOW);
    ledcWrite(PWM_CHANNEL, 0);
  }
}

void IRAM_ATTR buttonISR() {
  unsigned long now = millis();
  if (now - lastButtonPress > DEBOUNCE_DELAY) {
    buttonPressed = true;
    lastButtonPress = now;
  }
}

void handleButton() {
  Serial.println("Button pressed - toggling power");
  deviceState.power = !deviceState.power;
  updateLED();
  publishState();
  saveStateToEEPROM();
}

void publishStatus() {
  StaticJsonDocument<300> doc;
  doc["device_id"] = DEVICE_ID;
  doc["device_type"] = DEVICE_TYPE;
  doc["firmware_version"] = FIRMWARE_VERSION;
  doc["mac_address"] = MAC_ADDRESS;
  doc["ip_address"] = WiFi.localIP().toString();
  doc["online"] = deviceState.online;
  doc["wifi_rssi"] = WiFi.RSSI();
  doc["free_heap"] = ESP.getFreeHeap();
  doc["uptime"] = millis();
  
  String message;
  serializeJson(doc, message);
  
  if (mqttClient.connected()) {
    mqttClient.publish(TOPIC_STATUS.c_str(), message.c_str(), true);
  }
}

void publishState() {
  StaticJsonDocument<200> doc;
  doc["power"] = deviceState.power;
  doc["brightness"] = deviceState.brightness;
  doc["color_r"] = deviceState.color_r;
  doc["color_g"] = deviceState.color_g;
  doc["color_b"] = deviceState.color_b;
  doc["timestamp"] = millis();
  
  String message;
  serializeJson(doc, message);
  
  if (mqttClient.connected()) {
    mqttClient.publish(TOPIC_STATE.c_str(), message.c_str());
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
  
  deviceState.online = online;
}

void saveStateToEEPROM() {
  EEPROM.write(0, deviceState.power ? 1 : 0);
  EEPROM.write(1, deviceState.brightness);
  EEPROM.write(2, deviceState.color_r);
  EEPROM.write(3, deviceState.color_g);
  EEPROM.write(4, deviceState.color_b);
  EEPROM.commit();
}

void loadStateFromEEPROM() {
  deviceState.power = EEPROM.read(0) == 1;
  deviceState.brightness = EEPROM.read(1);
  deviceState.color_r = EEPROM.read(2);
  deviceState.color_g = EEPROM.read(3);
  deviceState.color_b = EEPROM.read(4);
  
  // Validate loaded values
  if (deviceState.brightness > 100) deviceState.brightness = 100;
  if (deviceState.color_r > 255) deviceState.color_r = 255;
  if (deviceState.color_g > 255) deviceState.color_g = 255;
  if (deviceState.color_b > 255) deviceState.color_b = 255;
  
  Serial.println("State loaded from EEPROM:");
  Serial.println("  Power: " + String(deviceState.power));
  Serial.println("  Brightness: " + String(deviceState.brightness));
}

void performOTAUpdate() {
  if (otaUrl.length() == 0) {
    otaInProgress = false;
    return;
  }
  
  Serial.println("Starting OTA update from: " + otaUrl);
  
  // Publish update status
  StaticJsonDocument<200> status;
  status["device_id"] = DEVICE_ID;
  status["status"] = "updating";
  status["progress"] = 0;
  
  String statusStr;
  serializeJson(status, statusStr);
  mqttClient.publish(TOPIC_STATUS.c_str(), statusStr.c_str());
  
  // Perform HTTP OTA update
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
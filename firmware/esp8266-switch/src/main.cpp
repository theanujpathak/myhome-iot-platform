#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <WiFiManager.h>
#include <ESPAsyncWebServer.h>
#include <AsyncElegantOTA.h>
#include <EEPROM.h>
#include <ESP8266httpUpdate.h>

// Hardware pin definitions
#define RELAY_PIN 5    // D1
#define LED_PIN 2      // D4 (built-in LED)
#define BUTTON_PIN 0   // D3

// Device configuration
const char* DEVICE_TYPE = "Smart Switch";
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

// WiFi and MQTT clients
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
AsyncWebServer server(80);

// Device state
struct SwitchState {
  bool power = false;
  bool online = false;
  unsigned long lastHeartbeat = 0;
  unsigned long lastStateUpdate = 0;
  unsigned long lastButtonPress = 0;
};

SwitchState switchState;

// Button handling
volatile bool buttonPressed = false;
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
void updateRelay();
void handleButton();
void IRAM_ATTR buttonISR();
void saveStateToEEPROM();
void loadStateFromEEPROM();
void performOTAUpdate();

void setup() {
  Serial.begin(115200);
  Serial.println("\n=== Home Automation Smart Switch ===");
  Serial.println("Firmware Version: " + String(FIRMWARE_VERSION));
  
  // Setup hardware
  setupHardware();
  
  // Load saved state
  loadStateFromEEPROM();
  
  // Generate device ID from MAC
  MAC_ADDRESS = WiFi.macAddress();
  DEVICE_ID = "smart_switch_" + MAC_ADDRESS;
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
  updateRelay();
  
  Serial.println("Setup complete!");
}

void loop() {
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
  if (now - switchState.lastHeartbeat > 30000) {
    publishOnlineStatus(true);
    switchState.lastHeartbeat = now;
  }
  
  // Send state update every 5 seconds if state changed
  if (now - switchState.lastStateUpdate > 5000) {
    publishState();
    switchState.lastStateUpdate = now;
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
  
  // Setup pins
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  
  // Initial state
  digitalWrite(RELAY_PIN, LOW);
  digitalWrite(LED_PIN, HIGH); // LED is inverted on ESP8266
  
  // Setup button interrupt
  attachInterrupt(digitalPinToInterrupt(BUTTON_PIN), buttonISR, FALLING);
  
  Serial.println("Hardware setup complete");
}

void setupWiFi() {
  Serial.println("Setting up WiFi...");
  
  WiFiManager wifiManager;
  wifiManager.setConfigPortalTimeout(300);
  
  if (!wifiManager.autoConnect(("SmartSwitch_" + DEVICE_ID).c_str())) {
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
    StaticJsonDocument<200> doc;
    doc["device_id"] = DEVICE_ID;
    doc["device_type"] = DEVICE_TYPE;
    doc["firmware_version"] = FIRMWARE_VERSION;
    doc["mac_address"] = MAC_ADDRESS;
    doc["ip_address"] = WiFi.localIP().toString();
    doc["power"] = switchState.power;
    doc["free_heap"] = ESP.getFreeHeap();
    doc["uptime"] = millis();
    
    String response;
    serializeJson(doc, response);
    request->send(200, "application/json", response);
  });
  
  server.on("/control", HTTP_POST, [](AsyncWebServerRequest *request){
    if (request->hasParam("power", true)) {
      String powerParam = request->getParam("power", true)->value();
      switchState.power = (powerParam == "true" || powerParam == "1");
      updateRelay();
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
    
    switchState.online = true;
  } else {
    Serial.println("MQTT connection failed, rc=" + String(mqttClient.state()));
    switchState.online = false;
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
  JsonObject parameters = doc["parameters"];
  
  Serial.println("Handling command: " + command);
  
  if (command == "set_power") {
    switchState.power = parameters["power"];
    updateRelay();
    publishState();
  } else if (command == "toggle") {
    switchState.power = !switchState.power;
    updateRelay();
    publishState();
  } else if (command == "get_status") {
    publishStatus();
    publishState();
  } else if (command == "restart") {
    Serial.println("Restart command received");
    publishOnlineStatus(false);
    delay(1000);
    ESP.restart();
  }
  
  saveStateToEEPROM();
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

void updateRelay() {
  digitalWrite(RELAY_PIN, switchState.power ? HIGH : LOW);
  digitalWrite(LED_PIN, switchState.power ? LOW : HIGH); // LED is inverted
}

void IRAM_ATTR buttonISR() {
  unsigned long now = millis();
  if (now - switchState.lastButtonPress > DEBOUNCE_DELAY) {
    buttonPressed = true;
    switchState.lastButtonPress = now;
  }
}

void handleButton() {
  Serial.println("Button pressed - toggling power");
  switchState.power = !switchState.power;
  updateRelay();
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
  doc["online"] = switchState.online;
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
  StaticJsonDocument<150> doc;
  doc["power"] = switchState.power;
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
  
  switchState.online = online;
}

void saveStateToEEPROM() {
  EEPROM.write(0, switchState.power ? 1 : 0);
  EEPROM.commit();
}

void loadStateFromEEPROM() {
  switchState.power = EEPROM.read(0) == 1;
  Serial.println("State loaded from EEPROM:");
  Serial.println("  Power: " + String(switchState.power));
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
  t_httpUpdate_return ret = ESPhttpUpdate.update(client, otaUrl);
  
  switch (ret) {
    case HTTP_UPDATE_FAILED:
      Serial.println("OTA Update failed: " + ESPhttpUpdate.getLastErrorString());
      status["status"] = "failed";
      status["error"] = ESPhttpUpdate.getLastErrorString();
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
#include <Arduino.h>
#include <Ethernet.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <EEPROM.h>

// Hardware pin definitions
#define DHT_PIN 2
#define DHT_TYPE DHT22
#define LED_PIN 13
#define RELAY_PIN 7
#define BUTTON_PIN 8
#define ANALOG_SENSOR_PIN A0

// Device configuration
const char* DEVICE_TYPE = "Arduino Gateway";
const char* FIRMWARE_VERSION = "1.0.0";
String DEVICE_ID = "arduino_gateway_001";

// Network configuration
byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };
IPAddress ip(192, 168, 1, 200);
IPAddress server(192, 168, 1, 100);

// MQTT Configuration
const char* MQTT_SERVER = "192.168.1.100";
const int MQTT_PORT = 1883;
const char* MQTT_USER = "";
const char* MQTT_PASSWORD = "";

// Topics
String TOPIC_BASE = "homeautomation/devices/" + DEVICE_ID;
String TOPIC_STATUS = TOPIC_BASE + "/status";
String TOPIC_STATE = TOPIC_BASE + "/state";
String TOPIC_ONLINE = TOPIC_BASE + "/online";
String TOPIC_COMMAND = TOPIC_BASE + "/command";

// Sensors and clients
DHT dht(DHT_PIN, DHT_TYPE);
EthernetClient ethClient;
PubSubClient mqttClient(ethClient);

// Device state
struct GatewayState {
  bool power = false;
  float temperature = 0.0;
  float humidity = 0.0;
  int analogValue = 0;
  bool online = false;
  unsigned long lastHeartbeat = 0;
  unsigned long lastSensorRead = 0;
  unsigned long lastButtonPress = 0;
  bool buttonPressed = false;
};

GatewayState gatewayState;

// Button handling
const unsigned long DEBOUNCE_DELAY = 50;

// Function declarations
void setupHardware();
void setupEthernet();
void setupMQTT();
void connectToMQTT();
void mqttCallback(char* topic, byte* payload, unsigned int length);
void publishStatus();
void publishState();
void publishOnlineStatus(bool online);
void handleCommand(StaticJsonDocument<256>& doc);
void updateRelay();
void handleButton();
void readSensors();
void saveStateToEEPROM();
void loadStateFromEEPROM();

void setup() {
  Serial.begin(9600);
  Serial.println("=== Home Automation Arduino Gateway ===");
  Serial.println("Firmware Version: " + String(FIRMWARE_VERSION));
  
  // Setup hardware
  setupHardware();
  
  // Load saved state
  loadStateFromEEPROM();
  
  // Setup Ethernet
  setupEthernet();
  
  // Setup MQTT
  setupMQTT();
  
  // Initialize DHT sensor
  dht.begin();
  
  // Initial state update
  updateRelay();
  
  Serial.println("Setup complete!");
}

void loop() {
  // Handle MQTT connection
  if (!mqttClient.connected()) {
    connectToMQTT();
  } else {
    mqttClient.loop();
  }
  
  // Handle button press
  if (digitalRead(BUTTON_PIN) == LOW) {
    if (!gatewayState.buttonPressed && 
        (millis() - gatewayState.lastButtonPress > DEBOUNCE_DELAY)) {
      handleButton();
      gatewayState.buttonPressed = true;
      gatewayState.lastButtonPress = millis();
    }
  } else {
    gatewayState.buttonPressed = false;
  }
  
  // Read sensors every 5 seconds
  unsigned long now = millis();
  if (now - gatewayState.lastSensorRead > 5000) {
    readSensors();
    gatewayState.lastSensorRead = now;
  }
  
  // Send heartbeat every 30 seconds
  if (now - gatewayState.lastHeartbeat > 30000) {
    publishOnlineStatus(true);
    publishState();
    gatewayState.lastHeartbeat = now;
  }
  
  // Maintain Ethernet connection
  Ethernet.maintain();
  
  delay(100);
}

void setupHardware() {
  Serial.println("Setting up hardware...");
  
  // Setup pins
  pinMode(LED_PIN, OUTPUT);
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  
  // Initial state
  digitalWrite(LED_PIN, LOW);
  digitalWrite(RELAY_PIN, LOW);
  
  Serial.println("Hardware setup complete");
}

void setupEthernet() {
  Serial.println("Setting up Ethernet...");
  
  // Start Ethernet with DHCP
  if (Ethernet.begin(mac) == 0) {
    Serial.println("Failed to configure Ethernet using DHCP");
    Serial.println("Using static IP configuration");
    Ethernet.begin(mac, ip);
  }
  
  // Give the Ethernet shield time to initialize
  delay(1000);
  
  Serial.print("IP address: ");
  Serial.println(Ethernet.localIP());
}

void setupMQTT() {
  Serial.println("Setting up MQTT...");
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
  Serial.println("MQTT setup complete");
}

void connectToMQTT() {
  Serial.println("Connecting to MQTT...");
  
  if (mqttClient.connect(DEVICE_ID.c_str(), MQTT_USER, MQTT_PASSWORD)) {
    Serial.println("MQTT connected!");
    
    // Subscribe to command topic
    String commandTopic = TOPIC_COMMAND;
    if (mqttClient.subscribe(commandTopic.c_str())) {
      Serial.println("Subscribed to: " + commandTopic);
    }
    
    // Publish online status
    publishOnlineStatus(true);
    publishStatus();
    
    gatewayState.online = true;
  } else {
    Serial.println("MQTT connection failed, rc=" + String(mqttClient.state()));
    gatewayState.online = false;
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
  StaticJsonDocument<256> doc;
  DeserializationError error = deserializeJson(doc, message);
  
  if (error) {
    Serial.println("Failed to parse JSON: " + String(error.c_str()));
    return;
  }
  
  if (topicStr == TOPIC_COMMAND) {
    handleCommand(doc);
  }
}

void handleCommand(StaticJsonDocument<256>& doc) {
  String command = doc["command"];
  JsonObject parameters = doc["parameters"];
  
  Serial.println("Handling command: " + command);
  
  if (command == "set_power") {
    gatewayState.power = parameters["power"];
    updateRelay();
    publishState();
  } else if (command == "toggle") {
    gatewayState.power = !gatewayState.power;
    updateRelay();
    publishState();
  } else if (command == "get_status") {
    publishStatus();
    publishState();
  } else if (command == "get_sensors") {
    readSensors();
    publishState();
  }
  
  // Save state after any change
  saveStateToEEPROM();
}

void updateRelay() {
  digitalWrite(RELAY_PIN, gatewayState.power ? HIGH : LOW);
  digitalWrite(LED_PIN, gatewayState.power ? HIGH : LOW);
}

void handleButton() {
  Serial.println("Button pressed - toggling power");
  gatewayState.power = !gatewayState.power;
  updateRelay();
  publishState();
  saveStateToEEPROM();
}

void readSensors() {
  // Read DHT sensor
  float temp = dht.readTemperature();
  float hum = dht.readHumidity();
  
  if (!isnan(temp) && !isnan(hum)) {
    gatewayState.temperature = temp;
    gatewayState.humidity = hum;
  }
  
  // Read analog sensor
  gatewayState.analogValue = analogRead(ANALOG_SENSOR_PIN);
}

void publishStatus() {
  StaticJsonDocument<400> doc;
  doc["device_id"] = DEVICE_ID;
  doc["device_type"] = DEVICE_TYPE;
  doc["firmware_version"] = FIRMWARE_VERSION;
  doc["ip_address"] = Ethernet.localIP().toString();
  doc["online"] = gatewayState.online;
  doc["free_memory"] = freeMemory();
  doc["uptime"] = millis();
  
  String message;
  serializeJson(doc, message);
  
  if (mqttClient.connected()) {
    mqttClient.publish(TOPIC_STATUS.c_str(), message.c_str(), true);
  }
}

void publishState() {
  StaticJsonDocument<300> doc;
  doc["device_id"] = DEVICE_ID;
  doc["power"] = gatewayState.power;
  doc["temperature"] = gatewayState.temperature;
  doc["humidity"] = gatewayState.humidity;
  doc["analog_value"] = gatewayState.analogValue;
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
  
  gatewayState.online = online;
}

void saveStateToEEPROM() {
  EEPROM.write(0, gatewayState.power ? 1 : 0);
}

void loadStateFromEEPROM() {
  gatewayState.power = EEPROM.read(0) == 1;
  Serial.println("State loaded from EEPROM:");
  Serial.println("  Power: " + String(gatewayState.power));
}

// Helper function to get free memory
int freeMemory() {
  extern int __heap_start, *__brkval;
  int v;
  return (int)&v - (__brkval == 0 ? (int)&__heap_start : (int)__brkval);
}
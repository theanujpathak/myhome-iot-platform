#!/usr/bin/env python3
"""
MQTT Bridge for ESP32 Emulator Integration
Connects the home automation system with emulated ESP32 devices via MQTT
"""

import asyncio
import json
import logging
import signal
import sys
from typing import Dict, Any
import paho.mqtt.client as mqtt
import requests
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MQTTBridge:
    """MQTT Bridge between home automation system and ESP32 emulator"""
    
    def __init__(self):
        self.mqtt_client = None
        self.emulator_url = "http://localhost:8090"
        self.device_service_url = "http://localhost:3002"
        self.running = True
        self.devices = {}
        
        # MQTT topics
        self.control_topic_prefix = "home/devices"
        self.status_topic_prefix = "home/status"
        self.discovery_topic = "home/discovery"
        
    def setup_mqtt_client(self):
        """Setup MQTT client for communication"""
        try:
            self.mqtt_client = mqtt.Client("home_automation_bridge")
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_message = self.on_mqtt_message
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            
            # Connect to MQTT broker (assuming Mosquitto is running)
            logger.info("Connecting to MQTT broker...")
            self.mqtt_client.connect("localhost", 1883, 60)
            self.mqtt_client.loop_start()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup MQTT client: {e}")
            logger.info("Make sure Mosquitto MQTT broker is running:")
            logger.info("  brew install mosquitto")
            logger.info("  brew services start mosquitto")
            return False
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            logger.info("Connected to MQTT broker successfully")
            
            # Subscribe to control topics for all devices
            control_topic = f"{self.control_topic_prefix}/+/control"
            client.subscribe(control_topic)
            logger.info(f"Subscribed to {control_topic}")
            
            # Subscribe to discovery requests
            client.subscribe(f"{self.discovery_topic}/request")
            logger.info(f"Subscribed to {self.discovery_topic}/request")
            
            # Publish initial device discovery
            self.publish_device_discovery()
            
        else:
            logger.error(f"Failed to connect to MQTT broker with code {rc}")
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        logger.warning("Disconnected from MQTT broker")
    
    def on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        try:
            topic = msg.topic
            payload = msg.payload.decode()
            
            logger.info(f"Received MQTT message - Topic: {topic}, Payload: {payload}")
            
            if topic.startswith(self.control_topic_prefix):
                # Extract device ID from topic: home/devices/{device_id}/control
                topic_parts = topic.split('/')
                if len(topic_parts) >= 4 and topic_parts[3] == 'control':
                    device_id = topic_parts[2]
                    self.handle_device_control(device_id, payload)
            
            elif topic == f"{self.discovery_topic}/request":
                # Handle discovery request
                self.publish_device_discovery()
            
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def handle_device_control(self, device_id: str, payload: str):
        """Handle device control commands from MQTT"""
        try:
            command = json.loads(payload)
            logger.info(f"Controlling device {device_id} with command: {command}")
            
            # Forward command to ESP32 emulator
            response = requests.post(
                f"{self.emulator_url}/api/devices/{device_id}/control",
                json=command,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    logger.info(f"Device {device_id} controlled successfully")
                    
                    # Publish updated device state
                    self.publish_device_state(device_id, result['device'])
                    
                else:
                    logger.error(f"Device control failed for {device_id}")
            else:
                logger.error(f"HTTP error controlling device {device_id}: {response.status_code}")
        
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON payload for device {device_id}: {payload}")
        except Exception as e:
            logger.error(f"Error controlling device {device_id}: {e}")
    
    def publish_device_state(self, device_id: str, device_data: Dict[str, Any]):
        """Publish device state to MQTT"""
        try:
            if not self.mqtt_client:
                return
            
            # Create status message
            status_data = {
                "device_id": device_id,
                "timestamp": device_data.get("last_seen"),
                "online": device_data.get("is_online", False),
                "power_state": device_data.get("power_state", False),
                "brightness": device_data.get("brightness", 0),
                "temperature": device_data.get("temperature", 0),
                "humidity": device_data.get("humidity", 0),
                "motion_detected": device_data.get("motion_detected", False),
                "door_open": device_data.get("door_open", False),
                "battery_level": device_data.get("battery_level", 0),
                "signal_strength": device_data.get("signal_strength", 0)
            }
            
            # Publish to device-specific status topic
            status_topic = f"{self.status_topic_prefix}/{device_id}"
            self.mqtt_client.publish(status_topic, json.dumps(status_data))
            
            logger.debug(f"Published state for {device_id} to {status_topic}")
            
        except Exception as e:
            logger.error(f"Error publishing device state for {device_id}: {e}")
    
    def publish_device_discovery(self):
        """Publish device discovery information to MQTT"""
        try:
            # Get devices from emulator
            response = requests.get(f"{self.emulator_url}/api/devices", timeout=5)
            if response.status_code == 200:
                devices = response.json()
                
                discovery_data = {
                    "timestamp": time.time(),
                    "source": "esp32_emulator",
                    "devices": []
                }
                
                for device in devices:
                    device_info = {
                        "device_id": device["device_id"],
                        "device_name": device["device_name"],
                        "device_type": device["device_type"],
                        "ip_address": device["ip_address"],
                        "mac_address": device["mac_address"],
                        "manufacturer": "Espressif",
                        "firmware_version": device["firmware_version"],
                        "capabilities": self.get_device_capabilities(device),
                        "control_topic": f"{self.control_topic_prefix}/{device['device_id']}/control",
                        "status_topic": f"{self.status_topic_prefix}/{device['device_id']}"
                    }
                    discovery_data["devices"].append(device_info)
                
                # Publish discovery data
                discovery_topic = f"{self.discovery_topic}/response"
                self.mqtt_client.publish(discovery_topic, json.dumps(discovery_data))
                
                logger.info(f"Published discovery data for {len(devices)} devices")
                
                # Update local device cache
                self.devices = {d["device_id"]: d for d in devices}
                
        except Exception as e:
            logger.error(f"Error publishing device discovery: {e}")
    
    def get_device_capabilities(self, device: Dict[str, Any]) -> Dict[str, Any]:
        """Get device capabilities for MQTT discovery"""
        capabilities = {
            "online": True,
            "power": device["device_type"] in ["Smart Light", "Smart Switch"],
            "brightness": device.get("supports_dimming", False),
            "color": device.get("supports_color", False),
            "temperature": device["device_type"] == "Temperature Sensor",
            "humidity": device["device_type"] == "Temperature Sensor",
            "motion": device["device_type"] == "Motion Sensor",
            "door": device["device_type"] == "Door Sensor",
            "battery": True,
            "signal": True
        }
        return capabilities
    
    def start_status_monitoring(self):
        """Start background thread to monitor and publish device status"""
        def monitor_devices():
            while self.running:
                try:
                    # Get current device states from emulator
                    response = requests.get(f"{self.emulator_url}/api/devices", timeout=5)
                    if response.status_code == 200:
                        devices = response.json()
                        
                        for device in devices:
                            self.publish_device_state(device["device_id"], device)
                    
                    time.sleep(10)  # Update every 10 seconds
                    
                except Exception as e:
                    logger.error(f"Error in status monitoring: {e}")
                    time.sleep(5)
        
        thread = threading.Thread(target=monitor_devices, daemon=True)
        thread.start()
        logger.info("Started device status monitoring thread")
    
    def test_mqtt_integration(self):
        """Test MQTT integration by sending test commands"""
        logger.info("Testing MQTT integration...")
        
        try:
            # Wait a moment for everything to initialize
            time.sleep(2)
            
            # Test device discovery
            logger.info("Testing device discovery...")
            self.mqtt_client.publish(f"{self.discovery_topic}/request", "discover")
            
            time.sleep(1)
            
            # Test device control
            if self.devices:
                device_id = list(self.devices.keys())[0]
                device = self.devices[device_id]
                
                if device["device_type"] in ["Smart Light", "Smart Switch"]:
                    logger.info(f"Testing control of {device['device_name']}...")
                    
                    # Turn on device
                    control_topic = f"{self.control_topic_prefix}/{device_id}/control"
                    control_command = {"power_state": True}
                    self.mqtt_client.publish(control_topic, json.dumps(control_command))
                    
                    time.sleep(1)
                    
                    # Turn off device
                    control_command = {"power_state": False}
                    self.mqtt_client.publish(control_topic, json.dumps(control_command))
            
            logger.info("✅ MQTT integration test completed")
            
        except Exception as e:
            logger.error(f"Error in MQTT integration test: {e}")
    
    def handle_shutdown(self, signum, frame):
        """Handle shutdown signal"""
        logger.info("Shutting down MQTT Bridge...")
        self.running = False
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        sys.exit(0)
    
    def run(self):
        """Start the MQTT bridge"""
        logger.info("Starting MQTT Bridge for ESP32 Emulator")
        logger.info("=" * 50)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        
        # Check emulator availability
        try:
            response = requests.get(f"{self.emulator_url}/api/devices", timeout=5)
            if response.status_code == 200:
                devices = response.json()
                logger.info(f"✅ ESP32 Emulator found with {len(devices)} devices")
            else:
                logger.error("❌ ESP32 Emulator not responding")
                return False
        except Exception as e:
            logger.error(f"❌ Cannot connect to ESP32 Emulator: {e}")
            logger.info("Make sure the emulator is running: python3 esp32_device_emulator.py")
            return False
        
        # Setup MQTT
        if not self.setup_mqtt_client():
            return False
        
        # Start status monitoring
        self.start_status_monitoring()
        
        # Test integration
        time.sleep(2)
        self.test_mqtt_integration()
        
        logger.info("🌉 MQTT Bridge is running!")
        logger.info("📡 MQTT Topics:")
        logger.info(f"   Control: {self.control_topic_prefix}/{{device_id}}/control")
        logger.info(f"   Status:  {self.status_topic_prefix}/{{device_id}}")
        logger.info(f"   Discovery: {self.discovery_topic}/request")
        logger.info("🔄 Use CTRL+C to stop")
        
        # Keep running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.handle_shutdown(signal.SIGINT, None)

if __name__ == "__main__":
    bridge = MQTTBridge()
    bridge.run()
#!/usr/bin/env python3
"""
ESP32 Device Emulator
Simulates multiple ESP32 IoT devices on the network with MQTT communication
"""

import asyncio
import json
import time
import uuid
import random
import socket
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import paho.mqtt.client as mqtt
import threading
import requests
from zeroconf import ServiceInfo, Zeroconf
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DeviceState:
    """Represents the current state of a simulated device"""
    device_id: str
    device_name: str
    device_type: str
    is_online: bool
    last_seen: str
    ip_address: str
    mac_address: str
    firmware_version: str
    
    # Device-specific states
    power_state: bool = False
    brightness: int = 100
    temperature: float = 22.5
    humidity: float = 45.0
    motion_detected: bool = False
    door_open: bool = False
    battery_level: int = 100
    signal_strength: int = -45
    
    # Control capabilities
    supports_dimming: bool = True
    supports_color: bool = False
    supports_scheduling: bool = True

class ESP32DeviceEmulator:
    """Emulates multiple ESP32 devices with different types and capabilities"""
    
    def __init__(self, port=8090):
        self.port = port
        self.devices: Dict[str, DeviceState] = {}
        self.mqtt_client = None
        self.mqtt_connected = False
        self.discovery_service = None
        self.zeroconf = None
        
        # Flask app for web interface
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'esp32_emulator_secret'
        
        # Enable CORS for all routes
        CORS(self.app, origins=["http://localhost:3000", "http://127.0.0.1:3000"])
        
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        self.setup_flask_routes()
        self.setup_socketio_events()
        self.create_sample_devices()
        
    def create_sample_devices(self):
        """Create sample ESP32 devices of different types"""
        device_configs = [
            {
                "device_name": "Living Room Smart Light",
                "device_type": "Smart Light",
                "mac_address": "AA:BB:CC:DD:EE:01",
                "supports_dimming": True,
                "supports_color": True
            },
            {
                "device_name": "Kitchen Smart Switch", 
                "device_type": "Smart Switch",
                "mac_address": "AA:BB:CC:DD:EE:02",
                "supports_dimming": False,
                "supports_color": False
            },
            {
                "device_name": "Bedroom Temperature Sensor",
                "device_type": "Temperature Sensor", 
                "mac_address": "AA:BB:CC:DD:EE:03",
                "supports_dimming": False,
                "supports_color": False
            },
            {
                "device_name": "Entry Motion Detector",
                "device_type": "Motion Sensor",
                "mac_address": "AA:BB:CC:DD:EE:04", 
                "supports_dimming": False,
                "supports_color": False
            },
            {
                "device_name": "Smart Door Sensor",
                "device_type": "Door Sensor",
                "mac_address": "AA:BB:CC:DD:EE:05",
                "supports_dimming": False,
                "supports_color": False
            }
        ]
        
        for i, config in enumerate(device_configs):
            device_id = f"ESP32_{config['mac_address'].replace(':', '')[-6:]}"
            ip_address = f"192.168.1.{100 + i}"
            
            device = DeviceState(
                device_id=device_id,
                device_name=config["device_name"],
                device_type=config["device_type"],
                is_online=True,
                last_seen=datetime.now().isoformat(),
                ip_address=ip_address,
                mac_address=config["mac_address"],
                firmware_version="1.0.0",
                supports_dimming=config["supports_dimming"],
                supports_color=config["supports_color"],
                temperature=random.uniform(18.0, 26.0),
                humidity=random.uniform(40.0, 60.0),
                battery_level=random.randint(85, 100),
                signal_strength=random.randint(-60, -30)
            )
            
            self.devices[device_id] = device
            logger.info(f"Created emulated device: {device.device_name} ({device_id})")
    
    def setup_flask_routes(self):
        """Setup Flask web routes for the emulator dashboard"""
        
        @self.app.route('/')
        def dashboard():
            return render_template('emulator_dashboard.html')
        
        @self.app.route('/api/devices')
        def get_devices():
            """Return all emulated devices"""
            return jsonify([asdict(device) for device in self.devices.values()])
        
        @self.app.route('/api/devices/<device_id>')
        def get_device(device_id):
            """Get specific device info"""
            if device_id in self.devices:
                return jsonify(asdict(self.devices[device_id]))
            return jsonify({"error": "Device not found"}), 404
        
        @self.app.route('/api/devices/<device_id>/control', methods=['POST'])
        def control_device(device_id):
            """Control a specific device"""
            if device_id not in self.devices:
                return jsonify({"error": "Device not found"}), 404
                
            device = self.devices[device_id]
            data = request.get_json()
            
            # Update device state based on control command
            if 'power_state' in data:
                device.power_state = data['power_state']
            if 'brightness' in data and device.supports_dimming:
                device.brightness = max(0, min(100, data['brightness']))
            if 'temperature' in data:
                device.temperature = data['temperature']
                
            device.last_seen = datetime.now().isoformat()
            
            # Broadcast state change via WebSocket
            self.socketio.emit('device_state_changed', {
                'device_id': device_id,
                'state': asdict(device)
            })
            
            # Send MQTT message if connected
            if self.mqtt_connected:
                self.publish_device_state(device_id)
            
            return jsonify({"success": True, "device": asdict(device)})
        
        @self.app.route('/api/discovery/info')
        def discovery_info():
            """Return device discovery information for mDNS/UPnP simulation"""
            discovery_devices = []
            for device in self.devices.values():
                discovery_devices.append({
                    "ip": device.ip_address,
                    "mac": device.mac_address,
                    "device_id": device.device_id,
                    "device_name": device.device_name,
                    "device_type": device.device_type,
                    "manufacturer": "Espressif",
                    "firmware_version": device.firmware_version,
                    "services": ["http", "mqtt"],
                    "ports": [80, 1883],
                    "discovery_method": "emulator"
                })
            return jsonify(discovery_devices)
    
    def setup_socketio_events(self):
        """Setup WebSocket events for real-time communication"""
        
        @self.socketio.on('connect')
        def handle_connect():
            logger.info("Dashboard client connected")
            emit('device_list', [asdict(device) for device in self.devices.values()])
        
        @self.socketio.on('simulate_sensor_reading')
        def handle_sensor_simulation(data):
            """Simulate sensor reading changes"""
            device_id = data.get('device_id')
            if device_id in self.devices:
                device = self.devices[device_id]
                
                # Simulate random sensor changes
                if device.device_type == "Temperature Sensor":
                    device.temperature = random.uniform(18.0, 28.0)
                    device.humidity = random.uniform(35.0, 65.0)
                elif device.device_type == "Motion Sensor":
                    device.motion_detected = not device.motion_detected
                elif device.device_type == "Door Sensor":
                    device.door_open = not device.door_open
                
                device.last_seen = datetime.now().isoformat()
                
                emit('device_state_changed', {
                    'device_id': device_id,
                    'state': asdict(device)
                }, broadcast=True)
                
                if self.mqtt_connected:
                    self.publish_device_state(device_id)
        
        @self.socketio.on('toggle_device_online')
        def handle_toggle_online(data):
            """Toggle device online/offline status"""
            device_id = data.get('device_id')
            if device_id in self.devices:
                device = self.devices[device_id]
                device.is_online = not device.is_online
                device.last_seen = datetime.now().isoformat()
                
                emit('device_state_changed', {
                    'device_id': device_id,
                    'state': asdict(device)
                }, broadcast=True)
    
    def setup_mqtt_client(self):
        """Setup MQTT client for communication with home automation system"""
        try:
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_message = self.on_mqtt_message
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            
            # Connect to local MQTT broker
            self.mqtt_client.connect("localhost", 1883, 60)
            self.mqtt_client.loop_start()
            
        except Exception as e:
            logger.error(f"Failed to setup MQTT client: {e}")
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.mqtt_connected = True
            logger.info("Connected to MQTT broker")
            
            # Subscribe to device control topics
            for device_id in self.devices.keys():
                topic = f"devices/{device_id}/control"
                client.subscribe(topic)
                logger.info(f"Subscribed to {topic}")
                
            # Publish initial device states
            for device_id in self.devices.keys():
                self.publish_device_state(device_id)
                
        else:
            logger.error(f"Failed to connect to MQTT broker with code {rc}")
    
    def on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        try:
            topic_parts = msg.topic.split('/')
            if len(topic_parts) >= 3 and topic_parts[2] == 'control':
                device_id = topic_parts[1]
                
                if device_id in self.devices:
                    command = json.loads(msg.payload.decode())
                    device = self.devices[device_id]
                    
                    # Process control command
                    if 'power_state' in command:
                        device.power_state = command['power_state']
                    if 'brightness' in command and device.supports_dimming:
                        device.brightness = max(0, min(100, command['brightness']))
                    
                    device.last_seen = datetime.now().isoformat()
                    
                    logger.info(f"MQTT control received for {device_id}: {command}")
                    
                    # Broadcast to dashboard
                    self.socketio.emit('device_state_changed', {
                        'device_id': device_id,
                        'state': asdict(device)
                    })
                    
                    # Publish updated state
                    self.publish_device_state(device_id)
                    
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.mqtt_connected = False
        logger.warning("Disconnected from MQTT broker")
    
    def publish_device_state(self, device_id):
        """Publish device state to MQTT"""
        if self.mqtt_connected and device_id in self.devices:
            device = self.devices[device_id]
            topic = f"devices/{device_id}/state"
            
            state_data = {
                "device_id": device.device_id,
                "is_online": device.is_online,
                "power_state": device.power_state,
                "brightness": device.brightness,
                "temperature": device.temperature,
                "humidity": device.humidity,
                "motion_detected": device.motion_detected,
                "door_open": device.door_open,
                "battery_level": device.battery_level,
                "signal_strength": device.signal_strength,
                "timestamp": device.last_seen
            }
            
            self.mqtt_client.publish(topic, json.dumps(state_data))
    
    def start_sensor_simulation(self):
        """Start background thread for sensor data simulation"""
        def simulate_sensors():
            while True:
                try:
                    for device_id, device in self.devices.items():
                        if device.is_online:
                            # Simulate temperature/humidity changes
                            if device.device_type == "Temperature Sensor":
                                device.temperature += random.uniform(-0.5, 0.5)
                                device.temperature = max(15.0, min(35.0, device.temperature))
                                device.humidity += random.uniform(-2.0, 2.0)
                                device.humidity = max(20.0, min(80.0, device.humidity))
                            
                            # Simulate motion detection (random)
                            elif device.device_type == "Motion Sensor":
                                if random.random() < 0.1:  # 10% chance per cycle
                                    device.motion_detected = True
                                elif random.random() < 0.3:  # 30% chance to clear
                                    device.motion_detected = False
                            
                            # Simulate battery drain
                            if random.random() < 0.01:  # 1% chance per cycle
                                device.battery_level = max(0, device.battery_level - 1)
                            
                            device.last_seen = datetime.now().isoformat()
                            
                            # Publish to MQTT
                            if self.mqtt_connected:
                                self.publish_device_state(device_id)
                    
                    # Broadcast all device states via WebSocket
                    self.socketio.emit('devices_updated', 
                        [asdict(device) for device in self.devices.values()])
                    
                    time.sleep(10)  # Update every 10 seconds
                    
                except Exception as e:
                    logger.error(f"Error in sensor simulation: {e}")
                    time.sleep(5)
        
        thread = threading.Thread(target=simulate_sensors, daemon=True)
        thread.start()
        logger.info("Started sensor simulation thread")
    
    def setup_device_discovery(self):
        """Setup mDNS service for device discovery"""
        try:
            self.zeroconf = Zeroconf()
            
            for device in self.devices.values():
                # Create mDNS service for each device
                service_name = f"{device.device_id}._http._tcp.local."
                service_info = ServiceInfo(
                    "_http._tcp.local.",
                    service_name,
                    addresses=[socket.inet_aton(device.ip_address)],
                    port=80,
                    properties={
                        "device_id": device.device_id.encode(),
                        "device_name": device.device_name.encode(),
                        "device_type": device.device_type.encode(),
                        "manufacturer": b"Espressif",
                        "firmware": device.firmware_version.encode(),
                        "mac": device.mac_address.encode()
                    }
                )
                
                self.zeroconf.register_service(service_info)
                logger.info(f"Registered mDNS service for {device.device_name}")
                
        except Exception as e:
            logger.error(f"Failed to setup device discovery: {e}")
    
    def run(self):
        """Start the ESP32 emulator"""
        logger.info("Starting ESP32 Device Emulator...")
        
        # Setup MQTT communication
        self.setup_mqtt_client()
        
        # Start sensor simulation
        self.start_sensor_simulation()
        
        # Setup device discovery
        self.setup_device_discovery()
        
        logger.info(f"ESP32 Emulator Dashboard: http://localhost:{self.port}")
        logger.info(f"API Endpoint: http://localhost:{self.port}/api/devices")
        logger.info("Emulated devices:")
        for device in self.devices.values():
            logger.info(f"  - {device.device_name} ({device.device_id}) at {device.ip_address}")
        
        # Start Flask app with SocketIO
        self.socketio.run(self.app, host='0.0.0.0', port=self.port, debug=False)

if __name__ == "__main__":
    emulator = ESP32DeviceEmulator(port=8090)
    emulator.run()
#!/usr/bin/env python3
"""
Add Emulated ESP32 Devices to Home Automation System
This script discovers emulated devices and adds them to the device service
"""

import requests
import json
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeviceRegistration:
    """Register emulated devices with the home automation system"""
    
    def __init__(self):
        self.emulator_url = "http://localhost:8090"
        self.discovery_url = "http://localhost:3005"
        self.device_service_url = "http://localhost:3002"
        self.user_service_url = "http://localhost:3001"
        
        # Get auth token (assuming admin user)
        self.auth_token = None
        self.user_id = None
        
    def authenticate(self):
        """Get authentication token"""
        try:
            # For demo purposes, we'll use a mock admin user
            # In real implementation, you'd get this from login
            logger.info("Using demo authentication for device registration")
            return True
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def get_emulated_devices(self):
        """Get list of emulated devices"""
        try:
            response = requests.get(f"{self.emulator_url}/api/devices")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get emulated devices: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error getting emulated devices: {e}")
            return []
    
    def create_locations(self):
        """Create locations for the devices"""
        locations = [
            {
                "name": "Living Room",
                "description": "Main living area with smart lighting",
                "floor": "Ground Floor"
            },
            {
                "name": "Kitchen", 
                "description": "Kitchen area with smart appliances",
                "floor": "Ground Floor"
            },
            {
                "name": "Bedroom",
                "description": "Master bedroom with climate sensors",
                "floor": "First Floor"
            },
            {
                "name": "Entry Hall",
                "description": "Main entrance with security sensors",
                "floor": "Ground Floor"
            }
        ]
        
        created_locations = {}
        for location in locations:
            try:
                response = requests.post(
                    f"{self.device_service_url}/api/locations",
                    json=location,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    location_data = response.json()
                    created_locations[location["name"]] = location_data["id"]
                    logger.info(f"Created location: {location['name']} (ID: {location_data['id']})")
                else:
                    logger.warning(f"Failed to create location {location['name']}: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Error creating location {location['name']}: {e}")
        
        return created_locations
    
    def create_device_types(self):
        """Create device types for the emulated devices"""
        device_types = [
            {
                "name": "Smart Light",
                "description": "WiFi-connected smart LED light with dimming",
                "icon": "💡",
                "capabilities": ["power", "brightness", "scheduling"]
            },
            {
                "name": "Smart Switch",
                "description": "WiFi-connected smart power switch",
                "icon": "🔌",
                "capabilities": ["power", "scheduling"]
            },
            {
                "name": "Temperature Sensor",
                "description": "Wireless temperature and humidity sensor",
                "icon": "🌡️",
                "capabilities": ["temperature", "humidity", "monitoring"]
            },
            {
                "name": "Motion Sensor",
                "description": "PIR motion detection sensor",
                "icon": "👁️",
                "capabilities": ["motion", "monitoring", "security"]
            },
            {
                "name": "Door Sensor",
                "description": "Magnetic door/window open/close sensor",
                "icon": "🚪",
                "capabilities": ["door_status", "monitoring", "security"]
            }
        ]
        
        created_types = {}
        for device_type in device_types:
            try:
                response = requests.post(
                    f"{self.device_service_url}/api/device-types",
                    json=device_type,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    type_data = response.json()
                    created_types[device_type["name"]] = type_data["id"]
                    logger.info(f"Created device type: {device_type['name']} (ID: {type_data['id']})")
                else:
                    logger.warning(f"Device type {device_type['name']} might already exist: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Error creating device type {device_type['name']}: {e}")
        
        return created_types
    
    def register_devices(self):
        """Register emulated devices with the device service"""
        # Get emulated devices
        devices = self.get_emulated_devices()
        if not devices:
            logger.error("No emulated devices found")
            return False
        
        # Create locations and device types
        locations = self.create_locations()
        device_types = self.create_device_types()
        
        # Location mapping for devices
        location_mapping = {
            "Living Room Smart Light": "Living Room",
            "Kitchen Smart Switch": "Kitchen", 
            "Bedroom Temperature Sensor": "Bedroom",
            "Entry Motion Detector": "Entry Hall",
            "Smart Door Sensor": "Entry Hall"
        }
        
        registered_devices = []
        
        for device in devices:
            try:
                # Get location and device type IDs
                location_name = location_mapping.get(device["device_name"], "Living Room")
                location_id = locations.get(location_name, 1)  # Default to first location
                device_type_id = device_types.get(device["device_type"], 1)  # Default to first type
                
                # Create device registration data
                device_data = {
                    "name": device["device_name"],
                    "device_id": device["device_id"],
                    "device_type_id": device_type_id,
                    "location_id": location_id,
                    "manufacturer": "Espressif",
                    "model": "ESP32-WROOM-32",
                    "firmware_version": device["firmware_version"],
                    "mac_address": device["mac_address"],
                    "ip_address": device["ip_address"],
                    "port": 80,
                    "protocol": "HTTP",
                    "is_online": device["is_online"],
                    "last_seen": device["last_seen"],
                    "capabilities": self.get_device_capabilities(device["device_type"]),
                    "settings": self.get_device_settings(device),
                    "discovery_method": "emulator"
                }
                
                # Register device
                response = requests.post(
                    f"{self.device_service_url}/api/devices",
                    json=device_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    registered_device = response.json()
                    registered_devices.append(registered_device)
                    logger.info(f"Registered device: {device['device_name']} (ID: {registered_device.get('id', 'unknown')})")
                else:
                    logger.error(f"Failed to register device {device['device_name']}: {response.status_code} - {response.text}")
                    
            except Exception as e:
                logger.error(f"Error registering device {device['device_name']}: {e}")
        
        logger.info(f"Successfully registered {len(registered_devices)} devices")
        return registered_devices
    
    def get_device_capabilities(self, device_type):
        """Get capabilities JSON for device type"""
        capabilities_map = {
            "Smart Light": ["power", "brightness", "scheduling"],
            "Smart Switch": ["power", "scheduling"],
            "Temperature Sensor": ["temperature", "humidity", "monitoring"],
            "Motion Sensor": ["motion", "monitoring", "security"],
            "Door Sensor": ["door_status", "monitoring", "security"]
        }
        return json.dumps(capabilities_map.get(device_type, ["basic"]))
    
    def get_device_settings(self, device):
        """Get device settings JSON"""
        settings = {
            "power_state": device.get("power_state", False),
            "brightness": device.get("brightness", 100),
            "temperature": device.get("temperature", 22.0),
            "humidity": device.get("humidity", 45.0),
            "motion_detected": device.get("motion_detected", False),
            "door_open": device.get("door_open", False),
            "battery_level": device.get("battery_level", 100),
            "signal_strength": device.get("signal_strength", -50),
            "supports_dimming": device.get("supports_dimming", False),
            "supports_color": device.get("supports_color", False)
        }
        return json.dumps(settings)
    
    def test_device_discovery(self):
        """Test discovery service integration"""
        try:
            logger.info("Testing discovery service integration...")
            
            # Trigger network scan
            response = requests.post(f"{self.discovery_url}/api/scan/network")
            if response.status_code == 200:
                scan_result = response.json()
                logger.info(f"Discovery scan completed: {scan_result['total_found']} devices found")
                
                # Show discovered devices
                for device in scan_result.get('devices', []):
                    if device['discovery_method'] == 'esp32_emulator':
                        logger.info(f"Discovered emulated device: {device['name']} ({device['type']}) at {device['ip']}")
                
                return True
            else:
                logger.error(f"Discovery scan failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error testing discovery: {e}")
            return False
    
    def run_full_integration(self):
        """Run complete device integration"""
        logger.info("Starting ESP32 Emulator Device Integration")
        logger.info("=" * 60)
        
        # Step 1: Check emulator availability
        logger.info("1. Checking ESP32 emulator availability...")
        devices = self.get_emulated_devices()
        if not devices:
            logger.error("❌ ESP32 emulator not available or no devices found")
            return False
        logger.info(f"✅ Found {len(devices)} emulated devices")
        
        # Step 2: Test discovery integration
        logger.info("\n2. Testing discovery service integration...")
        if self.test_device_discovery():
            logger.info("✅ Discovery service can find emulated devices")
        else:
            logger.warning("⚠️ Discovery service integration failed")
        
        # Step 3: Register devices
        logger.info("\n3. Registering devices with home automation system...")
        registered_devices = self.register_devices()
        if registered_devices:
            logger.info(f"✅ Successfully registered {len(registered_devices)} devices")
        else:
            logger.error("❌ Device registration failed")
            return False
        
        # Step 4: Verification
        logger.info("\n4. Verifying device registration...")
        try:
            response = requests.get(f"{self.device_service_url}/api/devices")
            if response.status_code == 200:
                all_devices = response.json()
                emulated_devices = [d for d in all_devices if d.get('discovery_method') == 'emulator']
                logger.info(f"✅ Found {len(emulated_devices)} emulated devices in system")
            else:
                logger.warning("⚠️ Could not verify device registration")
        except Exception as e:
            logger.warning(f"⚠️ Verification failed: {e}")
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 ESP32 Emulator Integration Complete!")
        logger.info("📱 You can now control these devices from your admin dashboard")
        logger.info("🌐 Emulator Dashboard: http://localhost:8090")
        logger.info("🏠 Admin Dashboard: http://localhost:3000/admin")
        
        return True

if __name__ == "__main__":
    registration = DeviceRegistration()
    registration.run_full_integration()
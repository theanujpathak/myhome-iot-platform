#!/usr/bin/env python3
"""
Discovery Integration for ESP32 Emulator
This script integrates the emulated devices with the discovery service
"""

import requests
import json
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DiscoveryIntegration:
    """Integrates emulated devices with the home automation discovery service"""
    
    def __init__(self):
        self.emulator_url = "http://localhost:8090"
        self.discovery_url = "http://localhost:3005"
        self.device_service_url = "http://localhost:3002"
        
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
    
    def register_devices_with_discovery(self):
        """Register emulated devices with the discovery service"""
        devices = self.get_emulated_devices()
        
        if not devices:
            logger.warning("No emulated devices found")
            return
        
        # Create discovery data format
        discovery_data = []
        for device in devices:
            discovery_device = {
                "ip": device["ip_address"],
                "mac": device["mac_address"],
                "device_id": device["device_id"],
                "device_name": device["device_name"],
                "device_type": device["device_type"],
                "manufacturer": "Espressif",
                "firmware_version": device["firmware_version"],
                "services": ["http", "mqtt"],
                "ports": [80, 1883],
                "discovery_method": "emulator",
                "online": device["is_online"],
                "signal_strength": device["signal_strength"],
                "battery_level": device["battery_level"]
            }
            discovery_data.append(discovery_device)
        
        logger.info(f"Registering {len(discovery_data)} emulated devices with discovery service")
        
        # You can add actual API calls to discovery service here
        # For now, we'll just log the data
        for device in discovery_data:
            logger.info(f"Discovered: {device['device_name']} ({device['device_id']}) at {device['ip']}")
        
        return discovery_data
    
    def create_device_locations(self):
        """Create locations for emulated devices"""
        locations = [
            {
                "name": "Living Room",
                "description": "Main living area with smart lighting"
            },
            {
                "name": "Kitchen", 
                "description": "Kitchen area with smart appliances"
            },
            {
                "name": "Bedroom",
                "description": "Master bedroom with climate sensors"
            },
            {
                "name": "Entry Hall",
                "description": "Main entrance with security sensors"
            }
        ]
        
        for location in locations:
            try:
                # This would normally make an API call to create locations
                logger.info(f"Would create location: {location['name']}")
            except Exception as e:
                logger.error(f"Error creating location {location['name']}: {e}")
    
    def pair_emulated_devices(self):
        """Pair emulated devices with the home automation system"""
        devices = self.get_emulated_devices()
        
        location_mapping = {
            "Living Room Smart Light": "Living Room",
            "Kitchen Smart Switch": "Kitchen", 
            "Bedroom Temperature Sensor": "Bedroom",
            "Entry Motion Detector": "Entry Hall",
            "Smart Door Sensor": "Entry Hall"
        }
        
        for device in devices:
            try:
                # Create pairing data
                pairing_data = {
                    "device_id": device["device_id"],
                    "device_name": device["device_name"],
                    "device_type": device["device_type"],
                    "location": location_mapping.get(device["device_name"], "Unknown"),
                    "manufacturer": "Espressif",
                    "firmware_version": device["firmware_version"],
                    "mac_address": device["mac_address"],
                    "ip_address": device["ip_address"],
                    "discovery_method": "emulator"
                }
                
                logger.info(f"Would pair device: {device['device_name']} ({device['device_id']})")
                # This would normally make an API call to pair the device
                
            except Exception as e:
                logger.error(f"Error pairing device {device['device_name']}: {e}")
    
    def test_device_control(self):
        """Test controlling emulated devices"""
        devices = self.get_emulated_devices()
        
        for device in devices:
            if device["device_type"] in ["Smart Light", "Smart Switch"]:
                try:
                    # Test turning device on
                    control_data = {"power_state": True}
                    response = requests.post(
                        f"{self.emulator_url}/api/devices/{device['device_id']}/control",
                        json=control_data
                    )
                    
                    if response.status_code == 200:
                        logger.info(f"Successfully controlled {device['device_name']}: Power ON")
                        
                        # Wait a bit then turn off
                        time.sleep(1)
                        control_data = {"power_state": False}
                        response = requests.post(
                            f"{self.emulator_url}/api/devices/{device['device_id']}/control",
                            json=control_data
                        )
                        
                        if response.status_code == 200:
                            logger.info(f"Successfully controlled {device['device_name']}: Power OFF")
                    
                except Exception as e:
                    logger.error(f"Error controlling device {device['device_name']}: {e}")
    
    def run_integration_test(self):
        """Run complete integration test"""
        logger.info("Starting ESP32 Emulator Integration Test")
        logger.info("=" * 50)
        
        # Step 1: Check emulator connection
        logger.info("1. Checking emulator connection...")
        devices = self.get_emulated_devices()
        if devices:
            logger.info(f"✅ Found {len(devices)} emulated devices")
        else:
            logger.error("❌ No emulated devices found")
            return
        
        # Step 2: Register with discovery
        logger.info("\n2. Registering devices with discovery service...")
        self.register_devices_with_discovery()
        
        # Step 3: Create locations
        logger.info("\n3. Creating device locations...")
        self.create_device_locations()
        
        # Step 4: Pair devices
        logger.info("\n4. Pairing devices with home automation system...")
        self.pair_emulated_devices()
        
        # Step 5: Test device control
        logger.info("\n5. Testing device control...")
        self.test_device_control()
        
        logger.info("\n" + "=" * 50)
        logger.info("✅ Integration test completed!")
        logger.info(f"🌐 Emulator Dashboard: http://localhost:8090")
        logger.info(f"📱 Device API: http://localhost:8090/api/devices")
        logger.info("Use the web dashboard to interact with the emulated devices!")

if __name__ == "__main__":
    integration = DiscoveryIntegration()
    integration.run_integration_test()
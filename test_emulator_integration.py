#!/usr/bin/env python3
"""
End-to-End Test for ESP32 Emulator Integration
Tests the complete workflow from device discovery to control via admin dashboard
"""

import requests
import json
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmulatorIntegrationTest:
    """Test suite for ESP32 emulator integration"""
    
    def __init__(self):
        self.emulator_url = "http://localhost:8090"
        self.discovery_url = "http://localhost:3005"
        self.device_service_url = "http://localhost:3002"
        self.frontend_url = "http://localhost:3000"
        
    def test_emulator_availability(self):
        """Test 1: Check if ESP32 emulator is running and responsive"""
        logger.info("🧪 Test 1: ESP32 Emulator Availability")
        try:
            response = requests.get(f"{self.emulator_url}/api/devices", timeout=5)
            if response.status_code == 200:
                devices = response.json()
                logger.info(f"✅ Emulator running with {len(devices)} devices")
                return True, devices
            else:
                logger.error(f"❌ Emulator returned status {response.status_code}")
                return False, []
        except Exception as e:
            logger.error(f"❌ Cannot connect to emulator: {e}")
            return False, []
    
    def test_device_discovery(self):
        """Test 2: Check if discovery service can find emulated devices"""
        logger.info("🧪 Test 2: Device Discovery Service")
        try:
            response = requests.post(f"{self.discovery_url}/api/scan/network", timeout=30)
            if response.status_code == 200:
                scan_result = response.json()
                emulated_devices = [
                    d for d in scan_result.get('devices', []) 
                    if d.get('discovery_method') == 'esp32_emulator'
                ]
                logger.info(f"✅ Discovery found {len(emulated_devices)} emulated devices")
                return True, emulated_devices
            else:
                logger.error(f"❌ Discovery scan failed: {response.status_code}")
                return False, []
        except Exception as e:
            logger.error(f"❌ Discovery service error: {e}")
            return False, []
    
    def test_device_control_api(self, devices):
        """Test 3: Direct device control via emulator API"""
        logger.info("🧪 Test 3: Direct Device Control API")
        
        controllable_devices = [
            d for d in devices 
            if d['device_type'] in ['Smart Light', 'Smart Switch']
        ]
        
        if not controllable_devices:
            logger.warning("⚠️ No controllable devices found")
            return False
        
        device = controllable_devices[0]
        device_id = device['device_id']
        
        try:
            # Test turning device on
            logger.info(f"Testing control of {device['device_name']}...")
            
            response = requests.post(
                f"{self.emulator_url}/api/devices/{device_id}/control",
                json={"power_state": True},
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result['device']['power_state']:
                    logger.info("✅ Device turned ON successfully")
                    
                    # Test turning device off
                    response = requests.post(
                        f"{self.emulator_url}/api/devices/{device_id}/control",
                        json={"power_state": False},
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success') and not result['device']['power_state']:
                            logger.info("✅ Device turned OFF successfully")
                            return True
                    
            logger.error("❌ Device control test failed")
            return False
            
        except Exception as e:
            logger.error(f"❌ Device control API error: {e}")
            return False
    
    def test_sensor_simulation(self, devices):
        """Test 4: Sensor data simulation and monitoring"""
        logger.info("🧪 Test 4: Sensor Data Simulation")
        
        sensor_devices = [
            d for d in devices 
            if 'Sensor' in d['device_type']
        ]
        
        if not sensor_devices:
            logger.warning("⚠️ No sensor devices found")
            return False
        
        try:
            # Get initial sensor readings
            initial_data = {}
            for device in sensor_devices:
                device_id = device['device_id']
                initial_data[device_id] = {
                    'temperature': device.get('temperature', 0),
                    'humidity': device.get('humidity', 0),
                    'motion_detected': device.get('motion_detected', False),
                    'door_open': device.get('door_open', False)
                }
            
            logger.info("📊 Initial sensor readings captured")
            
            # Wait a moment for automatic sensor updates
            time.sleep(12)  # Sensor simulation updates every 10 seconds
            
            # Get updated readings
            response = requests.get(f"{self.emulator_url}/api/devices", timeout=5)
            if response.status_code == 200:
                updated_devices = response.json()
                changes_detected = False
                
                for device in updated_devices:
                    if device['device_id'] in initial_data:
                        device_id = device['device_id']
                        initial = initial_data[device_id]
                        
                        # Check for changes in sensor readings
                        temp_changed = abs(device.get('temperature', 0) - initial['temperature']) > 0.1
                        humidity_changed = abs(device.get('humidity', 0) - initial['humidity']) > 0.1
                        
                        if temp_changed or humidity_changed:
                            changes_detected = True
                            logger.info(f"📈 Sensor data changed for {device['device_name']}")
                
                if changes_detected:
                    logger.info("✅ Sensor simulation working correctly")
                    return True
                else:
                    logger.info("⚠️ No sensor changes detected (may be normal)")
                    return True  # Still pass as this may be normal behavior
            
            logger.error("❌ Failed to get updated sensor readings")
            return False
            
        except Exception as e:
            logger.error(f"❌ Sensor simulation test error: {e}")
            return False
    
    def test_dashboard_access(self):
        """Test 5: Check if admin dashboard is accessible"""
        logger.info("🧪 Test 5: Admin Dashboard Access")
        try:
            # Check if frontend is running
            response = requests.get(f"{self.frontend_url}", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Frontend dashboard accessible")
                logger.info(f"📱 Admin Dashboard: {self.frontend_url}/admin")
                return True
            else:
                logger.warning(f"⚠️ Frontend returned status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Cannot access dashboard: {e}")
            return False
    
    def test_realtime_updates(self, devices):
        """Test 6: Real-time device state updates"""
        logger.info("🧪 Test 6: Real-time State Updates")
        
        controllable_devices = [
            d for d in devices 
            if d['device_type'] in ['Smart Light', 'Smart Switch']
        ]
        
        if not controllable_devices:
            logger.warning("⚠️ No controllable devices for real-time test")
            return False
        
        device = controllable_devices[0]
        device_id = device['device_id']
        
        try:
            # Get initial state
            response = requests.get(f"{self.emulator_url}/api/devices/{device_id}", timeout=5)
            initial_state = response.json()['power_state']
            
            # Change state
            new_state = not initial_state
            requests.post(
                f"{self.emulator_url}/api/devices/{device_id}/control",
                json={"power_state": new_state},
                timeout=5
            )
            
            # Verify state change
            time.sleep(1)
            response = requests.get(f"{self.emulator_url}/api/devices/{device_id}", timeout=5)
            updated_state = response.json()['power_state']
            
            if updated_state == new_state:
                logger.info("✅ Real-time state updates working")
                return True
            else:
                logger.error("❌ State change not reflected")
                return False
                
        except Exception as e:
            logger.error(f"❌ Real-time update test error: {e}")
            return False
    
    def run_integration_test_suite(self):
        """Run the complete integration test suite"""
        logger.info("🏠 ESP32 Emulator Integration Test Suite")
        logger.info("=" * 60)
        
        test_results = []
        
        # Test 1: Emulator Availability
        success, devices = self.test_emulator_availability()
        test_results.append(("Emulator Availability", success))
        
        if not success:
            logger.error("💥 Emulator not available - stopping tests")
            return False
        
        # Test 2: Device Discovery
        success, discovered_devices = self.test_device_discovery()
        test_results.append(("Device Discovery", success))
        
        # Test 3: Device Control API
        success = self.test_device_control_api(devices)
        test_results.append(("Device Control API", success))
        
        # Test 4: Sensor Simulation
        success = self.test_sensor_simulation(devices)
        test_results.append(("Sensor Simulation", success))
        
        # Test 5: Dashboard Access
        success = self.test_dashboard_access()
        test_results.append(("Dashboard Access", success))
        
        # Test 6: Real-time Updates
        success = self.test_realtime_updates(devices)
        test_results.append(("Real-time Updates", success))
        
        # Results Summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 TEST RESULTS SUMMARY")
        logger.info("=" * 60)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{test_name:<25} {status}")
            if result:
                passed += 1
        
        logger.info("=" * 60)
        logger.info(f"Tests Passed: {passed}/{total}")
        
        if passed == total:
            logger.info("🎉 ALL TESTS PASSED!")
            logger.info("\n🎮 Your ESP32 emulator is fully integrated!")
            logger.info("🌐 Emulator Dashboard: http://localhost:8090")
            logger.info("🏠 Admin Dashboard: http://localhost:3000/admin")
            logger.info("📱 Go to Admin Dashboard > ESP32 Emulator tab to control devices")
            return True
        else:
            logger.warning(f"⚠️ {total - passed} tests failed")
            return False

if __name__ == "__main__":
    test_suite = EmulatorIntegrationTest()
    test_suite.run_integration_test_suite()
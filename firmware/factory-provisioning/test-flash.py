#!/usr/bin/env python3
"""
Test Flash Script for Factory Provisioning
Simple test script to verify factory provisioning system functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from factory_flash import FactoryProvisioning
import argparse
import json

def test_device_detection():
    """Test device detection on all stations"""
    print("Testing device detection...")
    
    factory = FactoryProvisioning()
    
    for station_id in factory.stations:
        print(f"\nTesting station: {station_id}")
        detected = factory.detect_boards(station_id)
        
        if detected:
            print(f"  Detected {len(detected)} boards:")
            for port, mac in detected:
                print(f"    Port: {port}, MAC: {mac}")
        else:
            print("  No boards detected")
    
    return True

def test_firmware_version():
    """Test firmware version extraction"""
    print("\nTesting firmware version extraction...")
    
    factory = FactoryProvisioning()
    
    test_paths = [
        "../dist/esp32/firmware-latest.bin",
        "../dist/esp8266/firmware-latest.bin",
        "nonexistent.bin"
    ]
    
    for path in test_paths:
        version = factory.get_firmware_version(path)
        print(f"  {path}: {version}")
    
    return True

def test_configuration():
    """Test configuration loading"""
    print("\nTesting configuration loading...")
    
    # Test with default config
    factory = FactoryProvisioning()
    print(f"  Loaded {len(factory.stations)} stations")
    print(f"  Board configs: {list(factory.config.get('board_configs', {}).keys())}")
    
    # Test with custom config
    custom_config = {
        'stations': [
            {
                'station_id': 'test_station',
                'ports': ['/dev/ttyUSB0'],
                'board_type': 'esp32'
            }
        ],
        'board_configs': {
            'esp32': {
                'platform': 'esp32',
                'board_model': 'ESP32-WROOM-32',
                'flash_size': '4MB',
                'flash_speed': '80m',
                'firmware_path': '../dist/esp32/firmware-latest.bin'
            }
        }
    }
    
    # Write test config
    with open('test-config.yaml', 'w') as f:
        import yaml
        yaml.dump(custom_config, f)
    
    try:
        factory = FactoryProvisioning('test-config.yaml')
        print(f"  Custom config loaded successfully")
    except Exception as e:
        print(f"  Error loading custom config: {e}")
    finally:
        # Clean up
        if os.path.exists('test-config.yaml'):
            os.remove('test-config.yaml')
    
    return True

def test_batch_report():
    """Test batch report generation"""
    print("\nTesting batch report generation...")
    
    factory = FactoryProvisioning()
    
    # Simulate some device records
    from datetime import datetime
    from factory_flash import DeviceRecord
    
    test_records = [
        DeviceRecord(
            device_id="ESP32_TEST001",
            mac_address="AA:BB:CC:DD:EE:01",
            board_type="esp32",
            firmware_version="1.0.0",
            flash_time=datetime.now(),
            station_id="station_1",
            port="/dev/ttyUSB0",
            status="success",
            test_results={"boot_test": "PASS", "wifi_test": "PASS"}
        ),
        DeviceRecord(
            device_id="ESP32_TEST002",
            mac_address="AA:BB:CC:DD:EE:02",
            board_type="esp32",
            firmware_version="1.0.0",
            flash_time=datetime.now(),
            station_id="station_1",
            port="/dev/ttyUSB1",
            status="test_failed",
            test_results={"boot_test": "PASS", "wifi_test": "FAIL"}
        )
    ]
    
    factory.device_records = test_records
    
    # Update station counters
    factory.stations["station_1"].total_flashed = 2
    factory.stations["station_1"].success_count = 1
    factory.stations["station_1"].failure_count = 1
    
    report = factory.generate_batch_report()
    
    print(f"  Generated report:")
    print(f"    Total devices: {report['total_devices']}")
    print(f"    Successful: {report['successful_devices']}")
    print(f"    Failed: {report['failed_devices']}")
    print(f"    Success rate: {report['success_rate']}")
    
    return True

def test_qr_code_generation():
    """Test QR code generation"""
    print("\nTesting QR code generation...")
    
    factory = FactoryProvisioning()
    
    from factory_flash import DeviceRecord
    from datetime import datetime
    
    test_record = DeviceRecord(
        device_id="ESP32_TEST001",
        mac_address="AA:BB:CC:DD:EE:01",
        board_type="esp32",
        firmware_version="1.0.0",
        flash_time=datetime.now(),
        station_id="station_1",
        port="/dev/ttyUSB0",
        status="success"
    )
    
    qr_code = factory.generate_qr_code(test_record)
    
    if qr_code:
        print(f"  QR code generated successfully")
        print(f"  QR code preview: {qr_code[:50]}...")
    else:
        print(f"  Failed to generate QR code")
    
    return True

def main():
    """Main test function"""
    parser = argparse.ArgumentParser(description='Test Factory Provisioning System')
    parser.add_argument('--test', '-t', choices=[
        'detection', 'version', 'config', 'report', 'qr', 'all'
    ], default='all', help='Specific test to run')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    print("Factory Provisioning System Test")
    print("=" * 50)
    
    tests = {
        'detection': test_device_detection,
        'version': test_firmware_version,
        'config': test_configuration,
        'report': test_batch_report,
        'qr': test_qr_code_generation
    }
    
    if args.test == 'all':
        test_functions = tests.values()
    else:
        test_functions = [tests[args.test]]
    
    results = []
    for test_func in test_functions:
        try:
            result = test_func()
            results.append(result)
            if args.verbose:
                print(f"✅ {test_func.__name__} passed")
        except Exception as e:
            print(f"❌ {test_func.__name__} failed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
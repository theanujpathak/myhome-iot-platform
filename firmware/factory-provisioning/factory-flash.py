#!/usr/bin/env python3
"""
Factory Provisioning System for Fresh Boards
Automates the process of flashing firmware to new boards in production
"""

import os
import sys
import json
import time
import serial
import logging
import argparse
import subprocess
import threading
import queue
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import requests
import yaml
import csv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('factory-provisioning.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class BoardConfig:
    """Configuration for a board type"""
    platform: str
    board_model: str
    flash_size: str
    flash_speed: str
    firmware_path: str
    bootloader_path: Optional[str] = None
    partition_table_path: Optional[str] = None
    default_baudrate: int = 115200
    flash_baudrate: int = 921600
    reset_method: str = "hard_reset"
    
@dataclass
class FlashingStation:
    """Represents a flashing station with multiple ports"""
    station_id: str
    ports: List[str]
    board_type: str
    status: str = "idle"
    current_batch: Optional[str] = None
    total_flashed: int = 0
    success_count: int = 0
    failure_count: int = 0

@dataclass
class DeviceRecord:
    """Record of a flashed device"""
    device_id: str
    mac_address: str
    board_type: str
    firmware_version: str
    flash_time: datetime
    station_id: str
    port: str
    status: str
    test_results: Dict = None
    qr_code: Optional[str] = None

class FactoryProvisioning:
    """Main factory provisioning system"""
    
    def __init__(self, config_file: str = "factory-config.yaml"):
        self.config = self.load_config(config_file)
        self.stations = {}
        self.device_records = []
        self.batch_queue = queue.Queue()
        self.provisioning_service_url = self.config.get('provisioning_service_url', 'http://localhost:3002')
        self.ota_service_url = self.config.get('ota_service_url', 'http://localhost:3004')
        self.current_batch = None
        self.initialize_stations()
        
    def load_config(self, config_file: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
                logger.info(f"Configuration loaded from {config_file}")
                return config
        except FileNotFoundError:
            logger.error(f"Configuration file {config_file} not found")
            # Return default configuration
            return {
                'stations': [
                    {
                        'station_id': 'station_1',
                        'ports': ['/dev/ttyUSB0', '/dev/ttyUSB1'],
                        'board_type': 'esp32'
                    }
                ],
                'board_configs': {
                    'esp32': {
                        'platform': 'esp32',
                        'board_model': 'ESP32-WROOM-32',
                        'flash_size': '4MB',
                        'flash_speed': '80m',
                        'firmware_path': '../dist/esp32/firmware-latest.bin',
                        'bootloader_path': '../dist/esp32/bootloader.bin',
                        'partition_table_path': '../dist/esp32/partitions.bin'
                    }
                }
            }
    
    def initialize_stations(self):
        """Initialize flashing stations"""
        for station_config in self.config['stations']:
            station = FlashingStation(
                station_id=station_config['station_id'],
                ports=station_config['ports'],
                board_type=station_config['board_type']
            )
            self.stations[station.station_id] = station
            logger.info(f"Initialized station {station.station_id} with {len(station.ports)} ports")
    
    def detect_boards(self, station_id: str) -> List[Tuple[str, str]]:
        """Detect boards connected to a station"""
        station = self.stations[station_id]
        detected_boards = []
        
        for port in station.ports:
            try:
                # Try to connect to the port
                ser = serial.Serial(port, 115200, timeout=1)
                ser.close()
                
                # Get board info using esptool
                result = subprocess.run([
                    'python', '-m', 'esptool',
                    '--port', port,
                    '--baud', '115200',
                    'flash_id'
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    # Extract MAC address from output
                    mac_address = self.extract_mac_from_output(result.stdout)
                    detected_boards.append((port, mac_address))
                    logger.info(f"Detected board on {port} with MAC: {mac_address}")
                
            except Exception as e:
                logger.debug(f"No board detected on {port}: {e}")
        
        return detected_boards
    
    def extract_mac_from_output(self, output: str) -> str:
        """Extract MAC address from esptool output"""
        for line in output.split('\n'):
            if 'MAC:' in line:
                mac = line.split('MAC:')[1].strip()
                return mac.replace(':', '')
        return f"MAC_{int(time.time())}"  # Fallback
    
    def flash_board(self, port: str, board_config: BoardConfig, device_id: str) -> bool:
        """Flash firmware to a single board"""
        try:
            logger.info(f"Starting flash process for device {device_id} on {port}")
            
            # Prepare esptool command
            cmd = [
                'python', '-m', 'esptool',
                '--chip', board_config.platform,
                '--port', port,
                '--baud', str(board_config.flash_baudrate),
                '--before', 'default_reset',
                '--after', 'hard_reset',
                'write_flash',
                '--flash_mode', 'dio',
                '--flash_freq', board_config.flash_speed,
                '--flash_size', board_config.flash_size
            ]
            
            # Add firmware address and file
            if board_config.platform == 'esp32':
                if board_config.bootloader_path:
                    cmd.extend(['0x1000', board_config.bootloader_path])
                if board_config.partition_table_path:
                    cmd.extend(['0x8000', board_config.partition_table_path])
                cmd.extend(['0x10000', board_config.firmware_path])
            else:
                cmd.extend(['0x0', board_config.firmware_path])
            
            # Execute flashing
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Successfully flashed device {device_id} on {port}")
                return True
            else:
                logger.error(f"Failed to flash device {device_id} on {port}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Exception during flashing {device_id} on {port}: {e}")
            return False
    
    def test_board(self, port: str, device_id: str) -> Dict:
        """Test a freshly flashed board"""
        test_results = {
            'device_id': device_id,
            'port': port,
            'timestamp': datetime.now().isoformat(),
            'tests': {}
        }
        
        try:
            # Connect to board
            ser = serial.Serial(port, 115200, timeout=5)
            time.sleep(2)  # Wait for boot
            
            # Send test commands
            tests = [
                ('boot_test', 'info'),
                ('wifi_test', 'wifi_scan'),
                ('memory_test', 'memory_info'),
                ('sensor_test', 'sensor_check')
            ]
            
            for test_name, command in tests:
                try:
                    ser.write(f"{command}\n".encode())
                    time.sleep(1)
                    
                    response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                    
                    # Simple test evaluation
                    if 'OK' in response or 'SUCCESS' in response:
                        test_results['tests'][test_name] = 'PASS'
                    else:
                        test_results['tests'][test_name] = 'FAIL'
                        
                except Exception as e:
                    test_results['tests'][test_name] = f'ERROR: {str(e)}'
            
            ser.close()
            
        except Exception as e:
            logger.error(f"Testing failed for device {device_id}: {e}")
            test_results['tests']['connection'] = f'ERROR: {str(e)}'
        
        # Calculate overall result
        passed_tests = sum(1 for result in test_results['tests'].values() if result == 'PASS')
        total_tests = len(test_results['tests'])
        test_results['overall'] = 'PASS' if passed_tests == total_tests else 'FAIL'
        test_results['pass_rate'] = f"{passed_tests}/{total_tests}"
        
        return test_results
    
    def register_device(self, device_record: DeviceRecord) -> bool:
        """Register device with provisioning service"""
        try:
            # Register with provisioning service
            provisioning_data = {
                'device_name': f"{device_record.board_type}_{device_record.device_id}",
                'device_type': device_record.board_type.upper(),
                'device_model': self.config['board_configs'][device_record.board_type]['board_model'],
                'mac_address': device_record.mac_address,
                'manufacturer': 'Factory',
                'firmware_version': device_record.firmware_version,
                'description': f'Factory provisioned {device_record.board_type} device'
            }
            
            response = requests.post(
                f"{self.provisioning_service_url}/api/admin/device-registrations",
                json=provisioning_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 201:
                logger.info(f"Successfully registered device {device_record.device_id}")
                return True
            else:
                logger.error(f"Failed to register device {device_record.device_id}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Exception registering device {device_record.device_id}: {e}")
            return False
    
    def generate_qr_code(self, device_record: DeviceRecord) -> Optional[str]:
        """Generate QR code for device provisioning"""
        try:
            qr_data = {
                'device_id': device_record.device_id,
                'mac_address': device_record.mac_address,
                'board_type': device_record.board_type,
                'firmware_version': device_record.firmware_version,
                'provisioning_url': f"{self.provisioning_service_url}/provision/{device_record.device_id}"
            }
            
            # Generate QR code (this would use a QR code library)
            qr_code_data = f"PROVISION:{json.dumps(qr_data)}"
            
            # For now, return the data string
            return qr_code_data
            
        except Exception as e:
            logger.error(f"Failed to generate QR code for {device_record.device_id}: {e}")
            return None
    
    def process_station(self, station_id: str, batch_size: int = 10):
        """Process a single flashing station"""
        station = self.stations[station_id]
        board_config = BoardConfig(**self.config['board_configs'][station.board_type])
        
        logger.info(f"Starting processing for station {station_id}")
        station.status = "active"
        
        batch_count = 0
        while batch_count < batch_size:
            # Detect boards
            detected_boards = self.detect_boards(station_id)
            
            if not detected_boards:
                logger.info(f"No boards detected on station {station_id}, waiting...")
                time.sleep(5)
                continue
            
            # Process each detected board
            for port, mac_address in detected_boards:
                if batch_count >= batch_size:
                    break
                
                device_id = f"{station.board_type}_{mac_address}_{int(time.time())}"
                
                logger.info(f"Processing device {device_id} on port {port}")
                
                # Flash the board
                flash_success = self.flash_board(port, board_config, device_id)
                
                if flash_success:
                    station.success_count += 1
                    
                    # Wait for device to boot
                    time.sleep(3)
                    
                    # Test the board
                    test_results = self.test_board(port, device_id)
                    
                    # Create device record
                    device_record = DeviceRecord(
                        device_id=device_id,
                        mac_address=mac_address,
                        board_type=station.board_type,
                        firmware_version=self.get_firmware_version(board_config.firmware_path),
                        flash_time=datetime.now(),
                        station_id=station_id,
                        port=port,
                        status='success' if test_results['overall'] == 'PASS' else 'test_failed',
                        test_results=test_results
                    )
                    
                    # Generate QR code
                    device_record.qr_code = self.generate_qr_code(device_record)
                    
                    # Register device
                    if device_record.status == 'success':
                        registration_success = self.register_device(device_record)
                        if not registration_success:
                            device_record.status = 'registration_failed'
                    
                    # Save device record
                    self.device_records.append(device_record)
                    self.save_device_record(device_record)
                    
                    logger.info(f"Completed processing device {device_id} - Status: {device_record.status}")
                    
                else:
                    station.failure_count += 1
                    logger.error(f"Failed to flash device {device_id}")
                
                station.total_flashed += 1
                batch_count += 1
                
                # Remove the board (signal to operator)
                print(f"✅ Device {device_id} completed. Please remove from {port}")
                
                # Wait for board removal
                self.wait_for_board_removal(port)
        
        station.status = "idle"
        logger.info(f"Completed batch processing for station {station_id}")
    
    def wait_for_board_removal(self, port: str, timeout: int = 30):
        """Wait for board to be removed from port"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                ser = serial.Serial(port, 115200, timeout=1)
                ser.close()
                # Board still connected
                time.sleep(1)
            except:
                # Board disconnected
                logger.info(f"Board removed from {port}")
                return
        
        logger.warning(f"Board still connected to {port} after {timeout} seconds")
    
    def get_firmware_version(self, firmware_path: str) -> str:
        """Extract firmware version from path or metadata"""
        try:
            metadata_path = f"{firmware_path}.metadata.json"
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    return metadata.get('version', '1.0.0')
        except:
            pass
        
        # Fallback to extracting from filename
        filename = os.path.basename(firmware_path)
        if 'latest' in filename:
            return f"latest-{int(time.time())}"
        
        return "1.0.0"
    
    def save_device_record(self, device_record: DeviceRecord):
        """Save device record to CSV file"""
        csv_file = f"factory_records_{datetime.now().strftime('%Y%m%d')}.csv"
        
        # Check if file exists to determine if we need headers
        file_exists = os.path.exists(csv_file)
        
        with open(csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            
            if not file_exists:
                # Write headers
                writer.writerow([
                    'Device ID', 'MAC Address', 'Board Type', 'Firmware Version',
                    'Flash Time', 'Station ID', 'Port', 'Status', 'Test Results', 'QR Code'
                ])
            
            # Write device record
            writer.writerow([
                device_record.device_id,
                device_record.mac_address,
                device_record.board_type,
                device_record.firmware_version,
                device_record.flash_time.isoformat(),
                device_record.station_id,
                device_record.port,
                device_record.status,
                json.dumps(device_record.test_results) if device_record.test_results else '',
                device_record.qr_code or ''
            ])
    
    def run_batch_processing(self, batch_size: int = 50):
        """Run batch processing across all stations"""
        logger.info(f"Starting batch processing with size {batch_size}")
        
        threads = []
        
        # Calculate batch size per station
        stations_count = len(self.stations)
        batch_per_station = max(1, batch_size // stations_count)
        
        # Start processing threads for each station
        for station_id in self.stations:
            thread = threading.Thread(
                target=self.process_station,
                args=(station_id, batch_per_station)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Generate batch report
        self.generate_batch_report()
    
    def generate_batch_report(self):
        """Generate batch processing report"""
        total_devices = len(self.device_records)
        successful_devices = sum(1 for record in self.device_records if record.status == 'success')
        failed_devices = total_devices - successful_devices
        
        report = {
            'batch_date': datetime.now().isoformat(),
            'total_devices': total_devices,
            'successful_devices': successful_devices,
            'failed_devices': failed_devices,
            'success_rate': f"{(successful_devices / total_devices * 100):.1f}%" if total_devices > 0 else "0%",
            'stations': {}
        }
        
        # Add station statistics
        for station_id, station in self.stations.items():
            report['stations'][station_id] = {
                'total_flashed': station.total_flashed,
                'success_count': station.success_count,
                'failure_count': station.failure_count,
                'success_rate': f"{(station.success_count / station.total_flashed * 100):.1f}%" if station.total_flashed > 0 else "0%"
            }
        
        # Save report
        report_file = f"batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Batch report saved to {report_file}")
        logger.info(f"Batch completed: {successful_devices}/{total_devices} devices successful")
        
        return report

def main():
    parser = argparse.ArgumentParser(description='Factory Provisioning System')
    parser.add_argument('--config', '-c', default='factory-config.yaml', help='Configuration file')
    parser.add_argument('--batch-size', '-b', type=int, default=50, help='Batch size for processing')
    parser.add_argument('--station', '-s', help='Process specific station only')
    parser.add_argument('--test-mode', '-t', action='store_true', help='Run in test mode')
    
    args = parser.parse_args()
    
    # Initialize factory provisioning system
    factory = FactoryProvisioning(args.config)
    
    if args.test_mode:
        logger.info("Running in test mode - no actual flashing")
        # Run tests without actual flashing
        for station_id in factory.stations:
            boards = factory.detect_boards(station_id)
            logger.info(f"Station {station_id}: Detected {len(boards)} boards")
        return
    
    if args.station:
        # Process specific station
        if args.station in factory.stations:
            factory.process_station(args.station, args.batch_size)
        else:
            logger.error(f"Station {args.station} not found")
            return
    else:
        # Process all stations
        factory.run_batch_processing(args.batch_size)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Batch Firmware Flashing Manager
Advanced system for managing batch firmware updates across multiple devices
"""

import os
import sys
import json
import time
import yaml
import threading
import asyncio
import logging
import hashlib
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import subprocess
import requests
import queue
from pathlib import Path
import socket
import serial
import concurrent.futures

class FlashStatus(Enum):
    """Flash operation status"""
    PENDING = "pending"
    PREPARING = "preparing"
    FLASHING = "flashing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class DeviceType(Enum):
    """Supported device types"""
    ESP32 = "esp32"
    ESP8266 = "esp8266"
    ARDUINO = "arduino"
    STM32 = "stm32"
    PICO = "pico"

@dataclass
class FlashTarget:
    """Target device for flashing"""
    device_id: str
    device_type: DeviceType
    connection_info: Dict[str, Any]  # port, ip, etc.
    current_firmware: Optional[str] = None
    target_firmware: Optional[str] = None
    priority: int = 1
    retry_count: int = 0
    max_retries: int = 3
    status: FlashStatus = FlashStatus.PENDING
    error_message: Optional[str] = None
    flash_start_time: Optional[datetime] = None
    flash_end_time: Optional[datetime] = None
    verification_result: Optional[bool] = None
    backup_created: bool = False
    rollback_available: bool = False

@dataclass
class FirmwarePackage:
    """Firmware package information"""
    firmware_id: str
    version: str
    device_type: DeviceType
    file_path: str
    checksum: str
    size: int
    build_date: datetime
    changelog: str
    compatibility: Dict[str, Any]
    security_signature: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FlashBatch:
    """Batch flashing operation"""
    batch_id: str
    name: str
    description: str
    firmware_package: FirmwarePackage
    targets: List[FlashTarget]
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "created"
    progress: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    cancelled_count: int = 0
    total_count: int = 0
    strategy: str = "parallel"  # parallel, sequential, gradual
    max_concurrent: int = 10
    timeout: int = 300  # seconds
    rollback_on_failure: bool = False
    pre_flash_commands: List[str] = field(default_factory=list)
    post_flash_commands: List[str] = field(default_factory=list)

class DeviceInterface:
    """Abstract interface for device communication"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def connect(self) -> bool:
        """Connect to device"""
        raise NotImplementedError
    
    def disconnect(self):
        """Disconnect from device"""
        raise NotImplementedError
    
    def flash_firmware(self, firmware_path: str, target: FlashTarget) -> bool:
        """Flash firmware to device"""
        raise NotImplementedError
    
    def verify_firmware(self, target: FlashTarget) -> bool:
        """Verify flashed firmware"""
        raise NotImplementedError
    
    def backup_firmware(self, target: FlashTarget) -> bool:
        """Create firmware backup"""
        raise NotImplementedError
    
    def rollback_firmware(self, target: FlashTarget) -> bool:
        """Rollback to previous firmware"""
        raise NotImplementedError

class SerialDeviceInterface(DeviceInterface):
    """Serial interface for devices like ESP32, ESP8266"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.connection = None
        self.port = None
        self.baudrate = config.get('baudrate', 115200)
        self.flash_baudrate = config.get('flash_baudrate', 921600)
    
    def connect(self, port: str) -> bool:
        """Connect to serial device"""
        try:
            self.port = port
            self.connection = serial.Serial(port, self.baudrate, timeout=10)
            time.sleep(2)  # Wait for device initialization
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to {port}: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from serial device"""
        if self.connection and self.connection.is_open:
            self.connection.close()
            self.connection = None
    
    def flash_firmware(self, firmware_path: str, target: FlashTarget) -> bool:
        """Flash firmware using esptool"""
        try:
            port = target.connection_info.get('port')
            if not port:
                raise ValueError("No port specified for target")
            
            device_type = target.device_type.value
            
            # Build esptool command based on device type
            if device_type == "esp32":
                cmd = [
                    "python", "-m", "esptool",
                    "--chip", "esp32",
                    "--port", port,
                    "--baud", str(self.flash_baudrate),
                    "--before", "default_reset",
                    "--after", "hard_reset",
                    "write_flash",
                    "--flash_mode", "dio",
                    "--flash_freq", "80m",
                    "--flash_size", "4MB",
                    "0x10000", firmware_path
                ]
            elif device_type == "esp8266":
                cmd = [
                    "python", "-m", "esptool",
                    "--chip", "esp8266",
                    "--port", port,
                    "--baud", str(self.flash_baudrate),
                    "write_flash",
                    "--flash_size", "4MB",
                    "0x0", firmware_path
                ]
            else:
                raise ValueError(f"Unsupported device type: {device_type}")
            
            self.logger.info(f"Flashing {target.device_id} on {port}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                self.logger.info(f"Successfully flashed {target.device_id}")
                return True
            else:
                self.logger.error(f"Flash failed for {target.device_id}: {result.stderr}")
                target.error_message = result.stderr
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Flash timeout for {target.device_id}")
            target.error_message = "Flash operation timed out"
            return False
        except Exception as e:
            self.logger.error(f"Flash error for {target.device_id}: {e}")
            target.error_message = str(e)
            return False
    
    def verify_firmware(self, target: FlashTarget) -> bool:
        """Verify flashed firmware"""
        try:
            port = target.connection_info.get('port')
            if not self.connect(port):
                return False
            
            # Send verification command
            self.connection.write(b"verify_firmware\n")
            time.sleep(2)
            
            response = self.connection.read(self.connection.in_waiting)
            response_str = response.decode('utf-8', errors='ignore')
            
            self.disconnect()
            
            # Check for success indicators
            if "FIRMWARE_OK" in response_str or "VERIFIED" in response_str:
                return True
            else:
                target.error_message = f"Verification failed: {response_str}"
                return False
                
        except Exception as e:
            self.logger.error(f"Verification error for {target.device_id}: {e}")
            target.error_message = str(e)
            return False
    
    def backup_firmware(self, target: FlashTarget) -> bool:
        """Create firmware backup"""
        try:
            port = target.connection_info.get('port')
            backup_path = f"backup_{target.device_id}_{int(time.time())}.bin"
            
            device_type = target.device_type.value
            
            if device_type == "esp32":
                cmd = [
                    "python", "-m", "esptool",
                    "--chip", "esp32",
                    "--port", port,
                    "read_flash",
                    "0x10000", "0x300000",
                    backup_path
                ]
            elif device_type == "esp8266":
                cmd = [
                    "python", "-m", "esptool",
                    "--chip", "esp8266",
                    "--port", port,
                    "read_flash",
                    "0x0", "0x400000",
                    backup_path
                ]
            else:
                return False
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                target.connection_info['backup_path'] = backup_path
                self.logger.info(f"Backup created for {target.device_id}: {backup_path}")
                return True
            else:
                self.logger.error(f"Backup failed for {target.device_id}: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Backup error for {target.device_id}: {e}")
            return False
    
    def rollback_firmware(self, target: FlashTarget) -> bool:
        """Rollback to previous firmware"""
        try:
            backup_path = target.connection_info.get('backup_path')
            if not backup_path or not os.path.exists(backup_path):
                target.error_message = "No backup available for rollback"
                return False
            
            # Use the backup as firmware to flash back
            return self.flash_firmware(backup_path, target)
            
        except Exception as e:
            self.logger.error(f"Rollback error for {target.device_id}: {e}")
            target.error_message = str(e)
            return False

class NetworkDeviceInterface(DeviceInterface):
    """Network interface for OTA updates"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.timeout = config.get('timeout', 30)
    
    def connect(self, host: str, port: int = 80) -> bool:
        """Test network connectivity"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception as e:
            self.logger.error(f"Network connection failed: {e}")
            return False
    
    def flash_firmware(self, firmware_path: str, target: FlashTarget) -> bool:
        """Flash firmware via OTA"""
        try:
            host = target.connection_info.get('host')
            port = target.connection_info.get('port', 80)
            
            if not self.connect(host, port):
                target.error_message = f"Cannot connect to {host}:{port}"
                return False
            
            # Upload firmware via HTTP POST
            ota_url = f"http://{host}:{port}/update"
            
            with open(firmware_path, 'rb') as f:
                files = {'firmware': f}
                response = requests.post(ota_url, files=files, timeout=120)
            
            if response.status_code == 200:
                self.logger.info(f"OTA update successful for {target.device_id}")
                return True
            else:
                target.error_message = f"OTA update failed: {response.text}"
                return False
                
        except Exception as e:
            self.logger.error(f"OTA update error for {target.device_id}: {e}")
            target.error_message = str(e)
            return False
    
    def verify_firmware(self, target: FlashTarget) -> bool:
        """Verify firmware via network"""
        try:
            host = target.connection_info.get('host')
            port = target.connection_info.get('port', 80)
            
            # Get firmware info via HTTP
            info_url = f"http://{host}:{port}/info"
            response = requests.get(info_url, timeout=10)
            
            if response.status_code == 200:
                info = response.json()
                current_version = info.get('firmware_version')
                expected_version = target.firmware_package.version
                
                if current_version == expected_version:
                    return True
                else:
                    target.error_message = f"Version mismatch: expected {expected_version}, got {current_version}"
                    return False
            else:
                target.error_message = f"Cannot get firmware info: {response.text}"
                return False
                
        except Exception as e:
            self.logger.error(f"Network verification error for {target.device_id}: {e}")
            target.error_message = str(e)
            return False
    
    def backup_firmware(self, target: FlashTarget) -> bool:
        """Network devices typically don't support backup"""
        return True  # Skip backup for network devices
    
    def rollback_firmware(self, target: FlashTarget) -> bool:
        """Rollback firmware via network"""
        try:
            host = target.connection_info.get('host')
            port = target.connection_info.get('port', 80)
            
            rollback_url = f"http://{host}:{port}/rollback"
            response = requests.post(rollback_url, timeout=30)
            
            if response.status_code == 200:
                self.logger.info(f"Rollback successful for {target.device_id}")
                return True
            else:
                target.error_message = f"Rollback failed: {response.text}"
                return False
                
        except Exception as e:
            self.logger.error(f"Rollback error for {target.device_id}: {e}")
            target.error_message = str(e)
            return False

class BatchFlashManager:
    """Main batch flashing manager"""
    
    def __init__(self, config_file: str = "batch-flash-config.yaml"):
        self.config = self.load_config(config_file)
        self.batches: Dict[str, FlashBatch] = {}
        self.interfaces: Dict[str, DeviceInterface] = {}
        self.active_operations: Dict[str, threading.Thread] = {}
        self.operation_queue = queue.Queue()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
        
        # Setup logging
        self.setup_logging()
        
        # Initialize interfaces
        self.initialize_interfaces()
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('batch-flash.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_config(self, config_file: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
                self.logger.info(f"Configuration loaded from {config_file}")
                return config
        except FileNotFoundError:
            self.logger.warning(f"Config file {config_file} not found, using defaults")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            "interfaces": {
                "serial": {
                    "type": "serial",
                    "baudrate": 115200,
                    "flash_baudrate": 921600,
                    "timeout": 30
                },
                "network": {
                    "type": "network",
                    "timeout": 30,
                    "port": 80
                }
            },
            "flash_settings": {
                "max_concurrent": 10,
                "timeout": 300,
                "max_retries": 3,
                "retry_delay": 5,
                "verify_after_flash": True,
                "backup_before_flash": True
            },
            "quality_gates": {
                "min_success_rate": 80,
                "max_failure_rate": 20,
                "require_verification": True
            }
        }
    
    def initialize_interfaces(self):
        """Initialize device interfaces"""
        for name, config in self.config.get("interfaces", {}).items():
            if config["type"] == "serial":
                self.interfaces[name] = SerialDeviceInterface(config)
            elif config["type"] == "network":
                self.interfaces[name] = NetworkDeviceInterface(config)
    
    def create_firmware_package(self, firmware_path: str, device_type: str, 
                              version: str, metadata: Dict = None) -> FirmwarePackage:
        """Create firmware package from file"""
        if not os.path.exists(firmware_path):
            raise FileNotFoundError(f"Firmware file not found: {firmware_path}")
        
        # Calculate checksum
        with open(firmware_path, 'rb') as f:
            content = f.read()
            checksum = hashlib.sha256(content).hexdigest()
        
        # Get file size
        size = os.path.getsize(firmware_path)
        
        # Create package
        package = FirmwarePackage(
            firmware_id=f"{device_type}_{version}_{checksum[:8]}",
            version=version,
            device_type=DeviceType(device_type),
            file_path=firmware_path,
            checksum=checksum,
            size=size,
            build_date=datetime.now(),
            changelog=metadata.get('changelog', '') if metadata else '',
            compatibility=metadata.get('compatibility', {}) if metadata else {},
            metadata=metadata or {}
        )
        
        self.logger.info(f"Created firmware package: {package.firmware_id}")
        return package
    
    def create_flash_batch(self, name: str, firmware_package: FirmwarePackage,
                          targets: List[FlashTarget], **kwargs) -> FlashBatch:
        """Create new flash batch"""
        batch_id = f"batch_{int(time.time())}_{len(self.batches)}"
        
        batch = FlashBatch(
            batch_id=batch_id,
            name=name,
            description=kwargs.get('description', ''),
            firmware_package=firmware_package,
            targets=targets,
            created_at=datetime.now(),
            total_count=len(targets),
            strategy=kwargs.get('strategy', 'parallel'),
            max_concurrent=kwargs.get('max_concurrent', 10),
            timeout=kwargs.get('timeout', 300),
            rollback_on_failure=kwargs.get('rollback_on_failure', False),
            pre_flash_commands=kwargs.get('pre_flash_commands', []),
            post_flash_commands=kwargs.get('post_flash_commands', [])
        )
        
        self.batches[batch_id] = batch
        self.logger.info(f"Created flash batch: {batch_id} with {len(targets)} targets")
        
        return batch
    
    def start_batch_flash(self, batch_id: str) -> bool:
        """Start batch flashing operation"""
        if batch_id not in self.batches:
            self.logger.error(f"Batch {batch_id} not found")
            return False
        
        batch = self.batches[batch_id]
        
        if batch.status != "created":
            self.logger.error(f"Batch {batch_id} is not in created state")
            return False
        
        batch.status = "running"
        batch.started_at = datetime.now()
        
        self.logger.info(f"Starting batch flash: {batch_id}")
        
        # Start flashing based on strategy
        if batch.strategy == "parallel":
            self.start_parallel_flash(batch)
        elif batch.strategy == "sequential":
            self.start_sequential_flash(batch)
        elif batch.strategy == "gradual":
            self.start_gradual_flash(batch)
        
        return True
    
    def start_parallel_flash(self, batch: FlashBatch):
        """Start parallel flashing"""
        def flash_worker():
            futures = []
            
            # Submit all targets to thread pool
            for target in batch.targets:
                if target.status == FlashStatus.PENDING:
                    future = self.executor.submit(self.flash_single_target, target, batch)
                    futures.append(future)
            
            # Wait for completion
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    self.logger.error(f"Flash operation failed: {e}")
            
            # Update batch status
            self.update_batch_status(batch)
        
        # Start worker thread
        thread = threading.Thread(target=flash_worker)
        thread.daemon = True
        thread.start()
        
        self.active_operations[batch.batch_id] = thread
    
    def start_sequential_flash(self, batch: FlashBatch):
        """Start sequential flashing"""
        def flash_worker():
            for target in batch.targets:
                if target.status == FlashStatus.PENDING:
                    self.flash_single_target(target, batch)
                    
                    # Check if batch should be cancelled
                    if batch.status == "cancelled":
                        break
            
            # Update batch status
            self.update_batch_status(batch)
        
        # Start worker thread
        thread = threading.Thread(target=flash_worker)
        thread.daemon = True
        thread.start()
        
        self.active_operations[batch.batch_id] = thread
    
    def start_gradual_flash(self, batch: FlashBatch):
        """Start gradual flashing (batch by batch)"""
        def flash_worker():
            batch_size = min(batch.max_concurrent, len(batch.targets))
            
            for i in range(0, len(batch.targets), batch_size):
                batch_targets = batch.targets[i:i + batch_size]
                
                # Flash current batch
                futures = []
                for target in batch_targets:
                    if target.status == FlashStatus.PENDING:
                        future = self.executor.submit(self.flash_single_target, target, batch)
                        futures.append(future)
                
                # Wait for current batch to complete
                for future in concurrent.futures.as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        self.logger.error(f"Flash operation failed: {e}")
                
                # Check success rate before continuing
                current_success_rate = (batch.success_count / (batch.success_count + batch.failure_count)) * 100
                min_success_rate = self.config.get("quality_gates", {}).get("min_success_rate", 80)
                
                if current_success_rate < min_success_rate:
                    self.logger.warning(f"Success rate ({current_success_rate:.1f}%) below threshold ({min_success_rate}%)")
                    if batch.rollback_on_failure:
                        self.rollback_batch(batch)
                    break
                
                # Short delay between batches
                if i + batch_size < len(batch.targets):
                    time.sleep(5)
            
            # Update batch status
            self.update_batch_status(batch)
        
        # Start worker thread
        thread = threading.Thread(target=flash_worker)
        thread.daemon = True
        thread.start()
        
        self.active_operations[batch.batch_id] = thread
    
    def flash_single_target(self, target: FlashTarget, batch: FlashBatch) -> bool:
        """Flash single target device"""
        try:
            self.logger.info(f"Starting flash for {target.device_id}")
            
            target.status = FlashStatus.PREPARING
            target.flash_start_time = datetime.now()
            
            # Get appropriate interface
            interface_name = self.get_interface_for_device(target.device_type)
            if interface_name not in self.interfaces:
                target.status = FlashStatus.FAILED
                target.error_message = f"No interface available for {target.device_type}"
                return False
            
            interface = self.interfaces[interface_name]
            
            # Create backup if required
            if self.config.get("flash_settings", {}).get("backup_before_flash", True):
                self.logger.info(f"Creating backup for {target.device_id}")
                if interface.backup_firmware(target):
                    target.backup_created = True
                    target.rollback_available = True
            
            # Run pre-flash commands
            for command in batch.pre_flash_commands:
                self.logger.info(f"Running pre-flash command: {command}")
                # Execute command (implementation depends on command type)
            
            # Flash firmware
            target.status = FlashStatus.FLASHING
            flash_success = interface.flash_firmware(batch.firmware_package.file_path, target)
            
            if not flash_success:
                target.status = FlashStatus.FAILED
                batch.failure_count += 1
                
                # Rollback if enabled
                if batch.rollback_on_failure and target.rollback_available:
                    self.logger.info(f"Rolling back {target.device_id}")
                    interface.rollback_firmware(target)
                
                return False
            
            # Verify firmware if required
            if self.config.get("flash_settings", {}).get("verify_after_flash", True):
                target.status = FlashStatus.VERIFYING
                verify_success = interface.verify_firmware(target)
                target.verification_result = verify_success
                
                if not verify_success:
                    target.status = FlashStatus.FAILED
                    batch.failure_count += 1
                    
                    # Rollback if enabled
                    if batch.rollback_on_failure and target.rollback_available:
                        self.logger.info(f"Rolling back {target.device_id} due to verification failure")
                        interface.rollback_firmware(target)
                    
                    return False
            
            # Run post-flash commands
            for command in batch.post_flash_commands:
                self.logger.info(f"Running post-flash command: {command}")
                # Execute command (implementation depends on command type)
            
            # Success
            target.status = FlashStatus.COMPLETED
            target.flash_end_time = datetime.now()
            batch.success_count += 1
            
            self.logger.info(f"Successfully flashed {target.device_id}")
            return True
            
        except Exception as e:
            target.status = FlashStatus.FAILED
            target.error_message = str(e)
            target.flash_end_time = datetime.now()
            batch.failure_count += 1
            
            self.logger.error(f"Flash failed for {target.device_id}: {e}")
            return False
        
        finally:
            # Update batch progress
            completed_count = batch.success_count + batch.failure_count + batch.cancelled_count
            batch.progress = (completed_count / batch.total_count) * 100
    
    def get_interface_for_device(self, device_type: DeviceType) -> str:
        """Get appropriate interface for device type"""
        if device_type in [DeviceType.ESP32, DeviceType.ESP8266]:
            return "serial"
        elif device_type in [DeviceType.ARDUINO, DeviceType.STM32]:
            return "serial"
        elif device_type == DeviceType.PICO:
            return "serial"
        else:
            return "network"
    
    def update_batch_status(self, batch: FlashBatch):
        """Update batch status after operations complete"""
        if batch.status == "cancelled":
            return
        
        if batch.success_count + batch.failure_count + batch.cancelled_count == batch.total_count:
            batch.status = "completed"
            batch.completed_at = datetime.now()
            
            # Remove from active operations
            if batch.batch_id in self.active_operations:
                del self.active_operations[batch.batch_id]
            
            # Generate batch report
            self.generate_batch_report(batch)
            
            self.logger.info(f"Batch {batch.batch_id} completed: {batch.success_count} success, {batch.failure_count} failed")
    
    def cancel_batch(self, batch_id: str) -> bool:
        """Cancel batch operation"""
        if batch_id not in self.batches:
            return False
        
        batch = self.batches[batch_id]
        batch.status = "cancelled"
        
        # Cancel pending targets
        for target in batch.targets:
            if target.status == FlashStatus.PENDING:
                target.status = FlashStatus.CANCELLED
                batch.cancelled_count += 1
        
        self.logger.info(f"Cancelled batch {batch_id}")
        return True
    
    def rollback_batch(self, batch: FlashBatch):
        """Rollback entire batch"""
        self.logger.info(f"Rolling back batch {batch.batch_id}")
        
        rollback_targets = []
        for target in batch.targets:
            if target.status == FlashStatus.COMPLETED and target.rollback_available:
                rollback_targets.append(target)
        
        # Create rollback operations
        futures = []
        for target in rollback_targets:
            interface_name = self.get_interface_for_device(target.device_type)
            if interface_name in self.interfaces:
                interface = self.interfaces[interface_name]
                future = self.executor.submit(interface.rollback_firmware, target)
                futures.append(future)
        
        # Wait for rollback completion
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                self.logger.error(f"Rollback failed: {e}")
    
    def get_batch_status(self, batch_id: str) -> Optional[Dict]:
        """Get batch status"""
        if batch_id not in self.batches:
            return None
        
        batch = self.batches[batch_id]
        
        return {
            "batch_id": batch.batch_id,
            "name": batch.name,
            "status": batch.status,
            "progress": batch.progress,
            "total_count": batch.total_count,
            "success_count": batch.success_count,
            "failure_count": batch.failure_count,
            "cancelled_count": batch.cancelled_count,
            "created_at": batch.created_at.isoformat(),
            "started_at": batch.started_at.isoformat() if batch.started_at else None,
            "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
            "targets": [
                {
                    "device_id": target.device_id,
                    "status": target.status.value,
                    "error_message": target.error_message,
                    "retry_count": target.retry_count,
                    "verification_result": target.verification_result
                }
                for target in batch.targets
            ]
        }
    
    def generate_batch_report(self, batch: FlashBatch):
        """Generate comprehensive batch report"""
        report = {
            "batch_id": batch.batch_id,
            "name": batch.name,
            "description": batch.description,
            "firmware_package": {
                "firmware_id": batch.firmware_package.firmware_id,
                "version": batch.firmware_package.version,
                "device_type": batch.firmware_package.device_type.value,
                "size": batch.firmware_package.size,
                "checksum": batch.firmware_package.checksum
            },
            "summary": {
                "total_count": batch.total_count,
                "success_count": batch.success_count,
                "failure_count": batch.failure_count,
                "cancelled_count": batch.cancelled_count,
                "success_rate": (batch.success_count / batch.total_count) * 100 if batch.total_count > 0 else 0,
                "total_time": (batch.completed_at - batch.started_at).total_seconds() if batch.completed_at and batch.started_at else 0
            },
            "timeline": {
                "created_at": batch.created_at.isoformat(),
                "started_at": batch.started_at.isoformat() if batch.started_at else None,
                "completed_at": batch.completed_at.isoformat() if batch.completed_at else None
            },
            "targets": [],
            "statistics": {
                "average_flash_time": 0,
                "fastest_flash": None,
                "slowest_flash": None,
                "retry_statistics": {},
                "error_categories": {}
            }
        }
        
        # Calculate statistics
        flash_times = []
        retry_counts = {}
        error_categories = {}
        
        for target in batch.targets:
            # Target details
            target_report = {
                "device_id": target.device_id,
                "device_type": target.device_type.value,
                "status": target.status.value,
                "retry_count": target.retry_count,
                "error_message": target.error_message,
                "verification_result": target.verification_result,
                "backup_created": target.backup_created,
                "flash_time": None
            }
            
            if target.flash_start_time and target.flash_end_time:
                flash_time = (target.flash_end_time - target.flash_start_time).total_seconds()
                target_report["flash_time"] = flash_time
                flash_times.append(flash_time)
            
            report["targets"].append(target_report)
            
            # Retry statistics
            retry_counts[target.retry_count] = retry_counts.get(target.retry_count, 0) + 1
            
            # Error categories
            if target.error_message:
                category = self.categorize_error(target.error_message)
                error_categories[category] = error_categories.get(category, 0) + 1
        
        # Update statistics
        if flash_times:
            report["statistics"]["average_flash_time"] = sum(flash_times) / len(flash_times)
            report["statistics"]["fastest_flash"] = min(flash_times)
            report["statistics"]["slowest_flash"] = max(flash_times)
        
        report["statistics"]["retry_statistics"] = retry_counts
        report["statistics"]["error_categories"] = error_categories
        
        # Save report
        report_file = f"batch_report_{batch.batch_id}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Batch report saved to {report_file}")
        return report
    
    def categorize_error(self, error_message: str) -> str:
        """Categorize error message"""
        error_lower = error_message.lower()
        
        if "timeout" in error_lower:
            return "timeout"
        elif "connection" in error_lower or "connect" in error_lower:
            return "connection"
        elif "permission" in error_lower:
            return "permission"
        elif "verification" in error_lower or "verify" in error_lower:
            return "verification"
        elif "flash" in error_lower:
            return "flash"
        elif "network" in error_lower:
            return "network"
        else:
            return "other"
    
    def list_batches(self) -> List[Dict]:
        """List all batches"""
        return [
            {
                "batch_id": batch.batch_id,
                "name": batch.name,
                "status": batch.status,
                "progress": batch.progress,
                "total_count": batch.total_count,
                "success_count": batch.success_count,
                "failure_count": batch.failure_count,
                "created_at": batch.created_at.isoformat()
            }
            for batch in self.batches.values()
        ]
    
    def cleanup_old_batches(self, days: int = 30):
        """Clean up old batch records"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        to_remove = []
        for batch_id, batch in self.batches.items():
            if batch.created_at < cutoff_date and batch.status in ["completed", "cancelled"]:
                to_remove.append(batch_id)
        
        for batch_id in to_remove:
            del self.batches[batch_id]
            self.logger.info(f"Cleaned up old batch: {batch_id}")
    
    def shutdown(self):
        """Shutdown the batch manager"""
        self.logger.info("Shutting down batch flash manager")
        
        # Cancel all active operations
        for batch_id in list(self.active_operations.keys()):
            self.cancel_batch(batch_id)
        
        # Shutdown thread pool
        self.executor.shutdown(wait=True)
        
        # Disconnect interfaces
        for interface in self.interfaces.values():
            interface.disconnect()

def main():
    """Main function for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch Firmware Flash Manager')
    parser.add_argument('--config', '-c', default='batch-flash-config.yaml', help='Configuration file')
    parser.add_argument('--firmware', '-f', help='Firmware file path')
    parser.add_argument('--device-type', '-t', choices=['esp32', 'esp8266', 'arduino', 'stm32', 'pico'], 
                       default='esp32', help='Device type')
    parser.add_argument('--version', '-v', default='1.0.0', help='Firmware version')
    parser.add_argument('--targets', '-T', help='JSON file with target definitions')
    parser.add_argument('--list', '-l', action='store_true', help='List all batches')
    parser.add_argument('--status', '-s', help='Get batch status')
    parser.add_argument('--cancel', help='Cancel batch')
    
    args = parser.parse_args()
    
    # Create manager
    manager = BatchFlashManager(args.config)
    
    try:
        if args.list:
            batches = manager.list_batches()
            print("Batches:")
            for batch in batches:
                print(f"  {batch['batch_id']}: {batch['name']} ({batch['status']})")
        
        elif args.status:
            status = manager.get_batch_status(args.status)
            if status:
                print(json.dumps(status, indent=2))
            else:
                print("Batch not found")
        
        elif args.cancel:
            if manager.cancel_batch(args.cancel):
                print(f"Batch {args.cancel} cancelled")
            else:
                print("Failed to cancel batch")
        
        elif args.firmware and args.targets:
            # Create and start batch
            firmware_package = manager.create_firmware_package(
                args.firmware, args.device_type, args.version
            )
            
            # Load targets
            with open(args.targets, 'r') as f:
                targets_data = json.load(f)
            
            targets = []
            for target_data in targets_data:
                target = FlashTarget(
                    device_id=target_data['device_id'],
                    device_type=DeviceType(target_data['device_type']),
                    connection_info=target_data['connection_info']
                )
                targets.append(target)
            
            # Create batch
            batch = manager.create_flash_batch(
                name=f"Batch {args.version}",
                firmware_package=firmware_package,
                targets=targets
            )
            
            print(f"Created batch: {batch.batch_id}")
            
            # Start batch
            if manager.start_batch_flash(batch.batch_id):
                print(f"Started batch: {batch.batch_id}")
            else:
                print("Failed to start batch")
        
        else:
            print("Use --help for usage information")
    
    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        manager.shutdown()

if __name__ == "__main__":
    main()
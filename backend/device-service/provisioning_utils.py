#!/usr/bin/env python3
"""
Device Provisioning Utilities
Handles device UID generation, QR code creation, and provisioning logic
"""

import hashlib
import secrets
import string
import uuid
import json
import qrcode
import io
import base64
from typing import Dict, Any, Optional
from datetime import datetime, timezone


class DeviceUIDGenerator:
    """Generates unique device identifiers"""
    
    @staticmethod
    def generate_device_uid(mac_address: str, device_model: str) -> str:
        """
        Generate device UID from MAC address and device model hash
        Format: {MODEL_HASH}_{MAC_HASH}
        """
        # Clean MAC address (remove separators)
        clean_mac = mac_address.replace(":", "").replace("-", "").upper()
        
        # Create hash input
        hash_input = f"{device_model}_{clean_mac}".encode('utf-8')
        
        # Generate SHA256 hash and take first 16 characters
        hash_digest = hashlib.sha256(hash_input).hexdigest().upper()[:16]
        
        # Format as UID
        device_uid = f"{hash_digest[:8]}_{hash_digest[8:]}"
        
        return device_uid
    
    @staticmethod
    def generate_device_id(prefix: str = "ESP32") -> str:
        """Generate legacy device ID for backwards compatibility"""
        return f"{prefix}_{secrets.token_hex(4).upper()}"
    
    @staticmethod
    def generate_device_secret(length: int = 32) -> str:
        """Generate secure device secret"""
        alphabet = string.ascii_letters + string.digits + "-_"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def generate_provisioning_token() -> str:
        """Generate one-time provisioning token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_public_key_hash() -> str:
        """Generate mock public key hash (in real implementation, use actual device public key)"""
        return hashlib.sha256(secrets.token_bytes(32)).hexdigest()
    
    @staticmethod
    def generate_batch_id() -> str:
        """Generate unique batch ID"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        random_part = secrets.token_hex(4).upper()
        return f"BATCH_{timestamp}_{random_part}"


class QRCodeGenerator:
    """Handles QR code generation for device provisioning"""
    
    @staticmethod
    def create_qr_data(
        device_uid: str,
        device_id: str,
        provisioning_token: str,
        public_key_hash: str,
        device_model: str,
        manufacturer: str
    ) -> Dict[str, Any]:
        """Create QR code data structure"""
        return {
            "version": "1.0",
            "type": "device_provisioning",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "device": {
                "uid": device_uid,
                "id": device_id,
                "model": device_model,
                "manufacturer": manufacturer
            },
            "auth": {
                "provisioning_token": provisioning_token,
                "public_key_hash": public_key_hash
            },
            "config": {
                "ap_mode_ssid": f"ESP32-{device_id[-6:]}",
                "setup_url": "http://192.168.4.1"
            }
        }
    
    @staticmethod
    def generate_qr_code(qr_data: Dict[str, Any], size: int = 10, border: int = 4) -> str:
        """Generate QR code image as base64 string"""
        try:
            # Convert data to JSON string
            qr_string = json.dumps(qr_data, separators=(',', ':'))
            
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=size,
                border=border
            )
            qr.add_data(qr_string)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            raise Exception(f"Failed to generate QR code: {str(e)}")
    
    @staticmethod
    def parse_qr_data(qr_string: str) -> Optional[Dict[str, Any]]:
        """Parse QR code data string"""
        try:
            return json.loads(qr_string)
        except json.JSONDecodeError:
            return None


class ProvisioningValidator:
    """Validates provisioning data and constraints"""
    
    @staticmethod
    def validate_mac_address(mac_address: str) -> bool:
        """Validate MAC address format"""
        import re
        pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
        return bool(re.match(pattern, mac_address))
    
    @staticmethod
    def validate_device_model(device_model: str) -> bool:
        """Validate device model format"""
        allowed_models = [
            "ESP32-WROOM-32", "ESP32-WROOM-32D", "ESP32-WROOM-32U",
            "ESP32-WROVER", "ESP32-WROVER-B", "ESP32-WROVER-I",
            "ESP8266", "ESP8266-12E", "ESP8266-12F",
            "ESP32-S2", "ESP32-S3", "ESP32-C3", "ESP32-C6"
        ]
        return device_model in allowed_models or device_model.startswith("ESP")
    
    @staticmethod
    def validate_batch_size(device_count: int) -> bool:
        """Validate batch size limits"""
        MAX_BATCH_SIZE = 1000
        return 1 <= device_count <= MAX_BATCH_SIZE
    
    @staticmethod
    def check_duplicate_devices(devices: list, existing_uids: set) -> list:
        """Check for duplicate devices in batch and against existing devices"""
        errors = []
        seen_macs = set()
        seen_names = set()
        
        for i, device in enumerate(devices):
            # Check duplicate MAC in batch
            mac = device.get('mac_address', '').replace(":", "").replace("-", "").upper()
            if mac in seen_macs:
                errors.append(f"Device {i+1}: Duplicate MAC address in batch")
            seen_macs.add(mac)
            
            # Check duplicate name in batch
            name = device.get('device_name', '')
            if name in seen_names:
                errors.append(f"Device {i+1}: Duplicate device name in batch")
            seen_names.add(name)
            
            # Generate UID and check against existing
            device_uid = DeviceUIDGenerator.generate_device_uid(
                device.get('mac_address', ''),
                device.get('device_model', '')
            )
            if device_uid in existing_uids:
                errors.append(f"Device {i+1}: Device already exists (UID: {device_uid})")
        
        return errors


class ProvisioningManager:
    """Main provisioning management class"""
    
    def __init__(self):
        self.uid_generator = DeviceUIDGenerator()
        self.qr_generator = QRCodeGenerator()
        self.validator = ProvisioningValidator()
    
    def create_device_registration(
        self,
        device_name: str,
        device_model: str,
        mac_address: str,
        manufacturer: str = "Espressif",
        firmware_version: Optional[str] = None,
        hardware_revision: Optional[str] = None,
        description: Optional[str] = None,
        batch_id: Optional[str] = None,
        installer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a complete device registration with QR code"""
        
        # Validate inputs
        if not self.validator.validate_mac_address(mac_address):
            raise ValueError("Invalid MAC address format")
        
        if not self.validator.validate_device_model(device_model):
            raise ValueError("Invalid device model")
        
        # Generate identifiers
        device_uid = self.uid_generator.generate_device_uid(mac_address, device_model)
        device_id = self.uid_generator.generate_device_id()
        device_secret = self.uid_generator.generate_device_secret()
        provisioning_token = self.uid_generator.generate_provisioning_token()
        public_key_hash = self.uid_generator.generate_public_key_hash()
        
        # Create QR code data
        qr_data = self.qr_generator.create_qr_data(
            device_uid=device_uid,
            device_id=device_id,
            provisioning_token=provisioning_token,
            public_key_hash=public_key_hash,
            device_model=device_model,
            manufacturer=manufacturer
        )
        
        # Generate QR code image
        qr_code_url = self.qr_generator.generate_qr_code(qr_data)
        
        return {
            "device_id": device_id,
            "device_secret": device_secret,
            "device_name": device_name,
            "device_model": device_model,
            "mac_address": mac_address,
            "manufacturer": manufacturer,
            "firmware_version": firmware_version,
            "hardware_revision": hardware_revision,
            "description": description,
            "qr_code_data": json.dumps(qr_data),
            "qr_code_url": qr_code_url,
            "public_key_hash": public_key_hash,
            "provisioning_token": provisioning_token,
            "batch_id": batch_id,
            "installer_id": installer_id,
            "status": "registered",
            "paired": False,
            "provisioned": False
        }
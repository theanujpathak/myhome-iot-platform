#!/usr/bin/env python3
"""
Device Manager
Generates device IDs and secrets for ESP32 devices
"""

import uuid
import secrets
import string
import json
import os
from datetime import datetime
from typing import Dict, List

class DeviceManager:
    def __init__(self, devices_file: str = "devices.json"):
        self.devices_file = devices_file
        self.devices = self.load_devices()
        
    def load_devices(self) -> Dict:
        """Load devices from file"""
        if os.path.exists(self.devices_file):
            try:
                with open(self.devices_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading devices: {e}")
        return {}
    
    def save_devices(self):
        """Save devices to file"""
        try:
            with open(self.devices_file, 'w') as f:
                json.dump(self.devices, f, indent=2)
        except Exception as e:
            print(f"Error saving devices: {e}")
    
    def generate_device_id(self) -> str:
        """Generate a unique device ID"""
        # Format: ESP32_XXXXXXXX (8 random hex characters)
        return f"ESP32_{secrets.token_hex(4).upper()}"
    
    def generate_device_secret(self, length: int = 32) -> str:
        """Generate a secure device secret"""
        alphabet = string.ascii_letters + string.digits + "-_"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def register_device(self, device_name: str, device_type: str = "ESP32", 
                       manufacturer: str = "Espressif", description: str = "") -> Dict:
        """Register a new device"""
        device_id = self.generate_device_id()
        
        # Ensure unique device ID
        while device_id in self.devices:
            device_id = self.generate_device_id()
            
        device_secret = self.generate_device_secret()
        
        device_info = {
            'device_id': device_id,
            'device_secret': device_secret,
            'device_name': device_name,
            'device_type': device_type,
            'manufacturer': manufacturer,
            'description': description,
            'created_at': datetime.now().isoformat(),
            'status': 'registered',
            'paired': False,
            'user_id': None,
            'location_id': None
        }
        
        self.devices[device_id] = device_info
        self.save_devices()
        
        return device_info
    
    def get_device(self, device_id: str) -> Dict:
        """Get device information"""
        return self.devices.get(device_id)
    
    def list_devices(self) -> List[Dict]:
        """List all devices"""
        return list(self.devices.values())
    
    def pair_device(self, device_id: str, user_id: str, location_id: str = None) -> bool:
        """Pair device with user"""
        if device_id in self.devices:
            self.devices[device_id]['paired'] = True
            self.devices[device_id]['user_id'] = user_id
            self.devices[device_id]['location_id'] = location_id
            self.devices[device_id]['paired_at'] = datetime.now().isoformat()
            self.save_devices()
            return True
        return False
    
    def unpair_device(self, device_id: str) -> bool:
        """Unpair device from user"""
        if device_id in self.devices:
            self.devices[device_id]['paired'] = False
            self.devices[device_id]['user_id'] = None
            self.devices[device_id]['location_id'] = None
            self.devices[device_id]['unpaired_at'] = datetime.now().isoformat()
            self.save_devices()
            return True
        return False
    
    def delete_device(self, device_id: str) -> bool:
        """Delete device"""
        if device_id in self.devices:
            del self.devices[device_id]
            self.save_devices()
            return True
        return False
    
    def create_sample_devices(self, count: int = 5) -> List[Dict]:
        """Create sample devices for testing"""
        device_names = [
            "Living Room Light Controller",
            "Kitchen Temperature Monitor",
            "Bedroom Security System",
            "Garage Door Controller",
            "Garden Irrigation System"
        ]
        
        created_devices = []
        
        for i in range(min(count, len(device_names))):
            device_info = self.register_device(
                device_name=device_names[i],
                device_type="ESP32",
                manufacturer="Espressif",
                description=f"Sample ESP32 device for testing - {device_names[i]}"
            )
            created_devices.append(device_info)
            
        return created_devices

def main():
    """Main function for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ESP32 Device Manager")
    parser.add_argument('action', choices=['register', 'list', 'get', 'pair', 'unpair', 'delete', 'sample'],
                       help='Action to perform')
    parser.add_argument('--device-id', help='Device ID')
    parser.add_argument('--device-name', help='Device name')
    parser.add_argument('--device-type', default='ESP32', help='Device type')
    parser.add_argument('--manufacturer', default='Espressif', help='Manufacturer')
    parser.add_argument('--description', default='', help='Description')
    parser.add_argument('--user-id', help='User ID for pairing')
    parser.add_argument('--location-id', help='Location ID for pairing')
    parser.add_argument('--count', type=int, default=5, help='Number of sample devices to create')
    
    args = parser.parse_args()
    
    manager = DeviceManager()
    
    if args.action == 'register':
        if not args.device_name:
            print("Error: --device-name is required for registration")
            return
            
        device_info = manager.register_device(
            device_name=args.device_name,
            device_type=args.device_type,
            manufacturer=args.manufacturer,
            description=args.description
        )
        
        print("Device registered successfully:")
        print(f"Device ID: {device_info['device_id']}")
        print(f"Device Secret: {device_info['device_secret']}")
        print(f"Device Name: {device_info['device_name']}")
        
    elif args.action == 'list':
        devices = manager.list_devices()
        if devices:
            print(f"Found {len(devices)} devices:")
            for device in devices:
                print(f"  {device['device_id']}: {device['device_name']} ({device['status']})")
        else:
            print("No devices found")
            
    elif args.action == 'get':
        if not args.device_id:
            print("Error: --device-id is required")
            return
            
        device = manager.get_device(args.device_id)
        if device:
            print(json.dumps(device, indent=2))
        else:
            print("Device not found")
            
    elif args.action == 'pair':
        if not args.device_id or not args.user_id:
            print("Error: --device-id and --user-id are required for pairing")
            return
            
        if manager.pair_device(args.device_id, args.user_id, args.location_id):
            print("Device paired successfully")
        else:
            print("Failed to pair device")
            
    elif args.action == 'unpair':
        if not args.device_id:
            print("Error: --device-id is required")
            return
            
        if manager.unpair_device(args.device_id):
            print("Device unpaired successfully")
        else:
            print("Failed to unpair device")
            
    elif args.action == 'delete':
        if not args.device_id:
            print("Error: --device-id is required")
            return
            
        if manager.delete_device(args.device_id):
            print("Device deleted successfully")
        else:
            print("Failed to delete device")
            
    elif args.action == 'sample':
        devices = manager.create_sample_devices(args.count)
        print(f"Created {len(devices)} sample devices:")
        for device in devices:
            print(f"  {device['device_id']}: {device['device_name']}")
            print(f"    Secret: {device['device_secret']}")

if __name__ == "__main__":
    main()
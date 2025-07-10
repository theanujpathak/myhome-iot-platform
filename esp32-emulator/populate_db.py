#!/usr/bin/env python3
"""
Populate database with device registrations
"""

import json
import sys
import os
sys.path.append('../backend/device-service')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import DeviceRegistration, Base

# Database configuration
DATABASE_URL = "postgresql://homeuser:homepass@localhost:5433/home_automation"

# Create database engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def load_devices():
    """Load devices from JSON file"""
    if os.path.exists("devices.json"):
        with open("devices.json", "r") as f:
            return json.load(f)
    return {}

def populate_registrations():
    """Populate device registrations table"""
    devices = load_devices()
    
    if not devices:
        print("No devices found in devices.json")
        return
    
    db = SessionLocal()
    
    try:
        for device_id, device_info in devices.items():
            # Check if already exists
            existing = db.query(DeviceRegistration).filter(
                DeviceRegistration.device_id == device_id
            ).first()
            
            if existing:
                print(f"Device {device_id} already exists, skipping")
                continue
            
            # Create new registration
            registration = DeviceRegistration(
                device_id=device_info['device_id'],
                device_secret=device_info['device_secret'],
                device_name=device_info['device_name'],
                device_type=device_info['device_type'],
                manufacturer=device_info['manufacturer'],
                description=device_info['description'],
                status=device_info['status'],
                paired=device_info['paired'],
                user_id=device_info.get('user_id'),
                location_id=device_info.get('location_id')
            )
            
            db.add(registration)
            print(f"Added device registration: {device_id}")
        
        db.commit()
        print("Device registrations populated successfully")
        
    except Exception as e:
        print(f"Error populating registrations: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    populate_registrations()
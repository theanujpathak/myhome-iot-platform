from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from keycloak import KeycloakOpenID
import os
import jwt
from typing import Optional, Dict, Any, List
import redis
import json
import logging
from datetime import datetime

from database import get_db, engine
from models import Device, DeviceType, Location, DeviceState, DeviceRegistration, ProvisioningBatch, Base
from schemas import (
    DeviceCreate, DeviceUpdate, DeviceResponse, DeviceCommand, DeviceCommandResponse,
    LocationCreate, LocationUpdate, LocationResponse,
    DeviceTypeCreate, DeviceTypeResponse,
    DeviceStateResponse, DeviceStatusUpdate,
    DeviceRegistrationCreate, DeviceRegistrationUpdate, DeviceRegistrationResponse,
    DeviceRegistrationPublic, DevicePairRequest, DevicePairResponse,
    BulkDeviceRegistration, ProvisioningBatchCreate, ProvisioningBatchResponse,
    BulkProvisioningResult, QRCodeData
)
from provisioning_utils import ProvisioningManager, DeviceUIDGenerator
from mqtt_client import mqtt_client

# Create tables
Base.metadata.create_all(bind=engine)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Home Automation Device Service", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3002", "http://localhost:3003"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Configuration
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "home-automation")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "home-automation-backend")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6380")

# Initialize Keycloak client
keycloak_openid = KeycloakOpenID(
    server_url=KEYCLOAK_URL,
    client_id=KEYCLOAK_CLIENT_ID,
    realm_name=KEYCLOAK_REALM,
)

# Redis client for caching
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# Security scheme
security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify JWT token with Keycloak"""
    try:
        token = credentials.credentials
        
        # Check cache first
        cached_user = redis_client.get(f"user_token:{token}")
        if cached_user:
            return json.loads(cached_user)
        
        # Get Keycloak public key and verify token
        public_key_raw = keycloak_openid.public_key()
        # Format the public key properly for PyJWT with line breaks every 64 chars
        import textwrap
        formatted_key = '\n'.join(textwrap.wrap(public_key_raw, 64))
        public_key = f"-----BEGIN PUBLIC KEY-----\n{formatted_key}\n-----END PUBLIC KEY-----"
        options = {"verify_signature": True, "verify_aud": False, "verify_exp": True}
        
        token_info = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options=options
        )
        
        # Cache the user info for 5 minutes
        redis_client.setex(f"user_token:{token}", 300, json.dumps(token_info))
        
        return token_info
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except (jwt.InvalidTokenError, jwt.DecodeError, jwt.InvalidSignatureError, jwt.InvalidKeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

@app.on_event("startup")
async def startup_event():
    """Initialize MQTT client on startup"""
    logger.info("Starting Device Service")
    
    # Initialize default device types
    db = next(get_db())
    try:
        existing_types = db.query(DeviceType).count()
        if existing_types == 0:
            default_types = [
                DeviceType(
                    name="Smart Light",
                    description="Smart LED light bulb",
                    icon="lightbulb",
                    capabilities=["switch", "dimmer", "color"]
                ),
                DeviceType(
                    name="Smart Switch",
                    description="Smart wall switch",
                    icon="toggle_on",
                    capabilities=["switch"]
                ),
                DeviceType(
                    name="Temperature Sensor",
                    description="Temperature and humidity sensor",
                    icon="thermostat",
                    capabilities=["temperature", "humidity"]
                ),
                DeviceType(
                    name="Smart Plug",
                    description="Smart electrical outlet",
                    icon="power",
                    capabilities=["switch", "power_monitoring"]
                ),
                DeviceType(
                    name="Door Sensor",
                    description="Magnetic door/window sensor",
                    icon="door_open",
                    capabilities=["contact", "battery"]
                ),
                DeviceType(
                    name="Motion Sensor",
                    description="PIR motion detection sensor",
                    icon="motion_sensor",
                    capabilities=["motion", "battery"]
                )
            ]
            
            for device_type in default_types:
                db.add(device_type)
            db.commit()
            logger.info("Default device types created")
    finally:
        db.close()
    
    # Connect to MQTT broker
    if mqtt_client.connect():
        logger.info("Connected to MQTT broker")
    else:
        logger.error("Failed to connect to MQTT broker")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    mqtt_client.disconnect()
    logger.info("Device Service stopped")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "device-service"}

# Add OPTIONS handler for CORS preflight requests
@app.options("/{path:path}")
async def handle_options(path: str):
    """Handle CORS preflight OPTIONS requests"""
    return {"message": "OK"}

# Device Type endpoints
@app.get("/api/device-types", response_model=List[DeviceTypeResponse])
async def get_device_types(
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get all device types"""
    device_types = db.query(DeviceType).all()
    return device_types

@app.post("/api/device-types", response_model=DeviceTypeResponse)
async def create_device_type(
    device_type: DeviceTypeCreate,
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Create new device type (admin only)"""
    # Check if user has admin role
    roles = current_user.get("realm_access", {}).get("roles", [])
    if "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    db_device_type = DeviceType(**device_type.model_dump())
    db.add(db_device_type)
    db.commit()
    db.refresh(db_device_type)
    return db_device_type

# Location endpoints
@app.get("/api/locations", response_model=List[LocationResponse])
async def get_locations(
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get user's locations"""
    user_id = current_user.get("sub")
    locations = db.query(Location).filter(Location.user_id == user_id).all()
    return locations

@app.post("/api/locations", response_model=LocationResponse)
async def create_location(
    location: LocationCreate,
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Create new location"""
    user_id = current_user.get("sub")
    db_location = Location(**location.model_dump(), user_id=user_id)
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

@app.put("/api/locations/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: int,
    location: LocationUpdate,
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Update location"""
    user_id = current_user.get("sub")
    db_location = db.query(Location).filter(
        Location.id == location_id,
        Location.user_id == user_id
    ).first()
    
    if not db_location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    update_data = location.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_location, key, value)
    
    db.commit()
    db.refresh(db_location)
    return db_location

@app.delete("/api/locations/{location_id}")
async def delete_location(
    location_id: int,
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Delete location"""
    user_id = current_user.get("sub")
    db_location = db.query(Location).filter(
        Location.id == location_id,
        Location.user_id == user_id
    ).first()
    
    if not db_location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    db.delete(db_location)
    db.commit()
    return {"message": "Location deleted successfully"}

# Device endpoints
@app.get("/api/devices", response_model=List[DeviceResponse])
async def get_devices(
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get user's devices"""
    user_id = current_user.get("sub")
    devices = db.query(Device).filter(Device.user_id == user_id).all()
    
    # Load latest states for each device
    for device in devices:
        latest_states = db.query(DeviceState).filter(
            DeviceState.device_id == device.id
        ).order_by(DeviceState.timestamp.desc()).limit(10).all()
        device.device_states = latest_states
    
    return devices

@app.post("/api/devices", response_model=DeviceResponse)
async def create_device(
    device: DeviceCreate,
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Create new device"""
    user_id = current_user.get("sub")
    
    # Check if device_id is unique
    existing_device = db.query(Device).filter(Device.device_id == device.device_id).first()
    if existing_device:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device ID already exists"
        )
    
    # Verify device type exists
    device_type = db.query(DeviceType).filter(DeviceType.id == device.device_type_id).first()
    if not device_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device type not found"
        )
    
    # Verify location belongs to user if provided
    if device.location_id:
        location = db.query(Location).filter(
            Location.id == device.location_id,
            Location.user_id == user_id
        ).first()
        if not location:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Location not found"
            )
    
    db_device = Device(**device.model_dump(), user_id=user_id)
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device

@app.get("/api/devices/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get specific device"""
    user_id = current_user.get("sub")
    device = db.query(Device).filter(
        Device.id == device_id,
        Device.user_id == user_id
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Load latest states
    latest_states = db.query(DeviceState).filter(
        DeviceState.device_id == device.id
    ).order_by(DeviceState.timestamp.desc()).limit(10).all()
    device.device_states = latest_states
    
    return device

@app.put("/api/devices/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    device: DeviceUpdate,
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Update device"""
    user_id = current_user.get("sub")
    db_device = db.query(Device).filter(
        Device.id == device_id,
        Device.user_id == user_id
    ).first()
    
    if not db_device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Verify location belongs to user if provided
    if device.location_id:
        location = db.query(Location).filter(
            Location.id == device.location_id,
            Location.user_id == user_id
        ).first()
        if not location:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Location not found"
            )
    
    update_data = device.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_device, key, value)
    
    db.commit()
    db.refresh(db_device)
    return db_device

@app.delete("/api/devices/{device_id}")
async def delete_device(
    device_id: int,
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Delete device"""
    user_id = current_user.get("sub")
    db_device = db.query(Device).filter(
        Device.id == device_id,
        Device.user_id == user_id
    ).first()
    
    if not db_device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    db.delete(db_device)
    db.commit()
    return {"message": "Device deleted successfully"}

@app.post("/api/devices/{device_id}/command", response_model=DeviceCommandResponse)
async def send_device_command(
    device_id: int,
    command: DeviceCommand,
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Send command to device"""
    user_id = current_user.get("sub")
    device = db.query(Device).filter(
        Device.id == device_id,
        Device.user_id == user_id
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    if not device.is_online:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device is offline"
        )
    
    # Send command via MQTT
    success = mqtt_client.publish_device_command(
        device.device_id,
        command.command,
        command.parameters
    )
    
    if success:
        return DeviceCommandResponse(
            success=True,
            message="Command sent successfully",
            data={"device_id": device.device_id, "command": command.command}
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send command"
        )

@app.get("/api/devices/{device_id}/states", response_model=List[DeviceStateResponse])
async def get_device_states(
    device_id: int,
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get device state history"""
    user_id = current_user.get("sub")
    device = db.query(Device).filter(
        Device.id == device_id,
        Device.user_id == user_id
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    states = db.query(DeviceState).filter(
        DeviceState.device_id == device_id
    ).order_by(DeviceState.timestamp.desc()).limit(limit).all()
    
    return states

# Device Registration Endpoints

@app.post("/api/admin/device-registrations", response_model=DeviceRegistrationResponse)
async def create_device_registration(
    registration: DeviceRegistrationCreate,
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Create a new device registration (Admin only)"""
    user_roles = current_user.get("realm_access", {}).get("roles", [])
    if "admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    import secrets
    import string
    
    # Generate unique device ID
    device_id = f"ESP32_{secrets.token_hex(4).upper()}"
    while db.query(DeviceRegistration).filter(DeviceRegistration.device_id == device_id).first():
        device_id = f"ESP32_{secrets.token_hex(4).upper()}"
    
    # Generate secure secret
    alphabet = string.ascii_letters + string.digits + "-_"
    device_secret = ''.join(secrets.choice(alphabet) for _ in range(32))
    
    db_registration = DeviceRegistration(
        device_id=device_id,
        device_secret=device_secret,
        device_name=registration.device_name,
        device_type=registration.device_type,
        manufacturer=registration.manufacturer,
        description=registration.description
    )
    
    db.add(db_registration)
    db.commit()
    db.refresh(db_registration)
    
    return db_registration

@app.get("/api/admin/device-registrations", response_model=List[DeviceRegistrationPublic])
async def list_device_registrations(
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """List all device registrations (Admin only)"""
    user_roles = current_user.get("realm_access", {}).get("roles", [])
    if "admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    registrations = db.query(DeviceRegistration).all()
    return registrations

@app.get("/api/admin/device-registrations/{device_id}", response_model=DeviceRegistrationResponse)
async def get_device_registration(
    device_id: str,
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get device registration details (Admin only)"""
    user_roles = current_user.get("realm_access", {}).get("roles", [])
    if "admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    registration = db.query(DeviceRegistration).filter(
        DeviceRegistration.device_id == device_id
    ).first()
    
    if not registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device registration not found"
        )
    
    return registration

@app.post("/api/devices/pair", response_model=DevicePairResponse)
async def pair_device(
    pair_request: DevicePairRequest,
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Pair a device with the current user"""
    user_id = current_user.get("sub")
    
    # Find the device registration
    registration = db.query(DeviceRegistration).filter(
        DeviceRegistration.device_id == pair_request.device_id
    ).first()
    
    if not registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Verify the secret
    if registration.device_secret != pair_request.device_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid device secret"
        )
    
    # Check if device is already paired
    if registration.paired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device is already paired with another user"
        )
    
    # Find or create ESP32 device type
    device_type = db.query(DeviceType).filter(DeviceType.name == "ESP32").first()
    if not device_type:
        device_type = DeviceType(
            name="ESP32",
            description="ESP32 microcontroller with IoT capabilities",
            capabilities=["digital_io", "analog_io", "pwm", "mqtt", "wifi"]
        )
        db.add(device_type)
        db.commit()
        db.refresh(device_type)
    
    # Create device entry
    device_name = pair_request.device_name or registration.device_name
    device = Device(
        name=device_name,
        description=registration.description,
        device_id=registration.device_id,
        device_type_id=device_type.id,
        location_id=pair_request.location_id,
        user_id=user_id,
        is_online=False,
        firmware_version="1.0.0"
    )
    
    db.add(device)
    db.commit()
    db.refresh(device)
    
    # Update registration
    registration.paired = True
    registration.user_id = user_id
    registration.location_id = pair_request.location_id
    registration.paired_device_id = device.id
    registration.paired_at = datetime.utcnow()
    
    db.commit()
    
    return DevicePairResponse(
        success=True,
        message="Device paired successfully",
        device=device
    )

@app.get("/api/devices/available", response_model=List[DeviceRegistrationPublic])
async def get_available_devices(
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get available devices for pairing"""
    # Return unpaired devices
    registrations = db.query(DeviceRegistration).filter(
        DeviceRegistration.paired == False
    ).all()
    
    return registrations

# Bulk Provisioning Endpoints

@app.post("/api/admin/provisioning/bulk", response_model=BulkProvisioningResult)
async def bulk_provision_devices(
    batch_data: ProvisioningBatchCreate,
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Bulk provision devices from CSV or API (Admin only)"""
    user_roles = current_user.get("realm_access", {}).get("roles", [])
    if "admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    user_id = current_user.get("sub")
    provisioning_manager = ProvisioningManager()
    
    try:
        # Validate batch
        if not batch_data.devices or len(batch_data.devices) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No devices provided in batch"
            )
        
        if not provisioning_manager.validator.validate_batch_size(len(batch_data.devices)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch size exceeds maximum limit (1000 devices)"
            )
        
        # Check for existing devices
        existing_registrations = db.query(DeviceRegistration).all()
        existing_uids = {reg.device_id for reg in existing_registrations}
        
        # Validate devices for duplicates
        validation_errors = provisioning_manager.validator.check_duplicate_devices(
            [device.model_dump() for device in batch_data.devices],
            existing_uids
        )
        
        if validation_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Validation errors: {'; '.join(validation_errors)}"
            )
        
        # Generate batch ID
        batch_id = DeviceUIDGenerator.generate_batch_id()
        
        # Create provisioning batch record
        db_batch = ProvisioningBatch(
            batch_id=batch_id,
            batch_name=batch_data.batch_name,
            manufacturer=batch_data.manufacturer,
            device_model=batch_data.device_model,
            firmware_version=batch_data.firmware_version,
            total_devices=len(batch_data.devices),
            created_by=user_id,
            installer_id=batch_data.installer_id,
            notes=batch_data.notes,
            status="processing"
        )
        
        db.add(db_batch)
        db.commit()
        db.refresh(db_batch)
        
        # Process devices
        created_devices = []
        errors = []
        
        for i, device_data in enumerate(batch_data.devices):
            try:
                # Create device registration
                registration_data = provisioning_manager.create_device_registration(
                    device_name=device_data.device_name,
                    device_model=device_data.device_model,
                    mac_address=device_data.mac_address,
                    manufacturer=device_data.manufacturer,
                    firmware_version=device_data.firmware_version,
                    hardware_revision=device_data.hardware_revision,
                    description=device_data.description,
                    batch_id=batch_id,
                    installer_id=batch_data.installer_id
                )
                
                # Create database record
                db_registration = DeviceRegistration(**registration_data)
                db.add(db_registration)
                db.commit()
                db.refresh(db_registration)
                
                created_devices.append(db_registration)
                
            except Exception as e:
                error_msg = f"Device {i+1} ({device_data.device_name}): {str(e)}"
                errors.append(error_msg)
                logger.error(f"Failed to provision device: {error_msg}")
        
        # Update batch status
        db_batch.provisioned_devices = len(created_devices)
        db_batch.status = "completed" if len(errors) == 0 else "partial"
        if len(created_devices) == len(batch_data.devices):
            db_batch.completed_at = datetime.utcnow()
        
        db.commit()
        
        return BulkProvisioningResult(
            success=len(errors) == 0,
            message=f"Provisioned {len(created_devices)} of {len(batch_data.devices)} devices",
            batch=db_batch,
            created_devices=created_devices,
            errors=errors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk provisioning failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk provisioning failed: {str(e)}"
        )

@app.get("/api/admin/provisioning/batches", response_model=List[ProvisioningBatchResponse])
async def list_provisioning_batches(
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """List all provisioning batches (Admin only)"""
    user_roles = current_user.get("realm_access", {}).get("roles", [])
    if "admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    batches = db.query(ProvisioningBatch).order_by(ProvisioningBatch.created_at.desc()).all()
    return batches

@app.get("/api/admin/provisioning/batches/{batch_id}", response_model=ProvisioningBatchResponse)
async def get_provisioning_batch(
    batch_id: str,
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get provisioning batch details (Admin only)"""
    user_roles = current_user.get("realm_access", {}).get("roles", [])
    if "admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    batch = db.query(ProvisioningBatch).filter(
        ProvisioningBatch.batch_id == batch_id
    ).first()
    
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )
    
    return batch

@app.get("/api/admin/provisioning/batches/{batch_id}/devices", response_model=List[DeviceRegistrationResponse])
async def get_batch_devices(
    batch_id: str,
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get devices in a provisioning batch (Admin only)"""
    user_roles = current_user.get("realm_access", {}).get("roles", [])
    if "admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    devices = db.query(DeviceRegistration).filter(
        DeviceRegistration.batch_id == batch_id
    ).all()
    
    return devices

@app.get("/api/admin/provisioning/qr/{device_id}")
async def get_device_qr_code(
    device_id: str,
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get QR code for a specific device (Admin only)"""
    user_roles = current_user.get("realm_access", {}).get("roles", [])
    if "admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    device = db.query(DeviceRegistration).filter(
        DeviceRegistration.device_id == device_id
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    if not device.qr_code_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="QR code not generated for this device"
        )
    
    return {
        "device_id": device.device_id,
        "device_name": device.device_name,
        "qr_code_url": device.qr_code_url,
        "qr_code_data": device.qr_code_data
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3002)
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from keycloak import KeycloakOpenID
import os
import jwt
from typing import Optional, Dict, Any, List
import redis
import json
import logging
from datetime import datetime
import hashlib
import aiofiles
from pathlib import Path
import paho.mqtt.client as mqtt

# Import our new modules
from firmware_manager import FirmwareManager
from models import DeviceType, FirmwareStatus, UpdateStatus, RolloutStrategy
from schemas import (
    FirmwareUploadSchema, FirmwareMetadataSchema, FirmwareUpdateSchema,
    FirmwareRolloutCreateSchema, FirmwareRolloutSchema, FirmwareRolloutUpdateSchema,
    DeviceUpdateStatusSchema, BulkUpdateRequestSchema, CompatibilityCheckSchema,
    CompatibilityResultSchema, FirmwareStatsSchema, UpdateStatsSchema,
    RolloutStatsSchema, FirmwareSearchSchema, DeviceUpdateRequestSchema,
    DeviceRollbackRequestSchema, FirmwareDiffSchema, FirmwareDiffResultSchema
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Home Automation OTA Service", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3002", "http://localhost:3003"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "home-automation")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "home-automation-backend")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6380")
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1884"))

# Firmware storage
FIRMWARE_DIR = Path("firmware_storage")
FIRMWARE_DIR.mkdir(exist_ok=True)

# Initialize Keycloak client
keycloak_openid = KeycloakOpenID(
    server_url=KEYCLOAK_URL,
    client_id=KEYCLOAK_CLIENT_ID,
    realm_name=KEYCLOAK_REALM,
)

# Redis client for caching
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# MQTT client for device communication
mqtt_client = mqtt.Client()

# Security scheme
security = HTTPBearer()

# Firmware database (in production, use proper database)
firmware_db = {}
device_firmware_status = {}

class FirmwareInfo:
    def __init__(self, filename: str, version: str, device_type: str, 
                 description: str = "", checksum: str = ""):
        self.filename = filename
        self.version = version
        self.device_type = device_type
        self.description = description
        self.checksum = checksum
        self.upload_time = datetime.utcnow()
        self.file_size = 0

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

def calculate_file_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def setup_mqtt():
    """Setup MQTT client for device communication"""
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connected to MQTT broker")
            # Subscribe to device status updates
            client.subscribe("homeautomation/devices/+/status")
        else:
            logger.error(f"Failed to connect to MQTT broker: {rc}")
    
    def on_message(client, userdata, msg):
        try:
            topic_parts = msg.topic.split('/')
            if len(topic_parts) >= 3:
                device_id = topic_parts[2]
                payload = json.loads(msg.payload.decode())
                
                # Update device firmware status
                if "firmware_version" in payload:
                    device_firmware_status[device_id] = {
                        "current_version": payload["firmware_version"],
                        "device_type": payload.get("device_type", "unknown"),
                        "last_seen": datetime.utcnow().isoformat(),
                        "online": payload.get("online", False)
                    }
                    
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    
    try:
        mqtt_client.connect(MQTT_HOST, MQTT_PORT, 60)
        mqtt_client.loop_start()
        logger.info("MQTT client started")
    except Exception as e:
        logger.error(f"Failed to connect to MQTT: {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize OTA service on startup"""
    logger.info("Starting OTA Service")
    setup_mqtt()
    
    # Load existing firmware from storage
    for firmware_file in FIRMWARE_DIR.glob("*.bin"):
        # Load firmware metadata if exists
        metadata_file = firmware_file.with_suffix(".json")
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    firmware_info = FirmwareInfo(
                        filename=firmware_file.name,
                        version=metadata.get("version", "unknown"),
                        device_type=metadata.get("device_type", "unknown"),
                        description=metadata.get("description", ""),
                        checksum=metadata.get("checksum", "")
                    )
                    firmware_info.file_size = firmware_file.stat().st_size
                    firmware_db[firmware_file.name] = firmware_info
                    logger.info(f"Loaded firmware: {firmware_file.name}")
            except Exception as e:
                logger.error(f"Error loading firmware metadata: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    logger.info("OTA Service stopped")

# Mount static files for firmware downloads
app.mount("/firmware", StaticFiles(directory=str(FIRMWARE_DIR)), name="firmware")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ota-service"}

@app.post("/api/firmware/upload")
async def upload_firmware(
    file: UploadFile = File(...),
    version: str = Form(...),
    device_type: str = Form(...),
    description: str = Form(""),
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Upload new firmware (admin only)"""
    # Check if user has admin role
    roles = current_user.get("realm_access", {}).get("roles", [])
    if "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        # Validate file type
        if not file.filename.endswith('.bin'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only .bin files are allowed"
            )
        
        # Create unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{device_type}_{version}_{timestamp}.bin"
        file_path = FIRMWARE_DIR / filename
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Calculate checksum
        checksum = calculate_file_checksum(file_path)
        
        # Create firmware info
        firmware_info = FirmwareInfo(
            filename=filename,
            version=version,
            device_type=device_type,
            description=description,
            checksum=checksum
        )
        firmware_info.file_size = file_path.stat().st_size
        
        # Store in database
        firmware_db[filename] = firmware_info
        
        # Save metadata
        metadata = {
            "version": version,
            "device_type": device_type,
            "description": description,
            "checksum": checksum,
            "upload_time": firmware_info.upload_time.isoformat(),
            "file_size": firmware_info.file_size
        }
        
        metadata_file = file_path.with_suffix(".json")
        async with aiofiles.open(metadata_file, 'w') as f:
            await f.write(json.dumps(metadata, indent=2))
        
        logger.info(f"Firmware uploaded: {filename}")
        
        return {
            "success": True,
            "filename": filename,
            "version": version,
            "device_type": device_type,
            "checksum": checksum,
            "size": firmware_info.file_size,
            "download_url": f"/firmware/{filename}"
        }
        
    except Exception as e:
        logger.error(f"Error uploading firmware: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload firmware"
        )

@app.get("/api/firmware/list")
async def list_firmware(
    device_type: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """List available firmware"""
    firmware_list = []
    
    for filename, firmware_info in firmware_db.items():
        if device_type and firmware_info.device_type != device_type:
            continue
            
        firmware_list.append({
            "filename": firmware_info.filename,
            "version": firmware_info.version,
            "device_type": firmware_info.device_type,
            "description": firmware_info.description,
            "checksum": firmware_info.checksum,
            "upload_time": firmware_info.upload_time.isoformat(),
            "file_size": firmware_info.file_size,
            "download_url": f"/firmware/{firmware_info.filename}"
        })
    
    # Sort by upload time (newest first)
    firmware_list.sort(key=lambda x: x["upload_time"], reverse=True)
    
    return {"firmware": firmware_list}

@app.get("/api/firmware/{filename}")
async def get_firmware_info(
    filename: str,
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Get specific firmware information"""
    if filename not in firmware_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Firmware not found"
        )
    
    firmware_info = firmware_db[filename]
    
    return {
        "filename": firmware_info.filename,
        "version": firmware_info.version,
        "device_type": firmware_info.device_type,
        "description": firmware_info.description,
        "checksum": firmware_info.checksum,
        "upload_time": firmware_info.upload_time.isoformat(),
        "file_size": firmware_info.file_size,
        "download_url": f"/firmware/{firmware_info.filename}"
    }

@app.delete("/api/firmware/{filename}")
async def delete_firmware(
    filename: str,
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Delete firmware (admin only)"""
    # Check if user has admin role
    roles = current_user.get("realm_access", {}).get("roles", [])
    if "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    if filename not in firmware_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Firmware not found"
        )
    
    try:
        # Delete files
        file_path = FIRMWARE_DIR / filename
        metadata_file = file_path.with_suffix(".json")
        
        if file_path.exists():
            file_path.unlink()
        if metadata_file.exists():
            metadata_file.unlink()
        
        # Remove from database
        del firmware_db[filename]
        
        logger.info(f"Firmware deleted: {filename}")
        
        return {"success": True, "message": "Firmware deleted"}
        
    except Exception as e:
        logger.error(f"Error deleting firmware: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete firmware"
        )

@app.post("/api/devices/{device_id}/update")
async def trigger_device_update(
    device_id: str,
    update_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Trigger OTA update for a specific device"""
    try:
        firmware_filename = update_data.get("firmware_filename")
        force_update = update_data.get("force_update", False)
        
        if not firmware_filename or firmware_filename not in firmware_db:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Valid firmware filename required"
            )
        
        firmware_info = firmware_db[firmware_filename]
        
        # Check if device is online
        device_status = device_firmware_status.get(device_id)
        if not device_status or not device_status.get("online", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Device is offline"
            )
        
        # Check if update is needed
        current_version = device_status.get("current_version", "unknown")
        if not force_update and current_version == firmware_info.version:
            return {
                "success": True,
                "message": "Device already has the latest firmware",
                "current_version": current_version,
                "target_version": firmware_info.version
            }
        
        # Send OTA command via MQTT
        topic = f"homeautomation/devices/{device_id}/ota"
        message = {
            "action": "update",
            "url": f"http://localhost:3004/firmware/{firmware_filename}",
            "version": firmware_info.version,
            "checksum": firmware_info.checksum,
            "size": firmware_info.file_size
        }
        
        mqtt_client.publish(topic, json.dumps(message))
        
        logger.info(f"OTA update triggered for device {device_id}: {firmware_filename}")
        
        return {
            "success": True,
            "message": "OTA update triggered",
            "device_id": device_id,
            "current_version": current_version,
            "target_version": firmware_info.version,
            "firmware_filename": firmware_filename
        }
        
    except Exception as e:
        logger.error(f"Error triggering OTA update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger OTA update"
        )

@app.get("/api/devices/status")
async def get_devices_status(
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Get firmware status of all devices"""
    return {"devices": device_firmware_status}

@app.get("/api/devices/{device_id}/status")
async def get_device_status(
    device_id: str,
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Get firmware status of a specific device"""
    if device_id not in device_firmware_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return device_firmware_status[device_id]

@app.post("/api/devices/{device_id}/check-update")
async def check_device_update(
    device_id: str,
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Check if device needs firmware update"""
    device_status = device_firmware_status.get(device_id)
    if not device_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    device_type = device_status.get("device_type", "unknown")
    current_version = device_status.get("current_version", "unknown")
    
    # Find latest firmware for device type
    latest_firmware = None
    for firmware_info in firmware_db.values():
        if firmware_info.device_type == device_type:
            if not latest_firmware or firmware_info.upload_time > latest_firmware.upload_time:
                latest_firmware = firmware_info
    
    if not latest_firmware:
        return {
            "update_available": False,
            "message": "No firmware available for this device type",
            "current_version": current_version
        }
    
    update_available = current_version != latest_firmware.version
    
    return {
        "update_available": update_available,
        "current_version": current_version,
        "latest_version": latest_firmware.version,
        "latest_firmware": {
            "filename": latest_firmware.filename,
            "description": latest_firmware.description,
            "upload_time": latest_firmware.upload_time.isoformat()
        } if update_available else None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3004)